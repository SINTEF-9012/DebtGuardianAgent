"""
Utility functions for working with the code smell CSV dataset.
"""
import csv
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import Counter

def get_code_snippets(csv_file_path):
    """
    Extract all code snippets from the CSV file.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        List of code snippet strings in order
    """
    code_snippets = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        if 'code_snippet' not in reader.fieldnames:
            raise ValueError("Column 'code_snippet' not found in CSV file")
        
        for row in reader:
            snippet = row.get('code_snippet', '').strip()
            if snippet:
                code_snippets.append(snippet)
    
    return code_snippets

def get_td_ground_truth(csv_file_path):
    """
    Extract smell type, severity, and code snippet for evaluation.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        List of dictionaries with keys: 'smell', 'severity', 'code_snippet'
    """
    ground_truth = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        required_fields = ['smell', 'severity', 'code_snippet']
        for field in required_fields:
            if field not in reader.fieldnames:
                raise ValueError(f"Column '{field}' not found in CSV file")
        
        for row in reader:
            entry = {
                'smell': row.get('smell', '').strip(),
                'severity': row.get('severity', '').strip(),
                'code_snippet': row.get('code_snippet', '').strip()
            }
            if entry['code_snippet']:  # Only include rows with code snippets
                ground_truth.append(entry)
    
    return ground_truth

def get_td_all_data(csv_file_path):
    """
    Load all rows from the CSV file as dictionaries.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        List of dictionaries, one per row
    """
    data = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            data.append(row)
    
    return data

def filter_by_smell(csv_file_path, smell_type):
    """
    Filter rows by code smell type.
    
    Args:
        csv_file_path: Path to the CSV file
        smell_type: Type of code smell to filter (e.g., 'blob', 'feature envy')
        
    Returns:
        List of dictionaries matching the smell type
    """
    data = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            if row.get('smell', '').strip().lower() == smell_type.lower():
                data.append(row)
    
    return data


def get_unique_smells(csv_file_path):
    """
    Get list of unique code smell types in the dataset.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        Set of unique smell type strings
    """
    smells = set()
    
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            smell = row.get('smell', '').strip()
            if smell:
                smells.add(smell)
    
    return smells

def normalize_td_label(text: str) -> str:
    """
    Normalize a raw TD label output (from generator, critic, or refiner).
    Keeps only the digit (0–4); if not found, returns '0' (default: No smell).
    """
    if text is None:
        return "0"

    text = str(text).strip()

    # Remove model/system prefixes or artifacts
    text = re.sub(r"^```[a-z]*|```$", "", text)
    text = re.sub(r"You are a helpful assistant\.?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?i)(APPROVED|REJECTED)\|(\d)\|?.*", r"\2", text)  # handle critic-style outputs
    text = re.sub(r"[^0-4]", "", text)  # keep only digits 0–4

    # Take the first valid label found
    match = re.search(r"[0-4]", text)
    return match.group(0) if match else "0"


TD_LABELS = {
    "0": "No smell",
    "1": "Blob",
    "2": "Data Class",
    "3": "Feature Envy",
    "4": "Long Method"
}

def map_ground_truth_label(entry: Dict[str, Any]) -> str:
    """
    Map the ground truth severity and smell to a single label string ("0"-"4").
    - If severity is "none", label = "0"
    - Otherwise, map smell text to label according to TD_LABELS
    """
    severity = entry.get("severity", "").lower()
    smell = entry.get("smell", "").lower()

    if severity == "none":
        return "0"

    # Map smell text to label
    for k, v in TD_LABELS.items():
        if v.lower() == smell:
            return k

    # Default fallback
    return "0"

def save_td_labels(predicted_labels: List[str], llm_config: Dict[str, Any], design: str,
                   output_dir: str = "td_output") -> Tuple[str, str]:
    """
    Save raw and normalized technical debt detection results to files.
    
    Args:
        predicted_labels: List of raw LLM outputs (each may include extra formatting).
        llm_config: Dict with model configuration (expects ["config_list"][0]["model"]).
        design: Name or tag of the experimental design (e.g., "td_detection_v1").
        output_dir: Directory where results are saved.

    Returns:
        Tuple[str, str]: (raw_filename, normalized_filename)
    """
    os.makedirs(output_dir, exist_ok=True)
    model = llm_config["config_list"][0]["model"].replace(":", "-")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    raw_filename = f"{output_dir}/{design}_{model}_{timestamp}_raw.txt"
    normalized_filename = f"{output_dir}/{design}_{model}_{timestamp}_normalized.txt"

    normalized_labels = [normalize_td_label(l) for l in predicted_labels]

    # --- Write raw outputs ---
    with open(raw_filename, "w", encoding="utf-8") as f:
        for l in predicted_labels:
            f.write(str(l).strip() + "\n")

    # --- Write normalized labels ---
    with open(normalized_filename, "w", encoding="utf-8") as f:
        for l in normalized_labels:
            f.write(str(l) + "\n")

    # --- Summary report ---
    label_counts = Counter(normalized_labels)
    print(f"Saved {len(predicted_labels)} raw and normalized TD labels.")
    print("Label distribution:")
    for k in sorted(label_counts.keys()):
        label_name = TD_LABELS.get(k, "Unknown")
        print(f"  {k}: {label_counts[k]} ({label_name})")

    return raw_filename, normalized_filename


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python utils.py <csv_file_path>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Test the functions
    snippets = get_code_snippets(csv_file)
    print(f"Found {len(snippets)} code snippets")
    
    ground_truth = get_td_ground_truth(csv_file)
    print(f"Found {len(ground_truth)} ground truth entries")
    
    smells = get_unique_smells(csv_file)
    print(f"\nUnique smell types: {smells}")
    
    print(f"\nFirst ground truth entry:")
    if ground_truth:
        entry = ground_truth[0]
        print(f"  Smell: {entry['smell']}")
        print(f"  Severity: {entry['severity']}")
        print(f"  Code snippet preview: {entry['code_snippet'][:150]}...")