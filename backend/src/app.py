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
import logging
from website_analyzer import analyze_website
from api_test_generator import generate_api_tests_from_file

# Import configuration
from config import config

app = Flask(__name__)

# Apply configuration to Flask app
app.config.update(config.get_flask_config())

# Configure logging
if not app.config.get("DEBUG"):
    app.logger.setLevel(logging.ERROR)
else:
    app.logger.setLevel(logging.INFO)
app.logger.info("Flask app initialized with logging.")

# Configure CORS with environment-specific origins
CORS(app, origins=config.get_cors_origins())

# Configure OpenAI
client = openai.OpenAI(api_key=config.openai_api_key)

# Configure LLM Models
OPENAI_MODEL_TEXT = config.openai_model_text
OPENAI_MODEL_VISION = config.openai_model_vision
OPENAI_MODEL_WEBSITE = config.openai_model_website
OPENAI_MODEL_API = config.openai_model_api

# Configure upload settings
ALLOWED_EXTENSIONS = config.allowed_extensions


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def encode_image_to_base64(image_path):
    """Convert image to base64 string for OpenAI API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generate_test_cases_for_scenarios(scenarios):
    """
    Generate detailed test cases for selected scenarios using OpenAI
    Process each scenario individually in parallel for maximum speed
    """
    try:
        if not scenarios:
            return {"scenarios": []}

        app.logger.info(f"Processing {len(scenarios)} scenarios individually in parallel")

        # Process each scenario individually in parallel
        import concurrent.futures
        import threading

        def process_single_scenario(scenario):
            """Process a single scenario and return the result"""
            thread_id = threading.current_thread().ident
            scenario_id = scenario.get('id', 'unknown')
            app.logger.info(f"Thread {thread_id}: Processing scenario {scenario_id}")

            # Call the batch function with a single scenario
            result = generate_test_cases_for_batch([scenario])

            if "scenarios" in result and result["scenarios"]:
                app.logger.info(f"Thread {thread_id}: Successfully processed scenario {scenario_id}")
                return result["scenarios"][0]  # Return the single scenario result
            else:
                app.logger.error(f"Thread {thread_id}: Failed to process scenario {scenario_id}: {result.get('error', 'Unknown error')}")
                return None

        # Process all scenarios in parallel using ThreadPoolExecutor
        # Use up to 5 concurrent threads for good performance without overwhelming the API
        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all scenarios for parallel execution
            future_to_scenario = {executor.submit(process_single_scenario, scenario): scenario for scenario in scenarios}

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_scenario):
                scenario_result = future.result()
                if scenario_result:
                    all_results.append(scenario_result)

        # Sort results back to original order
        if all_results:
            all_results.sort(key=lambda x: x.get('id', ''))

        app.logger.info(f"Successfully processed {len(all_results)} out of {len(scenarios)} scenarios in parallel")
        return {"scenarios": all_results}

    except Exception as e:
        app.logger.exception("An error occurred in generate_test_cases_for_scenarios")
        return {"error": str(e)}


def generate_test_cases_for_batch(scenarios):
    """
    Generate detailed test cases for a batch of scenarios using OpenAI
    """
    try:
        # Prepare the system message
        system_message = """You are an expert QA testing agent. Your task is to generate detailed test cases for the provided test scenarios.\n\nCRITICAL: You must respond with ONLY valid JSON. Do not include any explanatory text, comments, or formatting outside of the JSON structure. Start your response directly with '{' and end with '}'.\n\nRequired JSON format:\n{\n    "scenarios": [\n        {\n            "id": "SC001",\n            "title": "Scenario Title",\n            "description": "Brief description of the scenario",\n            "preconditions": ["Precondition 1", "Precondition 2"],\n            "estimated_test_cases": 10,\n            "test_cases": [\n                {\n                    "id": "TC001",\n                    "title": "Test Case Title",\n                    "description": "Detailed test case description",\n                    "steps": ["Step 1", "Step 2", "Step 3"],\n                    "expected_result": "Expected outcome",\n                    "priority": "High/Medium/Low",\n                    "test_data": "Any required test data"\n                }\n            ]\n        }\n    ]\n}\n\nCRITICAL REQUIREMENT: For EACH scenario, if it has an 'estimated_test_cases' field, you MUST generate EXACTLY that many test cases. If no estimate is provided, generate 8-12 detailed test cases.\n\nEach test case must cover:\n- Functional testing (happy path, alternative flows, negative scenarios)\n- UI/UX testing (layout, accessibility, user experience, visual feedback)\n- Edge cases (boundary values, empty states, maximum limits, special characters)\n- Error handling (invalid inputs, system failures, network errors, timeouts)\n- Data validation (format checks, required fields, data types, constraints)\n- Security testing (authentication, authorization, input sanitization, XSS, SQL injection)\n- Performance aspects (response times, resource usage)\n- Integration scenarios (external dependencies, API calls)\n- User workflows (complete end-to-end flows, multi-step processes)\n\nGenerate MAXIMUM test cases (8-12 per scenario or match estimated_test_cases) for thorough coverage.\nRemember: Return ONLY the JSON object, no additional text."""

        # Count scenarios and calculate expected test case counts
        num_scenarios = len(scenarios) if isinstance(scenarios, list) else 0
        total_estimated = 0
        for scenario in scenarios:
            if isinstance(scenario, dict) and 'estimated_test_cases' in scenario:
                total_estimated += scenario['estimated_test_cases']

        if total_estimated > 0:
            user_message = f"Please generate detailed test cases for these {num_scenarios} scenarios.\n\nCRITICAL REQUIREMENT: You must generate EXACTLY {total_estimated} test cases total, matching the estimated_test_cases count for each scenario.\n\nFor each scenario:\n- If it has 'estimated_test_cases': 10, generate EXACTLY 10 test cases\n- If it has 'estimated_test_cases': 8, generate EXACTLY 8 test cases\n- This is mandatory for test planning accuracy.\n\nScenarios:\n{json.dumps(scenarios, indent=2)}"
        else:
            user_message = f"Please generate detailed test cases for these {num_scenarios} scenarios.\n\nCRITICAL: Generate 8-12 detailed test cases for EACH scenario below. Ensure comprehensive coverage across all testing types.\n\nScenarios:\n{json.dumps(scenarios, indent=2)}"

        # Make API call with increased token limit for batch processing
        response = client.chat.completions.create(
            model=OPENAI_MODEL_TEXT,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=7000,  # Further reduced to stay within 8192 token limit
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            result = json.loads(content)
            app.logger.info("Successfully parsed JSON response for batch")
            return result
        except json.JSONDecodeError as e:
            app.logger.error(f"Direct JSON parsing failed: {e}")

            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    app.logger.info("Successfully parsed JSON from regex match")
                    return result
                except json.JSONDecodeError as e2:
                    app.logger.error(f"Regex JSON parsing failed: {e2}")

            # Try to find and parse JSON array if it exists
            if content:
                array_match = re.search(r"\[.*\]", content, re.DOTALL)
            else:
                array_match = None
            if array_match:
                try:
                    scenarios_array = json.loads(array_match.group())
                    result = {"scenarios": scenarios_array}
                    app.logger.info("Successfully parsed scenarios array")
                    return result
                except json.JSONDecodeError as e3:
                    app.logger.error(f"Array JSON parsing failed: {e3}")

            # If all parsing fails, return error
            return {"error": f"Failed to parse AI response as JSON: {content[:500]}"}

    except Exception as e:
        app.logger.exception("An error occurred in generate_test_cases_for_batch")
        return {"error": str(e)}


def generate_test_scenarios_and_cases(description=None, image_path=None, scenarios_only=False):
    """
    Generate test scenarios and test cases using OpenAI
    If scenarios_only is True, return only scenarios without detailed test cases
    """
    try:
        app.logger.info(f"generate_test_scenarios_and_cases called with description={description is not None}, image_path={image_path is not None}, scenarios_only={scenarios_only}")
        
        # Prepare the system message
        system_message = """You are an expert QA testing agent. Your task is to generate comprehensive test scenarios from a given description or image.\n\nCRITICAL: You must respond with ONLY valid JSON. Do not include any explanatory text, comments, or formatting outside of the JSON structure. Start your response directly with '{' and end with '}'.\n\nRequired JSON format:\n{\n    "scenarios": [\n        {\n            "id": "SC001",\n            "title": "Scenario Title",\n            "description": "Brief description of the scenario",\n            "preconditions": ["Precondition 1", "Precondition 2"],\n            "estimated_test_cases": 8,\n            "test_cases": []\n        }\n    ]\n}\n\nIMPORTANT: Generate 12-15 comprehensive test scenarios covering MAXIMUM aspects.\n- If `scenarios_only` is true, return scenarios with EMPTY test_cases arrays [] and include estimated_test_cases count.\n- If `scenarios_only` is false, generate detailed test cases matching the estimated_test_cases count for each scenario.\n\nYou MUST cover ALL of these:\n- Functional testing (positive flows, core features, all user actions)\n- UI/UX testing (layout, responsiveness, accessibility, usability)\n- Edge cases (boundary values, empty states, maximum limits, unusual inputs)\n- Error handling (invalid inputs, network failures, timeouts, system errors)\n- Data validation (format checks, required fields, data types, constraints)\n- Security testing (authentication, authorization, XSS, SQL injection, CSRF)\n- Performance testing (load times, concurrent users, stress testing)\n- Integration testing (third-party services, APIs, external dependencies)\n- Compatibility testing (browsers, devices, screen sizes)\n- User workflows (complete user journeys, multi-step processes)\n\nGenerate MAXIMUM scenarios (12-15) for thorough test coverage.\nRemember: Return ONLY the JSON object, no additional text."""

        # Prepare user message
        user_message_content = []
        model = OPENAI_MODEL_TEXT

        if description:
            if scenarios_only:
                user_message_content.append({"type": "text", "text": f"Generate ONLY test scenarios (no test cases) for this feature:\n\n{description}\n\nIMPORTANT: Return scenarios with EMPTY test_cases arrays []"})
            else:
                user_message_content.append({"type": "text", "text": f"Generate test scenarios for this feature:\n\n{description}"})

        if image_path:
            base64_image = encode_image_to_base64(image_path)
            if scenarios_only:
                user_message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })
                user_message_content.append({"type": "text", "text": "\n\nIMPORTANT: Return scenarios with EMPTY test_cases arrays []"})
            else:
                user_message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })
            model = OPENAI_MODEL_VISION

        if not scenarios_only:
            user_message_content.append({"type": "text", "text": "\n\nCRITICAL: Generate 8-12 detailed test cases for EACH scenario. If a scenario has an 'estimated_test_cases' field, generate EXACTLY that many test cases."})

        # Make API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message_content}
            ],
            max_tokens=6000,
            temperature=0.3,
            timeout=300.0,
        )

        content = response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            result = json.loads(content)
            app.logger.info("Successfully parsed JSON response")
            return result
        except json.JSONDecodeError as e:
            app.logger.error(f"Direct JSON parsing failed: {e}")

            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    app.logger.info("Successfully parsed JSON from regex match")
                    return result
                except json.JSONDecodeError as e2:
                    app.logger.error(f"Regex JSON parsing failed: {e2}")

            # If all parsing fails, return error
            return {"error": f"Failed to parse AI response as JSON: {content[:500]}"}

    except Exception as e:
        app.logger.exception("Error generating test cases")
        return {"error": f"Error generating test cases: {str(e)}", "scenarios": []}


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        app.logger.info("Analyze endpoint called")
        data = {}

        # Check if description is provided
        if "description" in request.form and request.form["description"].strip():
            description = request.form["description"].strip()
            app.logger.info(f"Description received: {description[:100]}...")
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

        app.logger.info("About to call generate_test_scenarios_and_cases")
        # Generate test scenarios only
        result = generate_test_scenarios_and_cases(
            description=data.get("description"), image_path=data.get("image_path"), scenarios_only=True
        )
        app.logger.info(f"Function returned result with keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        if 'error' in result and result['error']:
            app.logger.error(f"Error in result: {result['error']}")
        if 'scenarios' in result:
            app.logger.info(f"Number of scenarios: {len(result['scenarios'])}")
            
            # CRITICAL: Force test_cases to be empty for scenarios_only mode
            for scenario in result['scenarios']:
                if isinstance(scenario, dict):
                    scenario['test_cases'] = []
                    app.logger.debug(f"Cleared test_cases for scenario: {scenario.get('id', 'unknown')}")

        # Clean up temporary image file if it exists
        if "image_path" in data and os.path.exists(data["image_path"]):
            os.unlink(data["image_path"])

        return jsonify(result)

    except Exception as e:
        app.logger.exception("Exception in analyze endpoint")
        return jsonify({"error": str(e)}), 500


@app.route("/generate_test_cases", methods=["POST"])
def generate_test_cases():
    """Generate detailed test cases for selected scenarios"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        json_data = request.get_json()
        if "scenarios" not in json_data:
            return jsonify({"error": "Missing 'scenarios' field in request"}), 400
        
        scenarios = json_data["scenarios"]
        if not scenarios or len(scenarios) == 0:
            return jsonify({"error": "No scenarios provided"}), 400
        
        app.logger.info(f"Generating test cases for {len(scenarios)} selected scenarios")
        
        # Generate test cases for selected scenarios
        result = generate_test_cases_for_scenarios(scenarios)
        result["generated_at"] = datetime.now().isoformat()
        result["input_type"] = "selected_scenarios"
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.exception("Exception in generate_test_cases endpoint")
        return jsonify({"error": str(e)}), 500


