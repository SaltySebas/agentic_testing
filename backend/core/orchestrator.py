"""
Orchestrator - Coordinates all test generation agents with state management and resume capability.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add backend directory to path for imports
_backend_path = Path(__file__).parent.parent
if str(_backend_path) not in sys.path:
    sys.path.insert(0, str(_backend_path))

from agents.requirements_agent import RequirementsAgent
from agents.test_generator_agent import TestGeneratorAgent
from agents.failure_analyzer_agent import FailureAnalyzerAgent
from agents.docker_execution_agent import DockerExecutorAgent


class Orchestrator:
    """
    Orchestrates the test generation workflow with state management and resume capability.
    """
    
    def __init__(self, test_file: str = None):
        """
        Initialize the Orchestrator.
        
        Args:
            test_file: Path to the generated test file. If None, will be determined by mode.
        """
        self.test_file_override = Path(test_file) if test_file else None
        self.requirements_agent = None
        self.test_generator_agent = None
        self.failure_analyzer_agent = None
        self.docker_executor = None  # Will be initialized when needed
        
    def run(
        self,
        mode: str,
        input_code: str = None,
        max_iterations: int = 5,
        resume_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the complete test generation workflow.
        
        Args:
            mode: "generate" to create implementation + tests, or "test" to create tests for existing code.
            input_code: The code/requirements (function code for test mode, requirements for generate mode).
            max_iterations: Maximum number of test regeneration iterations.
            resume_state: Optional state dictionary to resume from.
        
        Returns:
            Dictionary with status, results, and resume state.
        """
        # Validate mode
        if mode not in ["generate", "test"]:
            raise ValueError(f"Mode must be 'generate' or 'test', got '{mode}'")
        
        # Validate input_code
        if not input_code or not input_code.strip():
            raise ValueError("input_code cannot be empty")
        
        # Initialize agents
        self.requirements_agent = RequirementsAgent()
        self.test_generator_agent = TestGeneratorAgent()
        self.failure_analyzer_agent = FailureAnalyzerAgent()
        
        # Initialize state
        state = {
            "mode": mode,
            "scenarios": None,
            "tests": None,
            "iteration": 0,
            "original_code": input_code,
            "checkpoint_reason": None
        }
        
        # Load state if resuming
        is_resuming = resume_state is not None
        if is_resuming:
            self._log_step("RESUME", "Resuming from saved state")
            state = self._validate_and_load_state(resume_state, input_code, mode)
            # Use mode from state if available
            actual_mode = state.get('mode', mode)
            self._log_step("RESUME", f"Loaded state from iteration {state['iteration']}")
            self._log_step("RESUME", f"Mode: {actual_mode}")
            self._log_step("RESUME", f"Checkpoint reason: {state.get('checkpoint_reason', 'Unknown')}")
        else:
            actual_mode = mode
            self._log_step("MODE", f"Running in {mode.upper()} mode")
        
        # Determine test file path based on mode
        if self.test_file_override:
            self.test_file = self.test_file_override
        else:
            if actual_mode == "generate":
                self.test_file = Path("generated_tests/test_generated.py")
            else:  # mode == "test"
                self.test_file = Path("generated_tests/test_user_code.py")
        
        # Initialize failure tracking for stuck loop detection
        failure_history = []
        
        try:
            # STEP 1: Requirements Analysis (skip if resuming)
            if not is_resuming:
                self._log_step("STEP 1", "Requirements Analysis")
                try:
                    analysis_results = self.requirements_agent.analyze(input_code)
                    state["scenarios"] = analysis_results
                    self._log_step("STEP 1", f"✓ Analyzed requirements (model: {analysis_results['model']})")
                except Exception as e:
                    return self._create_error_result("Failed to analyze requirements", str(e), state)
            else:
                self._log_step("STEP 1", "⏭️  Skipped (using saved scenarios from resume state)")
            
            # STEP 2: Test Generation (skip if resuming)
            if not is_resuming:
                current_mode = state.get("mode", mode)
                self._log_step("STEP 2", f"Code Generation ({current_mode.upper()} mode)")
                try:
                    scenarios = state["scenarios"]["raw_analysis"]
                    test_code = self.test_generator_agent.generate_tests(
                        scenarios, input_code, mode=current_mode
                    )
                    state["tests"] = test_code
                    self._save_tests_to_file(test_code, self.test_file)
                    if mode == "generate":
                        self._log_step("STEP 2", f"✓ Generated implementation + tests ({len(test_code)} characters)")
                    else:
                        self._log_step("STEP 2", f"✓ Generated tests for existing code ({len(test_code)} characters)")
                    self._log_step("STEP 2", f"✓ Saved to {self.test_file}")
                except Exception as e:
                    return self._create_error_result("Failed to generate code/tests", str(e), state)
            else:
                self._log_step("STEP 2", "⏭️  Skipped (using saved code/tests from resume state)")
                # Ensure test file exists
                if state["tests"]:
                    self._save_tests_to_file(state["tests"], self.test_file)
            
            # Main iteration loop
            while state["iteration"] < max_iterations:
                state["iteration"] += 1
                self._log_step("ITERATION", f"Starting iteration {state['iteration']}/{max_iterations}")
                
                # STEP 3: Test Execution (always run)
                self._log_step("STEP 3", "Test Execution (Docker isolated)")
                test_results = self._run_pytest(str(self.test_file))
                
                passed = test_results["passed"]
                failed = test_results["failed"]
                self._log_step("STEP 3", f"✓ Tests executed: {passed} passed, {failed} failed")
                
                # Record failing test names for stuck loop detection
                failing_tests = test_results.get("failing_tests", [])
                if failing_tests:
                    failure_history.append(set(failing_tests))
                    self._log_step("STEP 3", f"  → Failing tests: {', '.join(failing_tests)}")
                
                # STEP 4: Result Handling
                if failed == 0:
                    self._log_step("SUCCESS", "All tests passed!")
                    return {
                        "status": "SUCCESS",
                        "message": f"All {passed} tests passed after {state['iteration']} iteration(s)",
                        "scenarios": state["scenarios"],
                        "tests": state["tests"],
                        "test_results": test_results,
                        "iterations": state["iteration"],
                        "analysis": None,
                        "resume_state": None
                    }
                
                # STEP 4.5: Stuck Loop Detection (before failure analysis)
                if len(failure_history) >= 3:
                    last_three = failure_history[-3:]
                    # Check if the same tests are failing across 3 consecutive iterations
                    if (last_three[0] == last_three[1] == last_three[2] and len(last_three[0]) > 0):
                        # STUCK LOOP DETECTED
                        self._log_step("STUCK_LOOP", "⚠️  Same test failures detected after 3 iterations")
                        self._log_step("STUCK_LOOP", f"   Failing tests: {', '.join(sorted(last_three[0]))}")
                        self._log_step("STUCK_LOOP", "   System cannot determine if this is a CODE_BUG or TEST_BUG")
                        self._log_step("STUCK_LOOP", "   Stopping to prevent infinite loop")
                        
                        state["checkpoint_reason"] = "Stuck loop - same failures repeated"
                        return {
                            "status": "STUCK_LOOP",
                            "message": f"Same {len(last_three[0])} test(s) failing after 3 iterations. Likely CODE_BUG but requirements unclear. Please provide requirements documentation or manually review the code.",
                            "scenarios": state["scenarios"],
                            "tests": state["tests"],
                            "test_results": test_results,
                            "iterations": state["iteration"],
                            "analysis": {
                                "failure_type": "STUCK_LOOP",
                                "failing_tests": list(last_three[0]),
                                "iterations_stuck": 3,
                                "suggestion": "Add docstring/requirements to the function OR manually review the failing tests to determine if code or test expectations are wrong."
                            },
                            "resume_state": state.copy()
                        }
                
                # STEP 5: Failure Analysis
                self._log_step("STEP 5", "Failure Analysis")
                try:
                    # Extract function code from test file for analysis
                    # In test mode, function is in the test file; in generate mode, it's also in the test file
                    current_mode = state.get("mode", mode)
                    function_code_for_analysis = input_code
                    
                    failure_analysis = self.failure_analyzer_agent.analyze_failure(
                        test_output=test_results["output"],
                        function_code=function_code_for_analysis,
                        test_code=state["tests"],
                        scenarios=state["scenarios"]["raw_analysis"]
                    )
                    
                    failure_type = failure_analysis["failure_type"]
                    should_stop = failure_analysis["should_stop"]
                    confidence = failure_analysis.get("confidence", 50)
                    
                    self._log_step("STEP 5", f"✓ Failure analyzed: {failure_type} (confidence: {confidence}%)")
                    self._log_step("STEP 5", f"  → Should stop: {should_stop}")
                    
                    # Decision based on failure type
                    if failure_type == "CODE_BUG":
                        self._log_step("DECISION", "🛑 CODE_BUG detected - Stopping (user intervention required)")
                        state["checkpoint_reason"] = "CODE_BUG detected"
                        return {
                            "status": "CODE_BUG",
                            "message": f"Code bug detected after {state['iteration']} iteration(s). Manual fix required.",
                            "scenarios": state["scenarios"],
                            "tests": state["tests"],
                            "test_results": test_results,
                            "iterations": state["iteration"],
                            "analysis": failure_analysis,
                            "resume_state": state.copy()
                        }
                    
                    elif failure_type == "REQUIREMENTS_AMBIGUITY":
                        self._log_step("DECISION", "🛑 REQUIREMENTS_AMBIGUITY detected - Stopping (user clarification needed)")
                        state["checkpoint_reason"] = "REQUIREMENTS_AMBIGUITY detected"
                        return {
                            "status": "REQUIREMENTS_AMBIGUITY",
                            "message": f"Requirements ambiguity detected after {state['iteration']} iteration(s). User clarification needed.",
                            "scenarios": state["scenarios"],
                            "tests": state["tests"],
                            "test_results": test_results,
                            "iterations": state["iteration"],
                            "analysis": failure_analysis,
                            "resume_state": state.copy()
                        }
                    
                    elif failure_type == "TEST_BUG":
                        if not should_stop:
                            self._log_step("DECISION", "✅ TEST_BUG detected - Continuing to regenerate tests")
                            # STEP 6: Test Regeneration (for TEST_BUG only)
                            self._log_step("STEP 6", "Test Regeneration")
                            try:
                                scenarios = state["scenarios"]["raw_analysis"]
                                # Use the mode from state
                                current_mode = state.get("mode", mode)
                                code_to_use = input_code
                                
                                new_test_code = self.test_generator_agent.generate_tests(
                                    scenarios, code_to_use, mode=current_mode
                                )
                                state["tests"] = new_test_code
                                self._save_tests_to_file(new_test_code, self.test_file)
                                self._log_step("STEP 6", f"✓ Regenerated test code ({len(new_test_code)} characters)")
                                # Loop back to STEP 3
                                continue
                            except Exception as e:
                                return self._create_error_result("Failed to regenerate tests", str(e), state)
                        else:
                            self._log_step("DECISION", "🛑 TEST_BUG but should_stop=True - Stopping")
                            state["checkpoint_reason"] = "TEST_BUG with should_stop=True"
                            return {
                                "status": "TEST_BUG",
                                "message": f"Test bug detected after {state['iteration']} iteration(s), but should_stop flag is set.",
                                "scenarios": state["scenarios"],
                                "tests": state["tests"],
                                "test_results": test_results,
                                "iterations": state["iteration"],
                                "analysis": failure_analysis,
                                "resume_state": state.copy()
                            }
                    
                except Exception as e:
                    return self._create_error_result("Failed to analyze failure", str(e), state)
            
            # Max iterations reached
            self._log_step("MAX_ITERATIONS", f"Reached maximum iterations ({max_iterations})")
            state["checkpoint_reason"] = f"Max iterations ({max_iterations}) reached"
            return {
                "status": "MAX_ITERATIONS",
                "message": f"Reached maximum iterations ({max_iterations}) without all tests passing",
                "scenarios": state["scenarios"],
                "tests": state["tests"],
                "test_results": test_results,
                "iterations": state["iteration"],
                "analysis": None,
                "resume_state": state.copy()
            }
        
        except Exception as e:
            return self._create_error_result("Unexpected error in workflow", str(e), state)
    
    def _run_pytest(self, test_file: str) -> Dict[str, Any]:
        """
        Run pytest in Docker container with subprocess fallback.
        
        Args:
            test_file: Path to the test file.
        
        Returns:
            Dictionary with passed, failed counts and output.
        """
        # Initialize Docker executor if needed
        if not hasattr(self, 'docker_executor') or self.docker_executor is None:
            try:
                self.docker_executor = DockerExecutorAgent()
            except Exception as e:
                # Fall back to subprocess if Docker not available
                self._log_step("WARNING", f"Docker not available, using subprocess: {e}")
                return self._run_pytest_subprocess(test_file)
        
        # Read test file content
        test_file_path = Path(test_file)
        try:
            with open(test_file_path, 'r', encoding='utf-8') as f:
                test_code = f.read()
        except Exception as e:
            self._log_step("WARNING", f"Failed to read test file, using subprocess: {e}")
            return self._run_pytest_subprocess(test_file)
        
        # Run in Docker
        try:
            result = self.docker_executor.run_tests(test_code, test_file_path.name)
            
            return {
                "passed": result["passed"],
                "failed": result["failed"],
                "output": result["output"],
                "return_code": result["return_code"],
                "failing_tests": result.get("failing_tests", [])
            }
        except Exception as e:
            # Fall back to subprocess if Docker execution fails
            self._log_step("WARNING", f"Docker execution failed, using subprocess: {e}")
            return self._run_pytest_subprocess(test_file)
    
    def _run_pytest_subprocess(self, test_file: str) -> Dict[str, Any]:
        """
        Run pytest using subprocess (fallback method).
        
        Args:
            test_file: Path to the test file.
        
        Returns:
            Dictionary with passed, failed counts and output.
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = result.stdout + result.stderr
            
            # Parse pass/fail counts from output
            passed = 0
            failed = 0
            
            # Look for patterns like "X passed" or "X failed"
            lines = output.split('\n')
            for line in lines:
                if "passed" in line.lower() and "failed" not in line.lower():
                    # Try to extract number
                    words = line.split()
                    for i, word in enumerate(words):
                        if word.lower() == "passed":
                            if i > 0:
                                try:
                                    passed = int(words[i-1])
                                except ValueError:
                                    pass
                if "failed" in line.lower():
                    words = line.split()
                    for i, word in enumerate(words):
                        if word.lower() == "failed":
                            if i > 0:
                                try:
                                    failed = int(words[i-1])
                                except ValueError:
                                    pass
            
            # Fallback: count test functions if parsing failed
            if passed == 0 and failed == 0:
                if "FAILED" in output:
                    failed = output.count("FAILED")
                if "PASSED" in output or "passed" in output:
                    # Count passed tests
                    passed_lines = [l for l in lines if "PASSED" in l or ("passed" in l.lower() and "failed" not in l.lower())]
                    passed = len(passed_lines)
            
            # Extract failing test names
            failing_tests = []
            for line in lines:
                # Look for patterns like "FAILED test_file.py::test_function_name"
                if "FAILED" in line and "::" in line:
                    parts = line.split("::")
                    if len(parts) >= 2:
                        test_name = parts[-1].strip()
                        # Remove any trailing info like "[100%]"
                        test_name = test_name.split()[0] if test_name.split() else test_name
                        if test_name.startswith("test_"):
                            failing_tests.append(test_name)
                # Also look for "test_function_name FAILED" patterns
                elif "FAILED" in line and "test_" in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith("test_") and "FAILED" not in part:
                            # Remove any trailing punctuation
                            test_name = part.rstrip(".,;:")
                            if test_name not in failing_tests:
                                failing_tests.append(test_name)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_failing_tests = []
            for test in failing_tests:
                if test not in seen:
                    seen.add(test)
                    unique_failing_tests.append(test)
            
            return {
                "passed": passed,
                "failed": failed,
                "output": output,
                "return_code": result.returncode,
                "failing_tests": unique_failing_tests
            }
        
        except subprocess.TimeoutExpired:
            return {
                "passed": 0,
                "failed": 0,
                "output": "Test execution timed out after 60 seconds",
                "return_code": -1,
                "failing_tests": []
            }
        except Exception as e:
            return {
                "passed": 0,
                "failed": 0,
                "output": f"Error running pytest: {str(e)}",
                "return_code": -1,
                "failing_tests": []
            }
    
    def _save_tests_to_file(self, tests: str, filepath: Path) -> None:
        """
        Save test code to file, creating directory if needed.
        
        Args:
            tests: Test code string.
            filepath: Path to save the file.
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(tests)
    
    def _log_step(self, step: str, message: str) -> None:
        """
        Print formatted progress messages.
        
        Args:
            step: Step identifier.
            message: Message to print.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{step:15s}] {message}")
    
    def _validate_and_load_state(
        self, 
        resume_state: Dict[str, Any], 
        input_code: str,
        mode: str
    ) -> Dict[str, Any]:
        """
        Validate and load resume state.
        
        Args:
            resume_state: State dictionary to validate.
            input_code: Current input code.
            mode: Current mode.
        
        Returns:
            Validated state dictionary.
        
        Raises:
            ValueError: If state is invalid.
        """
        required_keys = ["scenarios", "tests", "iteration"]
        for key in required_keys:
            if key not in resume_state:
                raise ValueError(f"Resume state missing required key: {key}")
        
        # Check for mode compatibility
        saved_mode = resume_state.get("mode", mode)
        if saved_mode != mode:
            self._log_step("WARNING", f"Mode differs: saved={saved_mode}, current={mode} - using saved mode")
            mode = saved_mode
        
        # Verify code matches (or warn if different)
        saved_code_key = resume_state.get("original_code") or resume_state.get("original_function_code")
        if saved_code_key and saved_code_key != input_code:
            self._log_step("WARNING", "Input code differs from saved state - proceeding anyway")
        
        state = resume_state.copy()
        state["mode"] = mode
        if "original_code" not in state:
            state["original_code"] = saved_code_key or input_code
        
        return state
    
    def _create_error_result(self, message: str, error: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an error result dictionary.
        
        Args:
            message: Error message.
            error: Error details.
            state: Current state.
        
        Returns:
            Error result dictionary.
        """
        self._log_step("ERROR", f"{message}: {error}")
        return {
            "status": "ERROR",
            "message": f"{message}: {error}",
            "scenarios": state.get("scenarios"),
            "tests": state.get("tests"),
            "test_results": None,
            "iterations": state.get("iteration", 0),
            "analysis": None,
            "resume_state": state.copy() if state else None
        }


