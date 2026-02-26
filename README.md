# 🧠 DebtGuardianAgent
> An LLM-powered multi-agent system for detecting Technical Debt in real-world software repositories.

**Multi-Agent Technical Debt Detection System**

DebtGuardianAgent is an advanced, AI-powered source code analysis tool that uses a multi-agent architecture to detect and explain technical debt (code smells) in source code repositories. It leverages specialized LLM agents for different granularities of analysis, providing comprehensive insights into code quality issues.

### Multi-Agent Architecture
- **Source Code Loader**: Tracks and loads source files from repositories
- **Program Slicer**: Extracts classes and methods with structural metrics
- **Class-Level Detector**: Identifies Blob and Data Class smells (optimized with Codestral)
- **Method-Level Detector**: Detects Feature Envy and Long Method smells (optimized with Qwen2.5-Coder)
- **Localization Agent**: Pinpoints exact line numbers of detected issues
- **Explanation Agent**: Provides human-readable explanations of why code is problematic
- **Fix Suggestion Agent**: Offers concrete refactoring recommendations

### Supported Code Smells
1. **Blob (God Class)** - Classes with too many responsibilities
2. **Data Class** - Classes with only getters/setters, no behavior
3. **Feature Envy** - Methods heavily dependent on another class
4. **Long Method** - Excessively long or complex methods

### Supported Languages
- ✅ Java (fully supported)
- 🔧 C# (slicer in progress)
- 🔧 Python (planned)
- 🔧 C++ (planned)

## 📁 Project Structure

```
DebtGuardianAgent/
├── data/                      # Input datasets
├── samples/                   # Sample files with code smells
│   ├── BlobExample.java
│   ├── LongMethodFeatureEnvy.java
│   └── DataClassExample.java
├── src/                   
│   ├── debt_detector.py           # Core detection agents
│   ├──coordinator.py             # Multi-agent workflow orchestrator
│   ├── debt_guardian.py           # Main pipeline
│   ├── program_slicer.py          # Java code slicer with metrics
│   ├── app.py                     # Flask REST API backend
│   ├── index.html                 # Web UI (standalone)
│   ├── config.py                  # Configuration and prompts
│   ├── agent_utils.py             # Generic agent utilities
│   ├── debt_utils.py              # Dataset utilities
│   ├── evaluation.py              # Evaluation metrics
├── results/                   # Analysis results
└── README.md                  # This file
```

## 🚀 Getting Started

### Prerequisites

1. **Python 3.12+**
2. **Ollama** (for local LLM inference)
3. **Required Models**:
   - `codestral:22b` (for class-level detection & explanations)
   - `qwen2.5-coder:7b-instruct` (for method-level detection)


### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/DebtGuardianAgent.git
cd DebtGuardianAgent

# Install Python dependencies
pip install -r requirements.txt

# Start Ollama server
ollama serve

# Pull required models
ollama pull codestral:22b
ollama pull qwen2.5-coder:7b-instruct
```

### Quick Start

#### 1. Analyze a Single File (CLI)

```bash
python debt_guardian.py samples/BlobExample.java --type file --format report
```

#### 2. Analyze a Directory

```bash
python debt_guardian.py samples/ --type dir --recursive --output results/analysis.json
```

#### 3. Analyze a Repository

```bash
python debt_guardian.py /path/to/repo --type repo --language java --output results/repo_analysis.json
```

#### 4. Web Interface

```bash
# Start the Flask API server
python app.py

# Open index.html in your browser
# or navigate to http://localhost:5000
```

## 🔧 Configuration

Edit `config.py` to customize:

### Agent Configuration

```python
AGENT_CONFIGS = {
    'class_detector': {
        'enabled': True,
        'model': 'codestral:22b',
        'shot': 'few',  # 'zero' or 'few'
        'temperature': 0.1,
    },
    'method_detector': {
        'enabled': True,
        'model': 'qwen2.5-coder:7b-instruct',
        'shot': 'zero',
        'temperature': 0.1,
    },
    'localization': {
        'enabled': True,
        'use_ast': True,
    },
    'explanation': {
        'enabled': True,
        'model': 'qwen2.5-coder:7b-instruct',
    },
    'fix_suggestion': {
        'enabled': False,  
        'validate_fixes': False,
    },
}
```