@app.route("/generate", methods=["POST"])
def generate():
    try:
        # Check if this is JSON data with scenarios
        if request.is_json:
            json_data = request.get_json()
            if "scenarios" in json_data:
                # Redirect to the dedicated endpoint
                return generate_test_cases()
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
        app.logger.exception("Exception in /generate endpoint")
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
        app.logger.exception("Exception in /analyze_website endpoint")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/analyze_api", methods=["POST"])
def analyze_api():
    """Generate API test scenarios only (first step)"""
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
            # Import the new functions
            from api_test_generator import generate_api_scenarios, detect_api_document_type, parse_swagger_spec, parse_postman_collection
            
            # Read and parse the JSON file
            with open(temp_api_path, 'r', encoding='utf-8') as f:
                api_data = json.load(f)

            # Detect document type
            document_type = detect_api_document_type(api_data)

            if document_type == "unknown":
                return jsonify({"error": "Unable to detect API document type. Please upload a valid Swagger/OpenAPI specification or Postman collection."}), 400

            # Parse the document based on type
            if document_type == "swagger":
                parsed_data = parse_swagger_spec(api_data)
            elif document_type == "postman":
                parsed_data = parse_postman_collection(api_data)
            else:
                return jsonify({"error": "Unsupported document type"}), 400

            # Generate scenarios only
            scenarios = generate_api_scenarios(parsed_data, document_type)

            # Prepare result
            result = {
                "document_type": document_type,
                "api_info": {
                    "title": parsed_data.get("title", ""),
                    "description": parsed_data.get("description", ""),
                    "endpoints_count": len(parsed_data.get("endpoints", [])),
                    "parsed_at": datetime.now().isoformat()
                },
                "scenarios": scenarios,
                "generated_at": datetime.now().isoformat(),
                "input_type": f"api_document_{document_type}",
                "workflow_step": "scenarios_only"
            }

            return jsonify(result)

        finally:
            # Clean up temporary file
            if os.path.exists(temp_api_path):
                os.unlink(temp_api_path)

    except Exception as e:
        app.logger.exception("Exception in analyze_api endpoint")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/generate_api_test_cases", methods=["POST"])