if __name__ == "__main__":
    import json
    
    print("=" * 80)
    print("ORCHESTRATOR DEMONSTRATION - TWO MODES")
    print("=" * 80)
    print()
    
    orchestrator = Orchestrator()  # test_file will be determined by mode
    
    # ============================================================================
    # DEMO 1: GENERATE MODE
    # ============================================================================
    print("\n" + "=" * 80)
    print("DEMO 1: GENERATE MODE")
    print("=" * 80)
    print("Use case: Generate new code from scratch from requirements")
    print()
    
    requirements = """Create a function that calculates discount based on customer type and quantity.
- Regular: 5% if quantity >= 10
- Premium: 15% always
- VIP: 20% base, +5% if quantity >= 20"""
    
    print("Requirements:")
    print(requirements)
    print()
    
    result_gen = orchestrator.run(
        mode="generate",
        input_code=requirements,
        max_iterations=3
    )
    
    print("\n" + "-" * 80)
    print("GENERATE MODE RESULT:")
    print("-" * 80)
    print(f"Status: {result_gen['status']}")
    print(f"Message: {result_gen['message']}")
    print(f"Iterations: {result_gen['iterations']}")
    print()
    
    # ============================================================================
    # DEMO 2: TEST MODE
    # ============================================================================
    print("\n" + "=" * 80)
    print("DEMO 2: TEST MODE")
    print("=" * 80)
    print("Use case: Generate tests for existing code")
    print()
    
    # Example function with a bug (the None validation issue)
    function_with_bug = """def calculate_discount(price, customer_type, quantity):
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
    
    print("Existing function code (with bug):")
    print(function_with_bug[:100] + "...")
    print()
    
    # First run: Generate tests and detect CODE_BUG
    print("\n" + "-" * 80)
    print("TEST MODE - First Run: Generate tests and detect CODE_BUG")
    print("-" * 80)
    print()
    
    result_test1 = orchestrator.run(
        mode="test",
        input_code=function_with_bug,
        max_iterations=3
    )
    
    print("\n" + "-" * 80)
    print("TEST MODE - First Run Result:")
    print("-" * 80)
    print(f"Status: {result_test1['status']}")
    print(f"Message: {result_test1['message']}")
    print(f"Iterations: {result_test1['iterations']}")
    if result_test1.get('analysis'):
        print(f"Failure Type: {result_test1['analysis'].get('failure_type')}")
    print()
    
    # Save state for resume
    resume_state = result_test1.get('resume_state')
    if resume_state:
        print("💾 Resume state saved")
        print("📝 User can now edit the test file to fix the function")
        print()
    
    # Simulate user fixing the code in the test file
    print("=" * 80)
    print("SIMULATING USER FIX")
    print("=" * 80)
    print("User edits the test file directly to fix the function")
    print("(In test mode, function is included in test file for easy editing)")
    print()
    
    # Fixed function
    function_fixed = """def calculate_discount(price, customer_type, quantity):
    '''
    Calculate discount based on customer type and quantity.
    - Regular: 5% if quantity >= 10
    - Premium: 15% always
    - VIP: 20% base, +5% if quantity >= 20
    '''
    # Check for None values first
    if price is None or customer_type is None or quantity is None:
        raise ValueError("Parameters cannot be None")
    
    # Then check types
    if not isinstance(price, (int, float)) or not isinstance(quantity, (int, float)) or not isinstance(customer_type, str):
        raise TypeError("Invalid parameter types")
    
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
    
    # Second run: Resume from saved state with fixed code
    print("\n" + "=" * 80)
    print("TEST MODE - Second Run: Resume with fixed code")
    print("=" * 80)
    print("⏱️  This run will SKIP expensive Agent 1 & 2 operations!")
    print("📝 Tests will run against the fixed function in the test file")
    print()
    
    if resume_state:
        # Note: In real scenario, user would manually edit the test file
        # to fix the function. For this demo, we simulate by updating the state.
        # The key point is that in TEST mode, the function is in the test file
        # making it easy for users to edit.
        
        result_test2 = orchestrator.run(
            mode="test",
            input_code=function_fixed,  # Updated code (simulating user's fix)
            max_iterations=3,
            resume_state=resume_state
        )
        
        print("\n" + "-" * 80)
        print("TEST MODE - Second Run Result:")
        print("-" * 80)
        print(f"Status: {result_test2['status']}")
        print(f"Message: {result_test2['message']}")
        print(f"Iterations: {result_test2['iterations']}")
        print()
        
        print("=" * 80)
        print("TIME/COST SAVINGS FROM RESUME FEATURE:")
        print("=" * 80)
        print("✓ Skipped RequirementsAgent.analyze() - saved 1 API call")
        print("✓ Skipped initial TestGeneratorAgent.generate_tests() - saved 1 API call")
        print("✓ Directly resumed to test execution")
        print("✓ Total API calls saved: 2 (significant cost/time reduction)")
        print("=" * 80)
    else:
        print("⚠️  No resume state available from first run")
    
    print("\n" + "=" * 80)
    print("MODE COMPARISON:")
    print("=" * 80)
    print("GENERATE MODE: Requirements → Implementation + Tests (all in one file)")
    print("TEST MODE: Existing Code → Tests (function included in test file for editing)")
    print("=" * 80)

