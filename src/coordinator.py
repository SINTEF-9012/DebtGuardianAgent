"""
Coordinator Module
Orchestrates the multi-agent technical debt detection workflow
"""
import re
import concurrent.futures
from typing import Dict, Any, List, Optional
from pathlib import Path

import config as cfg
from debt_detector import (
    ClassDebtDetector,
    MethodDebtDetector,
    RelationshipDebtDetector,
    SecurityDebtDetector,
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
        self.relationship_detector = None
        self.security_detector = None
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
        
        # Relationship detector
        rel_config = config.get('relationship_detector', {})
        if rel_config.get('enabled', True):
            self.relationship_detector = RelationshipDebtDetector(rel_config)
            print("[Init] Relationship Debt Detector initialized")
        
        # Security detector
        sec_config = config.get('security_detector', {})
        if sec_config.get('enabled', True):
            self.security_detector = SecurityDebtDetector(sec_config)
            print("[Init] Security Debt Detector initialized")
        
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
        
        # Detect relationship-level debts (Refused Bequest, Shotgun Surgery, Inappropriate Intimacy)
        if self.relationship_detector and classes:
            self._resolve_bidirectional_dependencies(classes)
            relationship_results = self._detect_relationship_debts(classes)
            all_detections.extend(relationship_results)
        
        # Detect security debts (Hardcoded Secrets, SQL/Command Injection)
        if self.security_detector:
            security_results = self._detect_security_debts(classes, methods)
            all_detections.extend(security_results)
        
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
    
    def _detect_relationship_debts(self, classes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect relationship-level debts (Refused Bequest, Shotgun Surgery,
        Inappropriate Intimacy) in all classes.
        """
        results = []

        # Build a code lookup for providing related class context
        class_code_lookup = {c['name']: c.get('code', '') for c in classes}

        # Pre-compute thresholds once (they don't change per class)
        coupling_threshold = cfg.THRESHOLDS.get('shotgun_surgery_coupled_classes', 5) // 2
        intimacy_threshold = max(1, cfg.THRESHOLDS.get('inappropriate_intimacy_bidirectional_threshold', 3) // 2)

        for class_info in classes:
            metrics = class_info.get('metrics', {})

            has_inheritance = bool(metrics.get('extends'))
            has_high_coupling = metrics.get('coupled_class_count', 0) >= coupling_threshold
            has_bidirectional = len(metrics.get('bidirectional_dependencies', [])) >= intimacy_threshold

            if not (has_inheritance or has_high_coupling or has_bidirectional):
                continue

            # Build related code context for the LLM
            related_code = ''
            if has_inheritance and metrics.get('extends') in class_code_lookup:
                related_code = class_code_lookup[metrics['extends']]
            elif has_bidirectional:
                related_parts = []
                for dep_name in metrics.get('bidirectional_dependencies', [])[:2]:
                    if dep_name in class_code_lookup:
                        related_parts.append(class_code_lookup[dep_name])
                related_code = '\n\n'.join(related_parts)

            enriched_info = dict(class_info)
            enriched_info['related_code'] = related_code

            result = self.relationship_detector.detect(enriched_info)
            results.append(result)
            print(f"  [Relationship] {class_info['name']}: {result.get('debt_type', 'Unknown')}")

        return [r for r in results if r.get('label') != '0']

    def _resolve_bidirectional_dependencies(self, classes: List[Dict[str, Any]]):
        """
        Cross-reference outgoing class references across all classes in the file
        to identify bidirectional dependencies (Inappropriate Intimacy signal).
        """
        class_names = {c['name'] for c in classes}

        outgoing = {}
        for c in classes:
            refs = set(c.get('metrics', {}).get('coupled_classes', []))
            outgoing[c['name']] = refs & class_names

        for c in classes:
            bidirectional = []
            for other_name in outgoing.get(c['name'], []):
                if c['name'] in outgoing.get(other_name, set()):
                    bidirectional.append(other_name)
            c.setdefault('metrics', {})['bidirectional_dependencies'] = bidirectional

    def _detect_security_debts(self, classes: List[Dict[str, Any]],
                                methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect security debts in classes and methods.
        Scans both class-level code (for hardcoded secrets) and method-level
        code (for injection vulnerabilities).
        """
        results = []

        # Analyse classes for hardcoded secrets
        for class_info in classes:
            security_metrics = self._compute_security_metrics(class_info.get('code', ''))
            if security_metrics.get('has_security_signals'):
                enriched = dict(class_info)
                enriched['security_metrics'] = security_metrics
                result = self.security_detector.detect(enriched)
                results.append(result)
                print(f"  [Security] {class_info['name']}: {result.get('debt_type', 'Unknown')}")

        # Analyse all methods (standalone + those inside classes) for injection
        all_methods = list(methods)
        for class_info in classes:
            all_methods.extend(class_info.get('methods', []))

        for method_info in all_methods:
            security_metrics = self._compute_security_metrics(method_info.get('code', ''))
            if security_metrics.get('has_security_signals'):
                enriched = dict(method_info)
                enriched['security_metrics'] = security_metrics
                result = self.security_detector.detect(enriched)
                results.append(result)
                print(f"  [Security] {method_info['name']}: {result.get('debt_type', 'Unknown')}")

        return [r for r in results if r.get('label') != '0']

    @staticmethod
    def _compute_security_metrics(code: str) -> Dict[str, Any]:
        """Compute heuristic security metrics from source code."""

        metrics: Dict[str, Any] = {
            'hardcoded_string_count': 0,
            'secret_pattern_matches': [],
            'sql_concat_count': 0,
            'exec_calls': [],
            'has_security_signals': False,
        }

        if not code:
            return metrics

        # --- Hardcoded secrets heuristics ---
        secret_patterns = [
            (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']', 'password'),
            (r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][^"\']{8,}["\']', 'api_key'),
            (r'(?i)(secret|token|auth)\s*=\s*["\'][^"\']{8,}["\']', 'secret/token'),
            (r'(?i)(aws_access_key|aws_secret)\s*=\s*["\'][^"\']+["\']', 'aws_credential'),
            (r'(?i)jdbc:[a-z]+://[^\s]+', 'jdbc_connection_string'),
            (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', 'private_key'),
        ]

        for pattern, label in secret_patterns:
            if re.search(pattern, code):
                metrics['secret_pattern_matches'].append(label)

        # Count suspicious hardcoded strings (long strings assigned to security-related vars)
        hardcoded = re.findall(r'(?i)(?:password|secret|key|token|credential)\s*=\s*["\'][^"\']{8,}["\']', code)
        metrics['hardcoded_string_count'] = len(hardcoded)

        # --- SQL/Command injection heuristics ---
        # String concatenation in SQL contexts
        sql_concat_patterns = [
            r'(?i)["\']SELECT\s.*?\+',
            r'(?i)["\']INSERT\s.*?\+',
            r'(?i)["\']UPDATE\s.*?\+',
            r'(?i)["\']DELETE\s.*?\+',
            r'(?i)executeQuery\s*\(\s*[^")]+\+',
            r'(?i)executeUpdate\s*\(\s*[^")]+\+',
            r'(?i)execute\s*\(\s*["\'].*?\+',
        ]
        for pattern in sql_concat_patterns:
            metrics['sql_concat_count'] += len(re.findall(pattern, code))

        # Command execution calls
        exec_patterns = [
            (r'Runtime\.getRuntime\(\)\.exec\s*\(', 'Runtime.exec'),
            (r'ProcessBuilder\s*\(', 'ProcessBuilder'),
            (r'(?i)os\.system\s*\(', 'os.system'),
            (r'(?i)subprocess\.\w+\s*\(', 'subprocess'),
            (r'(?i)eval\s*\(', 'eval'),
        ]
        for pattern, label in exec_patterns:
            if re.search(pattern, code):
                metrics['exec_calls'].append(label)

        metrics['has_security_signals'] = bool(
            metrics['secret_pattern_matches'] or
            metrics['hardcoded_string_count'] > 0 or
            metrics['sql_concat_count'] > 0 or
            metrics['exec_calls']
        )

        return metrics

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
                          file_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Analyze an entire repository.
        
        Args:
            repo_path: Path to repository root
            file_patterns: Glob patterns for files to analyze
            
        Returns:
            Repository-wide analysis results
        """
        if file_patterns is None:
            file_patterns = ['**/*.java', '**/*.cs', '**/*.py', '**/*.js', '**/*.ts', '**/*.cpp']
        
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

    def analyze_file_list(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Analyze a specific list of files (e.g. from CodeScene hotspots).

        Args:
            file_paths: Absolute or relative paths to the files to analyze

        Returns:
            Repository-style results dict
        """
        slicer = ProgramSlicerAgent()

        repo_results = {
            'source': 'file_list',
            'total_files': len(file_paths),
            'analyzed_files': 0,
            'total_debts': 0,
            'file_results': [],
            'summary': {}
        }

        for i, fp in enumerate(file_paths, 1):
            fp = Path(fp)
            if not fp.exists():
                print(f"[Skip] File not found: {fp}")
                repo_results['file_results'].append({
                    'file_path': str(fp), 'error': 'file not found'
                })
                continue

            print(f"\n[{i}/{len(file_paths)}] Analyzing {fp.name}...")

            try:
                sliced_data = slicer.slice_file(str(fp))

                with open(fp, 'r', encoding='utf-8') as f:
                    source_content = f.read()

                file_result = self.analyze_file(sliced_data, source_content)

                repo_results['file_results'].append(file_result)
                repo_results['analyzed_files'] += 1
                repo_results['total_debts'] += file_result.get('filtered_detections', 0)

            except Exception as e:
                print(f"[Error] Failed to analyze {fp}: {e}")
                repo_results['file_results'].append({
                    'file_path': str(fp), 'error': str(e)
                })

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
