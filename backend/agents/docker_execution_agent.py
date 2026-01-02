"""
DockerExecutorAgent - Safely runs pytest tests in isolated Docker containers.
"""

import os
import re
import logging
import tempfile
import shutil
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import docker
    from docker.errors import DockerException, ContainerError, ImageNotFound, APIError
except ImportError:
    raise ImportError(
        "docker package is required. Install it with: pip install docker"
    )


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DockerExecutorAgent:
    """
    Agent that safely executes pytest tests in isolated Docker containers.
    
    This class provides a secure way to run untrusted test code by:
    - Running tests in isolated Docker containers
    - Using a non-root user inside containers
    - Enforcing timeouts
    - Cleaning up resources automatically
    """
    
    def __init__(
        self,
        image_name: str = "agentic_test-runner:latest",
        timeout: int = 60,
        docker_client: Optional[docker.DockerClient] = None
    ):
        """
        Initialize the DockerExecutorAgent.
        
        Args:
            image_name: Docker image name to use for test execution
            timeout: Maximum time (in seconds) to wait for test execution
            docker_client: Optional Docker client. If not provided, creates a new one.
        
        Raises:
            DockerException: If Docker daemon is not running or accessible
            ImageNotFound: If the specified Docker image is not found
        """
        self.image_name = image_name
        self.timeout = timeout
        
        try:
            self.client = docker_client or docker.from_env()
            # Test Docker connection
            self.client.ping()
            logger.info(f"Docker client initialized successfully")
        except DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise DockerException(
                "Docker daemon is not running or not accessible. "
                "Please ensure Docker is running and you have permission to access it."
            ) from e
        
        # Verify image exists
        try:
            self.client.images.get(image_name)
            logger.info(f"Docker image '{image_name}' found")
        except ImageNotFound:
            logger.warning(
                f"Docker image '{image_name}' not found. "
                f"Please build it with: docker build -t {image_name} -f docker/Dockerfile ."
            )
            raise ImageNotFound(
                f"Docker image '{image_name}' not found. "
                f"Build it first with: docker build -t {image_name} -f docker/Dockerfile ."
            )
    
    def run_tests(self, test_code: str, test_filename: str = "test_generated.py") -> Dict[str, Any]:
        """
        Run pytest tests in an isolated Docker container.
        
        Args:
            test_code: Python code containing pytest tests
            test_filename: Name of the test file to create (default: test_generated.py)
        
        Returns:
            Dictionary containing:
            - passed: Number of passed tests
            - failed: Number of failed tests
            - output: Full stdout/stderr output from pytest
            - return_code: Exit code from pytest (0 = success, non-zero = failure)
            - failing_tests: List of failed test function names
        
        Raises:
            DockerException: If Docker operations fail
            TimeoutError: If test execution exceeds timeout
        """
        temp_dir = None
        container = None
        
        try:
            # Create temporary directory for test file
            temp_dir = tempfile.mkdtemp(prefix="docker_test_")
            logger.info(f"Created temporary directory: {temp_dir}")
            
            # Write test code to file
            test_file_path = Path(temp_dir) / test_filename
            test_file_path.write_text(test_code, encoding='utf-8')
            logger.info(f"Written test code to {test_file_path}")
            
            # Create container with volume mount
            container = self._create_container(temp_dir, test_filename)
            logger.info(f"Created container: {container.id[:12]}")
            
            # Run pytest in container
            result = self._execute_tests(container)
            
            return result
            
        except Exception as e:
            logger.error(f"Error during test execution: {e}", exc_info=True)
            # Return error result
            return {
                "passed": 0,
                "failed": 0,
                "output": f"Error: {str(e)}",
                "return_code": -1,
                "failing_tests": []
            }
        
        finally:
            # Clean up container
            if container:
                self._cleanup_container(container)
            
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")
    
    def _create_container(self, temp_dir: str, test_filename: str) -> docker.models.containers.Container:
        """
        Create a Docker container with the test directory mounted.
        
        Args:
            temp_dir: Path to temporary directory containing test files
            test_filename: Name of the test file to run
        
        Returns:
            Docker container instance
        
        Raises:
            APIError: If container creation fails
        """
        try:
            container = self.client.containers.create(
                image=self.image_name,
                command=["pytest", "-v", "--tb=short", f"/app/tests/{test_filename}"],
                volumes={
                    temp_dir: {
                        'bind': '/app/tests',
                        'mode': 'ro'  # Read-only mount for security
                    }
                },
                working_dir='/app',
                detach=True,
                # remove parameter not needed - we clean up manually
                mem_limit='512m',  # Limit memory usage
                cpu_period=100000,
                cpu_quota=50000,  # Limit CPU to 50%
                network_disabled=True,  # Disable network for security
                security_opt=['no-new-privileges:true'],  # Security hardening
            )
            return container
        except APIError as e:
            logger.error(f"Failed to create container: {e}")
            raise
    
    def _execute_tests(
        self,
        container: docker.models.containers.Container
    ) -> Dict[str, Any]:
        """
        Execute tests in the container and capture output.
        
        Args:
            container: Docker container instance
        
        Returns:
            Dictionary with test results
        
        Raises:
            TimeoutError: If execution exceeds timeout
        """
        try:
            # Start container
            container.start()
            logger.info(f"Started container: {container.id[:12]}")
            
            # Wait for container to finish with timeout
            try:
                exit_code = container.wait(timeout=self.timeout)['StatusCode']
            except Exception as e:
                # Container might still be running, try to stop it
                try:
                    container.stop(timeout=5)
                except:
                    pass
                raise TimeoutError(
                    f"Test execution exceeded timeout of {self.timeout} seconds"
                ) from e
            
            # Get logs (stdout and stderr)
            logs = container.logs(stdout=True, stderr=True).decode('utf-8', errors='replace')
            logger.info(f"Container exited with code {exit_code}")
            logger.debug(f"Test output:\n{logs}")
            
            # Parse pytest output
            parsed_results = self._parse_pytest_output(logs)
            
            return {
                "passed": parsed_results["passed"],
                "failed": parsed_results["failed"],
                "output": logs,
                "return_code": exit_code,
                "failing_tests": parsed_results["failing_tests"]
            }
            
        except ContainerError as e:
            logger.error(f"Container error: {e}")
            logs = e.container.logs(stdout=True, stderr=True).decode('utf-8', errors='replace')
            parsed_results = self._parse_pytest_output(logs)
            return {
                "passed": parsed_results["passed"],
                "failed": parsed_results["failed"],
                "output": logs,
                "return_code": e.exit_status,
                "failing_tests": parsed_results["failing_tests"]
            }
    
    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """
        Parse pytest output to extract test results.
        
        Args:
            output: Raw pytest output string
        
        Returns:
            Dictionary with parsed results:
            - passed: Number of passed tests
            - failed: Number of failed tests
            - failing_tests: List of failed test function names
        """
        passed = 0
        failed = 0
        failing_tests = []
        
        # Pattern to match pytest summary line: "X passed, Y failed in Z.XXs"
        summary_pattern = r'(\d+)\s+passed|(\d+)\s+failed'
        
        # Find all matches
        matches = re.findall(summary_pattern, output)
        for match in matches:
            if match[0]:  # passed count
                passed = int(match[0])
            if match[1]:  # failed count
                failed = int(match[1])
        
        # Extract failing test names
        # Pattern: "FAILED test_filename.py::test_function_name"
        failed_test_pattern = r'FAILED\s+[\w/]+::(\w+)'
        failing_tests = re.findall(failed_test_pattern, output)
        
        # Also try pattern: "test_function_name FAILED"
        if not failing_tests:
            failed_test_pattern2 = r'(\w+)\s+FAILED'
            failing_tests = re.findall(failed_test_pattern2, output)
        
        # Remove duplicates while preserving order
        failing_tests = list(dict.fromkeys(failing_tests))
        
        logger.info(f"Parsed results: {passed} passed, {failed} failed")
        if failing_tests:
            logger.info(f"Failing tests: {', '.join(failing_tests)}")
        
        return {
            "passed": passed,
            "failed": failed,
            "failing_tests": failing_tests
        }
    
    def _cleanup_container(self, container: docker.models.containers.Container) -> None:
        """
        Clean up Docker container, ensuring it's removed.
        
        Args:
            container: Docker container instance to clean up
        """
        try:
            # Try to stop if still running
            try:
                container.reload()
                if container.status == 'running':
                    container.stop(timeout=5)
                    logger.info(f"Stopped container: {container.id[:12]}")
            except Exception as e:
                logger.warning(f"Error stopping container: {e}")
            
            # Remove container
            try:
                container.remove()
                logger.info(f"Removed container: {container.id[:12]}")
            except Exception as e:
                logger.warning(f"Error removing container: {e}")
                
        except Exception as e:
            logger.warning(f"Error during container cleanup: {e}")


