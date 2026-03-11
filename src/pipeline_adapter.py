#!/usr/bin/env python3
"""
Adapter Layer: Bridges old Flask backend with new DebtGuardian architecture
"""
import os
import tempfile
from typing import List, Dict, Any
from pathlib import Path

# Import new system
from debt_guardian import DebtGuardian
import config


class DebtGuardianPipeline:
    """
    Adapter class that mimics the old pipeline interface
    but uses the new DebtGuardian system internally
    """
    
    def __init__(self, repo_path: str, output_dir: str = None):
        """
        Initialize pipeline (matches old interface)
        
        Args:
            repo_path: Path to repository/folder to analyze
            output_dir: Output directory (optional)
        """
        self.repo_path = repo_path
        self.output_dir = output_dir or tempfile.mkdtemp()
        
        # Initialize new DebtGuardian
        self.guardian = DebtGuardian()
        self.coordinator = CoordinatorAdapter(self.guardian.coordinator)
        
        # Store results
        self.results = []
    
    def analyze_repository(self) -> List[Dict[str, Any]]:
        """
        Analyze repository and return results in old format
        
        Returns:
            List of detection results compatible with old backend
        """
        print(f"[Pipeline] Analyzing repository: {self.repo_path}")
        
        # Find all supported files
        supported_extensions = {'.java', '.cpp', '.cs', '.py', '.js'}
        files_to_analyze = []
        
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in supported_extensions):
                    file_path = os.path.join(root, file)
                    files_to_analyze.append(file_path)
        
        print(f"[Pipeline] Found {len(files_to_analyze)} files to analyze")
        
        # Analyze each file
        all_results = []
        
        for i, file_path in enumerate(files_to_analyze, 1):
            print(f"[Pipeline] Analyzing file {i}/{len(files_to_analyze)}: {Path(file_path).name}")
            
            try:
                # Use new DebtGuardian system
                file_result = self.guardian.analyze_file(file_path, output_format='json')
                
                # Convert to old format
                converted_results = self._convert_to_old_format(file_result, file_path)
                all_results.extend(converted_results)
                
            except Exception as e:
                print(f"[Warning] Failed to analyze {file_path}: {str(e)}")
                continue
        
        self.results = all_results
        print(f"[Pipeline] Analysis complete. Found {len(all_results)} issues")
        
        return all_results
    
    def _convert_to_old_format(self, new_result: Dict[str, Any], file_path: str) -> List[Dict[str, Any]]:
        """
        Convert new DebtGuardian result format to old format expected by backend
        
        Args:
            new_result: Result from new DebtGuardian
            file_path: Path to analyzed file
            
        Returns:
            List of detections in old format
        """
        converted = []
        
        for debt in new_result.get('debts', []):
            # Map debt_type to category integer
            debt_type = debt.get('debt_type', '')
            category_map = {
                'No Smell': 0,
                'Blob': 1,
                'Data Class': 2,
                'Feature Envy': 3,
                'Long Method': 4
            }
            
            category_int = category_map.get(debt_type, 0)
            
            # Skip if no smell detected
            if category_int == 0:
                continue
            
            # Build old format result
            old_format = {
                'file_path': file_path,
                'code_name': debt.get('name', 'Unknown'),
                'code_type': debt.get('granularity', 'unknown'),  # 'class' or 'method'
                'detected_category_int': category_int,
                'confidence': debt.get('confidence', 0.0),
                'granularity': debt.get('granularity', 'unknown'),
            }
            
            # Add localization if available
            location = debt.get('location', {})
            if 'start_line' in location:
                old_format['localization'] = {
                    'start_line': location['start_line'],
                    'end_line': location['end_line']
                }
            
            # Add explanation if available
            if debt.get('explanation'):
                old_format['explanation'] = {
                    'text': debt['explanation']
                }
            
            # Add fix suggestion if available
            if debt.get('fix_suggestion'):
                old_format['fix_suggestion'] = {
                    'text': debt['fix_suggestion']
                }
            
            # Add code snippet (truncate if too long)
            if debt.get('code'):
                old_format['code_snippet'] = debt['code'][:1000]
            
            converted.append(old_format)
        
        return converted


class CoordinatorAdapter:
    """
    Adapter for coordinator to match old interface
    """
    
    def __init__(self, new_coordinator):
        self.coordinator = new_coordinator
    
    def generate_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary report in old format
        
        Args:
            results: List of detection results
            
        Returns:
            Summary dict compatible with old backend
        """
        # Count by category
        by_category = {}
        by_severity = {'high': 0, 'medium': 0, 'low': 0}
        by_granularity = {'class': 0, 'method': 0}
        
        for result in results:
            cat = result.get('detected_category_int', -1)
            if cat > 0:
                # Get category name
                cat_info = config.TD_CATEGORIES.get(cat, {})
                cat_name = cat_info.get('name', 'Unknown')
                
                # Count by category
                by_category[cat_name] = by_category.get(cat_name, 0) + 1
                
                # Count by severity
                severity = cat_info.get('severity', 'low')
                by_severity[severity] = by_severity.get(severity, 0) + 1
                
                # Count by granularity
                gran = result.get('granularity', 'unknown')
                if gran in by_granularity:
                    by_granularity[gran] += 1
        
        return {
            'total_issues': len(results),
            'by_category': by_category,
            'by_severity': by_severity,
            'by_granularity': by_granularity
        }


# For backward compatibility - keep old function names
def create_pipeline(repo_path: str, output_dir: str = None) -> DebtGuardianPipeline:
    """Factory function to create pipeline (old interface)"""
    return DebtGuardianPipeline(repo_path, output_dir)