from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import sys
import tempfile
import base64
from PIL import Image
import io
import json
from datetime import datetime
from dotenv import load_dotenv
import requests
from urllib.parse import urlparse
from website_analyzer import analyze_website
from api_test_generator import generate_api_tests_from_file

# Load environment variables from root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)

# Configure CORS dynamically based on frontend port
frontend_port = os.getenv("FRONTEND_PORT")
if not frontend_port:
    print("❌ Error: FRONTEND_PORT is not set in the .env file.", file=sys.stderr)
    sys.exit(1)

CORS(
    app,
    origins=[f"http://localhost:{frontend_port}", f"http://127.0.0.1:{frontend_port}"],
)

# Configure OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure LLM Models
OPENAI_MODEL_TEXT = os.getenv("OPENAI_MODEL_TEXT", "gpt-4")
OPENAI_MODEL_VISION = os.getenv("OPENAI_MODEL_VISION", "gpt-4o")
OPENAI_MODEL_WEBSITE = os.getenv("OPENAI_MODEL_WEBSITE", "gpt-4")
OPENAI_MODEL_API = os.getenv("OPENAI_MODEL_API", "gpt-4")

# Configure upload settings
app.config["MAX_CONTENT_LENGTH"] = int(
    os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)
)  # Default 16MB
ALLOWED_EXTENSIONS = set(
    os.getenv("ALLOWED_EXTENSIONS", "png,jpg,jpeg,gif,bmp,webp").split(",")
)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def encode_image_to_base64(image_path):
    """Convert image to base64 string for OpenAI API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generate_test_cases_for_scenarios(scenarios):
    """
    Generate detailed test cases for selected scenarios using OpenAI
    """
    try:
        # Prepare the system message
        system_message = """You are an expert QA testing agent. Your task is to generate detailed test cases for the provided test scenarios.\n\nCRITICAL: You must respond with ONLY valid JSON. Do not include any explanatory text, comments, or formatting outside of the JSON structure. Start your response directly with '{' and end with '}'.\n\nRequired JSON format:\n{\n    "scenarios": [\n        {\n            "id": "SC001",\n            "title": "Scenario Title",\n            "description": "Brief description of the scenario",\n            "preconditions": ["Precondition 1", "Precondition 2"],\n            "test_cases": [\n                {\n                    "id": "TC001",\n                    "title": "Test Case Title",\n                    "description": "Detailed test case description",\n                    "steps": ["Step 1", "Step 2", "Step 3"],\n                    "expected_result": "Expected outcome",\n                    "priority": "High/Medium/Low",\n                    "test_data": "Any required test data"\n                }\n            ]\n        }\n    ]\n}\n\nFor each scenario provided, generate comprehensive test cases covering:\n- Functional testing\n- UI/UX testing\n- Edge cases\n- Error handling\n- Data validation\n- User workflows\n\nRemember: Return ONLY the JSON object, no additional text."""

        user_message = f"Please generate detailed test cases for these scenarios:\n\n{json.dumps(scenarios, indent=2)}"

        # Make API call
        response = client.chat.completions.create(
            model=OPENAI_MODEL_TEXT,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=4000,
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            result = json.loads(content)
            print("Successfully parsed JSON response")
            return result
        except json.JSONDecodeError as e:
            print(f"Direct JSON parsing failed: {e}")

            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    print("Successfully parsed JSON from regex match")
                    return result
                except json.JSONDecodeError as e2:
                    print(f"Regex JSON parsing failed: {e2}")

            # Try to find and parse JSON array if it exists
            if content:
                array_match = re.search(r"\[.*\]", content, re.DOTALL)
            else:
                array_match = None
            if array_match:
                try:
                    scenarios_array = json.loads(array_match.group())
                    result = {"scenarios": scenarios_array}
                    print("Successfully parsed scenarios array")
                    return result
                except json.JSONDecodeError as e3:
                    print(f"Array JSON parsing failed: {e3}")

            # If all parsing fails, return error
            return {"error": f"Failed to parse AI response as JSON: {content[:500]}"}

    except Exception as e:
        return {"error": str(e)}


def generate_test_scenarios_and_cases(description=None, image_path=None, scenarios_only=False):
    """
    Generate test scenarios and test cases using OpenAI
    If scenarios_only is True, return only scenarios without detailed test cases
    """
    try:
        print(f"generate_test_scenarios_and_cases called with description={description is not None}, image_path={image_path is not None}, scenarios_only={scenarios_only}")
        
        # Prepare the system message
        system_message = """You are an expert QA testing agent. Your task is to generate comprehensive test scenarios from a given description or image.\n\nCRITICAL: You must respond with ONLY valid JSON. Do not include any explanatory text, comments, or formatting outside of the JSON structure. Start your response directly with '{' and end with '}'.\n\nRequired JSON format:\n{\n    "scenarios": [\n        {\n            "id": "SC001",\n            "title": "Scenario Title",\n            "description": "Brief description of the scenario",\n            "preconditions": ["Precondition 1", "Precondition 2"],\n            "test_cases": []\n        }\n    ]\n}\n\nFor each feature or UI, generate a list of test scenarios.\n- If `scenarios_only` is true, return only the scenario title, description, and preconditions.\n- If `scenarios_only` is false, also generate detailed test cases for each scenario.\n\nFocus on:\n- Functional testing\n- UI/UX testing\n- Edge cases\n- Error handling\n- Data validation\n- User workflows\n\nRemember: Return ONLY the JSON object, no additional text."""

        # Prepare user message
        user_message_content = []
        model = OPENAI_MODEL_TEXT

        if description:
            user_message_content.append({"type": "text", "text": f"Generate test scenarios for this feature:\n\n{description}"})

        if image_path:
            base64_image = encode_image_to_base64(image_path)
            user_message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
            model = OPENAI_MODEL_VISION

        if not scenarios_only:
            user_message_content.append({"type": "text", "text": "\n\nPlease also generate detailed test cases for each scenario."})

        # Make API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message_content}
            ],
            max_tokens=4000,
            temperature=0.3,
            timeout=300.0,
        )

        content = response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            result = json.loads(content)
            print("Successfully parsed JSON response")
            return result
        except json.JSONDecodeError as e:
            print(f"Direct JSON parsing failed: {e}")

            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    print("Successfully parsed JSON from regex match")
                    return result
                except json.JSONDecodeError as e2:
                    print(f"Regex JSON parsing failed: {e2}")

            # If all parsing fails, return error
            return {"error": f"Failed to parse AI response as JSON: {content[:500]}"}

    except Exception as e:
        return {"error": f"Error generating test cases: {str(e)}", "scenarios": []}


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        print("Analyze endpoint called")
        data = {}

        # Check if description is provided
        if "description" in request.form and request.form["description"].strip():
            description = request.form["description"].strip()
            print(f"Description received: {description[:100]}...")
            data["description"] = description
        elif "image" in request.files and request.files["image"].filename:
            # Handle image upload
            image_file = request.files["image"]

            if image_file and allowed_file(image_file.filename):
                # Save image temporarily
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(image_file.filename)[1]
                ) as temp_file:
                    image_file.save(temp_file.name)
                    temp_image_path = temp_file.name

                data["image_path"] = temp_image_path
            else:
                return (
                    jsonify(
                        {
                            "error": "Invalid image file. Allowed formats: PNG, JPG, JPEG, GIF, BMP, WebP"
                        }
                    ),
                    400,
                )
        else:
            return (
                jsonify(
                    {"error": "Please provide either a description or upload an image"}
                ),
                400,
            )

        print("About to call generate_test_scenarios_and_cases")
        # Generate test scenarios only
        result = generate_test_scenarios_and_cases(
            description=data.get("description"), image_path=data.get("image_path"), scenarios_only=True
        )
        print(f"Function returned result with keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")

        # Clean up temporary image file if it exists
        if "image_path" in data and os.path.exists(data["image_path"]):
            os.unlink(data["image_path"])

        return jsonify(result)

    except Exception as e:
        print(f"Exception in analyze endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/generate", methods=["POST"])
def generate():
    try:
        # Check if this is JSON data with scenarios
        if request.is_json:
            json_data = request.get_json()
            if "scenarios" in json_data:
                # Generate test cases for selected scenarios
                scenarios = json_data["scenarios"]
                result = generate_test_cases_for_scenarios(scenarios)
                result["generated_at"] = datetime.now().isoformat()
                result["input_type"] = "selected_scenarios"
                return jsonify(result)
            else:
                return jsonify({"error": "Invalid JSON data. Expected 'scenarios' field"}), 400

        # Original form-based handling
        data = {}

        # Check if description is provided
        if "description" in request.form and request.form["description"].strip():
            description = request.form["description"].strip()
            data["description"] = description
        elif "image" in request.files and request.files["image"].filename:
            # Handle image upload
            image_file = request.files["image"]

            if image_file and allowed_file(image_file.filename):
                # Save image temporarily
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(image_file.filename)[1]
                ) as temp_file:
                    image_file.save(temp_file.name)
                    temp_image_path = temp_file.name

                data["image_path"] = temp_image_path
            else:
                return (
                    jsonify(
                        {
                            "error": "Invalid image file. Allowed formats: PNG, JPG, JPEG, GIF, BMP, WebP"
                        }
                    ),
                    400,
                )
        else:
            return (
                jsonify(
                    {"error": "Please provide either a description or upload an image"}
                ),
                400,
            )

        # Generate test scenarios and cases
        result = generate_test_scenarios_and_cases(
            description=data.get("description"), image_path=data.get("image_path")
        )

        # Clean up temporary image file if it exists
        if "image_path" in data and os.path.exists(data["image_path"]):
            os.unlink(data["image_path"])

        # Add metadata
        result["generated_at"] = datetime.now().isoformat()
        result["input_type"] = "description" if "description" in data else "image"

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}", "scenarios": []}), 500


@app.route("/analyze_website", methods=["POST"])
def analyze_website_endpoint():
    try:
        # Get URL from request
        if request.is_json:
            data = request.get_json()
            url = data.get("url", "").strip()
        else:
            url = request.form.get("url", "").strip()

        if not url:
            return jsonify({"error": "Please provide a website URL"}), 400

        # Analyze the website
        result = analyze_website(url)

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/generate_api_tests", methods=["POST"])
def generate_api_tests():
    try:
        # Check if API document file is provided
        if "api_file" not in request.files:
            return jsonify({"error": "Please upload an API document file (Swagger/OpenAPI JSON or Postman collection)"}), 400

        api_file = request.files["api_file"]

        if api_file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Check file extension
        if not api_file.filename.lower().endswith('.json'):
            return jsonify({"error": "Please upload a JSON file"}), 400

        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            api_file.save(temp_file.name)
            temp_api_path = temp_file.name

        try:
            # Generate API test cases
            result = generate_api_tests_from_file(temp_api_path)

            if "error" in result:
                return jsonify(result), 400

            return jsonify(result)

        finally:
            # Clean up temporary file
            if os.path.exists(temp_api_path):
                os.unlink(temp_api_path)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


def main():
    """Main entry point for the backend server"""
    # Get environment settings
    env = os.getenv("ENV", "development")
    is_production = env == "production"

    # Get server configuration from environment
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port_str = os.getenv("BACKEND_PORT")
    if not port_str:
        print("❌ Error: BACKEND_PORT is not set in the .env file.", file=sys.stderr)
        sys.exit(1)

    try:
        port = int(port_str)
    except ValueError:
        print(f"❌ Error: Invalid BACKEND_PORT '{port_str}'. Must be a number.", file=sys.stderr)
        sys.exit(1)

    debug = (
        os.getenv("FLASK_DEBUG", "False" if is_production else "True").lower() == "true"
    )

    if is_production:
        print("🏭 Starting PRODUCTION server...")
        print(f"🔒 Debug mode: DISABLED")
        print(f"🌐 Host: {host}:{port}")
        print("⚠️  Using production WSGI server recommended (gunicorn, uwsgi)")
        print("   Example: gunicorn --bind 0.0.0.0:8000 backend.src.app:app")
    else:
        print("🛠️  Starting DEVELOPMENT server...")
        print(f"🔧 Debug mode: ENABLED")
        print(f"🌐 Host: {host}:{port}")

    app.run(debug=debug, host=host, port=port)


if __name__ == "__main__":
    main()