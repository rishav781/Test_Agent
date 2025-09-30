"""
API Test Generator Module
Handles generation of test cases from Swagger/OpenAPI specifications and Postman collections.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Configure OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key-here"))

# Configure LLM Model
OPENAI_MODEL_API = os.getenv("OPENAI_MODEL_API", "gpt-4")


def detect_api_document_type(api_data: Dict[str, Any]) -> str:
    """
    Detect if the uploaded JSON is a Swagger/OpenAPI spec or Postman collection
    """
    # Check for Postman collection indicators
    if "info" in api_data and "name" in api_data.get("info", {}):
        if "item" in api_data:  # Postman collections have "item" array
            return "postman"
        elif "swagger" in api_data or "openapi" in api_data:
            return "swagger"

    # Check for OpenAPI/Swagger specific fields
    if "swagger" in api_data or "openapi" in api_data:
        return "swagger"

    # Check for Postman collection v2.1 structure
    if "item" in api_data and isinstance(api_data["item"], list):
        return "postman"

    return "unknown"


def parse_swagger_spec(swagger_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Swagger/OpenAPI specification and extract relevant information
    """
    parsed_data = {
        "title": swagger_data.get("info", {}).get("title", "API Specification"),
        "version": swagger_data.get("info", {}).get("version", "1.0.0"),
        "description": swagger_data.get("info", {}).get("description", ""),
        "host": swagger_data.get("host", ""),
        "base_path": swagger_data.get("basePath", ""),
        "schemes": swagger_data.get("schemes", ["https"]),
        "endpoints": []
    }

    # Extract paths and operations
    paths = swagger_data.get("paths", {})
    for path, methods in paths.items():
        for method, operation in methods.items():
            if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "operation_id": operation.get("operationId", ""),
                    "tags": operation.get("tags", []),
                    "parameters": operation.get("parameters", []),
                    "request_body": operation.get("requestBody", {}),
                    "responses": operation.get("responses", {})
                }
                parsed_data["endpoints"].append(endpoint)

    return parsed_data


