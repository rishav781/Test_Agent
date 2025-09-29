"""
Website Analyzer Module
Handles website analysis, API endpoint extraction, performance testing, and test scenario generation.
"""

import json
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

import openai
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Configure OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key-here"))

# Configure LLM Model
OPENAI_MODEL_WEBSITE = os.getenv("OPENAI_MODEL_WEBSITE", "gpt-4")


def extract_api_endpoints(html_content, base_url):
    """
    Extract potential API endpoints from HTML content
    """
    endpoints = set()

    # Parse base URL
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    # Extract fetch() calls
    fetch_matches = re.findall(r'fetch\s*\(\s*["\']([^"\']+)["\']', html_content, re.IGNORECASE)
    for match in fetch_matches:
        if match.startswith(('http://', 'https://')):
            parsed = urlparse(match)
            if parsed.netloc and parsed.netloc != base_domain:
                endpoints.add(match)

    # Extract XMLHttpRequest calls (simplified)
    xhr_matches = re.findall(r'open\s*\(\s*["\'](?:GET|POST|PUT|DELETE)["\']\s*,\s*["\']([^"\']+)["\']', html_content, re.IGNORECASE)
    for match in xhr_matches:
        if match.startswith(('http://', 'https://')):
            parsed = urlparse(match)
            if parsed.netloc and parsed.netloc != base_domain:
                endpoints.add(match)

    # Extract script src attributes that look like APIs
    script_matches = re.findall(r'<script[^>]*src=["\']([^"\']+)["\'][^>]*>', html_content, re.IGNORECASE)
    for match in script_matches:
        full_url = urljoin(base_url, match)
        parsed = urlparse(full_url)
        if parsed.netloc and parsed.netloc != base_domain:
            # Check if it looks like an API endpoint (contains api, v1, v2, etc.)
            if any(keyword in full_url.lower() for keyword in ['api', 'v1', 'v2', 'v3', 'graphql', 'rest']):
                endpoints.add(full_url)

    # Extract link href attributes for external resources
    link_matches = re.findall(r'<link[^>]*href=["\']([^"\']+)["\'][^>]*>', html_content, re.IGNORECASE)
    for match in link_matches:
        full_url = urljoin(base_url, match)
        parsed = urlparse(full_url)
        if parsed.netloc and parsed.netloc != base_domain:
            endpoints.add(full_url)

    return list(endpoints)[:10]  # Limit to 10 endpoints to avoid too many requests


def test_api_performance(api_endpoints):
    """
    Test API endpoints for response times and performance metrics
    """
    performance_data = {}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for endpoint in api_endpoints[:5]:  # Test max 5 endpoints
        try:
            start_time = time.time()
            response = requests.get(endpoint, headers=headers, timeout=5)
            end_time = time.time()

            response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds

            performance_data[endpoint] = {
                "response_time_ms": response_time,
                "status_code": response.status_code,
                "content_length": len(response.content),
                "success": response.status_code < 400
            }

        except Exception as e:
            performance_data[endpoint] = {
                "error": str(e),
                "success": False
            }

    return performance_data


def generate_website_test_scenarios(analysis_result, url, title, api_performance):
    """
    Generate test scenarios based on website analysis results
    """
    try:
        # Prepare prompt for generating test scenarios
        system_message = """You are an expert QA engineer. Based on the website analysis, generate comprehensive test scenarios and test cases.

CRITICAL: Respond with ONLY valid JSON. Start directly with '[' and end with ']'.

Required JSON format for each scenario:
{
    "title": "Scenario Title",
    "description": "Brief description of the scenario",
    "category": "website_testing",
    "test_cases": [
        {
            "title": "Test Case Title",
            "description": "Detailed test case description",
            "priority": "high|medium|low",
            "category": "functional|performance|security|usability|accessibility",
            "preconditions": ["Precondition 1", "Precondition 2"],
            "steps": ["Step 1", "Step 2", "Step 3"],
            "test_data": {"key": "value"}
        }
    ]
}

Generate scenarios covering:
1. Functional testing (forms, navigation, links)
2. Performance testing (loading times, API responses)
3. Security testing (HTTPS, input validation)
4. Usability testing (user experience, responsiveness)
5. Accessibility testing (WCAG compliance)
6. API endpoint testing (if any APIs found)

Focus on issues identified in the analysis and create actionable test cases."""

        user_message = f"""Website: {url}
Title: {title}

Analysis Results:
Overall Rating: {analysis_result.get('overall_rating', 'N/A')}/5

Parameter Ratings:
{json.dumps(analysis_result.get('parameters', {}), indent=2)}

Analysis Report:
{analysis_result.get('report', 'No report available')}

Recommendations:
{json.dumps(analysis_result.get('recommendations', []), indent=2)}

API Performance Data:
{json.dumps(api_performance, indent=2)}

Generate comprehensive test scenarios and test cases based on this analysis."""

        # Make API call
        api_response = client.chat.completions.create(
            model=OPENAI_MODEL_WEBSITE,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=3000,
            temperature=0.3
        )

        content = api_response.choices[0].message.content.strip()

        # Parse JSON response
        scenarios = json.loads(content)

        # Validate and clean scenarios
        validated_scenarios = []
        for scenario in scenarios:
            if isinstance(scenario, dict) and 'title' in scenario and 'test_cases' in scenario:
                # Ensure test_cases is a list
                if not isinstance(scenario['test_cases'], list):
                    scenario['test_cases'] = []

                # Set default category for scenario
                scenario.setdefault('category', 'website_testing')

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
                        validated_test_cases.append(test_case)

                scenario['test_cases'] = validated_test_cases
                validated_scenarios.append(scenario)

        return validated_scenarios

    except Exception as e:
        # Return a basic scenario if AI generation fails
        return [{
            "title": "Basic Website Functionality Test",
            "description": "Test basic website functionality and accessibility",
            "category": "website_testing",
            "test_cases": [
                {
                    "title": "Website Loads Successfully",
                    "description": "Verify that the website loads without errors",
                    "priority": "high",
                    "category": "functional",
                    "preconditions": ["Internet connection is available"],
                    "steps": ["Navigate to the website URL", "Wait for page to load completely"],
                    "test_data": {"url": url}
                },
                {
                    "title": "HTTPS Security Check",
                    "description": "Verify website uses secure HTTPS connection",
                    "priority": "high",
                    "category": "security",
                    "preconditions": ["Website is accessible"],
                    "steps": ["Check URL protocol", "Verify SSL certificate validity"],
                    "test_data": {"expected_protocol": "https"}
                }
            ]
        }]


