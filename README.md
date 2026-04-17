# DebtGuardianAgentic
> An LLM-powered multi-agent system for detecting Technical Debt in real-world software repositories.

DebtGuardianAgentic is an AI-powered source code analysis tool that uses a multi-agent architecture to detect and explain technical debt (code smells) in source code. It leverages specialized LLM agents at different granularities and exposes both a CLI and a web UI served by a Flask REST API.

---

## Multi-Agent Architecture

| Agent | Role |
|---|---|
| **Program Slicer** | AST-based extraction of classes and methods with structural metrics (LOC, complexity, field/method counts). Powered by [source-parser](https://github.com/microsoft/source_parser). |
| **Class-Level Detector** | Detects Blob and Data Class smells using few-shot LLM prompting |
| **Method-Level Detector** | Detects Feature Envy and Long Method smells using zero-shot LLM prompting |
| **Relationship Detector** | Detects Refused Bequest, Shotgun Surgery, and Inappropriate Intimacy smells |
| **Security Detector** | Detects Hardcoded Secrets and SQL/Command Injection vulnerabilities |
| **Localization Agent** | Pinpoints exact start/end line numbers of detected issues |
| **Explanation Agent** | Generates human-readable Markdown explanations of why code is problematic |
| **Fix Suggestion Agent** | Suggests concrete refactoring steps (disabled by default — expensive) |
| **Coordinator** | Orchestrates all agents, applies confidence filtering and conflict resolution |

---

## Supported Code Smells

| # | Smell | Granularity | Severity |
|---|---|---|---|
| 1 | **Blob (God Class)** | Class | High |
| 2 | **Data Class** | Class | Medium |
| 3 | **Feature Envy** | Method | Medium |
| 4 | **Long Method** | Method | High |
| 5 | **Refused Bequest** | Class | Medium |
| 6 | **Shotgun Surgery** | Class | High |
| 7 | **Inappropriate Intimacy** | Class | Medium |
| 8 | **Hardcoded Secrets** | Class | Critical |
| 9 | **SQL/Command Injection** | Method | Critical |

---

## Supported Languages

All languages are supported via [source-parser](https://github.com/microsoft/source_parser) (Microsoft's tree-sitter-based AST library):

| Language | Extension(s) | Status |
|---|---|---|
| Java | `.java` | ✅ Full support |
| C# | `.cs` | ✅ Full support |
| Python | `.py` | ✅ Full support |
| JavaScript | `.js` | ✅ Full support |
| TypeScript | `.ts` | ✅ Full support |
| C++ | `.cpp` `.cc` `.cxx` | ✅ Full support |
| C | `.c` `.h` `.hpp` | ✅ Full support |

---

## Project Structure

```
DebtGuardianAgent/
├── data/                          # Input datasets (MLCQ)
├── samples/                       # Sample files with code smells (Java)
├── samples cs/                    # Sample files with code smells (C#)
├── samples js/                    # Sample files with code smells (JavaScript)
├── src/
│   ├── app.py                     # Flask REST API + web UI server
│   ├── index.html                 # Web UI (served at http://localhost:5000)
│   ├── debt_guardian.py           # Main pipeline (CLI entry point)
│   ├── coordinator.py             # Multi-agent workflow orchestrator
│   ├── pipeline_adapter.py        # Adapter bridging Flask backend to DebtGuardian
│   ├── debt_detector.py           # ClassDebtDetector, MethodDebtDetector, agents
│   ├── program_slicer.py          # Multi-language AST slicer (via source-parser)
│   ├── config.py                  # All configuration: models, agents, thresholds
│   ├── prompts.py                 # Loads LLM prompts from src/prompts/*.md
│   ├── prompts/                   # Prompt templates (Markdown files)
│   ├── agent_utils.py             # AutoGen agent factory helpers
│   ├── ollama_utils.py            # Ollama server management
│   ├── debt_utils.py              # Debt result utilities
│   ├── evaluation.py              # Evaluation metrics
│   └── settings.py                # Runtime settings
├── results/                       # Analysis output files
├── requirements.txt               # Python dependencies
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Ollama** — local LLM inference server

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/DebtGuardianAgent.git
cd DebtGuardianAgent

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install all dependencies (includes source-parser)
pip install -r requirements.txt

# Start Ollama and pull the default model
ollama serve &
ollama pull qwen2.5-coder-32768:14b
```

> The default model is configured in `src/config.py` as `LLM_MODEL`. Change it once there and it propagates everywhere.

---

## Running the Web UI

```bash
cd src
python app.py
```

Then open **http://localhost:5000** in your browser.

The web UI allows you to:
- Upload individual files or entire project folders
- Toggle agents (class detection, method detection, explanations, fix suggestions, program slicing)
- Set a minimum confidence threshold
- View results with Markdown-rendered explanations and fix suggestions
- Inspect collapsible code snippets
- Export results as a timestamped `.json` file

---

## CLI Usage

Run from the `src/` directory:

```bash
cd src

# Analyze a single file
python debt_guardian.py ../samples/BlobExample.java --type file --format report

# Analyze a directory (all supported languages)
python debt_guardian.py ../samples/ --type dir --recursive --output ../results/analysis.json

# Analyze a directory filtering by language
python debt_guardian.py ../samples/ --type dir --language java --recursive

# Analyze a repository
python debt_guardian.py /path/to/repo --type repo --language all --output ../results/repo.json

# Analyze only files listed in a text file (one path per line, relative to repo root)
python debt_guardian.py /path/to/repo --type repo --file-list hotspots.txt --output ../results/hotspots.json

# Fetch hotspot targets from a local CodeScene Docker instance and analyze them
python debt_guardian.py /path/to/repo --type repo \
  --codescene-url http://localhost:3003 \
  --codescene-token YOUR_TOKEN \
  --codescene-project "My Project" \
  --output ../results/hotspots.json
```

**`--language` options:** `java`, `python`, `csharp` / `cs`, `javascript`, `typescript`, `cpp`, `c`, `all`

### Narrowing repo analysis with CodeScene

For large repositories, analyzing every file is slow. You can narrow the scope two ways:

1. **`--file-list hotspots.txt`** — a plain text file with one repo-relative path per line (lines starting with `#` are ignored). Generate it however you like — manually, from CodeScene's UI, or from any other tool.

2. **`--codescene-url` + `--codescene-token`** — fetches prioritised refactoring targets directly from a CodeScene instance (cloud or local Docker). Add `--codescene-project` if the token sees more than one project.

---

## Configuration

All configuration lives in [src/config.py](src/config.py). Change values there — they propagate automatically to all agents.

### Model / LLM settings

```python
LLM_MODEL       = "qwen2.5-coder-32768:14b"   # single source of truth
LLM_SERVICE     = "ollama"
OLLAMA_BASE_URL = "http://localhost:11434/v1"
TEMPERATURE     = 0.1
```

### Agent Configuration

```python
AGENT_CONFIGS = {
    'program_slicer': {
        'enabled':         True,
        'extract_metrics': True,
        'min_method_loc':  3,     # skip methods shorter than this
        'max_class_loc':   2000,  # skip classes larger than this
    },
    'class_detector': {
        'enabled':     True,
        'model':       LLM_MODEL,
        'shot':        'few',     # 'few' | 'zero'
        'timeout':     300,
        'temperature': 0.1,
    },
    'method_detector': {
        'enabled':     True,
        'model':       LLM_MODEL,
        'shot':        'zero',    # 'few' | 'zero'
        'timeout':     300,
        'temperature': 0.1,
    },
    'relationship_detector': {
        'enabled':     True,
        'model':       LLM_MODEL,
        'shot':        'few',     # 'few' | 'zero'
        'timeout':     300,
        'temperature': 0.1,
    },
    'security_detector': {
        'enabled':     True,
        'model':       LLM_MODEL,
        'shot':        'few',     # 'few' | 'zero'
        'timeout':     300,
        'temperature': 0.1,
    },
    'localization': {
        'enabled': True,
        'use_ast': True,
    },
    'explanation': {
        'enabled':    True,
        'model':      LLM_MODEL,
        'max_tokens': 1000,
    },
    'fix_suggestion': {
        'enabled':        False,  # expensive — enable when needed
        'model':          LLM_MODEL,
        'max_tokens':     2000,
        'validate_fixes': False,
    },
    'coordinator': {
        'parallel_detection':           True,
        'conflict_resolution_strategy': 'prioritize_class',
        'min_confidence':               0.0,
    },
}
```

### Technical Debt Categories

```python
TD_CATEGORIES = {
    0: {'name': 'No Smell',               'severity': 'none'},
    1: {'name': 'Blob',                   'severity': 'high'},
    2: {'name': 'Data Class',             'severity': 'medium'},
    3: {'name': 'Feature Envy',           'severity': 'medium'},
    4: {'name': 'Long Method',            'severity': 'high'},
    5: {'name': 'Refused Bequest',        'severity': 'medium'},
    6: {'name': 'Shotgun Surgery',        'severity': 'high'},
    7: {'name': 'Inappropriate Intimacy', 'severity': 'medium'},
    8: {'name': 'Hardcoded Secrets',      'severity': 'critical'},
    9: {'name': 'SQL/Command Injection',  'severity': 'critical'},
}
```

---

## REST API Reference

The Flask server (`src/app.py`) exposes the following endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the web UI (`index.html`) |
| `GET` | `/api/health` | Health check — returns status, version, supported languages |
| `GET` | `/api/config` | Get current agent configuration |
| `POST` | `/api/config` | Update configuration at runtime |
| `POST` | `/api/upload` | Upload source files or a project folder |
| `POST` | `/api/analyze` | Analyze an uploaded session |
| `POST` | `/api/analyze/file` | Analyze a single inline code snippet |
| `GET` | `/api/models` | List available Ollama models |
| `GET` | `/api/sessions` | List active upload sessions |
| `DELETE` | `/api/sessions/<id>` | Delete an upload session |

### POST /api/config — runtime toggles

```json
{
  "enableClassDetection": true,
  "enableMethodDetection": true,
  "enableExplanations": true,
  "enableFixSuggestions": false,
  "applyProgramSlicing": true,
  "minConfidence": 0.5,
  "conflictStrategy": "prioritize_class"
}
```

### POST /api/analyze/file — single snippet

```json
{
  "code": "public class Foo { ... }",
  "language": "java",
  "granularity": "class"
}
```

`language`: `java` | `cpp` | `cs` | `python` | `javascript`
`granularity`: `class` | `method`

---

## Dependencies

Key dependencies (see `requirements.txt` for full pinned list):

| Package | Purpose |
|---|---|
| `source-parser==1.2.0` | Multi-language AST parsing (Microsoft) |
| `ag2==0.10.0` | AutoGen multi-agent framework |
| `flask==3.1.2` | REST API server |
| `flask-cors==6.0.1` | CORS support for browser clients |
| `ollama==0.6.1` | Ollama Python client |
| `openai==2.20.0` | OpenAI-compatible API client (used by AutoGen) |
| `pydantic==2.9.2` | Data validation |
| `pandas==2.2.3` | Dataset handling |

---

## License

See [LICENSE](LICENSE).
