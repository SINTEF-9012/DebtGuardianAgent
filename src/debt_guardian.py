"""
DebtGuardian - Main Pipeline
Multi-agent technical debt detection system
"""
import os
import json
import time
import argparse
import config as cfg
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from program_slicer import ProgramSlicerAgent
from coordinator import DebtDetectionCoordinator
from ollama_utils import start_ollama_server, is_ollama_running, start_ollama_server_log, stop_ollama_server
# Suppress warnings for cleaner output
import warnings
import logging
warnings.filterwarnings('ignore', message='Field "model_client_cls"')
logging.getLogger('autogen.oai.client').setLevel(logging.ERROR)

class DebtGuardian:
    """
    Main pipeline for DebtGuardianAgentic system.
    Orchestrates source loading, slicing, detection, and reporting.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize DebtGuardian pipeline.
        
        Args:
            config: Configuration dict (uses config.py if not provided)
        """
        if config is None:
            self.config = cfg
        else:
            self.config = config
        
        # Initialize components
        self.slicer = ProgramSlicerAgent(
            self.config.AGENT_CONFIGS.get('program_slicer', {})
        )
        self.coordinator = DebtDetectionCoordinator(
            self.config.AGENT_CONFIGS
        )
        
        # Pipeline settings
        pipeline_config = getattr(self.config, 'PIPELINE_CONFIG', {})
        self.enable_localization = pipeline_config.get('enable_localization', True)
        self.enable_explanation = pipeline_config.get('enable_explanation', True)
        self.enable_fix_suggestion = pipeline_config.get('enable_fix_suggestion', False)
        self.batch_size = pipeline_config.get('batch_size', 10)
        
        print("[DebtGuardian] Initialized successfully")
    
    def analyze_file(self, file_path: str, 
                     output_format: str = 'json') -> Dict[str, Any]:
        """
        Analyze a single source file.
        
        Args:
            file_path: Path to source file
            output_format: 'json' or 'report'
            
        Returns:
            Analysis results
        """
        start_time = time.time()
        
        print(f"\n{'='*70}")
        print(f"[DebtGuardian] Analyzing: {file_path}")
        print(f"{'='*70}")
        
        # Step 1: Slice the file
        print("\n[Step 1] Slicing source code...")
        sliced_data = self.slicer.slice_file(file_path)
        
        if 'error' in sliced_data:
            return {
                'file_path': file_path,
                'error': sliced_data['error'],
                'status': 'failed'
            }
        
        print(f"[Step 1] Extracted {len(sliced_data.get('classes', []))} classes, "
              f"{len(sliced_data.get('methods', []))} methods")
        
        # Step 2: Load source content for localization
        print("\n[Step 2] Loading source content...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_content = f.read()
        except Exception as e:
            print(f"[Warning] Could not read source file: {e}")
            source_content = None
        
        # Step 3: Detect technical debt
        print("\n[Step 3] Detecting technical debt...")
        results = self.coordinator.analyze_file(sliced_data, source_content)
        
        # Add metadata
        results['analysis_time'] = time.time() - start_time
        results['timestamp'] = datetime.now().isoformat()
        results['status'] = 'completed'
        
        print(f"\n[Complete] Analysis finished in {results['analysis_time']:.2f}s")
        print(f"[Summary] Found {results['filtered_detections']} technical debts")
        
        if output_format == 'report':
            return self._format_as_report(results)
        else:
            return results
    
    def analyze_directory(self, directory: str,
                          file_extension: Optional[str] = None,
                          recursive: bool = True) -> Dict[str, Any]:
        """
        Analyze all files in a directory.

        Args:
            directory: Directory path
            file_extension: File extension to match (e.g. '.cs'). If None,
                            all supported extensions are included.
            recursive: Whether to search recursively

        Returns:
            Aggregated results for all files
        """
        SUPPORTED_EXTENSIONS = {'.java', '.cs', '.py', '.js', '.ts', '.cpp', '.cc', '.cxx', '.c'}

        dir_path = Path(directory)

        if file_extension:
            exts = {file_extension}
        else:
            exts = SUPPORTED_EXTENSIONS

        prefix = '**/*' if recursive else '*'
        files = []
        for ext in sorted(exts):
            files.extend(dir_path.glob(f'{prefix}{ext}'))

        ext_label = file_extension if file_extension else 'supported'
        print(f"\n[DebtGuardian] Found {len(files)} {ext_label} files in {directory}")
        
        results = {
            'directory': str(directory),
            'total_files': len(files),
            'analyzed_files': 0,
            'failed_files': 0,
            'file_results': [],
            'aggregate_summary': {},
            'timestamp': datetime.now().isoformat()
        }
        
        for i, file_path in enumerate(files, 1):
            print(f"\n[Progress] Analyzing file {i}/{len(files)}: {file_path.name}")
            
            try:
                file_result = self.analyze_file(str(file_path), output_format='json')
                
                if file_result.get('status') == 'completed':
                    results['analyzed_files'] += 1
                else:
                    results['failed_files'] += 1
                
                results['file_results'].append(file_result)
                
            except Exception as e:
                print(f"[Error] Failed to analyze {file_path}: {str(e)}")
                results['failed_files'] += 1
                results['file_results'].append({
                    'file_path': str(file_path),
                    'error': str(e),
                    'status': 'failed'
                })
        
        # Generate aggregate summary
        results['aggregate_summary'] = self._aggregate_results(results['file_results'])
        
        return results
    
    def analyze_repository(self, repo_path: str,
                          language: str = 'all') -> Dict[str, Any]:
        """
        Analyze a source code repository.

        Args:
            repo_path: Path to repository
            language: Programming language ('java', 'python', 'csharp', 'javascript',
                      'typescript', 'cpp', 'c') or 'all' for every supported type.

        Returns:
            Repository analysis results
        """
        extension_map = {
            'java':       ['**/*.java'],
            'python':     ['**/*.py'],
            'javascript': ['**/*.js'],
            'typescript': ['**/*.ts'],
            'csharp':     ['**/*.cs'],
            'cs':         ['**/*.cs'],
            'cpp':        ['**/*.cpp', '**/*.cc', '**/*.cxx'],
            'c':          ['**/*.c'],
            'all':        ['**/*.java', '**/*.cs', '**/*.py', '**/*.js',
                           '**/*.ts', '**/*.cpp', '**/*.cc', '**/*.cxx', '**/*.c'],
        }

        patterns = extension_map.get(language.lower(), extension_map['all'])

        return self.coordinator.analyze_repository(repo_path, patterns)

    def analyze_file_list(self, file_paths: List[str]) -> Dict[str, Any]:
        """Analyze an explicit list of files (e.g. from a CodeScene hotspot export)."""
        return self.coordinator.analyze_file_list(file_paths)

    def _aggregate_results(self, file_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results"""
        aggregate = {
            'total_debts': 0,
            'by_type': {},
            'by_granularity': {'class': 0, 'method': 0},
            'high_confidence_debts': 0,
            'files_with_debts': 0,
            'average_debts_per_file': 0.0,
        }
        
        valid_files = 0
        
        for result in file_results:
            if result.get('status') != 'completed':
                continue
            
            valid_files += 1
            debts = result.get('debts', [])
            
            if debts:
                aggregate['files_with_debts'] += 1
            
            aggregate['total_debts'] += len(debts)
            
            for debt in debts:
                # By type
                debt_type = debt.get('debt_type', 'Unknown')
                aggregate['by_type'][debt_type] = \
                    aggregate['by_type'].get(debt_type, 0) + 1
                
                # By granularity
                granularity = debt.get('granularity', 'unknown')
                if granularity in aggregate['by_granularity']:
                    aggregate['by_granularity'][granularity] += 1
                
                # High confidence
                if debt.get('confidence', 0) >= 0.8:
                    aggregate['high_confidence_debts'] += 1
        
        if valid_files > 0:
            aggregate['average_debts_per_file'] = aggregate['total_debts'] / valid_files
        
        return aggregate
    
    def _format_as_report(self, results: Dict[str, Any]) -> str:
        """Format results"""
        lines = []
        lines.append("=" * 80)
        lines.append("TECHNICAL DEBT ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(f"File: {results['file_path']}")
        lines.append(f"Timestamp: {results['timestamp']}")
        lines.append(f"Analysis Time: {results['analysis_time']:.2f}s")
        lines.append("")
        
        # Summary
        summary = results.get('summary', {})
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Technical Debts Found: {summary.get('total_debts', 0)}")
        lines.append(f"High Confidence Detections: {summary.get('high_confidence', 0)}")
        lines.append("")
        
        # By type
        lines.append("Debts by Type:")
        for debt_type, count in summary.get('by_type', {}).items():
            lines.append(f"  - {debt_type}: {count}")
        lines.append("")
        
        # By granularity
        lines.append("Debts by Granularity:")
        for gran, count in summary.get('by_granularity', {}).items():
            lines.append(f"  - {gran.capitalize()}: {count}")
        lines.append("")
        
        # Detailed findings
        lines.append("DETAILED FINDINGS")
        lines.append("-" * 80)
        
        debts = results.get('debts', [])
        for i, debt in enumerate(debts, 1):
            lines.append(f"\n{i}. {debt.get('debt_type', 'Unknown')} - {debt.get('name', 'Unknown')}")
            lines.append(f"   Granularity: {debt.get('granularity', 'unknown')}")
            lines.append(f"   Confidence: {debt.get('confidence', 0):.2f}")
            
            # Location
            location = debt.get('location', {})
            if 'start_line' in location:
                lines.append(f"   Location: Lines {location['start_line']}-{location['end_line']}")
            
            # Explanation
            explanation = debt.get('explanation')
            if explanation:
                lines.append(f"\n   Explanation:")
                for line in explanation.split('\n'):
                    lines.append(f"   {line}")
            
            # Fix suggestion
            fix = debt.get('fix_suggestion')
            if fix:
                lines.append(f"\n   Fix Suggestion:")
                for line in fix.split('\n'):
                    lines.append(f"   {line}")
            
            lines.append("")
        
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        return '\n'.join(lines)
    
    def save_results(self, results: Dict[str, Any], 
                    output_path: str, 
                    format: str = 'json'):
        """
        Save analysis results to file.
        
        Args:
            results: Analysis results
            output_path: Output file path
            format: 'json' or 'report'
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"[Saved] Results saved to {output_path}")
        
        elif format == 'report':
            report = self._format_as_report(results) if isinstance(results, dict) else results
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"[Saved] Report saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="DebtGuardianAgentic - Multi-agent Technical Debt Detection"
    )
    parser.add_argument('path', help='File or directory to analyze')
    parser.add_argument('--type', choices=['file', 'dir', 'repo'], default='file',
                       help='Type of analysis')
    parser.add_argument('--language', default='all',
                       help='Language filter: java, python, csharp, javascript, typescript, cpp, c, or all (default: all)')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'report'], default='json',
                       help='Output format')
    parser.add_argument('--recursive', action='store_true',
                       help='Recursive directory search')
    parser.add_argument('--file-list',
                       help='Text file with one file path per line (limits repo analysis to those files)')
    parser.add_argument('--codescene-url',
                       help='CodeScene base URL (e.g. http://localhost:3003 for Docker)')
    parser.add_argument('--codescene-token',
                       help='CodeScene API access token')
    parser.add_argument('--codescene-project',
                       help='CodeScene project name or numeric ID')
    
    args = parser.parse_args()
    
    # Start ollama server if not running
    proc = None
    if not is_ollama_running():
        print("[Ollama] Starting Ollama server...")
        proc = start_ollama_server_log()
        time.sleep(5)  # Wait for server to start
    else:
        print("[Ollama] Ollama server is already running")

    # Initialize DebtGuardian
    guardian = DebtGuardian()
    
    # Perform analysis
    if args.type == 'file':
        results = guardian.analyze_file(args.path, output_format=args.format)
    elif args.type == 'dir':
        lang_ext_map = {
            'java': '.java', 'python': '.py', 'csharp': '.cs', 'cs': '.cs',
            'javascript': '.js', 'typescript': '.ts', 'cpp': '.cpp', 'c': '.c',
        }
        ext = lang_ext_map.get(args.language.lower()) if args.language else None
        results = guardian.analyze_directory(args.path, file_extension=ext, recursive=args.recursive)
    elif args.type == 'repo':
        # Determine file list: CodeScene API > --file-list > full glob
        file_list = None

        if args.codescene_url and args.codescene_token:
            from codescene_client import fetch_hotspot_file_paths
            proj = args.codescene_project
            proj_id = int(proj) if proj and proj.isdigit() else None
            proj_name = proj if proj and not (proj and proj.isdigit()) else None
            file_list = fetch_hotspot_file_paths(
                args.codescene_url, args.codescene_token, args.path,
                project_id=proj_id, project_name=proj_name,
            )
            print(f"[CodeScene] Fetched {len(file_list)} hotspot targets")

        elif args.file_list:
            with open(args.file_list, 'r') as fl:
                file_list = [
                    line.strip() for line in fl
                    if line.strip() and not line.strip().startswith('#')
                ]
            # Resolve relative paths against repo root
            repo = Path(args.path)
            file_list = [
                str(repo / p) if not os.path.isabs(p) else p
                for p in file_list
            ]
            print(f"[File List] Loaded {len(file_list)} files from {args.file_list}")

        if file_list:
            results = guardian.analyze_file_list(file_list)
        else:
            results = guardian.analyze_repository(args.path, language=args.language)
    else:
        print(f"Unknown analysis type: {args.type}")
        return
    
    # Save or print results
    if args.output:
        guardian.save_results(results, args.output, format=args.format)
    else:
        if args.format == 'json':
            print(json.dumps(results, indent=2))
        else:
            print(results)
    
    # Only stop the server if we started it
    if proc is not None:
        stop_ollama_server(proc)

if __name__ == '__main__':
    main()
