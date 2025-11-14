
import textwrap

def wrap_text(text, width=200):
    """
    Wrap the given text to the specified width.

    :param text: Text to wrap
    :param width: Width at which to wrap the text
    :return: Wrapped text
    """
    return textwrap.fill(text, width)

# Function to normalize technical debt types (e.g., case-insensitive, strip whitespace)
def normalize_debt_type(debt_type):
    return debt_type.strip().lower()