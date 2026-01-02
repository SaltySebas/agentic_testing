"""
FailureAnalyzerAgent - Analyzes test failures and determines root causes using Claude.
"""

import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from anthropic import Anthropic


class FailureAnalyzerAgent:
    """
    Agent that analyzes test failures and determines root causes using Claude Sonnet 4.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the FailureAnalyzerAgent.
        
        Args:
            api_key: Optional API key. If not provided, loads from ANTHROPIC_API_KEY env var.
        
        Raises:
            ValueError: If API key is not found.
        """
        load_dotenv()
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Please set it in your environment "
                "variables or .env file."
            )
        
        self.model = "claude-sonnet-4-20250514"
        self.client = Anthropic(api_key=self.api_key)
    
    def analyze_failure(
        self,
        test_output: str,
        function_code: str,
        test_code: str,
        scenarios: str
    ) -> Dict[str, Any]:
        """
        Analyze test failures and determine root causes.
        
        Args:
            test_output: Pytest output showing failures (with stack traces, assertions, errors).
            function_code: The original function code being tested.
            test_code: The generated test code.
            scenarios: Test scenarios from RequirementsAgent.
        
        Returns:
            Dictionary containing:
                - failure_type: "CODE_BUG" | "TEST_BUG" | "REQUIREMENTS_AMBIGUITY"
                - should_stop: boolean (stop iteration or continue)
                - analysis: detailed explanation
                - suggested_fix: specific code changes
                - confidence: 0-100 score
                - failing_tests: list of test names that failed
        
        Raises:
            ValueError: If inputs are empty.
            Exception: If API call fails or response is invalid.
        """
        if not test_output or not test_output.strip():
            raise ValueError("Test output cannot be empty.")
        
        if not function_code or not function_code.strip():
            raise ValueError("Function code cannot be empty.")
        
        if not test_code or not test_code.strip():
            raise ValueError("Test code cannot be empty.")
        
        prompt = self._build_prompt(test_output, function_code, test_code, scenarios)
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract the text content from the response
            raw_analysis = message.content[0].text if message.content else ""
            
            if not raw_analysis:
                raise Exception("Analysis response is empty.")
            
            # Parse the structured response
            parsed_result = self._parse_analysis(raw_analysis, test_output)
            
            return parsed_result
        
        except Exception as e:
            raise Exception(f"Failed to analyze failure: {str(e)}") from e
    
    def _build_prompt(
        self,
        test_output: str,
        function_code: str,
        test_code: str,
        scenarios: str
    ) -> str:
        """
        Build the prompt for Claude to analyze test failures.
        
        Args:
            test_output: The pytest output with failures.
            function_code: The function being tested.
            test_code: The test code.
            scenarios: The test scenarios.
        
        Returns:
            Formatted prompt string.
        """
        return f"""You are an expert test failure analyzer. Analyze the following test failure and determine the ROOT CAUSE.

FUNCTION CODE BEING TESTED:
{function_code}

TEST CODE:
{test_code}

ORIGINAL TEST SCENARIOS:
{scenarios}

PYTEST OUTPUT WITH FAILURES:
{test_output}

Your task is to:
1. Carefully analyze each test failure
2. Determine the ROOT CAUSE of the failure
3. Classify the failure as ONE of these three types:

   a) CODE_BUG: The implementation has a bug
      - Wrong logic, off-by-one errors, missing edge cases
      - Incorrect exception types raised
      - Wrong calculations or return values
      - Missing validation or checks
      - Mark as STOP (alert user, don't iterate automatically)
   
   b) TEST_BUG: The test has wrong expectations
      - Wrong assertion values
      - Misunderstood requirements
      - Incorrect exception type expected
      - Wrong test logic
      - Mark as CONTINUE (regenerate test automatically)
   
   c) REQUIREMENTS_AMBIGUITY: The requirements are unclear
      - Multiple valid interpretations
      - Edge cases not specified
      - Unclear behavior expectations
      - Mark as STOP (need user input)

For CODE_BUG:
- Identify the exact line(s) with the bug
- Explain what's wrong in detail
- Provide specific code fix (show the corrected code)
- Explain why this is a code bug vs test bug

For TEST_BUG:
- Identify what's wrong with the test expectation
- Explain the correct expectation based on the function code
- Provide corrected test code
- Explain why this is a test bug vs code bug

For REQUIREMENTS_AMBIGUITY:
- Identify what's unclear in the requirements
- Provide 2-3 interpretation options
- Explain what clarification is needed from the user
- Suggest how to resolve the ambiguity

IMPORTANT ANALYSIS GUIDELINES:
- Look at actual error messages and stack traces
- Compare expected vs actual values carefully
- Check exception types (TypeError vs ValueError vs others)
- Verify if the function logic matches the requirements
- Check if test expectations match the function's actual behavior
- Consider edge cases and boundary conditions
- Be precise about line numbers and specific issues

OUTPUT FORMAT (use this exact structure):
FAILURE_TYPE: [CODE_BUG|TEST_BUG|REQUIREMENTS_AMBIGUITY]
SHOULD_STOP: [true|false]
CONFIDENCE: [0-100]
FAILING_TESTS: [comma-separated list of test function names]

ANALYSIS:
[Detailed explanation of the root cause, what went wrong, and why]

SUGGESTED_FIX:
[Specific code changes - show the corrected code or test code]

REASONING:
[Explain why you classified it this way and why it's not the other types]
"""
    
    def _parse_analysis(self, raw_analysis: str, test_output: str) -> Dict[str, Any]:
        """
        Parse Claude's structured response into a dictionary.
        
        Args:
            raw_analysis: Claude's raw analysis text.
            test_output: Original test output for extracting test names.
        
        Returns:
            Parsed dictionary with structured failure analysis.
        """
        # Extract failing test names from test output
        failing_tests = self._extract_failing_tests(test_output)
        
        # Parse the structured response
        result = {
            "failure_type": "CODE_BUG",  # Default
            "should_stop": True,  # Default
            "analysis": raw_analysis,
            "suggested_fix": "",
            "confidence": 50,  # Default
            "failing_tests": failing_tests
        }
        
        # Try to extract structured fields from the response
        lines = raw_analysis.split('\n')
        current_section = None
        sections = {
            "FAILURE_TYPE": "failure_type",
            "SHOULD_STOP": "should_stop",
            "CONFIDENCE": "confidence",
            "ANALYSIS": "analysis",
            "SUGGESTED_FIX": "suggested_fix",
            "REASONING": "reasoning"
        }
        
        analysis_text = []
        fix_text = []
        reasoning_text = []
        
        for line in lines:
            line_upper = line.strip().upper()
            
            # Check for section headers
            if line_upper.startswith("FAILURE_TYPE:"):
                value = line.split(":", 1)[1].strip()
                if value.upper() in ["CODE_BUG", "TEST_BUG", "REQUIREMENTS_AMBIGUITY"]:
                    result["failure_type"] = value.upper()
            elif line_upper.startswith("SHOULD_STOP:"):
                value = line.split(":", 1)[1].strip().lower()
                result["should_stop"] = value in ["true", "yes", "1"]
            elif line_upper.startswith("CONFIDENCE:"):
                try:
                    value = int(line.split(":", 1)[1].strip())
                    result["confidence"] = max(0, min(100, value))
                except ValueError:
                    pass
            elif line_upper.startswith("ANALYSIS:"):
                current_section = "analysis"
                continue
            elif line_upper.startswith("SUGGESTED_FIX:"):
                current_section = "fix"
                continue
            elif line_upper.startswith("REASONING:"):
                current_section = "reasoning"
                continue
            elif line_upper.startswith("FAILING_TESTS:"):
                # Override with parsed list if provided
                value = line.split(":", 1)[1].strip()
                if value:
                    result["failing_tests"] = [t.strip() for t in value.split(",")]
                current_section = None
                continue
            
            # Collect section content
            if current_section == "analysis":
                analysis_text.append(line)
            elif current_section == "fix":
                fix_text.append(line)
            elif current_section == "reasoning":
                reasoning_text.append(line)
        
        # Update sections if we found them
        if analysis_text:
            result["analysis"] = "\n".join(analysis_text).strip()
        if fix_text:
            result["suggested_fix"] = "\n".join(fix_text).strip()
        if reasoning_text:
            result["reasoning"] = "\n".join(reasoning_text).strip()
        
        # If we couldn't parse structured format, use the whole response as analysis
        if not result["analysis"] or result["analysis"] == raw_analysis:
            result["analysis"] = raw_analysis
        
        return result
    
    def _extract_failing_tests(self, test_output: str) -> List[str]:
        """
        Extract failing test function names from pytest output.
        
        Args:
            test_output: Pytest output text.
        
        Returns:
            List of failing test function names.
        """
        failing_tests = []
        lines = test_output.split('\n')
        
        for line in lines:
            # Look for patterns like "FAILED test_file.py::test_function_name"
            if "FAILED" in line and "::" in line:
                parts = line.split("::")
                if len(parts) >= 2:
                    test_name = parts[-1].strip()
                    if test_name.startswith("test_"):
                        failing_tests.append(test_name)
            # Also look for "test_function_name FAILED" patterns
            elif "FAILED" in line and "test_" in line:
                parts = line.split()
                for part in parts:
                    if part.startswith("test_") and "FAILED" not in part:
                        failing_tests.append(part)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tests = []
        for test in failing_tests:
            if test not in seen:
                seen.add(test)
                unique_tests.append(test)
        
        return unique_tests if unique_tests else ["unknown"]


