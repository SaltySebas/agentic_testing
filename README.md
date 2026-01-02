# Agentic Test Generator

> AI-powered test generation using multi-agent orchestration with Claude

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Features

- **🤖 Multi-Agent System**: Coordinated AI agents for requirements analysis, test generation, and failure analysis
- **⚡ Dual Modes**: 
  - **GENERATE**: Create implementation + tests from natural language requirements
  - **TEST**: Generate comprehensive tests for existing code
- **💾 Smart Resume**: Save API costs by resuming from checkpoints after fixing bugs
- **🔄 Iterative Refinement**: Automatically regenerates tests when failures are detected
- **🎨 Beautiful CLI**: Colored terminal output with real-time progress indicators
- **🧠 Intelligent Analysis**: Distinguishes between code bugs, test bugs, and requirement ambiguities
- **🛡️ Stuck Loop Detection**: Prevents wasting iterations on unsolvable problems

## 📦 Installation

### From Source (Current)
```bash
git clone https://github.com/SaltySebas/agentic-testing.git
cd agentic-testing
pip install -e .
```

### Requirements
- Python 3.8+
- Anthropic API key ([Get one here](https://console.anthropic.com/))

## 🎯 Quick Start

### 1. Configure API Key
```bash
agentic-test init
# Enter your Anthropic API key when prompted
```

### 2. Generate Implementation + Tests
```bash
agentic-test generate "function that validates email addresses"
```

**Output:**
- ✅ Complete implementation
- ✅ 15-25 comprehensive tests
- ✅ All tests passing
- ✅ Saved to `generated_tests/`

### 3. Test Existing Code
```bash
agentic-test test my_code.py --function my_function
```

**If bugs detected:**
- 🔍 Analyzes failures
- 💡 Suggests specific fixes
- 💾 Saves state for resume

### 4. Resume After Fixing
```bash
# Fix your code based on suggestions
agentic-test resume
```

**Skips expensive operations:**
- ⏭️ Requirements analysis (cached)
- ⏭️ Test generation (cached)
- ✅ Re-runs tests with fixed code

## 📚 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `generate` | Create implementation + tests from requirements | `agentic-test generate "discount calculator"` |
| `test` | Generate tests for existing code | `agentic-test test app.py --function calculate` |
| `resume` | Continue from saved checkpoint | `agentic-test resume` |
| `init` | Configure API key | `agentic-test init` |
| `info` | Show configuration and status | `agentic-test info` |

### Command Options
```bash
# Verbose mode (show detailed progress)
agentic-test generate "..." --verbose

# Custom output directory
agentic-test generate "..." --output tests/

# Max iterations (default: 5)
agentic-test test code.py --max-iterations 3

# Specific function
agentic-test test module.py --function my_func
```

## 🏗️ Architecture

### Multi-Agent System
```
User Input
    ↓
Agent 1: Requirements Analyzer
  → Identifies test scenarios (happy path, edge cases, boundaries, errors)
    ↓
Agent 2: Test Generator
  → Writes executable pytest code
    ↓
Agent 3: Test Executor
  → Runs tests, captures results
    ↓
Agent 4: Failure Analyzer
  → Classifies failures (CODE_BUG vs TEST_BUG vs AMBIGUITY)
    ↓
Orchestrator
  → Coordinates agents, manages iteration loops, handles state
```

### Intelligent Iteration
```python
while not all_tests_pass and iterations < max:
    run_tests()
    if failures:
        analysis = analyze_failures()
        
        if analysis.type == "CODE_BUG":
            # Stop, alert user with specific fix
            save_state()
            break
            
        elif analysis.type == "TEST_BUG":
            # Auto-regenerate tests
            regenerate_tests()
            continue
            
        elif analysis.type == "REQUIREMENTS_AMBIGUITY":
            # Stop, ask user for clarification
            save_state()
            break
```

## 💡 Examples

### Example 1: Generate Discount Calculator
```bash
$ agentic-test generate "Calculate discount: Regular 5% if qty>=10, Premium 15%, VIP 20% + 5% bonus if qty>=20"

[1/4] Analyzing requirements...
      ✓ Identified 25 test scenarios
[2/4] Generating implementation + tests...
      ✓ Generated 234 lines of code
[3/4] Running tests...
      ✓ 20/20 tests passed
[4/4] Saving results...
      ✓ Saved to generated_tests/test_generated.py

✅ SUCCESS! Generated working implementation with 20 comprehensive tests.
```

### Example 2: Test Existing Code with Bug
```bash
$ agentic-test test calculator.py --function calculate_discount

[1/4] Reading file...
[2/4] Generating tests...
[3/4] Running tests...
      ⚠️ 18/25 passed, 7 failed
[4/4] Analyzing failures...
      🔴 CODE BUG DETECTED (confidence: 95%)

Bug found on line 12:
  Current: if quantity > 10:
  Should be: if quantity >= 10:
  
Reason: Off-by-one error. Quantity of exactly 10 should qualify.

💾 State saved. Fix the bug and run: agentic-test resume
```

## 🛠️ Tech Stack

- **LLM**: Claude Sonnet 4 (Anthropic)
- **Framework**: Click (CLI), FastAPI (future web API)
- **Testing**: pytest
- **State**: JSON persistence
- **Languages**: Python 3.8+

## 📊 Project Status

**Current:** v0.1.0 - CLI MVP Complete

**Implemented:**
- ✅ Multi-agent orchestration
- ✅ GENERATE mode
- ✅ TEST mode
- ✅ State persistence & resume
- ✅ Stuck loop detection
- ✅ Professional CLI

**Roadmap:**
- 🔨 Agent 3: Docker test executor
- 🔨 Web UI (FastAPI + React)
- 🔨 VS Code extension
- 🔨 GitHub Action integration
- 🔨 PyPI publication

## 🤝 Contributing

This is a portfolio/learning project. Suggestions and feedback welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Built with [Claude](https://claude.ai) (Anthropic)
- Inspired by modern AI-powered development tools
- Created as a learning project in multi-agent systems

## 📧 Contact

Sebastian Alvarez (SaltySebas) - [GitHub](https://github.com/SaltySebas)

Project Link: [https://github.com/SaltySebas/agentic-testing](https://github.com/SaltySebas/agentic-testing)

---

**⭐ If you find this project useful, please star the repo!**

