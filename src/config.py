import os
import sys

# ========================================================================================
# DIRECTORY CONFIGURATION
# ========================================================================================
ROOT_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(ROOT_DIR, 'data')
LOG_DIR    = os.path.join(ROOT_DIR, 'logs')
RESULT_DIR = os.path.join(ROOT_DIR, 'results')
WORK_DIR   = os.path.join(ROOT_DIR, 'work')
REPO_DIR   = os.path.join(ROOT_DIR, 'repositories')

for directory in [DATA_DIR, RESULT_DIR, WORK_DIR, REPO_DIR]:
    os.makedirs(directory, exist_ok=True)
    sys.path.append(directory)

# ========================================================================================
# ★  MODEL CONFIGURATION  —  change here only, propagates everywhere  ★
# ========================================================================================
LLM_MODEL       = "nemotron-3-nano:latest"   # single source of truth for the model name
LLM_SERVICE     = "ollama"
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_API_KEY  = "ollama"
TEMPERATURE     = 0.1

# Pre-built LLM config block used by autogen agents
LLM_CONFIG = {
    "cache_seed": None,
    "config_list": [
        {
            "model":    LLM_MODEL,
            "base_url": OLLAMA_BASE_URL,
            "api_key":  OLLAMA_API_KEY,
        }
    ],
    "temperature": TEMPERATURE,
    "timeout":     600,
}

# ========================================================================================
# DATASET FILES
# ========================================================================================
IN_FILE = "mlcq_cleaned_and_pruned_dataset_385.csv"
GT_FILE = "mlcq_cleaned_and_pruned_dataset_385.csv"

# ========================================================================================
# AGENT CONFIGURATIONS  —  all reference LLM_MODEL / OLLAMA_BASE_URL / OLLAMA_API_KEY
# ========================================================================================
AGENT_CONFIGS = {
    'source_loader': {
        'enabled': True,
    },
    'program_slicer': {
        'enabled':         True,
        'extract_metrics': True,
        'min_method_loc':  3,     # minimum LOC for a method to be analysed
        'max_class_loc':   2000,  # skip classes larger than this
    },
    'class_detector': {
        'model':       LLM_MODEL,
        'base_url':    OLLAMA_BASE_URL,
        'api_key':     OLLAMA_API_KEY,
        'shot':        'few',   # 'few' | 'zero'
        'timeout':     300,
        'temperature': TEMPERATURE,
        'enabled':     True,
    },
    'method_detector': {
        'model':       LLM_MODEL,
        'base_url':    OLLAMA_BASE_URL,
        'api_key':     OLLAMA_API_KEY,
        'shot':        'zero',  # 'few' | 'zero'
        'timeout':     300,
        'temperature': TEMPERATURE,
        'enabled':     True,
    },
    'localization': {
        'enabled': True,
        'use_ast': True,
    },
    'explanation': {
        'model':       LLM_MODEL,
        'base_url':    OLLAMA_BASE_URL,
        'api_key':     OLLAMA_API_KEY,
        'temperature': TEMPERATURE,
        'max_tokens':  1000,
        'enabled':     True,
    },
    'fix_suggestion': {
        'model':          LLM_MODEL,
        'base_url':       OLLAMA_BASE_URL,
        'api_key':        OLLAMA_API_KEY,
        'temperature':    TEMPERATURE,
        'max_tokens':     2000,
        'enabled':        False,  # expensive — enable when needed
        'validate_fixes': False,
    },
    'coordinator': {
        'parallel_detection':           True,
        'conflict_resolution_strategy': 'prioritize_class',  # 'keep_all' | 'prioritize_method'
        'min_confidence':               0.0,
    },
}

# ========================================================================================
# PIPELINE CONFIGURATION
# ========================================================================================
PIPELINE_CONFIG = {
    'parallel_detection':    True,
    'enable_localization':   True,
    'enable_explanation':    True,
    'enable_fix_suggestion': False,
    'batch_size':            10,
    'max_workers':           4,
}

