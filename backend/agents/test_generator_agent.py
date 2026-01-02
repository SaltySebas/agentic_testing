"""
TestGeneratorAgent - Converts test scenarios into executable pytest code using Claude.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from anthropic import Anthropic


class TestGeneratorAgent:
    """
    Agent that generates executable pytest test code from test scenarios using Claude Sonnet 4.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the TestGeneratorAgent.
        
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
    
    def generate_tests(self, scenarios: str, function_code: str, mode: str = "test") -> str:
        """
        Generate executable pytest test code from test scenarios.
        
        Args:
            scenarios: Test scenarios output from RequirementsAgent (raw_analysis).
            function_code: The original function code being tested (or requirements for generate mode).
            mode: "generate" to create implementation + tests, or "test" to create tests for existing code.
        
        Returns:
            Complete pytest test code as a string, ready to execute.
        
        Raises:
            ValueError: If inputs are empty or mode is invalid.
            Exception: If API call fails or response is invalid.
        """
        if mode not in ["generate", "test"]:
            raise ValueError(f"Mode must be 'generate' or 'test', got '{mode}'")
        
        if not scenarios or not scenarios.strip():
            raise ValueError("Scenarios input cannot be empty.")
        
        if not function_code or not function_code.strip():
            raise ValueError("Function code input cannot be empty.")
        
        prompt = self._build_prompt(scenarios, function_code, mode)
        
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
            generated_code = message.content[0].text if message.content else ""
            
            if not generated_code:
                raise Exception("Generated test code is empty.")
            
            return generated_code
        
        except Exception as e:
            raise Exception(f"Failed to generate tests: {str(e)}") from e
    
    def _build_prompt(self, scenarios: str, function_code: str, mode: str) -> str:
        if mode == "generate":
            return f"""Write complete, executable code that includes BOTH the implementation AND tests in one file.

Requirements/Specifications:
{function_code}

Test Scenarios:
{scenarios}

MODE: GENERATE (create implementation + tests)

Requirements:
1. Write a complete Python file with:
   - The function implementation at the top
   - All necessary imports (pytest, etc.)
   - Complete test suite below the implementation
2. The implementation should fully satisfy the requirements/specifications
3. Create one test function for each scenario identified
4. Use descriptive test function names matching the scenario names (e.g., test_regular_customer_with_quantity_discount)
   - Convert scenario names to valid Python function names (lowercase, underscores, no spaces)
5. Add docstrings to each test function explaining what it validates
6. Write proper assertions with clear failure messages
7. Use pytest.raises() for error case tests
8. Follow pytest best practices and conventions:
   - Test functions must start with "test_"
   - Use descriptive names
   - Keep tests focused and independent
   - Use appropriate assertions (assert, assertAlmostEqual for floats, etc.)
9. Handle edge cases appropriately (e.g., floating point comparisons)
10. Test all scenarios mentioned in the analysis

CRITICAL OUTPUT FORMATTING RULES:
- Output ONLY raw Python code
- DO NOT wrap the code in markdown code fences (no ```python or ```)
- DO NOT include any explanations, comments, or text before or after the code
- The response must be valid Python that can be saved directly to a .py file
- Start with the function implementation, then imports, then tests
- End your response with the last line of the last test function - nothing after it
"""
        else:  # mode == "test"
            return f"""You are writing comprehensive pytest tests for an EXISTING function.

CRITICAL INSTRUCTIONS FOR TEST MODE:
1. The user has provided their function implementation below
2. You MUST include their function EXACTLY as written at the top of your output
3. DO NOT modify, fix, or improve their function in any way
4. DO NOT change variable names, logic, conditions, or calculations
5. Your job is to write tests that will expose any bugs in their implementation
6. Include the function verbatim, then write tests below it

EXISTING FUNCTION (include this EXACTLY as-is):
{function_code}

TEST SCENARIOS TO COVER:
{scenarios}

Your output should be:
1. First: The exact function code above (copy it verbatim)
2. Then: import pytest
3. Then: Comprehensive test functions

The tests should be thorough enough to catch any bugs in the implementation.
DO NOT MODIFY THE FUNCTION - your tests should work with it as-is.

CRITICAL OUTPUT FORMATTING RULES:
- Output ONLY raw Python code
- DO NOT wrap the code in markdown code fences (no ```python or ```)
- DO NOT include any explanations, comments, or text before or after the code
- The response must be valid Python that can be saved directly to a .py file
- Start with the function code (copy it exactly), then imports, then tests
- End your response with the last line of the last test function - nothing after it
"""


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add parent directory to path to import RequirementsAgent
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from agents.requirements_agent import RequirementsAgent
    
    # Example function to test
    example_code = """def calculate_discount(price, customer_type, quantity):
    '''
    Calculate discount based on customer type and quantity.
    - Regular: 5% if quantity >= 10
    - Premium: 15% always
    - VIP: 20% base, +5% if quantity >= 20
    '''
    pass"""
    
    try:
        # Step 1: Analyze requirements using RequirementsAgent
        print("Step 1: Analyzing requirements...")
        requirements_agent = RequirementsAgent()
        analysis_results = requirements_agent.analyze(example_code)
        scenarios = analysis_results['raw_analysis']
        
        print("✓ Requirements analyzed successfully\n")
        
        # Step 2: Generate pytest code using TestGeneratorAgent
        print("Step 2: Generating pytest test code...")
        test_generator = TestGeneratorAgent()
        generated_code = test_generator.generate_tests(scenarios, example_code)
        
        print("✓ Test code generated successfully\n")
        
        # Step 3: Print the generated code
        print("=" * 80)
        print("GENERATED PYTEST CODE")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)
        print()
        
        # Step 4: Create generated_tests/ directory if it doesn't exist
        test_dir = Path("generated_tests")
        test_dir.mkdir(exist_ok=True)
        print(f"✓ Directory '{test_dir}' ready")
        
        # Step 5: Save the code to generated_tests/test_discount.py
        test_file = test_dir / "test_discount.py"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(generated_code)
        
        print(f"✓ Test code saved to '{test_file}'")
        print(f"\nYou can now run the tests with: pytest {test_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

