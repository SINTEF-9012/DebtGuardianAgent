"""
prompts.py
Loads all LLM prompts from src/prompts/*.md files.
To change a prompt, edit the corresponding .md file — no Python changes needed.
"""
import os

_PROMPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prompts')


def _load(filename: str) -> str:
    """Read a prompt .md file and return its contents as a string."""
    path = os.path.join(_PROMPT_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ── Class-level detection ────────────────────────────────────────────────────
CLASS_DETECTOR_FEW_SHOT  = _load('class_detector_few_shot.md')
CLASS_DETECTOR_ZERO_SHOT = _load('class_detector_zero_shot.md')

# ── Method-level detection ───────────────────────────────────────────────────
METHOD_DETECTOR_FEW_SHOT  = _load('method_detector_few_shot.md')
METHOD_DETECTOR_ZERO_SHOT = _load('method_detector_zero_shot.md')

# ── Relationship-level detection ─────────────────────────────────────────────
RELATIONSHIP_DETECTOR_FEW_SHOT  = _load('relationship_detector_few_shot.md')
RELATIONSHIP_DETECTOR_ZERO_SHOT = _load('relationship_detector_zero_shot.md')

# ── Security-debt detection ──────────────────────────────────────────────────
SECURITY_DETECTOR_FEW_SHOT  = _load('security_detector_few_shot.md')
SECURITY_DETECTOR_ZERO_SHOT = _load('security_detector_zero_shot.md')

# ── Explanation & fix-suggestion agents ──────────────────────────────────────
EXPLANATION_AGENT   = _load('explanation_agent.md')
FIX_SUGGESTION_AGENT = _load('fix_suggestion_agent.md')

# ── Multi-agent (generator / critic / refiner) ───────────────────────────────
TD_GENERATOR_FEW_SHOT  = _load('td_generator_few_shot.md')
TD_GENERATOR_ZERO_SHOT = _load('td_generator_zero_shot.md')
TD_CRITIC_FEW_SHOT     = _load('td_critic_few_shot.md')
TD_CRITIC_ZERO_SHOT    = _load('td_critic_zero_shot.md')
TD_REFINER_FEW_SHOT    = _load('td_refiner_few_shot.md')
TD_REFINER_ZERO_SHOT   = _load('td_refiner_zero_shot.md')

# ── Task prefix strings (short, kept inline) ─────────────────────────────────
TASK_CLASS_DETECTION        = "Analyze the following class and respond with only a single digit (0, 1, or 2) representing the code smell category:\n\n"
TASK_METHOD_DETECTION       = "Analyze the following method and respond with only a single digit (0, 3, or 4) representing the code smell category:\n\n"
TASK_RELATIONSHIP_DETECTION = "Analyze the following class for relationship-level code smells and respond with only a single digit (0, 5, 6, or 7) representing the code smell category:\n\n"
TASK_SECURITY_DETECTION     = "Analyze the following code for security-related technical debt and respond with only a single digit (0, 8, or 9) representing the category:\n\n"
TASK_TD_DETECTION           = "Look at the following code snippet and respond with only a single digit (0-9) that represents the most appropriate category:\n"
