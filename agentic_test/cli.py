"""
Agentic Test Generator CLI - Professional command-line interface for AI-powered test generation.
"""

import sys
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

import click
from colorama import init, Fore, Style

# Initialize colorama for Windows support
init(autoreset=True)

# Add backend to path for imports
_backend_path = Path(__file__).parent.parent / "backend"
if str(_backend_path) not in sys.path:
    sys.path.insert(0, str(_backend_path))

from core.orchestrator import Orchestrator


# ============================================================================
# Helper Functions
# ============================================================================

def print_banner():
    """Print ASCII art banner."""
    banner = f"""
{Fore.CYAN}{'=' * 70}
{Fore.CYAN}  Agentic Test Generator
{Fore.CYAN}  AI-Powered Test Creation with Multi-Agent Orchestration
{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}
"""
    click.echo(banner)


def print_progress(step: int, total: int, message: str):
    """Print formatted progress indicator."""
    click.echo(f"{Fore.YELLOW}[{step}/{total}]{Style.RESET_ALL} {message}")


def print_success(msg: str):
    """Print success message with green checkmark."""
    click.echo(f"{Fore.GREEN}✓{Style.RESET_ALL} {msg}")


def print_error(msg: str):
    """Print error message with red X."""
    click.echo(f"{Fore.RED}✗{Style.RESET_ALL} {msg}", err=True)


def print_warning(msg: str):
    """Print warning message with yellow warning symbol."""
    click.echo(f"{Fore.YELLOW}⚠{Style.RESET_ALL} {msg}")


def print_info(msg: str):
    """Print info message."""
    click.echo(f"{Fore.BLUE}ℹ{Style.RESET_ALL} {msg}")


