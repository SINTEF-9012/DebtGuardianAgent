"""
Program Slicer Agent
Extracts classes and methods from Java source files with metrics
"""
import re
import javalang
from typing import List, Dict, Any, Optional
from pathlib import Path
import config


class ProgramSlicerAgent:
    """
    Slices Java source code into analyzable units (classes and methods).
    Extracts structural information and basic metrics.
    """
    
    def __init__(self, slicer_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the slicer with configuration.
        
        Args:
            slicer_config: Configuration dict from config.AGENT_CONFIGS['program_slicer']
        """
        self.config = slicer_config or config.AGENT_CONFIGS.get('program_slicer', {})
        self.extract_metrics = self.config.get('extract_metrics', True)
        self.min_method_loc = self.config.get('min_method_loc', 3)
        self.max_class_loc = self.config.get('max_class_loc', 1000)
    
   

    def slice_file(self, file_path: str) -> Dict[str, Any]:
        """
        Slice a Java file into classes and methods with metadata.
        
        Args:
            file_path: Path to Java source file
            
        Returns:
            Dictionary containing extracted classes and methods with metrics
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            return self.slice_code(source_code, file_path)
        except Exception as e:
            print(f"[Error] Failed to slice file {file_path}: {str(e)}")
            return {'classes': [], 'methods': [], 'error': str(e)}
    
    def slice_code(self, source_code: str, file_path: str = "unknown") -> Dict[str, Any]:
        """
        Slice Java source code into analyzable units.
        
        Args:
            source_code: Java source code as string
            file_path: Original file path (for reference)
            
        Returns:
            Dictionary with extracted classes and methods
        """
        result = {
            'file_path': file_path,
            'classes': [],
            'methods': [],
            'total_loc': self._count_loc(source_code)
        }
        
        try:
            # Parse with javalang first 
            tree = javalang.parse.parse(source_code)
            
            # Extract classes
            for path, node in tree.filter(javalang.tree.ClassDeclaration):
                class_info = self._extract_class_from_ast(node, source_code, file_path)
                if class_info:
                    result['classes'].append(class_info)
            
        except Exception as e:
            print(f"[Warning] javalang parsing failed for {file_path}, using regex fallback: {str(e)}")
            # Fallback to regex-based extraction
            result['classes'] = self._extract_classes_regex(source_code, file_path)
            result['methods'] = self._extract_methods_regex(source_code, file_path)
        
        return result
    
    def _strip_comments(self, code: str) -> str:
        # Remove block comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.S)
        # Remove line comments
        code = re.sub(r'//.*', '', code)
        return code
    
    def _extract_class_from_ast(self, node: javalang.tree.ClassDeclaration, 
                                source_code: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract a class using AST with its metadata and metrics."""
        try:
            class_name = node.name
            
            # For javalang, extract the actual code using regex
            class_code = self._extract_class_code_by_name(source_code, class_name)
            
            if not class_code:
                return None
            
            loc = self._count_loc(class_code)
            
            # Skip very large classes
            if loc > self.max_class_loc:
                print(f"[Info] Skipping large class {class_name} ({loc} LOC)")
                return None
            
            # Extract methods within this class
            methods = []
            method_count = 0
            
            if node.methods:
                for method_node in node.methods:
                    method_count += 1
                    method_info = self._extract_method_from_ast(
                        method_node, class_code, file_path, class_name
                    )
                    #if method_info and method_info['loc'] >= self.min_method_loc:
                    if method_info and method_info['metrics'].get('loc', 0) >= self.min_method_loc:
                        methods.append(method_info)
            
            # Extract fields
            field_count = len(node.fields) if node.fields else 0
            
            # Calculate metrics
            metrics = {}
            if self.extract_metrics:
                metrics = {
                    'loc': loc,
                    'method_count': method_count,
                    'field_count': field_count,
                    'is_abstract': 'abstract' in (node.modifiers or []),
                }
                
                # Estimate getter/setter ratio for Data Class detection
                getter_setter_count = self._count_getters_setters(methods)
                metrics['getter_setter_ratio'] = (
                    getter_setter_count / method_count if method_count > 0 else 0
                )
            
            return {
                'type': 'class',
                'name': class_name,
                'code': class_code,
                'file_path': file_path,
                'methods': methods,
                'metrics': metrics,
                'granularity': 'class'
            }
            
        except Exception as e:
            print(f"[Warning] Failed to extract class: {str(e)}")
            return None
    
    def _extract_method_from_ast(self, node: javalang.tree.MethodDeclaration, 
                                 source_code: str, file_path: str, 
                                 parent_class: str = None) -> Optional[Dict[str, Any]]:
        """Extract a method using AST with its metadata and metrics."""
        try:
            method_name = node.name
            
            # Extract method code using regex
            method_code = self._extract_method_code_by_name(source_code, method_name)
            
            if not method_code:
                return None
            
            loc = self._count_loc(method_code)
            
            # Calculate metrics
            metrics = {}
            if self.extract_metrics:
                metrics = {
                    'loc': loc,
                    'parameter_count': len(node.parameters) if node.parameters else 0,
                    'cyclomatic_complexity': self._estimate_complexity(method_code),
                    'external_calls': self._count_external_calls(method_code),
                }
            
            return {
                'type': 'method',
                'name': method_name,
                'code': method_code,
                'file_path': file_path,
                'parent_class': parent_class,
                'metrics': metrics,
                'granularity': 'method'
            }
            
        except Exception as e:
            print(f"[Warning] Failed to extract method: {str(e)}")
            return None
    
    def _extract_class_code_by_name(self, source_code: str, class_name: str) -> Optional[str]:
        """Extract class code using class name."""
        # Pattern to match class declaration
        pattern = rf'(public\s+|private\s+|protected\s+)?(abstract\s+|final\s+)?class\s+{re.escape(class_name)}\s*(?:<[^>]+>)?(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{{'
        
        match = re.search(pattern, source_code)
        if not match:
            return None
        
        start_pos = match.start()
        class_code = self._extract_block(source_code, start_pos)
        
        return class_code
    
    def _extract_method_code_by_name(self, source_code: str, method_name: str) -> Optional[str]:
        """Extract method code using method name."""
        # Pattern to match method declaration
        pattern = rf'(public|private|protected)?\s+(static\s+)?[\w<>\[\]]+\s+{re.escape(method_name)}\s*\([^\)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{{'
        
        match = re.search(pattern, source_code)
        if not match:
            return None
        
        start_pos = match.start()
        method_code = self._extract_block(source_code, start_pos)
        
        return method_code
    
    def _extract_classes_regex(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """Fallback: Extract classes using regex when AST parsing fails."""
        classes = []
        
        # Match class declarations
        class_pattern = r'(public\s+|private\s+|protected\s+)?(abstract\s+|final\s+)?class\s+(\w+)'
        matches = re.finditer(class_pattern, source_code)
        
        for match in matches:
            class_name = match.group(3)
            start_pos = match.start()
            
            # Find the matching closing brace
            class_code = self._extract_block(source_code, start_pos)
            
            if class_code:
                loc = self._count_loc(class_code)
                if loc <= self.max_class_loc:
                    # Extract methods from this class
                    class_methods = self._extract_methods_regex(class_code, file_path)
                    
                    metrics = {'loc': loc} if self.extract_metrics else {}
                    if class_methods:
                        metrics['method_count'] = len(class_methods)
                    
                    classes.append({
                        'type': 'class',
                        'name': class_name,
                        'code': class_code,
                        'file_path': file_path,
                        'methods': class_methods,
                        'metrics': metrics,
                        'granularity': 'class'
                    })
        
        return classes
    
    def _extract_methods_regex(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """Fallback: Extract methods using regex."""
        methods = []
        
        # Match method declarations (simplified)
        method_pattern = r'(public|private|protected)?\s+(static\s+)?[\w<>\[\]]+\s+(\w+)\s*\([^\)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{'
        matches = re.finditer(method_pattern, source_code)
        
        for match in matches:
            method_name = match.group(3)
            
            # Skip constructors and common getters/setters for now if too simple
            if method_name in ['get', 'set', 'is']:
                continue
            
            start_pos = match.start()
            method_code = self._extract_block(source_code, start_pos)
            
            if method_code:
                loc = self._count_loc(method_code)
                if loc >= self.min_method_loc:
                    metrics = {'loc': loc} if self.extract_metrics else {}
                    
                    methods.append({
                        'type': 'method',
                        'name': method_name,
                        'code': method_code,
                        'file_path': file_path,
                        'parent_class': None,
                        'metrics': metrics,
                        'granularity': 'method'
                    })
        
        return methods
    
    def _extract_block(self, source_code: str, start_pos: int) -> Optional[str]:
        """Extract a code block starting from a position (finds matching braces)."""
        # Find the opening brace
        brace_pos = source_code.find('{', start_pos)
        if brace_pos == -1:
            return None
        
        # Count braces to find matching closing brace
        count = 0
        in_string = False
        in_char = False
        escape = False
        
        for i in range(brace_pos, len(source_code)):
            char = source_code[i]
            
            # Handle escape sequences
            if escape:
                escape = False
                continue
            
            if char == '\\':
                escape = True
                continue
            
            # Handle strings and chars
            if char == '"' and not in_char:
                in_string = not in_string
            elif char == "'" and not in_string:
                in_char = not in_char
            
            # Count braces only outside strings
            if not in_string and not in_char:
                if char == '{':
                    count += 1
                elif char == '}':
                    count -= 1
                    if count == 0:
                        return source_code[start_pos:i+1]
        
        return None
    
    def _count_loc(self, code: str) -> int:
        """Count lines of code (excluding blank lines and comments)."""
        lines = code.split('\n')
        loc = 0
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # Handle multi-line comments
            if '/*' in stripped:
                in_multiline_comment = True
            if '*/' in stripped:
                in_multiline_comment = False
                continue
            
            if in_multiline_comment:
                continue
            
            # Skip blank lines and single-line comments
            if stripped and not stripped.startswith('//'):
                loc += 1
        
            #if stripped and not stripped.startswith('//') and stripped not in ('{', '}'):
            #    loc += 1
        return loc
    
    def _estimate_complexity(self, code: str) -> int:
        """Estimate cyclomatic complexity (simplified)."""
        # Count decision points
        complexity = 1  # Base complexity
        
        keywords = ['if', 'else', 'for', 'while', 'case', 'catch', '&&', '||', '?']
        for keyword in keywords:
            # Use word boundaries for keywords to avoid partial matches
            if keyword in ['&&', '||', '?']:
                complexity += code.count(keyword)
            else:
                pattern = r'\b' + keyword + r'\b'
                complexity += len(re.findall(pattern, code))
        
        return complexity
    
    def _count_external_calls(self, code: str) -> int:
        """Count approximate number of external method calls."""
        # Look for patterns like: object.method()
        pattern = r'\w+\.\w+\('
        clean_code = self._strip_comments(code)
        matches = re.findall(pattern, clean_code)
        #matches = re.findall(pattern, code)
        return len(matches)
    
    def _count_getters_setters(self, methods: List[Dict[str, Any]]) -> int:
        """Count methods that appear to be getters or setters."""
        count = 0
        for method in methods:
            name = method['name']
            if name.startswith('get') or name.startswith('set') or name.startswith('is'):
                # Simple heuristic: short methods with getter/setter names
                if method.get('metrics', {}).get('loc', 0) <= 3:
                    count += 1
        return count

def slice_java_file(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to slice a Java file.
    Compatible with the old workflow.
    
    Args:
        file_path: Path to Java file
        
    Returns:
        Dictionary with classes and methods
    """
    slicer = ProgramSlicerAgent()
    return slicer.slice_file(file_path)


def slice_java_code(source_code: str, filename: str = "snippet.java") -> Dict[str, Any]:
    """
    Convenience function to slice Java code string.
    Compatible with the old workflow.
    
    Args:
        source_code: Java source code as string
        filename: Optional filename for reference
        
    Returns:
        Dictionary with classes and methods
    """
    slicer = ProgramSlicerAgent()
    return slicer.slice_code(source_code, filename)