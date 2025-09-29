from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
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
frontend_port = os.getenv("FRONTEND_PORT", "8000")
CORS(
    app,
    origins=[f"http://localhost:{frontend_port}", f"http://127.0.0.1:{frontend_port}"],
)

# Configure OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key-here"))

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
        system_message = """You are an expert QA testing agent. Your task is to generate detailed test cases for the provided test scenarios.

CRITICAL: You must respond with ONLY valid JSON. Do not include any explanatory text, comments, or formatting outside of the JSON structure. Start your response directly with '{' and end with '}'.

Required JSON format:
{
    "scenarios": [
        {
            "id": "SC001",
            "title": "Scenario Title",
            "description": "Brief description of the scenario",
            "preconditions": ["Precondition 1", "Precondition 2"],
            "test_cases": [
                {
                    "id": "TC001",
                    "title": "Test Case Title",
                    "description": "Detailed test case description",
                    "steps": ["Step 1", "Step 2", "Step 3"],
                    "expected_result": "Expected outcome",
                    "priority": "High/Medium/Low",
                    "test_data": "Any required test data"
                }
            ]
        }
    ]
}

For each scenario provided, generate comprehensive test cases covering:
- Functional testing
- UI/UX testing
- Edge cases
- Error handling
- Data validation
- User workflows

Remember: Return ONLY the JSON object, no additional text."""

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
        # Prepare the system message based on scenarios_only flag
        if scenarios_only:
            system_message = """You are an expert QA testing agent. Your task is to analyze the given input (either a description or an image of a software feature/interface) and generate the MAXIMUM number of comprehensive test scenarios with maximum test cases for each scenario.

CRITICAL: You must respond with ONLY valid JSON. Do not include any explanatory text, comments, or formatting outside of the JSON structure. Start your response directly with '{' and end with '}'.

Required JSON format:
{
    "scenarios": [
        {
            "id": "SC001",
            "title": "Scenario Title",
            "description": "Brief description of what this scenario tests",
            "preconditions": ["Precondition 1", "Precondition 2"],
            "test_cases": [
                {
                    "id": "TC001",
                    "title": "Test Case Title",
                    "description": "Detailed test case description",
                    "steps": ["Step 1", "Step 2", "Step 3"],
                    "expected_result": "Expected outcome",
                    "priority": "High/Medium/Low",
                    "test_data": "Any required test data"
                },
                {
                    "id": "TC002",
                    "title": "Another Test Case Title",
                    "description": "Another detailed test case description",
                    "steps": ["Step 1", "Step 2", "Step 3"],
                    "expected_result": "Expected outcome",
                    "priority": "High/Medium/Low",
                    "test_data": "Any required test data"
                }
            ]
        }
    ]
}

Generate the MAXIMUM number of distinct test scenarios possible for comprehensive coverage. For each scenario, generate the MAXIMUM number of comprehensive test cases covering:
- Functional testing (positive and negative cases)
- UI/UX testing (interactions, validations, error states)
- Edge cases and boundary conditions
- Error handling and exception scenarios
- Data validation (valid/invalid inputs, formats, ranges)
- User workflow scenarios (happy paths, alternative paths)
- Performance and security considerations
- Cross-browser/device compatibility
- Accessibility requirements
- Integration with other features
- API testing scenarios
- Database interaction scenarios
- Third-party integration scenarios
- Mobile responsiveness scenarios
- Network connectivity scenarios
- Authentication and authorization scenarios
- Data persistence scenarios
- Multi-user concurrency scenarios

Generate as many UNIQUE and DISTINCT scenarios as possible. Each scenario should have at least 8-15 detailed test cases. Aim for 10-20+ total scenarios depending on the complexity of the input.

Remember: Return ONLY the JSON object, no additional text."""
        else:
            system_message = """You are an expert QA testing agent. Your task is to analyze the given input (either a description or an image of a software feature/interface) and generate comprehensive test scenarios and test cases.

CRITICAL: You must respond with ONLY valid JSON. Do not include any explanatory text, comments, or formatting outside of the JSON structure. Start your response directly with '{' and end with '}'.

Required JSON format:
{
    "scenarios": [
        {
            "id": "SC001",
            "title": "Scenario Title",
            "description": "Brief description of the scenario",
            "preconditions": ["Precondition 1", "Precondition 2"],
            "test_cases": [
                {
                    "id": "TC001",
                    "title": "Test Case Title",
                    "description": "Detailed test case description",
                    "steps": ["Step 1", "Step 2", "Step 3"],
                    "expected_result": "Expected outcome",
                    "priority": "High/Medium/Low",
                    "test_data": "Any required test data"
                }
            ]
        }
    ]
}

Focus on:
- Functional testing
- UI/UX testing
- Edge cases
- Error handling
- Data validation
- User workflows
- Performance considerations
- Security aspects

Remember: Return ONLY the JSON object, no additional text."""

        # Build user message
        if description:
            user_message = (
                "Please analyze this software feature description and generate test scenarios "
                "and test cases:\n\n" + description
            )
        else:
            user_message = "Please analyze the input and generate comprehensive test scenarios and test cases."

        content = None  # Response content

        if image_path:
            # Image analysis via GPT-4o Vision
            base64_image = encode_image_to_base64(image_path)
            response = client.chat.completions.create(
                model=OPENAI_MODEL_VISION,
                messages=[
                    {"role": "system", "content": system_message},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_message},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    },
                ],
                max_tokens=8000,
                temperature=0.1,
            )
            content = response.choices[0].message.content
        else:
            # Text-only analysis (description path)
            response = client.chat.completions.create(
                model=OPENAI_MODEL_TEXT,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=8000,
                temperature=0.1,
            )
            content = response.choices[0].message.content

        # Parse the JSON response
        try:
            # First try to parse the entire response as JSON
            result = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            print(f"Direct JSON parsing failed: {e}")
            if content:
                print(f"Raw content preview: {content[:500]}...")
            else:
                print("No content received from API")

            # If direct parsing fails, try to extract JSON from the response
            import re

            # Look for JSON-like content between curly braces
            if content:
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
            else:
                json_match = None
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
                    scenarios = json.loads(array_match.group())
                    print("Successfully parsed JSON array")
                    return {"scenarios": scenarios}
                except json.JSONDecodeError as e3:
                    print(f"Array JSON parsing failed: {e3}")

            # If all parsing attempts fail, return error with raw response
            print("All JSON parsing attempts failed")
            raw_response = content[:1000] if content else "No response received"
            return {
                "error": "Failed to parse AI response - invalid JSON format",
                "raw_response": raw_response,  # Limit response size for error display
                "scenarios": [],
            }

    except Exception as e:
        return {"error": f"Error generating test cases: {str(e)}", "scenarios": []}


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
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

        # Generate test scenarios only
        result = generate_test_scenarios_and_cases(
            description=data.get("description"), image_path=data.get("image_path"), scenarios_only=True
        )

        # Clean up temporary image file if it exists
        if "image_path" in data and os.path.exists(data["image_path"]):
            os.unlink(data["image_path"])

        return jsonify(result)

    except Exception as e:
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
    # Create necessary directories if they don't exist
    os.makedirs("../frontend/static", exist_ok=True)
    os.makedirs("../frontend/templates", exist_ok=True)

    # Get environment settings
    env = os.getenv("ENV", "development")
    is_production = env == "production"

    # Get server configuration from environment
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 5000))
    debug = (
        os.getenv("FLASK_DEBUG", "False" if is_production else "True").lower() == "true"
    )

    if is_production:
        print("🏭 Starting PRODUCTION server...")
        print(f"🔒 Debug mode: DISABLED")
        print(f"🌐 Host: {host}:{port}")
        print("⚠️  Using production WSGI server recommended (gunicorn, uwsgi)")
        print("   Example: gunicorn --bind 0.0.0.0:8000 backend.app:app")
    else:
        print("🛠️  Starting DEVELOPMENT server...")
        print(f"🔧 Debug mode: ENABLED")
        print(f"🌐 Host: {host}:{port}")

    app.run(debug=debug, host=host, port=port)


if __name__ == "__main__":
    main()
