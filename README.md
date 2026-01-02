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

### CLI Tool

**From Source:**
```bash
git clone https://github.com/SaltySebas/agentic-testing.git
cd agentic-testing
pip install -e .
```

**Requirements:**
- Python 3.8+
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Web Interface

**Prerequisites:**
- Python 3.8+
- Node.js 18+
- Docker Desktop
- Anthropic API key

**Backend Setup:**
```bash
# Clone and install
git clone https://github.com/SaltySebas/agentic-testing.git
cd agentic-testing
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure API key
agentic-test init

# Build Docker image
docker build -t agentic_test-runner:latest docker/
```

**Frontend Setup:**
```bash
cd frontend
npm install
```

**Run:**
```bash
# Terminal 1: Backend
python backend/api/main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

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

## 🌐 Web Interface

### Access the Web UI

**Start the backend:**
```bash
python backend/api/main.py
# Server runs on http://localhost:8000
```

**Start the frontend:**
```bash
cd frontend
npm install  # First time only
npm run dev
# UI opens on http://localhost:5173
```

**Open browser:** http://localhost:5173

### Features

- **🎨 Beautiful Dark Theme**: Modern UI with Tailwind CSS
- **📝 Dual Modes**: Switch between Generate and Test modes
- **⚡ Real-time Progress**: Live updates via WebSocket
- **👥 Agent Visualization**: See agents working in real-time
- **💾 Download Results**: Export generated tests
- **🔄 Resume Support**: Continue from saved checkpoints
- **📊 Test Results**: Visual pass/fail statistics
- **🎯 Syntax Highlighting**: Color-coded Python code display

### Usage

1. **Generate Mode:**
   - Enter requirements in natural language
   - Adjust max iterations (1-10)
   - Click "Generate Tests"
   - Watch agents work in real-time
   - Download generated code

2. **Test Mode:**
   - Paste your function code
   - Click "Test Code"
   - View test results and analysis
   - Fix code if bugs detected
   - Resume to re-run tests

### API Endpoints

The backend provides REST API and WebSocket endpoints:

**REST API:**
- `POST /api/generate` - Generate implementation + tests
- `POST /api/test` - Generate tests for existing code
- `POST /api/resume` - Resume from checkpoint
- `GET /api/status` - System status (Docker availability)
- `GET /health` - Health check

**WebSocket:**
- `WS /ws/{client_id}` - Real-time progress updates

**API Documentation:** http://localhost:8000/docs (Swagger UI)

### Tech Stack

**Backend:**
- FastAPI (Python web framework)
- WebSockets (real-time communication)
- Docker integration
- CORS enabled

**Frontend:**
- React 18 (UI framework)
- Vite 5 (build tool)
- Tailwind CSS (styling)
- Axios (HTTP client)
- React Syntax Highlighter (code display)

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

## 📸 Screenshots

### Web Interface
- **Generate Mode**: AI creates implementation + tests from requirements
- **Test Mode**: Generate tests for existing code
- **Real-time Progress**: Watch agents work through the pipeline
- **Results Display**: View test results with syntax highlighting

[Add actual screenshots when available]

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
- **Framework**: Click (CLI), FastAPI (Web API)
- **Frontend**: React 18, Vite, Tailwind CSS
- **Testing**: pytest, Docker executor
- **State**: JSON persistence
- **Languages**: Python 3.8+, JavaScript (ES6+)

## 📊 Project Status

**Current:** v1.0.0 - Production Ready

**Completed:**
- ✅ Multi-agent orchestration (4 agents)
- ✅ GENERATE mode (requirements → code + tests)
- ✅ TEST mode (code → tests)
- ✅ Docker test executor (isolated, secure)
- ✅ State persistence & resume capability
- ✅ Stuck loop detection
- ✅ Professional CLI (5 commands)
- ✅ REST API backend (FastAPI)
- ✅ Web UI (React + Tailwind)
- ✅ Real-time WebSocket updates
- ✅ API documentation (Swagger)

**Deployment Ready:**
- Backend: Railway, Heroku, AWS
- Frontend: Vercel, Netlify
- Docker: Docker Hub, AWS ECR

**Roadmap:**
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