def generate_api_test_cases_endpoint():
    """Generate detailed API test cases for selected scenarios (second step)"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        json_data = request.get_json()
        
        if "scenarios" not in json_data:
            return jsonify({"error": "Missing 'scenarios' field in request"}), 400
        
        if "api_info" not in json_data:
            return jsonify({"error": "Missing 'api_info' field in request"}), 400
            
        scenarios = json_data["scenarios"]
        api_info = json_data["api_info"]
        
        if not scenarios or len(scenarios) == 0:
            return jsonify({"error": "No scenarios provided"}), 400
        
        app.logger.info(f"Generating detailed API test cases for {len(scenarios)} selected scenarios")
        
        # Import the new function
        from api_test_generator import generate_api_test_cases_for_scenarios
        
        # Create mock API data for context (in real implementation, you might store this)
        mock_api_data = {
            "title": api_info.get("title", "API"),
            "description": api_info.get("description", ""),
            "endpoints": []  # This would ideally be stored from the first step
        }
        
        document_type = json_data.get("document_type", "swagger")
        
        # Generate detailed test cases
        detailed_scenarios = generate_api_test_cases_for_scenarios(scenarios, mock_api_data, document_type)
        
        # Prepare result
        result = {
            "document_type": document_type,
            "api_info": api_info,
            "scenarios": detailed_scenarios,
            "generated_at": datetime.now().isoformat(),
            "input_type": f"selected_api_scenarios_{document_type}",
            "workflow_step": "detailed_test_cases"
        }
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.exception("Exception in generate_api_test_cases endpoint")
        return jsonify({"error": str(e)}), 500


@app.route("/generate_api_tests", methods=["POST"])
def generate_api_tests():
    """Legacy endpoint - generates both scenarios and test cases in one step"""
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
            # Generate API test cases (legacy behavior)
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
        app.logger.critical("❌ Error: BACKEND_PORT is not set in the .env file.")
        sys.exit(1)

    try:
        port = int(port_str)
    except ValueError:
        app.logger.critical(f"❌ Error: Invalid BACKEND_PORT '{port_str}'. Must be a number.")
        sys.exit(1)

    debug = (
        os.getenv("FLASK_DEBUG", "False" if is_production else "True").lower() == "true"
    )

    if is_production:
        app.logger.info("🏭 Starting PRODUCTION server...")
        app.logger.info(f"🔒 Debug mode: DISABLED")
        app.logger.info(f"🌐 Host: {host}:{port}")
        app.logger.warning("⚠️  Using production WSGI server recommended (gunicorn, uwsgi)")
        app.logger.warning("   Example: gunicorn --bind 0.0.0.0:8000 backend.src.app:app")
    else:
        app.logger.info("🛠️  Starting DEVELOPMENT server...")
        app.logger.info(f"🔧 Debug mode: ENABLED")
        app.logger.info(f"🌐 Host: {host}:{port}")

    app.run(debug=debug, host=host, port=port)


if __name__ == "__main__":
    main()