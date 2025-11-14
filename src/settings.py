import os
import sys

# Set the ROOT_DIR to the directory where settings.py resides,
# which we'll assume is your repository root.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Set the DATA_DIR to the directory where your data resides.
DATA_DIR = os.path.join(ROOT_DIR, 'data')

LOG_DIR = os.path.join(ROOT_DIR, 'logs')

RESULT_DIR = os.path.join(ROOT_DIR, 'results')

# Initialize MODEL_TYPE as None
MODEL_TYPE = None

def get_model_type():
    """Returns the current model type."""
    global MODEL_TYPE
    return MODEL_TYPE

sys.path.append(ROOT_DIR)
sys.path.append(DATA_DIR)
sys.path.append(LOG_DIR)
sys.path.append(RESULT_DIR)