if __name__ == "__main__":
    """
    Example usage of DockerExecutorAgent.
    """
    print("=" * 60)
    print("DockerExecutorAgent Test")
    print("=" * 60)
    
    try:
        # Initialize agent
        print("\n1. Initializing DockerExecutorAgent...")
        executor = DockerExecutorAgent()
        print("✓ DockerExecutorAgent initialized successfully")
        
        # Test 1: Simple passing test
        print("\n2. Running passing test...")
        passing_test = """
def test_simple_addition():
    '''Test that 1 + 1 equals 2'''
    assert 1 + 1 == 2
"""
        result1 = executor.run_tests(passing_test, "test_passing.py")
        print(f"   Return code: {result1['return_code']}")
        print(f"   Passed: {result1['passed']}")
        print(f"   Failed: {result1['failed']}")
        print(f"   Failing tests: {result1['failing_tests']}")
        if result1['return_code'] == 0:
            print("   ✓ Test passed successfully!")
        else:
            print("   ✗ Test failed unexpectedly")
            print(f"   Output:\n{result1['output']}")
        
        # Test 2: Failing test
        print("\n3. Running failing test...")
        failing_test = """
def test_wrong_assertion():
    '''Test that intentionally fails'''
    assert 1 + 1 == 3, "This should fail"
"""
        result2 = executor.run_tests(failing_test, "test_failing.py")
        print(f"   Return code: {result2['return_code']}")
        print(f"   Passed: {result2['passed']}")
        print(f"   Failed: {result2['failed']}")
        print(f"   Failing tests: {result2['failing_tests']}")
        if result2['return_code'] != 0 and result2['failed'] > 0:
            print("   ✓ Failure detected correctly!")
        else:
            print("   ✗ Expected failure but test passed")
        
        # Test 3: Multiple tests (some pass, some fail)
        print("\n4. Running multiple tests (mixed results)...")
        mixed_tests = """
def test_passing_one():
    assert 2 * 2 == 4

def test_passing_two():
    assert "hello".upper() == "HELLO"

def test_failing_one():
    assert 5 + 5 == 20

def test_failing_two():
    assert True == False
"""
        result3 = executor.run_tests(mixed_tests, "test_mixed.py")
        print(f"   Return code: {result3['return_code']}")
        print(f"   Passed: {result3['passed']}")
        print(f"   Failed: {result3['failed']}")
        print(f"   Failing tests: {result3['failing_tests']}")
        if result3['passed'] == 2 and result3['failed'] == 2:
            print("   ✓ Mixed results detected correctly!")
        else:
            print("   ✗ Unexpected results")
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except DockerException as e:
        print(f"\n✗ Docker error: {e}")
        print("   Make sure Docker is running and the image is built:")
        print("   docker build -t agentic_test-runner:latest -f docker/Dockerfile .")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