def parse_postman_collection(postman_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Postman collection and extract relevant information
    """
    parsed_data = {
        "title": postman_data.get("info", {}).get("name", "Postman Collection"),
        "description": postman_data.get("info", {}).get("description", ""),
        "endpoints": []
    }

    def extract_requests(items, parent_path=""):
        """Recursively extract requests from Postman collection items"""
        for item in items:
            if "request" in item:
                # This is a request
                request = item["request"]
                url = request.get("url", {})

                # Handle different URL formats in Postman
                if isinstance(url, str):
                    path = url
                elif isinstance(url, dict):
                    # Postman v2.1 format
                    host = url.get("host", [])
                    path_parts = url.get("path", [])
                    if isinstance(host, list) and isinstance(path_parts, list):
                        path = "/" + "/".join(path_parts)
                    else:
                        path = str(url.get("raw", ""))
                else:
                    path = str(url)

                # Clean up the path
                if path.startswith("http"):
                    # Extract path from full URL
                    from urllib.parse import urlparse
                    parsed = urlparse(path)
                    path = parsed.path

                method = request.get("method", "GET")

                endpoint = {
                    "path": path,
                    "method": method,
                    "name": item.get("name", ""),
                    "description": request.get("description", ""),
                    "headers": request.get("header", []),
                    "body": request.get("body", {}),
                    "auth": request.get("auth", {}),
                    "tests": item.get("event", [])
                }
                parsed_data["endpoints"].append(endpoint)

            elif "item" in item:
                # This is a folder, recurse
                folder_path = parent_path + "/" + item.get("name", "")
                extract_requests(item["item"], folder_path)

    extract_requests(postman_data.get("item", []))
    return parsed_data


def generate_api_scenarios(api_data: Dict[str, Any], document_type: str) -> List[Dict[str, Any]]:
    """
    Generate API test scenarios without detailed test cases (first step)
    """
    try:
        # Prepare the system message for scenarios only
        system_message = """You are an expert API testing specialist. Your task is to generate comprehensive test scenarios for API endpoints based on the provided API documentation.

CRITICAL: You must respond with ONLY valid JSON. Do not include any explanatory text, comments, or formatting outside of the JSON structure. Start your response directly with '[' and end with ']'.

Required JSON format for each test scenario:
{
    "id": "API_SC001",
    "title": "API Endpoint Test Scenario",
    "description": "Detailed description of what this scenario tests",
    "category": "functional|negative|performance|security|integration",
    "endpoints": ["/api/endpoint1", "/api/endpoint2"],
    "test_types": ["authentication", "data_validation", "error_handling"],
    "priority": "high|medium|low",
    "estimated_test_cases": 5
}

For each API endpoint or group of related endpoints, generate scenarios covering:
1. Functional Testing: Happy path, data validation, CRUD operations
2. Negative Testing: Invalid inputs, error conditions, boundary values  
3. Security Testing: Authentication, authorization, input validation
4. Performance Testing: Response times, load handling
5. Integration Testing: Dependencies, data flow

Focus on scenario-level descriptions without detailed test case steps. Each scenario should represent a logical group of related test cases."""

        # Prepare the user message
        user_message = f"""
Please analyze this {document_type} API specification and generate comprehensive test scenarios:

API Title: {api_data.get('title', 'Unknown')}
API Description: {api_data.get('description', 'No description')}

Endpoints Summary:
"""
        
        # Add endpoint information
        for endpoint in api_data.get('endpoints', [])[:10]:  # Limit to first 10 for prompt size
            user_message += f"- {endpoint.get('method', 'GET')} {endpoint.get('path', '/unknown')}: {endpoint.get('summary', 'No summary')}\n"
        
        if len(api_data.get('endpoints', [])) > 10:
            user_message += f"... and {len(api_data.get('endpoints', [])) - 10} more endpoints\n"

        user_message += "\nGenerate 8-12 comprehensive test scenarios covering all major testing aspects."

        # Make API call
        response = client.chat.completions.create(
            model=OPENAI_MODEL_API,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=3000,
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            scenarios = json.loads(content)
            print(f"Successfully generated {len(scenarios)} API scenarios")
            return scenarios
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            # Try to extract JSON array from response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                try:
                    scenarios = json.loads(json_match.group())
                    print(f"Successfully parsed {len(scenarios)} scenarios from regex match")
                    return scenarios
                except json.JSONDecodeError:
                    pass
            
            return [{"error": f"Failed to parse AI response as JSON: {content[:500]}"}]

    except Exception as e:
        print(f"Error generating API scenarios: {str(e)}")
        return [{"error": f"Error generating scenarios: {str(e)}"}]


def generate_api_test_cases_for_scenarios(scenarios: List[Dict[str, Any]], api_data: Dict[str, Any], document_type: str) -> List[Dict[str, Any]]:
    """
    Generate detailed test cases for selected API scenarios (second step)
    """
    try:
        # If we have many scenarios, process them in batches to avoid token limits
        if len(scenarios) > 5:
            print(f"Processing {len(scenarios)} scenarios in batches to avoid token limits")
            all_detailed_scenarios = []
            batch_size = 3  # Process 3 scenarios at a time
            
            for i in range(0, len(scenarios), batch_size):
                batch = scenarios[i:i + batch_size]
                print(f"Processing batch {i//batch_size + 1}: scenarios {i+1}-{min(i+batch_size, len(scenarios))}")
                batch_result = _generate_batch_test_cases(batch, api_data, document_type)
                if isinstance(batch_result, list) and len(batch_result) > 0:
                    all_detailed_scenarios.extend(batch_result)
                
            return all_detailed_scenarios
        else:
            # Process all scenarios at once if there are 5 or fewer
            return _generate_batch_test_cases(scenarios, api_data, document_type)

    except Exception as e:
        print(f"Error generating detailed API test cases: {str(e)}")
        return [{"error": f"Error generating detailed test cases: {str(e)}"}]


def _generate_batch_test_cases(scenarios: List[Dict[str, Any]], api_data: Dict[str, Any], document_type: str) -> List[Dict[str, Any]]:
    """
    Generate test cases for a batch of scenarios
    """
    try:
        # Prepare the system message for detailed test cases (more concise)
        system_message = """You are an expert API testing specialist. Generate detailed test cases for the provided API scenarios.

CRITICAL: Respond with ONLY valid JSON. Start with '[' and end with ']'.

JSON format:
{
    "id": "API_SC001",
    "title": "Scenario Title",
    "description": "Brief description",
    "category": "functional|negative|security",
    "test_cases": [
        {
            "id": "API_TC001",
            "title": "Test Case Title",
            "description": "Test description",
            "priority": "high|medium|low",
            "category": "functional|negative|security",
            "steps": ["Step 1", "Step 2", "Step 3"],
            "test_data": {
                "method": "GET|POST|PUT|DELETE",
                "endpoint": "/api/endpoint",
                "expected_status_code": 200
            },
            "expected_result": "Expected outcome"
        }
    ]
}

Generate 3-5 test cases per scenario."""

        # Prepare user message (more concise)
        user_message = f"""
Generate detailed test cases for these {len(scenarios)} API scenarios:

{json.dumps(scenarios, indent=1)}

Document Type: {document_type}
Generate test cases for ALL {len(scenarios)} scenarios.
"""

        # Make API call with appropriate token limit
        response = client.chat.completions.create(
            model=OPENAI_MODEL_API,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=4000,
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()
        
        # Parse JSON response
        print(f"Batch AI Response length: {len(content)} characters")
        
        try:
            detailed_scenarios = json.loads(content)
            print(f"Successfully generated detailed test cases for {len(detailed_scenarios)} scenarios in batch")
            return detailed_scenarios
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            # Try to extract JSON array from response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                try:
                    detailed_scenarios = json.loads(json_match.group())
                    print(f"Successfully parsed {len(detailed_scenarios)} detailed scenarios from regex match")
                    return detailed_scenarios
                except json.JSONDecodeError:
                    pass
            
            return [{"error": f"Failed to parse AI response as JSON: {content[:500]}"}]

    except Exception as e:
        print(f"Error generating batch test cases: {str(e)}")
        return [{"error": f"Error in batch generation: {str(e)}"}]


def generate_api_test_cases(api_data: Dict[str, Any], document_type: str) -> List[Dict[str, Any]]:
    """
    Generate comprehensive test cases for API endpoints using OpenAI
    """
    try:
        # Prepare the system message
        system_message = """You are an expert API testing specialist. Your task is to generate comprehensive, detailed test cases for API endpoints based on the provided API documentation.

CRITICAL: You must respond with ONLY valid JSON. Do not include any explanatory text, comments, or formatting outside of the JSON structure. Start your response directly with '[' and end with ']'.

Required JSON format for each test scenario:
{
    "title": "API Endpoint Test Scenario",
    "description": "Detailed description of what this scenario tests",
    "category": "api_testing",
    "test_cases": [
        {
            "title": "Specific Test Case Title",
            "description": "Detailed description of this test case",
            "priority": "high|medium|low",
            "category": "functional|negative|performance|security|integration",
            "preconditions": ["Precondition 1", "Precondition 2"],
            "steps": [
                "Step 1: Detailed action to perform",
                "Step 2: Detailed action to perform",
                "Step 3: Detailed action to perform"
            ],
            "test_data": {
                "method": "GET|POST|PUT|DELETE",
                "endpoint": "/api/endpoint",
                "headers": {"Content-Type": "application/json"},
                "request_body": {"key": "value"},
                "expected_status_code": 200,
                "expected_response_schema": {"type": "object", "properties": {}}
            },
            "expected_result": "Detailed description of expected outcome",
            "validation_criteria": ["Criterion 1", "Criterion 2"]
        }
    ]
}

For each API endpoint, generate comprehensive test cases covering:
1. Functional Testing: Happy path, edge cases, data validation
2. Negative Testing: Invalid inputs, error conditions, boundary values
3. Security Testing: Authentication, authorization, input validation
4. Performance Testing: Response times, load handling
5. Integration Testing: Dependencies, data flow

Consider:
- HTTP status codes (200, 201, 400, 401, 403, 404, 422, 500)
- Request/response headers
- Authentication and authorization
- Data validation and sanitization
- Error handling and edge cases
- Performance and scalability
- API versioning and backward compatibility

Generate multiple test cases per endpoint with different scenarios and priorities."""

        # Prepare user message based on document type
        if document_type == "swagger":
            user_message = f"""Generate comprehensive API test cases for this Swagger/OpenAPI specification:

API Title: {api_data.get('title', 'Unknown API')}
Version: {api_data.get('version', 'Unknown')}
Description: {api_data.get('description', '')}
Host: {api_data.get('host', '')}
Base Path: {api_data.get('base_path', '')}
Schemes: {', '.join(api_data.get('schemes', []))}

Endpoints:
{json.dumps(api_data.get('endpoints', []), indent=2)}

Please generate detailed test scenarios and test cases for each endpoint, considering the API specification, parameters, request/response schemas, and potential edge cases."""
        else:  # postman
            user_message = f"""Generate comprehensive API test cases for this Postman collection:

Collection Title: {api_data.get('title', 'Unknown Collection')}
Description: {api_data.get('description', '')}

Endpoints:
{json.dumps(api_data.get('endpoints', []), indent=2)}

Please generate detailed test scenarios and test cases for each endpoint, considering the request methods, headers, body content, and potential test scenarios."""

        # Make API call
        response = client.chat.completions.create(
            model=OPENAI_MODEL_API,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=4000,
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        # Parse JSON response
        scenarios = json.loads(content)

        # Validate and clean scenarios
        validated_scenarios = []
        for scenario in scenarios:
            if isinstance(scenario, dict) and 'title' in scenario and 'test_cases' in scenario:
                # Ensure test_cases is a list
                if not isinstance(scenario['test_cases'], list):
                    scenario['test_cases'] = []

                # Validate each test case
                validated_test_cases = []
                for test_case in scenario['test_cases']:
                    if isinstance(test_case, dict) and 'title' in test_case:
                        # Set defaults for missing fields
                        test_case.setdefault('description', '')
                        test_case.setdefault('priority', 'medium')
                        test_case.setdefault('category', 'functional')
                        test_case.setdefault('preconditions', [])
                        test_case.setdefault('steps', [])
                        test_case.setdefault('test_data', {})
                        test_case.setdefault('expected_result', '')
                        test_case.setdefault('validation_criteria', [])
                        validated_test_cases.append(test_case)

                scenario['test_cases'] = validated_test_cases
                validated_scenarios.append(scenario)

        return validated_scenarios

    except Exception as e:
        # Return a basic scenario if AI generation fails
        return [{
            "title": "Basic API Endpoint Testing",
            "description": "Basic test cases for API endpoints",
            "category": "api_testing",
            "test_cases": [
                {
                    "title": "Successful API Request",
                    "description": "Test successful API request with valid data",
                    "priority": "high",
                    "category": "functional",
                    "preconditions": ["API endpoint is accessible", "Valid authentication credentials"],
                    "steps": ["Send valid request to API endpoint", "Verify response received", "Check response status code"],
                    "test_data": {
                        "method": "GET",
                        "endpoint": "/api/test",
                        "headers": {"Content-Type": "application/json"},
                        "expected_status_code": 200
                    },
                    "expected_result": "API returns successful response with expected data",
                    "validation_criteria": ["Status code is 200", "Response contains expected data structure"]
                },
                {
                    "title": "Invalid Request Handling",
                    "description": "Test API behavior with invalid request data",
                    "priority": "medium",
                    "category": "negative",
                    "preconditions": ["API endpoint is accessible"],
                    "steps": ["Send request with invalid data", "Verify error response", "Check error message format"],
                    "test_data": {
                        "method": "POST",
                        "endpoint": "/api/test",
                        "headers": {"Content-Type": "application/json"},
                        "request_body": {"invalid": "data"},
                        "expected_status_code": 400
                    },
                    "expected_result": "API returns appropriate error response",
                    "validation_criteria": ["Status code indicates error", "Error message is informative"]
                }
            ]
        }]


def generate_api_tests_from_file(file_path: str) -> Dict[str, Any]:
    """
    Main function to generate API test cases from uploaded file
    """
    try:
        # Read and parse the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            api_data = json.load(f)

        # Detect document type
        document_type = detect_api_document_type(api_data)

        if document_type == "unknown":
            return {"error": "Unable to detect API document type. Please upload a valid Swagger/OpenAPI specification or Postman collection."}

        # Parse the document based on type
        if document_type == "swagger":
            parsed_data = parse_swagger_spec(api_data)
        elif document_type == "postman":
            parsed_data = parse_postman_collection(api_data)
        else:
            return {"error": "Unsupported document type"}

        # Generate test cases
        test_scenarios = generate_api_test_cases(parsed_data, document_type)

        # Prepare result
        result = {
            "document_type": document_type,
            "api_info": {
                "title": parsed_data.get("title", ""),
                "description": parsed_data.get("description", ""),
                "endpoints_count": len(parsed_data.get("endpoints", [])),
                "parsed_at": datetime.now().isoformat()
            },
            "scenarios": test_scenarios,
            "generated_at": datetime.now().isoformat(),
            "input_type": f"api_document_{document_type}"
        }

        return result

    except json.JSONDecodeError:
        return {"error": "Invalid JSON file. Please upload a valid JSON file."}
    except Exception as e:
        return {"error": f"Error processing API document: {str(e)}"}