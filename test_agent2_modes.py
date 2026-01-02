import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from agents.test_generator_agent import TestGeneratorAgent

buggy_code = """def calculate_discount(price, customer_type, quantity):
    if customer_type == "regular" and quantity > 10:  # BUG: > instead of >=
        return price * 0.05
    return 0"""

scenarios = "Test regular customer at threshold (qty=10 should get discount)"

agent = TestGeneratorAgent()

print("="*80)
print("TESTING TEST MODE - Should preserve bug")
print("="*80)
result = agent.generate_tests(scenarios, buggy_code, mode="test")
print(result[:500])  # First 500 chars

# Check if bug is preserved
if "quantity > 10" in result:
    print("\n✅ SUCCESS: Bug preserved (> instead of >=)")
else:
    print("\n❌ FAILED: Bug was fixed by Agent 2")