def get_config_dir() -> Path:
    """Get configuration directory path."""
    home = Path.home()
    config_dir = home / ".agentic-test"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_config_file() -> Path:
    """Get configuration file path."""
    return get_config_dir() / "config.json"


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    config_file = get_config_file()
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(config: Dict[str, Any]):
    """Save configuration to file."""
    config_file = get_config_file()
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def load_state(state_file: str) -> Optional[Dict[str, Any]]:
    """Load state from JSON file."""
    state_path = Path(state_file)
    if not state_path.exists():
        return None
    
    try:
        with open(state_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load state file: {e}")
        return None


def save_state(state_file: str, data: Dict[str, Any]):
    """Save state to JSON file."""
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(state_path, 'w') as f:
            json.dump(data, f, indent=2)
        print_success(f"State saved to {state_path}")
    except Exception as e:
        print_error(f"Failed to save state: {e}")


def read_file_content(filepath: Path) -> Optional[str]:
    """Read file content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print_error(f"Failed to read file {filepath}: {e}")
        return None


def extract_function_from_code(code: str, function_name: str) -> Optional[str]:
    """Extract a specific function from code."""
    lines = code.split('\n')
    in_function = False
    function_lines = []
    indent_level = None
    
    for line in lines:
        # Check if this is the function we're looking for
        if f"def {function_name}" in line:
            in_function = True
            function_lines.append(line)
            # Determine indent level
            indent_level = len(line) - len(line.lstrip())
            continue
        
        if in_function:
            # Check if we've reached the end of the function
            current_indent = len(line) - len(line.lstrip()) if line.strip() else None
            if current_indent is not None and current_indent <= indent_level and line.strip():
                if not line.strip().startswith('#'):
                    break
            
            function_lines.append(line)
    
    if function_lines:
        return '\n'.join(function_lines)
    return None


# ============================================================================
# CLI Commands
# ============================================================================

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Agentic Test Generator - AI-powered test creation with multi-agent orchestration"""
    pass


@cli.command()
@click.argument('requirements', type=str)
@click.option('--output', '-o', default='generated_tests/', help='Output directory for generated tests')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed progress')
@click.option('--max-iterations', default=5, help='Maximum test regeneration iterations')
def generate(requirements, output, verbose, max_iterations):
    """Generate implementation and tests from requirements.
    
    Example: agentic-test generate "function that validates email addresses"
    """
    print_banner()
    
    try:
        print_progress(1, 4, "Initializing orchestrator...")
        orchestrator = Orchestrator()
        
        print_progress(2, 4, "Analyzing requirements and generating code...")
        if verbose:
            click.echo(f"{Fore.CYAN}Requirements:{Style.RESET_ALL} {requirements[:100]}...")
        
        result = orchestrator.run(
            mode="generate",
            input_code=requirements,
            max_iterations=max_iterations
        )
        
        print_progress(3, 4, "Processing results...")
        
        # Print results summary
        click.echo()
        click.echo(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}RESULTS SUMMARY{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        
        status = result.get('status', 'UNKNOWN')
        status_colors = {
            'SUCCESS': Fore.GREEN,
            'CODE_BUG': Fore.YELLOW,
            'TEST_BUG': Fore.YELLOW,
            'REQUIREMENTS_AMBIGUITY': Fore.YELLOW,
            'MAX_ITERATIONS': Fore.YELLOW,
            'ERROR': Fore.RED
        }
        status_color = status_colors.get(status, Fore.WHITE)
        
        click.echo(f"Status: {status_color}{status}{Style.RESET_ALL}")
        click.echo(f"Message: {result.get('message', 'N/A')}")
        click.echo(f"Iterations: {result.get('iterations', 0)}")
        
        if result.get('test_results'):
            test_results = result['test_results']
            passed = test_results.get('passed', 0)
            failed = test_results.get('failed', 0)
            click.echo(f"Tests: {Fore.GREEN}{passed} passed{Style.RESET_ALL}, {Fore.RED}{failed} failed{Style.RESET_ALL}")
        
        print_progress(4, 4, "Finalizing...")
        
        # Show file location
        if result.get('tests'):
            test_file = orchestrator.test_file
            click.echo()
            print_success(f"Generated code saved to: {Fore.CYAN}{test_file}{Style.RESET_ALL}")
            
            if status == 'CODE_BUG' and result.get('resume_state'):
                state_file = '.agentic-test-state.json'
                save_state(state_file, result['resume_state'])
                print_warning(f"Code bug detected. State saved to {state_file}")
                print_info("Fix the code and run: agentic-test resume")
        
        click.echo()
        return 0
        
    except Exception as e:
        print_error(f"Generation failed: {e}")
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        return 1


@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--function', '-f', help='Specific function name to test')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed progress')
@click.option('--max-iterations', default=5, help='Maximum test regeneration iterations')
def test(filepath, function, verbose, max_iterations):
    """Generate tests for existing code.
    
    Example: agentic-test test calculator.py --function calculate_discount
    """
    print_banner()
    
    try:
        file_path = Path(filepath)
        
        print_progress(1, 4, f"Reading file: {file_path}")
        code = read_file_content(file_path)
        if not code:
            return 1
        
        # Extract function if specified
        if function:
            print_progress(2, 4, f"Extracting function: {function}")
            extracted = extract_function_from_code(code, function)
            if extracted:
                code = extracted
                if verbose:
                    click.echo(f"{Fore.CYAN}Extracted function:{Style.RESET_ALL}")
                    click.echo(code[:200] + "..." if len(code) > 200 else code)
            else:
                print_warning(f"Function '{function}' not found. Using entire file.")
        
        print_progress(3, 4, "Initializing orchestrator and generating tests...")
        orchestrator = Orchestrator()
        
        result = orchestrator.run(
            mode="test",
            input_code=code,
            max_iterations=max_iterations
        )
        
        print_progress(4, 4, "Processing results...")
        
        # Print results summary
        click.echo()
        click.echo(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}RESULTS SUMMARY{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        
        status = result.get('status', 'UNKNOWN')
        status_colors = {
            'SUCCESS': Fore.GREEN,
            'CODE_BUG': Fore.YELLOW,
            'TEST_BUG': Fore.YELLOW,
            'REQUIREMENTS_AMBIGUITY': Fore.YELLOW,
            'MAX_ITERATIONS': Fore.YELLOW,
            'STUCK_LOOP': Fore.RED,
            'ERROR': Fore.RED
        }
        status_color = status_colors.get(status, Fore.WHITE)
        
        click.echo(f"Status: {status_color}{status}{Style.RESET_ALL}")
        click.echo(f"Message: {result.get('message', 'N/A')}")
        click.echo(f"Iterations: {result.get('iterations', 0)}")
        
        if result.get('test_results'):
            test_results = result['test_results']
            passed = test_results.get('passed', 0)
            failed = test_results.get('failed', 0)
            click.echo(f"Tests: {Fore.GREEN}{passed} passed{Style.RESET_ALL}, {Fore.RED}{failed} failed{Style.RESET_ALL}")
        
        # Show stuck loop analysis if detected
        if status == 'STUCK_LOOP' and result.get('analysis'):
            analysis = result['analysis']
            click.echo()
            click.echo(f"{Fore.RED}{'=' * 70}{Style.RESET_ALL}")
            click.echo(f"{Fore.RED}STUCK LOOP DETECTED{Style.RESET_ALL}")
            click.echo(f"{Fore.RED}{'=' * 70}{Style.RESET_ALL}")
            
            failing = analysis.get('failing_tests', [])
            click.echo(f"Same {len(failing)} test(s) failing after {analysis.get('iterations_stuck', 3)} iterations:")
            for test in failing:
                click.echo(f"  - {test}")
            
            click.echo()
            print_warning("Cannot determine if code or tests are wrong without requirements.")
            print_info("Suggestions:")
            click.echo("  1. Add a docstring to your function specifying expected behavior")
            click.echo("  2. Review the failing tests manually to see what they expect")
            click.echo("  3. Run with: agentic-test test --requirements 'your specs here'")
            
            test_file = orchestrator.test_file
            click.echo()
            print_info(f"Review tests in: {Fore.CYAN}{test_file}{Style.RESET_ALL}")
        
        # Show analysis if CODE_BUG detected
        if status == 'CODE_BUG' and result.get('analysis'):
            analysis = result['analysis']
            click.echo()
            click.echo(f"{Fore.YELLOW}{'=' * 70}{Style.RESET_ALL}")
            click.echo(f"{Fore.YELLOW}FAILURE ANALYSIS{Style.RESET_ALL}")
            click.echo(f"{Fore.YELLOW}{'=' * 70}{Style.RESET_ALL}")
            click.echo(f"Failure Type: {analysis.get('failure_type', 'N/A')}")
            click.echo(f"Confidence: {analysis.get('confidence', 0)}%")
            click.echo()
            if analysis.get('analysis'):
                click.echo("Analysis:")
                click.echo(analysis['analysis'][:500] + "..." if len(analysis.get('analysis', '')) > 500 else analysis.get('analysis', ''))
            if analysis.get('suggested_fix'):
                click.echo()
                click.echo("Suggested Fix:")
                click.echo(analysis['suggested_fix'][:500] + "..." if len(analysis.get('suggested_fix', '')) > 500 else analysis.get('suggested_fix', ''))
        
        # Show file location and instructions
        if result.get('tests'):
            test_file = orchestrator.test_file
            click.echo()
            print_success(f"Tests saved to: {Fore.CYAN}{test_file}{Style.RESET_ALL}")
            print_info("The function is included in the test file for easy editing.")
            
            if status == 'CODE_BUG' and result.get('resume_state'):
                state_file = '.agentic-test-state.json'
                save_state(state_file, result['resume_state'])
                click.echo()
                print_warning("Code bug detected. State saved for resume.")
                print_info(f"1. Edit the function in: {test_file}")
                print_info(f"2. Run: {Fore.CYAN}agentic-test resume{Style.RESET_ALL}")
        
        click.echo()
        return 0
        
    except Exception as e:
        print_error(f"Test generation failed: {e}")
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        return 1


@cli.command()
@click.option('--state-file', default='.agentic-test-state.json', help='State file path')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed progress')
def resume(state_file, verbose):
    """Resume from saved state after fixing code bugs.
    
    Example: agentic-test resume
    """
    print_banner()
    
    try:
        print_progress(1, 3, f"Loading state from {state_file}...")
        resume_state = load_state(state_file)
        
        if not resume_state:
            print_error(f"State file not found: {state_file}")
            print_info("Run 'agentic-test test' or 'agentic-test generate' first to create state.")
            return 1
        
        mode = resume_state.get('mode', 'test')
        checkpoint = resume_state.get('checkpoint_reason', 'Unknown')
        
        click.echo()
        print_info(f"Resuming from: {checkpoint}")
        print_info(f"Mode: {mode}")
        print_info(f"Iteration: {resume_state.get('iteration', 0)}")
        click.echo()
        
        print_progress(2, 3, "Initializing orchestrator...")
        orchestrator = Orchestrator()
        
        # Get function code from state or test file
        input_code = resume_state.get('original_code', '')
        if not input_code and resume_state.get('tests'):
            # Try to extract from test file
            test_file = orchestrator.test_file
            if Path(test_file).exists():
                code = read_file_content(Path(test_file))
                if code:
                    # Extract function (simplified - just use first function found)
                    lines = code.split('\n')
                    func_start = None
                    for i, line in enumerate(lines):
                        if line.strip().startswith('def '):
                            func_start = i
                            break
                    if func_start:
                        # Get function (up to next def or end)
                        func_lines = []
                        for i in range(func_start, len(lines)):
                            if i > func_start and lines[i].strip().startswith('def '):
                                break
                            func_lines.append(lines[i])
                        input_code = '\n'.join(func_lines)
        
        print_progress(3, 3, "Resuming test execution (skipping expensive operations)...")
        click.echo()
        print_info("⏱️  Skipping RequirementsAgent and TestGeneratorAgent calls")
        print_info("   (saving API costs and time)")
        click.echo()
        
        result = orchestrator.run(
            mode=mode,
            input_code=input_code,
            resume_state=resume_state
        )
        
        # Print results
        click.echo()
        click.echo(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}RESUME RESULTS{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        
        status = result.get('status', 'UNKNOWN')
        status_colors = {
            'SUCCESS': Fore.GREEN,
            'CODE_BUG': Fore.YELLOW,
            'TEST_BUG': Fore.YELLOW,
            'REQUIREMENTS_AMBIGUITY': Fore.YELLOW,
            'MAX_ITERATIONS': Fore.YELLOW,
            'STUCK_LOOP': Fore.RED,
            'ERROR': Fore.RED
        }
        status_color = status_colors.get(status, Fore.WHITE)
        
        click.echo(f"Status: {status_color}{status}{Style.RESET_ALL}")
        click.echo(f"Message: {result.get('message', 'N/A')}")
        click.echo(f"Iterations: {result.get('iterations', 0)}")
        
        if result.get('test_results'):
            test_results = result['test_results']
            passed = test_results.get('passed', 0)
            failed = test_results.get('failed', 0)
            click.echo(f"Tests: {Fore.GREEN}{passed} passed{Style.RESET_ALL}, {Fore.RED}{failed} failed{Style.RESET_ALL}")
        
        if status == 'SUCCESS':
            click.echo()
            print_success("All tests passed!")
        elif status == 'STUCK_LOOP' and result.get('analysis'):
            analysis = result['analysis']
            click.echo()
            print_warning("Stuck loop detected. Same tests failing repeatedly.")
            print_info("Consider adding requirements or reviewing the failing tests manually.")
        
        click.echo()
        return 0
        
    except Exception as e:
        print_error(f"Resume failed: {e}")
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        return 1


@cli.command()
def init():
    """Initialize configuration (set API key).
    
    Example: agentic-test init
    """
    print_banner()
    
    try:
        config_dir = get_config_dir()
        config_file = get_config_file()
        
        click.echo(f"Configuration directory: {Fore.CYAN}{config_dir}{Style.RESET_ALL}")
        click.echo()
        
        # Check if config exists
        existing_config = load_config()
        if existing_config.get('api_key'):
            click.echo("Current API key is set.")
            if not click.confirm("Do you want to update it?"):
                return 0
        
        # Prompt for API key
        click.echo("Enter your Anthropic API key:")
        click.echo("(You can get one from https://console.anthropic.com/)")
        api_key = click.prompt("API Key", hide_input=True)
        
        if not api_key:
            print_error("API key cannot be empty")
            return 1
        
        # Save config
        config = {'api_key': api_key}
        save_config(config)
        
        # Set environment variable for current session
        os.environ['ANTHROPIC_API_KEY'] = api_key
        
        click.echo()
        print_success("Configuration saved successfully!")
        print_info(f"Config file: {config_file}")
        
        # Validate by making a test call
        click.echo()
        click.echo("Validating API key...")
        try:
            from agents.requirements_agent import RequirementsAgent
            agent = RequirementsAgent()
            print_success("API key is valid!")
        except Exception as e:
            print_warning(f"API key validation failed: {e}")
            print_info("You may need to check your API key later.")
        
        click.echo()
        return 0
        
    except Exception as e:
        print_error(f"Initialization failed: {e}")
        return 1


@cli.command()
def info():
    """Show current configuration and project status.
    
    Example: agentic-test info
    """
    print_banner()
    
    try:
        config = load_config()
        config_file = get_config_file()
        state_file = Path('.agentic-test-state.json')
        
        click.echo(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}CONFIGURATION{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        
        if config.get('api_key'):
            masked_key = config['api_key'][:8] + "..." + config['api_key'][-4:] if len(config['api_key']) > 12 else "***"
            click.echo(f"API Key: {Fore.GREEN}Set{Style.RESET_ALL} ({masked_key})")
        else:
            click.echo(f"API Key: {Fore.RED}Not set{Style.RESET_ALL}")
            print_info("Run 'agentic-test init' to set your API key")
        
        click.echo(f"Config file: {config_file}")
        click.echo()
        
        # Check environment variable
        env_key = os.getenv('ANTHROPIC_API_KEY')
        if env_key:
            click.echo(f"Environment variable: {Fore.GREEN}Set{Style.RESET_ALL}")
        else:
            click.echo(f"Environment variable: {Fore.YELLOW}Not set{Style.RESET_ALL}")
        
        click.echo()
        
        # Check for state file
        click.echo(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}PROJECT STATUS{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        
        if state_file.exists():
            state = load_state(str(state_file))
            if state:
                mode = state.get('mode', 'unknown')
                iteration = state.get('iteration', 0)
                checkpoint = state.get('checkpoint_reason', 'Unknown')
                
                click.echo(f"State file: {Fore.GREEN}Found{Style.RESET_ALL}")
                click.echo(f"  Mode: {mode}")
                click.echo(f"  Iteration: {iteration}")
                click.echo(f"  Checkpoint: {checkpoint}")
                click.echo()
                print_info(f"Run 'agentic-test resume' to continue from saved state")
            else:
                click.echo(f"State file: {Fore.YELLOW}Exists but invalid{Style.RESET_ALL}")
        else:
            click.echo(f"State file: {Fore.YELLOW}Not found{Style.RESET_ALL}")
        
        # Check generated tests directory
        test_dir = Path('generated_tests')
        if test_dir.exists():
            test_files = list(test_dir.glob('test_*.py'))
            click.echo()
            click.echo(f"Generated tests: {Fore.GREEN}{len(test_files)} files{Style.RESET_ALL}")
            for test_file in test_files[:5]:  # Show first 5
                click.echo(f"  - {test_file.name}")
            if len(test_files) > 5:
                click.echo(f"  ... and {len(test_files) - 5} more")
        else:
            click.echo()
            click.echo(f"Generated tests: {Fore.YELLOW}No tests generated yet{Style.RESET_ALL}")
        
        click.echo()
        return 0
        
    except Exception as e:
        print_error(f"Info command failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(cli())