# ========================================================================================
# TECHNICAL DEBT CATEGORIES
# ========================================================================================
TD_CATEGORIES = {
    0: {'name': 'No Smell',     'granularity': 'any',    'severity': 'none',   'description': 'Code is clean and well-structured'},
    1: {'name': 'Blob',         'granularity': 'class',  'severity': 'high',   'description': 'Class with too many responsibilities (God Class)'},
    2: {'name': 'Data Class',   'granularity': 'class',  'severity': 'medium', 'description': 'Class with only getters/setters, no behavior'},
    3: {'name': 'Feature Envy', 'granularity': 'method', 'severity': 'medium', 'description': 'Method heavily dependent on another class'},
    4: {'name': 'Long Method',  'granularity': 'method', 'severity': 'high',   'description': 'Excessively long or complex method'},
}

# ========================================================================================
# DETECTION THRESHOLDS
# ========================================================================================
THRESHOLDS = {
    'blob_class_loc':          500,
    'blob_method_count':       20,
    'long_method_loc':         20,
    'long_method_complexity':  10,
    'data_class_method_ratio': 0.8,
}

# ========================================================================================
# SUPPORTED FILE EXTENSIONS
# ========================================================================================
SUPPORTED_EXTENSIONS = {
    'java':       '.java',
    'cpp':        '.cpp',
    'cs':         '.cs',
    'python':     '.py',
    'javascript': '.js',
}

# ========================================================================================
# PROMPTS  —  loaded from src/prompts/*.md via prompts.py
# To change a prompt, edit the relevant .md file only.
# ========================================================================================
from prompts import (
    CLASS_DETECTOR_FEW_SHOT,
    CLASS_DETECTOR_ZERO_SHOT,
    METHOD_DETECTOR_FEW_SHOT,
    METHOD_DETECTOR_ZERO_SHOT,
    EXPLANATION_AGENT,
    FIX_SUGGESTION_AGENT,
    TD_GENERATOR_FEW_SHOT,
    TD_GENERATOR_ZERO_SHOT,
    TD_CRITIC_FEW_SHOT,
    TD_CRITIC_ZERO_SHOT,
    TD_REFINER_FEW_SHOT,
    TD_REFINER_ZERO_SHOT,
    TASK_CLASS_DETECTION,
    TASK_METHOD_DETECTION,
    TASK_TD_DETECTION,
)

# Legacy aliases — keep existing code working without any changes
SYS_MSG_CLASS_DETECTOR_FEW_SHOT          = CLASS_DETECTOR_FEW_SHOT
SYS_MSG_CLASS_DETECTOR_ZERO_SHOT         = CLASS_DETECTOR_ZERO_SHOT
SYS_MSG_METHOD_DETECTOR_FEW_SHOT         = METHOD_DETECTOR_FEW_SHOT
SYS_MSG_METHOD_DETECTOR_ZERO_SHOT        = METHOD_DETECTOR_ZERO_SHOT
SYS_MSG_EXPLANATION_AGENT                = EXPLANATION_AGENT
SYS_MSG_FIX_SUGGESTION_AGENT             = FIX_SUGGESTION_AGENT
SYS_MSG_TD_DETECTION_GENERATOR_FEW_SHOT  = TD_GENERATOR_FEW_SHOT
SYS_MSG_TD_DETECTION_GENERATOR_ZERO_SHOT = TD_GENERATOR_ZERO_SHOT
SYS_MSG_TD_DETECTION_CRITIC_FEW_SHOT     = TD_CRITIC_FEW_SHOT
SYS_MSG_TD_DETECTION_CRITIC_ZERO_SHOT    = TD_CRITIC_ZERO_SHOT
SYS_MSG_TD_DETECTION_REFINER_FEW_SHOT    = TD_REFINER_FEW_SHOT
SYS_MSG_TD_DETECTION_REFINER_ZERO_SHOT   = TD_REFINER_ZERO_SHOT
TASK_PROMPT_CLASS_DETECTION              = TASK_CLASS_DETECTION
TASK_PROMPT_METHOD_DETECTION             = TASK_METHOD_DETECTION
TASK_PROMPT_TD_DETECTION                 = TASK_TD_DETECTION
SYS_MSG_CLASS_LEVEL_FEW                  = CLASS_DETECTOR_FEW_SHOT
SYS_MSG_METHOD_LEVEL_FEW                 = METHOD_DETECTOR_FEW_SHOT
