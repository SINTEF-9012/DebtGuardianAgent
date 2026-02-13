"""
Coordinator Module
Orchestrates the multi-agent technical debt detection workflow
"""
import concurrent.futures
from typing import Dict, Any, List, Optional
from pathlib import Path

from debt_detector import (
    ClassDebtDetector,
    MethodDebtDetector,
    LocalizationAgent,
    ExplanationAgent,
    FixSuggestionAgent
)
from program_slicer import ProgramSlicerAgent

class DebtDetectionCoordinator:
    """
    Coordinates the multi-agent technical debt detection pipeline.
    Manages detection, and post-processing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize coordinator with agent configurations.
        
        Args:
            config: Complete configuration dict (from config.AGENT_CONFIGS)
        """
        if config is None:
            import config as cfg
            config = cfg.AGENT_CONFIGS
        
        self.config = config
        
        # Initialize agents based on config
        self.class_detector = None
        self.method_detector = None
        self.localizer = None
        self.explainer = None
        self.fix_suggester = None
        
        # Load settings
        coordinator_config = config.get('coordinator', {})
        self.parallel_detection = coordinator_config.get('parallel_detection', False)
        self.conflict_strategy = coordinator_config.get(
            'conflict_resolution_strategy', 'prioritize_class'
        )
        self.min_confidence = coordinator_config.get('min_confidence', 0.5)
        
        # Initialize enabled agents
        self._initialize_agents(config)
    
    def _initialize_agents(self, config: Dict[str, Any]):
        """Initialize agents that are enabled in config"""
        
        # Class detector
        class_config = config.get('class_detector', {})
        if class_config.get('enabled', True):
            self.class_detector = ClassDebtDetector(class_config)
            print("[Init] Class Debt Detector initialized")
        
        # Method detector
        method_config = config.get('method_detector', {})
        if method_config.get('enabled', True):
            self.method_detector = MethodDebtDetector(method_config)
            print("[Init] Method Debt Detector initialized")
        
        # Localizer
        loc_config = config.get('localization', {})
        if loc_config.get('enabled', True):
            self.localizer = LocalizationAgent(loc_config)
            print("[Init] Localization Agent initialized")
        
        # Explainer
        exp_config = config.get('explanation', {})
        if exp_config.get('enabled', True):
            self.explainer = ExplanationAgent(exp_config)
            print("[Init] Explanation Agent initialized")
        
        # Fix suggester
        fix_config = config.get('fix_suggestion', {})
        if fix_config.get('enabled', False):  # Disabled by default
            self.fix_suggester = FixSuggestionAgent(fix_config)
            print("[Init] Fix Suggestion Agent initialized")
    
    def analyze_file(self, sliced_data: Dict[str, Any], 
                     source_file_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a sliced Java file for technical debt.
        
        Args:
            sliced_data: Output from ProgramSlicerAgent.slice_file()
            source_file_content: Optional full source file (for localization)
            
        Returns:
            Analysis results with all detected debts
        """
        file_path = sliced_data.get('file_path', 'unknown')
        classes = sliced_data.get('classes', [])
        methods = sliced_data.get('methods', [])
        
        print(f"\n[Analysis] Analyzing {file_path}")
        print(f"[Analysis] Found {len(classes)} classes, {len(methods)} standalone methods")
        
        all_detections = []
        
        # Detect class-level debts
        if self.class_detector and classes:
            class_results = self._detect_class_debts(classes)
            all_detections.extend(class_results)
        
        # Detect method-level debts
        if self.method_detector and methods:
            method_results = self._detect_method_debts(methods)
            all_detections.extend(method_results)
        
        # Extract methods from classes for method-level detection
        if self.method_detector:
            for class_info in classes:
                class_methods = class_info.get('methods', [])
                if class_methods:
                    method_results = self._detect_method_debts(class_methods)
                    all_detections.extend(method_results)
        
        # Filter by confidence threshold
        filtered_detections = [
            d for d in all_detections 
            if d.get('confidence', 0) >= self.min_confidence
        ]
        
        print(f"[Analysis] Found {len(filtered_detections)} debts above confidence threshold")
        
        # Post-process detections
        if source_file_content:
            filtered_detections = self._post_process(
                filtered_detections, source_file_content
            )
        
        return {
            'file_path': file_path,
            'total_detections': len(all_detections),
            'filtered_detections': len(filtered_detections),
            'debts': filtered_detections,
            'summary': self._generate_summary(filtered_detections)
        }
    
    def _detect_class_debts(self, classes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect debts in all classes"""
        results = []
        
        if self.parallel_detection and len(classes) > 1:
            # Parallel detection
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(self.class_detector.detect, class_info)
                    for class_info in classes
                ]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
        else:
            # Sequential detection
            for class_info in classes:
                result = self.class_detector.detect(class_info)
                results.append(result)
                print(f"  [Class] {class_info['name']}: {result.get('debt_type', 'Unknown')}")
        
        # Filter out "No Smell" results
        return [r for r in results if r.get('label') != '0']
    
    def _detect_method_debts(self, methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect debts in all methods"""
        results = []
        
        if self.parallel_detection and len(methods) > 1:
            # Parallel detection
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(self.method_detector.detect, method_info)
                    for method_info in methods
                ]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
        else:
            # Sequential detection
            for method_info in methods:
                result = self.method_detector.detect(method_info)
                results.append(result)
                print(f"  [Method] {method_info['name']}: {result.get('debt_type', 'Unknown')}")
        
        # Filter out "No Smell" results
        return [r for r in results if r.get('label') != '0']
    
    def _post_process(self, detections: List[Dict[str, Any]], 
                     source_content: str) -> List[Dict[str, Any]]:
        """
        Apply post-processing: localization, explanation, fix suggestions.
        
        Args:
            detections: List of detection results
            source_content: Full source file content
            
        Returns:
            Enhanced detection results
        """
        processed = []
        
        for detection in detections:
            # Localize
            if self.localizer:
                detection = self.localizer.localize(detection, source_content)
            
            # Explain
            if self.explainer:
                detection = self.explainer.explain(detection)
            
            # Suggest fixes
            if self.fix_suggester:
                detection = self.fix_suggester.suggest_fix(detection)
            
            processed.append(detection)
        
        return processed
    
    def _generate_summary(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for detected debts"""
        summary = {
            'total_debts': len(detections),
            'by_type': {},
            'by_granularity': {'class': 0, 'method': 0},
            'high_confidence': 0,
        }
        
        for detection in detections:
            # Count by type
            debt_type = detection.get('debt_type', 'Unknown')
            summary['by_type'][debt_type] = summary['by_type'].get(debt_type, 0) + 1
            
            # Count by granularity
            granularity = detection.get('granularity', 'unknown')
            if granularity in summary['by_granularity']:
                summary['by_granularity'][granularity] += 1
            
            # Count high confidence
            if detection.get('confidence', 0) >= 0.8:
                summary['high_confidence'] += 1
        
        return summary
    
    def analyze_repository(self, repo_path: str, 
                          file_patterns: List[str] = ['**/*.java']) -> Dict[str, Any]:
        """
        Analyze an entire repository.
        
        Args:
            repo_path: Path to repository root
            file_patterns: Glob patterns for files to analyze
            
        Returns:
            Repository-wide analysis results
        """
        
        repo_path = Path(repo_path)
        slicer = ProgramSlicerAgent()
        
        # Find all matching files
        all_files = []
        for pattern in file_patterns:
            all_files.extend(repo_path.glob(pattern))
        
        print(f"\n[Repo Analysis] Found {len(all_files)} files to analyze")
        
        repo_results = {
            'repo_path': str(repo_path),
            'total_files': len(all_files),
            'analyzed_files': 0,
            'total_debts': 0,
            'file_results': [],
            'summary': {}
        }
        
        for file_path in all_files:
            print(f"\n[Repo] Analyzing {file_path.name}...")
            
            try:
                # Slice the file
                sliced_data = slicer.slice_file(str(file_path))
                
                # Read source for localization
                with open(file_path, 'r', encoding='utf-8') as f:
                    source_content = f.read()
                
                # Analyze
                file_result = self.analyze_file(sliced_data, source_content)
                
                repo_results['file_results'].append(file_result)
                repo_results['analyzed_files'] += 1
                repo_results['total_debts'] += file_result.get('filtered_detections', 0)
                
            except Exception as e:
                print(f"[Error] Failed to analyze {file_path}: {str(e)}")
                repo_results['file_results'].append({
                    'file_path': str(file_path),
                    'error': str(e)
                })
        
        # Generate repository-wide summary
        repo_results['summary'] = self._aggregate_repo_summary(repo_results['file_results'])
        
        return repo_results
    
    def _aggregate_repo_summary(self, file_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate summaries from all files"""
        total_summary = {
            'total_debts': 0,
            'by_type': {},
            'by_granularity': {'class': 0, 'method': 0},
            'high_confidence': 0,
            'files_with_debts': 0,
        }
        
        for file_result in file_results:
            if 'error' in file_result:
                continue
            
            summary = file_result.get('summary', {})
            
            if summary.get('total_debts', 0) > 0:
                total_summary['files_with_debts'] += 1
            
            total_summary['total_debts'] += summary.get('total_debts', 0)
            total_summary['high_confidence'] += summary.get('high_confidence', 0)
            
            # Aggregate by type
            for debt_type, count in summary.get('by_type', {}).items():
                total_summary['by_type'][debt_type] = \
                    total_summary['by_type'].get(debt_type, 0) + count
            
            # Aggregate by granularity
            for gran, count in summary.get('by_granularity', {}).items():
                if gran in total_summary['by_granularity']:
                    total_summary['by_granularity'][gran] += count
        
        return total_summary


def analyze_file_simple(file_path: str) -> Dict[str, Any]:
    """
    Simple convenience function to analyze a single file.
    
    Args:
        file_path: Path to Java source file
        
    Returns:
        Analysis results
    """

    # Slice the file
    slicer = ProgramSlicerAgent()
    sliced_data = slicer.slice_file(file_path)
    
    # Read source content
    with open(file_path, 'r', encoding='utf-8') as f:
        source_content = f.read()
    
    # Analyze
    coordinator = DebtDetectionCoordinator()
    results = coordinator.analyze_file(sliced_data, source_content)
    
    return results
