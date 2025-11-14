# %%
import json
import os
import re
from pathlib import Path
import logging
from collections import Counter, defaultdict
from settings import ROOT_DIR, LOG_DIR, RESULT_DIR
from typing import Dict, List, Tuple, Set


def split_ground_truth_by_type(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    split_data = defaultdict(dict)
    
    # Iterate over the data
    for key, items in data.items():
        for item in items:
            for debt in item.get("technicalDebts", []):
                debt_type = debt["type"]
                
                # Copy item and keep only relevant "technicalDebts"
                filtered_item = item.copy()
                filtered_item["technicalDebts"] = [debt]
                
                if key not in split_data[debt_type]:
                    split_data[debt_type][key] = []
                split_data[debt_type][key].append(filtered_item)
    
    # Save each split file
    base_name, ext = os.path.splitext(input_file)
    for debt_type, split_content in split_data.items():
        output_file = f"{base_name}_{debt_type.replace(' ', '_')}{ext}"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(split_content, f, indent=4)
        print(f"Created: {output_file}")


# %%
def sanitize_filename(repo_url):
    """Extract meaningful repository name and format it as a filename."""
    match = re.search(r'github\.com[:/](.+?)\.git', repo_url)
    if match:
        repo_path = match.group(1)
        return repo_path.replace('/', '_')
    return re.sub(r'[^a-zA-Z0-9_-]', '_', repo_url)

def split_json_by_repository(input_file, output_dir):
    """Splits a JSON file into multiple files based on repository names."""
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Load JSON data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    repo_data = {}
    
    # Organize data by repository
    for key, items in data.items():
        for item in items:
            repo_name = item["repository"]
            sanitized_repo_name = sanitize_filename(repo_name)
            
            if sanitized_repo_name not in repo_data:
                repo_data[sanitized_repo_name] = {}
            
            if key not in repo_data[sanitized_repo_name]:
                repo_data[sanitized_repo_name][key] = []
            
            repo_data[sanitized_repo_name][key].append(item)
    
    # Write each repository's data to a separate file
    for repo, content in repo_data.items():
        output_path = os.path.join(output_dir, f"{repo}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=4)
    
    print(f"Successfully split JSON into {len(repo_data)} files in '{output_dir}'")
# sanitized_repo_name = sanitize_filename("git@github.com:spring-projects/spring-data-jdbc-ext.git")
# input_file = 'data/Groundtruth_data/mlcq_data_updated_severe_filtered.json'  
#output_dir = "data/Groundtruth_data/mlcq_data_sever_filtered_split" 
#split_json_by_repository(input_file, output_dir)


# %%
def update_file_with_repo_names(input_file):
    """
    Reads a JSON file, updates repository URLs, and saves the updated content to a new file.

    Args:
        input_file (str): Path to the input JSON file.

    Returns:
        str: Path to the updated JSON file.
    """
    # Extract filename without extension and directory
    base_name, ext = os.path.splitext(input_file)

    # Create a new filename with "_updated" appended
    output_file = f"{base_name}_updated{ext}"
    
    # Read JSON data
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Function to update repository URLs
    def update_repository_url(repo_url):
        if repo_url.startswith("git@github.com:"):
            return repo_url.replace("git@github.com:", "https://github.com/")
        return repo_url  # Return unchanged if it doesn't match the pattern

    # Iterate through JSON data and update repository URLs
    for key, value in data.items():
        for entry in value:
            entry["repository"] = update_repository_url(entry["repository"])

    # Write the updated data to a new file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return output_file  # Return the updated file name

#input_file = 'data/Groundtruth_data/mlcq_data_updated_all.json' 
#updated_file = update_file_with_repo_names(input_file)
#print(f"Updated JSON saved to {updated_file}")


# %%
class JSONValidationError(Exception):
    """Custom exception for JSON validation errors."""
    pass

def validate_json_structure(data: dict) -> None:
    """
    Validate the structure of the JSON data.
    
    Args:
        data (dict): The JSON data to validate
        
    Raises:
        JSONValidationError: If the JSON structure is invalid
    """
    if not isinstance(data, dict):
        raise JSONValidationError("Root element must be a dictionary")
        
    for commit_hash, entries in data.items():
        if not isinstance(entries, list):
            raise JSONValidationError(f"Entries for commit {commit_hash} must be a list")
            
        for entry in entries:
            if not isinstance(entry, dict):
                raise JSONValidationError(f"Each entry in commit {commit_hash} must be a dictionary")
                
            if 'technicalDebts' in entry and not isinstance(entry['technicalDebts'], list):
                raise JSONValidationError(f"technicalDebts in commit {commit_hash} must be a list")

def remove_duplicate_locations(input_file_path: str) -> Dict[str, Dict[str, int]]:
    """
    Remove duplicate location entries from the JSON file with enhanced features.
    
    Args:
        input_file_path (str): Path to the input JSON file
        
    Returns:
        Dict containing statistics about the cleaning process
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        JSONValidationError: If the JSON structure is invalid
        json.JSONDecodeError: If the JSON is malformed
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('duplicate_removal.log'),
            logging.StreamHandler()
        ]
    )
    
    # Generate output file path
    input_path = Path(input_file_path)
    output_file_path = input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}"
    
    # Initialize statistics
    stats = {
        'total_commits_processed': 0,
        'commits_with_duplicates': 0,
        'total_duplicates_removed': 0,
        'per_commit_stats': {},
        'output_file': str(output_file_path)
    }
    
    logging.info(f"Starting processing of file: {input_file_path}")
    logging.info(f"Output will be written to: {output_file_path}")
    
    # Check if input file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file_path}")
    
    # Read and parse the JSON file
    try:
        with open(input_file_path, 'r') as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON file: {str(e)}")
        raise
    
    # Validate JSON structure
    try:
        validate_json_structure(data)
    except JSONValidationError as e:
        logging.error(f"Invalid JSON structure: {str(e)}")
        raise
    
    # Process each commit
    for commit_hash, entries in data.items():
        stats['total_commits_processed'] += 1
        commit_duplicates = 0
        
        for entry in entries:
            if 'technicalDebts' in entry:
                for debt in entry['technicalDebts']:
                    if 'locations' in debt:
                        original_length = len(debt['locations'])
                        
                        # Convert locations to tuples for hashable comparison
                        unique_locations: List[dict] = []
                        seen: Set[Tuple[int, int]] = set()
                        
                        for loc in debt['locations']:
                            # Create a tuple of the location's values
                            loc_tuple = (loc['start_line'], loc['end_line'])
                            
                            # Only add if we haven't seen this combination before
                            if loc_tuple not in seen:
                                seen.add(loc_tuple)
                                unique_locations.append(loc)
                            else:
                                logging.info(
                                    f"Removed duplicate location in commit {commit_hash}: "
                                    f"lines {loc['start_line']}-{loc['end_line']}"
                                )
                        
                        # Calculate duplicates removed
                        duplicates_removed = original_length - len(unique_locations)
                        commit_duplicates += duplicates_removed
                        
                        # Replace the locations with deduplicated list
                        debt['locations'] = unique_locations
        
        # Update statistics
        if commit_duplicates > 0:
            stats['commits_with_duplicates'] += 1
            stats['total_duplicates_removed'] += commit_duplicates
            stats['per_commit_stats'][commit_hash] = {
                'duplicates_removed': commit_duplicates
            }
    
    # Write the cleaned data to the output file
    try:
        with open(output_file_path, 'w') as file:
            json.dump(data, file, indent=4)
    except IOError as e:
        logging.error(f"Failed to write output file: {str(e)}")
        raise
    
    # Log summary statistics
    logging.info(f"Processing complete. Summary statistics:")
    logging.info(f"Total commits processed: {stats['total_commits_processed']}")
    logging.info(f"Commits with duplicates: {stats['commits_with_duplicates']}")
    logging.info(f"Total duplicates removed: {stats['total_duplicates_removed']}")
    logging.info(f"Output file created: {output_file_path}")
    
    return stats


# %%
"""
try:
    stats = remove_duplicate_locations("data/Groundtruth_data/mlcq_data_updated_severe_filtered_updated.json")
    
    # Print summary statistics
    print(f"\nProcessing Summary:")
    print(f"Total commits processed: {stats['total_commits_processed']}")
    print(f"Commits with duplicates: {stats['commits_with_duplicates']}")
    print(f"Total duplicates removed: {stats['total_duplicates_removed']}")
    print(f"Output file created: {stats['output_file']}")
    
    # Print per-commit details for commits with duplicates
    if stats['commits_with_duplicates'] > 0:
        print("\nCommits with duplicates removed:")
        for commit, commit_stats in stats['per_commit_stats'].items():
            print(f"Commit {commit}: {commit_stats['duplicates_removed']} duplicates removed")

except (FileNotFoundError, json.JSONDecodeError, JSONValidationError, IOError) as e:
    print(f"Error: {str(e)}")
"""

# %%
def remove_null_commits(input_file_path: str) -> Dict[str, any]:
    """
    Remove entries with null commit hashes from the JSON file.
    
    Args:
        input_file_path (str): Path to the input JSON file
        
    Returns:
        Dict containing statistics about the cleaning process
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        json.JSONDecodeError: If the JSON is malformed
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('null_commits_removal.log'),
            logging.StreamHandler()
        ]
    )
    
    # Generate output file path
    input_path = Path(input_file_path)
    output_file_path = input_path.parent / f"{input_path.stem}_no_null{input_path.suffix}"
    
    # Initialize statistics
    stats = {
        'total_entries_processed': 0,
        'null_commits_removed': 0,
        'output_file': str(output_file_path)
    }
    
    logging.info(f"Starting processing of file: {input_file_path}")
    logging.info(f"Output will be written to: {output_file_path}")
    
    # Check if input file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file_path}")
    
    # Read and parse the JSON file
    try:
        with open(input_file_path, 'r') as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON file: {str(e)}")
        raise
    
    # Count total entries
    stats['total_entries_processed'] = sum(len(entries) for entries in data.values())
    
    # Remove null commit entries
    if "null" in data:
        null_entries_count = len(data["null"])
        del data["null"]
        stats['null_commits_removed'] = null_entries_count
        logging.info(f"Removed {null_entries_count} entries with null commit hash")
    
    # Write the cleaned data to the output file
    try:
        with open(output_file_path, 'w') as file:
            json.dump(data, file, indent=4)
    except IOError as e:
        logging.error(f"Failed to write output file: {str(e)}")
        raise
    
    # Log summary statistics
    logging.info(f"Processing complete. Summary statistics:")
    logging.info(f"Total entries processed: {stats['total_entries_processed']}")
    logging.info(f"Null commits removed: {stats['null_commits_removed']}")
    logging.info(f"Output file created: {output_file_path}")
    
    return stats

