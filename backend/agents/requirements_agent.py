"""
RequirementsAgent - Analyzes user requirements and identifies test scenarios using Claude.
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from anthropic import Anthropic


class RequirementsAgent:
    """
    Agent that analyzes requirements and identifies test scenarios using Claude Sonnet 4.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the RequirementsAgent.
        
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
    
    def analyze(self, requirements: str) -> Dict[str, Any]:
        """
        Analyze requirements and identify test scenarios.
        
        Args:
            requirements: User input (code or plain text requirements).
        
        Returns:
            Dictionary containing:
                - raw_analysis: Claude's full response
                - requirements: Original input
                - model: Model name used
        
        Raises:
            Exception: If API call fails or response is invalid.
        """
        if not requirements or not requirements.strip():
            raise ValueError("Requirements input cannot be empty.")
        
        prompt = self._build_prompt(requirements)
        
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
            
            return {
                "raw_analysis": raw_analysis,
                "requirements": requirements,
                "model": self.model
            }
        
        except Exception as e:
            raise Exception(f"Failed to analyze requirements: {str(e)}") from e
    
    def _build_prompt(self, requirements: str) -> str:
        """
        Build the prompt for Claude to analyze requirements.
        
        Args:
            requirements: The requirements input.
        
        Returns:
            Formatted prompt string.
        """
        return f"""Analyze the following requirements and identify all test scenarios needed.

Requirements:
{requirements}

Please identify:
1. All test scenarios needed, including:
   - Happy path scenarios (normal, expected use cases)
   - Edge cases (boundary conditions, unusual but valid inputs)
   - Error cases (invalid inputs, error conditions)
   - Boundary cases (minimum/maximum values, limits)

2. For each test scenario, provide:
   - name: A short, descriptive name for the test scenario
   - description: A detailed description of what the scenario tests
   - expected_outcome: What should happen when this scenario is executed
   - type: One of: "happy_path", "edge_case", "error_case", or "boundary_case"

Format your response as a clear, structured analysis. Include reasoning for why each scenario is important and what it validates.
"""


def _print_analysis_results(results: Dict[str, Any]) -> None:
    """
    Print analysis results in a clean, formatted way.
    
    Args:
        results: The results dictionary from analyze().
    """
    print("=" * 80)
    print("REQUIREMENTS ANALYSIS RESULTS")
    print("=" * 80)
    print(f"\nModel Used: {results['model']}")
    print(f"\nOriginal Requirements:")
    print("-" * 80)
    print(results['requirements'])
    print("\n" + "=" * 80)
    print("CLAUDE'S ANALYSIS:")
    print("=" * 80)
    print(results['raw_analysis'])
    print("=" * 80)


if __name__ == "__main__":
    # Example test case
    example_code = """def calculate_discount(price, customer_type, quantity):
    '''
    Calculate discount based on customer type and quantity.
    - Regular: 5% if quantity >= 10
    - Premium: 15% always
    - VIP: 20% base, +5% if quantity >= 20
    '''
    pass"""
    
    try:
        agent = RequirementsAgent()
        print("Analyzing requirements...")
        results = agent.analyze(example_code)
        _print_analysis_results(results)
    except Exception as e:
        print(f"Error: {e}")