def analyze_website(url):
    """
    Analyze a website on multiple parameters using OpenAI
    """
    try:
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {"error": "Invalid URL format"}

        # Fetch website content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Extract basic info
        html_content = response.text[:20000]  # Increased limit for better parsing
        title = ""
        meta_desc = ""

        # Simple parsing for title and meta
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()

        meta_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\'][^>]*>', html_content, re.IGNORECASE)
        if meta_match:
            meta_desc = meta_match.group(1).strip()

        # Parse HTML for API endpoints and external resources
        api_endpoints = extract_api_endpoints(html_content, url)

        # Test API endpoints for performance
        api_performance = test_api_performance(api_endpoints)

        # Prepare prompt for OpenAI
        system_message = """You are an expert web analyst. Analyze the provided website content and rate it on multiple parameters out of 5 stars.

CRITICAL: Respond with ONLY valid JSON. Start directly with '{' and end with '}'.

Required JSON format:
{
    "overall_rating": 4,
    "parameters": {
        "performance": {"rating": 4, "explanation": "Brief explanation"},
        "seo": {"rating": 3, "explanation": "Brief explanation"},
        "usability": {"rating": 5, "explanation": "Brief explanation"},
        "accessibility": {"rating": 4, "explanation": "Brief explanation"},
        "security": {"rating": 3, "explanation": "Brief explanation"}
    },
    "report": "Detailed analysis report summarizing strengths and weaknesses",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
}

Rate each parameter 1-5 stars based on:
- Performance: Loading speed, optimization, mobile-friendliness, API response times
- SEO: Meta tags, content quality, structure
- Usability: Navigation, user experience, design
- Accessibility: WCAG compliance, screen reader support
- Security: HTTPS, vulnerabilities, best practices

Overall rating should be the average of parameter ratings."""

        user_message = f"""Website URL: {url}
Title: {title}
Meta Description: {meta_desc}

API Performance Data:
{json.dumps(api_performance, indent=2)}

HTML Content Preview:
{html_content[:10000]}"""

        # Make API call
        api_response = client.chat.completions.create(
            model=OPENAI_MODEL_WEBSITE,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=2000,
            temperature=0.3
        )

        content = api_response.choices[0].message.content.strip()

        # Parse JSON response
        analysis_result = json.loads(content)
        analyzed_at = datetime.now().isoformat()

        # Generate test scenarios based on website analysis
        test_scenarios = generate_website_test_scenarios(analysis_result, url, title, api_performance)

        # Prepare result in the same format as API test generator
        result = {
            "document_type": "website",
            "website_info": {
                "title": title,
                "url": url,
                "description": meta_desc,
                "overall_rating": analysis_result.get("overall_rating", 0),
                "parameters": analysis_result.get("parameters", {}),
                "report": analysis_result.get("report", ""),
                "recommendations": analysis_result.get("recommendations", []),
                "api_endpoints_found": len(api_endpoints),
                "analyzed_at": analyzed_at
            },
            "scenarios": test_scenarios,
            "generated_at": datetime.now().isoformat(),
            "input_type": "website_url"
        }

        return result

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch website: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response"}
    except Exception as e:
        return {"error": f"Analysis error: {str(e)}"}