# %%
"""try:
    # Remove null commits first
    null_stats = remove_null_commits("data/Groundtruth_data/mlcq_data_updated_all_updated.json")
    print(f"\nNull Commits Removal Summary:")
    print(f"Total entries processed: {null_stats['total_entries_processed']}")
    print(f"Null commits removed: {null_stats['null_commits_removed']}")
    print(f"Output file created: {null_stats['output_file']}")
    
    # Then you can run remove_duplicate_locations on the cleaned file
    location_stats = remove_duplicate_locations(null_stats['output_file'])

except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
    print(f"Error: {str(e)}")
"""

# %%
def clean_location_entries(json_filename):
    # Load JSON data from file
    with open(json_filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Function to recursively process lists and dictionaries
    def process_item(item):
        if isinstance(item, dict):
            if "location" in item and isinstance(item["location"], str) and item["location"].startswith("/"):
                item["location"] = item["location"][1:]  # Remove leading slash
            for key in item:
                process_item(item[key])
        elif isinstance(item, list):
            for sub_item in item:
                process_item(sub_item)
    
    # Process the entire JSON structure
    process_item(data)
    
    # Create output filename
    base, ext = os.path.splitext(json_filename)
    new_filename = f"{base}_further{ext}"
    
    # Save cleaned data to a new file
    with open(new_filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)
    
    print(f"Processed file saved as: {new_filename}")

#clean_location_entries("data/Groundtruth_data/mlcq_data_updated_severe_filtered_updated_cleaned.json")
#clean_location_entries("data/Groundtruth_data/mlcq_data_updated_all_updated_no_null_cleaned.json")

# %%
def extract_repo_commits_from_file(json_file):
    """
    Extracts repository URLs and their associated unique commit hashes from a JSON file.

    Args:
        json_file (str): Path to the JSON file.

    Returns:
        dict: A dictionary where keys are repository URLs and values are lists of unique commit hashes.
    """
    repo_commits = defaultdict(set)  # Using a set to store unique commit hashes

    # Load JSON data from file
    with open(json_file, 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    # Process the JSON data
    for commit_hash, entries in json_data.items():
        for entry in entries:
            repo_url = entry.get("repository")
            if repo_url:
                repo_commits[repo_url].add(commit_hash)  # Add commit hash to set (removes duplicates)

    # Convert sets to lists for JSON compatibility
    return {repo: list(commits) for repo, commits in repo_commits.items()}

#json_file_path = "data/Groundtruth_data/groundtruth_MLCQ_data_severe_filtered_updated.json" 
#result = extract_repo_commits_from_file(json_file_path)

# %%

def extract_unique_repo_commits(json_file):
    """
    Extracts unique repository URLs with their associated commit hashes and file locations.

    :param json_file: Path to the JSON file containing commit data
    :return: Dictionary mapping repository URLs to commit hashes and their respective relevant file locations
    """
    with open(json_file, 'r') as file:
        data = json.load(file)

    repo_data = {}

    for commit_hash, entries in data.items():
        for entry in entries:
            repo_url = entry.get("repository")
            location = entry.get("location")  # The file path to be analyzed

            if repo_url:
                if repo_url not in repo_data:
                    repo_data[repo_url] = {}

                if commit_hash not in repo_data[repo_url]:
                    repo_data[repo_url][commit_hash] = set()  # Using a set to prevent duplicate file paths

                if location:
                    repo_data[repo_url][commit_hash].add(location)  # Store only relevant file paths

    # Convert sets to lists for JSON serialization
    return {repo: {commit: list(files) for commit, files in commit_dict.items()} for repo, commit_dict in repo_data.items()}


def extract_commit_repo_pairs_from_log_file(log_file_path):
    """
    Extracts commit hashes and repository URLs from a log file where commits have no modified files.

    :param log_file_path: Path to the log file
    :return: List of (commit_hash, repository_url) tuples
    """
    pattern = re.compile(
        r"Commit (\b[a-fA-F0-9]{40}\b) in (https?://github\.com/\S+?\.git) has no modified files!"
    )

    commit_repo_pairs = []

    with open(log_file_path, "r", encoding="utf-8") as file:
        for line in file:
            match = pattern.search(line)
            if match:
                commit_hash, repo_url = match.groups()
                commit_repo_pairs.append((commit_hash, repo_url))

    print(f"\nTotal number of extracted commit-repository pairs: {len(commit_repo_pairs)}")

    return commit_repo_pairs


def remove_entries_from_ground_truth(ground_truth_file, commit_repo_pairs):
    """
    Removes entries from the ground truth file that match the given commit-repository pairs.

    :param ground_truth_file: Path to the ground truth JSON file
    :param commit_repo_pairs: List of (commit_hash, repository_url) tuples
    :return: Path to the new ground truth file after removal
    """

    with open(ground_truth_file, "r", encoding="utf-8") as file:
        ground_truth_data = json.load(file)

    
    original_entry_count = len(ground_truth_data)
    print(f"Original number of entries in ground truth file: {original_entry_count}")

    commit_repo_set = set(commit_repo_pairs)

    # Filter out matching entries
    filtered_data = {
        commit: [
            entry for entry in entries if entry["repository"] not in 
            {repo_url for (commit_hash, repo_url) in commit_repo_set if commit_hash == commit}
        ]
        for commit, entries in ground_truth_data.items()
    }

    # Remove any empty lists from the dictionary
    filtered_data = {commit: entries for commit, entries in filtered_data.items() if entries}
    
    filtered_entry_count = len(filtered_data)
    print(f"Number of entries in new ground truth file after removal: {filtered_entry_count}")

    base, ext = os.path.splitext(ground_truth_file)
    new_file_path = f"{base}_further{ext}"

    with open(new_file_path, "w", encoding="utf-8") as file:
        json.dump(filtered_data, file, indent=4)

    print(f"New ground truth file saved as: {new_file_path}")

    return new_file_path

