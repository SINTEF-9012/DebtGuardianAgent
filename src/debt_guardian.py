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
                          file_extension: str = '.java',
                          recursive: bool = True) -> Dict[str, Any]:
        """
        Analyze all files in a directory.
        
        Args:
            directory: Directory path
            file_extension: File extension to match
            recursive: Whether to search recursively
            
        Returns:
            Aggregated results for all files
        """
        dir_path = Path(directory)
        
        # Find files
        if recursive:
            pattern = f'**/*{file_extension}'
        else:
            pattern = f'*{file_extension}'
        
        files = list(dir_path.glob(pattern))
        
        print(f"\n[DebtGuardian] Found {len(files)} {file_extension} files in {directory}")
        
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
                          language: str = 'java') -> Dict[str, Any]:
        """
        Analyze a source code repository.
        
        Args:
            repo_path: Path to repository
            language: Programming language ('java', 'python', etc.)
            
        Returns:
            Repository analysis results
        """
        # Determine file patterns based on language
        extension_map = {
            'java': '**/*.java',
            'python': '**/*.py',
            'javascript': '**/*.js',
            'csharp': '**/*.cs',
            'cpp': '**/*.cpp'
        }
        
        pattern = extension_map.get(language, '**/*.java')
        
        return self.coordinator.analyze_repository(repo_path, [pattern])
    
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
    parser.add_argument('--language', default='java',
                       help='Programming language (for repo analysis)')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'report'], default='json',
                       help='Output format')
    parser.add_argument('--recursive', action='store_true',
                       help='Recursive directory search')
    
    args = parser.parse_args()
    
    # Initialize DebtGuardian
    guardian = DebtGuardian()
    
    # Perform analysis
    if args.type == 'file':
        results = guardian.analyze_file(args.path, output_format=args.format)
    elif args.type == 'dir':
        results = guardian.analyze_directory(args.path, recursive=args.recursive)
    elif args.type == 'repo':
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


if __name__ == '__main__':
    main()