def _print_analysis_results(results: Dict[str, Any]) -> None:
    """
    Print analysis results in a clean, formatted way.
    
    Args:
        results: The results dictionary from analyze_failure().
    """
    print("=" * 80)
    print("TEST FAILURE ANALYSIS")
    print("=" * 80)
    
    # Failure type with color coding
    failure_type = results['failure_type']
    print(f"\nFailure Type: {failure_type}")
    
    if failure_type == "CODE_BUG":
        print("  → This is a bug in the implementation code")
        print("  → Action: STOP - User intervention required")
    elif failure_type == "TEST_BUG":
        print("  → This is a bug in the test expectations")
        print("  → Action: CONTINUE - Test can be regenerated automatically")
    elif failure_type == "REQUIREMENTS_AMBIGUITY":
        print("  → Requirements are unclear or ambiguous")
        print("  → Action: STOP - User clarification needed")
    
    print(f"\nShould Stop: {results['should_stop']}")
    print(f"Confidence: {results['confidence']}%")
    
    print(f"\nFailing Tests: {', '.join(results['failing_tests'])}")
    
    print("\n" + "-" * 80)
    print("DETAILED ANALYSIS:")
    print("-" * 80)
    print(results['analysis'])
    
    if results.get('suggested_fix'):
        print("\n" + "-" * 80)
        print("SUGGESTED FIX:")
        print("-" * 80)
        print(results['suggested_fix'])
    
    if results.get('reasoning'):
        print("\n" + "-" * 80)
        print("REASONING:")
        print("-" * 80)
        print(results['reasoning'])
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Simulate a test failure scenario
    # This simulates the TypeError vs ValueError mismatch issue
    
    function_code = """def calculate_discount(price, customer_type, quantity):
    '''
    Calculate discount based on customer type and quantity.
    - Regular: 5% if quantity >= 10
    - Premium: 15% always
    - VIP: 20% base, +5% if quantity >= 20
    '''
    if not isinstance(price, (int, float)) or not isinstance(quantity, (int, float)) or not isinstance(customer_type, str):
        raise TypeError("Invalid parameter types")
    
    if price is None or customer_type is None or quantity is None:
        raise ValueError("Parameters cannot be None")
    
    if price < 0 or quantity < 0:
        raise ValueError("Price and quantity must be non-negative")
    
    discount_percentage = 0
    
    if customer_type == "Regular":
        if quantity >= 10:
            discount_percentage = 5
    elif customer_type == "Premium":
        discount_percentage = 15
    elif customer_type == "VIP":
        discount_percentage = 20
        if quantity >= 20:
            discount_percentage = 25
    
    return price * discount_percentage / 100"""
    
    test_code = """def test_none_values():
    \"\"\"Test behavior when parameters are None\"\"\"
    with pytest.raises(TypeError, match="Invalid parameter types"):
        calculate_discount(None, None, None)"""
    
    # Simulated pytest output showing the failure
    test_output = """============================= test session starts ==============================
platform win32 -- Python 3.12.0, pytest-8.0.0, pluggy-1.4.0
collected 1 item

test_discount.py::test_none_values FAILED                              [100%]

================================== FAILURES ===================================
_____________________________ test_none_values _______________________________

    def test_none_values():
        \"\"\"Test behavior when parameters are None\"\"\"
        with pytest.raises(TypeError, match="Invalid parameter types"):
>           calculate_discount(None, None, None)
E           Failed: DID NOT RAISE

test_discount.py:121: AssertionError
=========================== short test summary info ============================
FAILED test_discount.py::test_none_values - Failed: DID NOT RAISE

============================== 1 failed in 0.05s =============================="""
    
    scenarios = """Test scenarios for calculate_discount function:
- Test behavior when parameters are None (error case)
- Should raise appropriate exception for None values"""
    
    try:
        print("Analyzing test failure...")
        print("=" * 80)
        print("SIMULATED TEST FAILURE:")
        print("=" * 80)
        print("Test: test_none_values")
        print("Expected: TypeError('Invalid parameter types')")
        print("Actual: No exception raised (but ValueError should be raised first)")
        print("=" * 80)
        print()
        
        analyzer = FailureAnalyzerAgent()
        results = analyzer.analyze_failure(
            test_output=test_output,
            function_code=function_code,
            test_code=test_code,
            scenarios=scenarios
        )
        
        _print_analysis_results(results)
        
        print("\n" + "=" * 80)
        print("TOOL RESPONSE:")
        print("=" * 80)
        if results['should_stop']:
            print("🛑 STOPPING: User intervention required")
            if results['failure_type'] == "CODE_BUG":
                print("   → Code bug detected - manual fix needed")
            elif results['failure_type'] == "REQUIREMENTS_AMBIGUITY":
                print("   → Requirements unclear - user clarification needed")
        else:
            print("✅ CONTINUING: Test can be regenerated automatically")
            print("   → Test bug detected - will regenerate test with correct expectations")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

