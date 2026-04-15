"""
Program Slicer Agent
Extracts classes and methods from source files using source_parser AST parsers.
Supports: Java, C#, Python, JavaScript/TypeScript, C++
"""
import re
import warnings
from typing import List, Dict, Any, Optional
from pathlib import Path
import config

# Suppress tree-sitter deprecation warnings from source_parser
warnings.filterwarnings('ignore', category=FutureWarning, module='tree_sitter')

# Language parser map — populated lazily
_PARSER_MAP = {
    '.java': None,
    '.cs':   None,
    '.py':   None,
    '.js':   None,
    '.ts':   None,
    '.cpp':  None,
    '.cc':   None,
    '.cxx':  None,
    '.c':    None,
    '.h':    None,
    '.hpp':  None,
}


def _get_parser_class(ext: str):
    """Return the source_parser class for the given file extension."""
    from source_parser.parsers import (
        JavaParser, CSharpParser, PythonParser,
        JavascriptParser, CppParser,
    )
    mapping = {
        '.java': JavaParser,
        '.cs':   CSharpParser,
        '.py':   PythonParser,
        '.js':   JavascriptParser,
        '.ts':   JavascriptParser,
        '.cpp':  CppParser,
        '.cc':   CppParser,
        '.cxx':  CppParser,
        '.c':    CppParser,
        '.h':    CppParser,
        '.hpp':  CppParser,
    }
    return mapping.get(ext)


class ProgramSlicerAgent:
    """
    Slices source code into analysable units (classes and methods).
    Uses source_parser AST parsers for all supported languages.
    Supported: Java, C#, Python, JavaScript/TypeScript, C/C++
    """

    def __init__(self, slicer_config: Optional[Dict[str, Any]] = None):
        self.config = slicer_config or config.AGENT_CONFIGS.get('program_slicer', {})
        self.extract_metrics = self.config.get('extract_metrics', True)
        self.min_method_loc = self.config.get('min_method_loc', 3)
        self.max_class_loc = self.config.get('max_class_loc', 2000)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def slice_file(self, file_path: str) -> Dict[str, Any]:
        """Slice a source file into classes and methods."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            return self.slice_code(source_code, file_path)
        except Exception as e:
            print(f"[Error] Failed to slice file {file_path}: {e}")
            return {'classes': [], 'methods': [], 'error': str(e)}

    def slice_code(self, source_code: str, file_path: str = "unknown") -> Dict[str, Any]:
        """
        Slice source code into analysable units using the appropriate AST parser.

        Args:
            source_code: Source code string.
            file_path:   Path used to determine the language.

        Returns:
            Dict with 'classes', 'methods', 'file_path', 'total_loc'.
        """
        ext = Path(file_path).suffix.lower()
        parser_cls = _get_parser_class(ext)

        result = {
            'file_path': file_path,
            'classes': [],
            'methods': [],
            'total_loc': self._count_loc(source_code),
        }

        if parser_cls is None:
            print(f"[Warning] No source parser available for extension '{ext}' ({file_path}). "
                  f"Supported: .java .cs .py .js .ts .cpp .cc .cxx .c .h .hpp")
            return result

        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                parser = parser_cls(source_code)
            schema = parser.schema
        except Exception as e:
            print(f"[Error] source_parser failed for {file_path}: {e}")
            return result

        # --- Extract top-level / standalone methods ---
        for m in schema.get('methods', []):
            method_info = self._build_method_info(m, file_path, parent_class=None)
            if method_info and method_info['metrics'].get('loc', 0) >= self.min_method_loc:
                result['methods'].append(method_info)

        # --- Extract classes and their methods ---
        for cls in schema.get('classes', []):
            class_info = self._build_class_info(cls, file_path)
            if class_info:
                result['classes'].append(class_info)

        return result

    # ------------------------------------------------------------------
    # Schema → internal dict builders
    # ------------------------------------------------------------------

    def _build_class_info(self, cls: Dict[str, Any], file_path: str) -> Optional[Dict[str, Any]]:
        """Convert a source_parser class schema entry to internal format."""
        try:
            class_name = cls.get('name', 'Unknown')
            class_code = cls.get('original_string', '')

            if not class_code:
                return None

            loc = self._count_loc(class_code)
            if loc > self.max_class_loc:
                print(f"[Info] Skipping large class {class_name} ({loc} LOC)")
                return None

            # Build method list for this class
            methods = []
            for m in cls.get('methods', []):
                method_info = self._build_method_info(m, file_path, parent_class=class_name)
                if method_info and method_info['metrics'].get('loc', 0) >= self.min_method_loc:
                    methods.append(method_info)

            method_count = len(cls.get('methods', []))

            # Field count — available in some parsers via attributes
            attrs = cls.get('attributes', {})
            fields = attrs.get('fields', []) or []
            properties = attrs.get('properties', []) or []  # C# auto-properties
            expr_stmts = attrs.get('expression_statements', []) or []
            field_count = len(fields) or len(properties) or len(expr_stmts)

            metrics = {}
            if self.extract_metrics:
                # For C# auto-properties, count those with get/set as getter/setter equivalents
                cs_prop_gs_count = sum(
                    1 for p in properties
                    if 'get' in p.get('accessors', '') or 'set' in p.get('accessors', '')
                )
                method_gs_count = self._count_getters_setters(methods)
                getter_setter_count = cs_prop_gs_count + method_gs_count

                # For C# the "method_count" should include properties for ratio purposes
                effective_total = method_count + len(properties)
                metrics = {
                    'loc': loc,
                    'method_count': method_count,
                    'field_count': field_count,
                    'is_abstract': self._is_abstract(cls),
                    'getter_setter_ratio': (
                        getter_setter_count / effective_total if effective_total > 0 else 0
                    ),
                }

                # --- Relationship metrics ---
                # Inheritance info (Refused Bequest detection)
                defn = cls.get('definition', '') or ''
                extends_name = self._extract_extends(defn)
                implements_names = self._extract_implements(defn)

                metrics['extends'] = extends_name
                metrics['implements'] = implements_names

                # Override ratio
                override_count = self._count_overrides_from_schema(cls)
                inherited_estimate = self._estimate_inherited_methods(class_code, extends_name)
                metrics['override_count'] = override_count
                metrics['override_ratio'] = (
                    override_count / inherited_estimate
                    if inherited_estimate > 0 else 0.0
                )

                # Coupling metrics (Shotgun Surgery detection)
                coupled_classes = self._extract_coupled_classes(class_code, class_name)
                metrics['coupled_classes'] = coupled_classes
                metrics['coupled_class_count'] = len(coupled_classes)
                metrics['fan_out'] = self._count_external_calls(class_code)

                # Outgoing references for bidirectional analysis (Inappropriate Intimacy)
                metrics['outgoing_class_references'] = coupled_classes
                metrics['bidirectional_dependencies'] = []  # Populated by coordinator

            return {
                'type': 'class',
                'name': class_name,
                'code': class_code,
                'file_path': file_path,
                'methods': methods,
                'metrics': metrics,
                'granularity': 'class',
            }

        except Exception as e:
            print(f"[Warning] Failed to extract class '{cls.get('name', '?')}': {e}")
            return None

    def _build_method_info(self, m: Dict[str, Any], file_path: str,
                           parent_class: Optional[str]) -> Optional[Dict[str, Any]]:
        """Convert a source_parser method schema entry to internal format."""
        try:
            method_name = m.get('name', 'Unknown')
            method_code = m.get('original_string', '')

            if not method_code:
                return None

            loc = self._count_loc(method_code)
            attrs = m.get('attributes', {}) or {}

            # Parameter count — field name differs by language
            param_count = len(
                attrs.get('parameters', []) or
                attrs.get('params', []) or
                []
            )

            metrics = {}
            if self.extract_metrics:
                metrics = {
                    'loc': loc,
                    'parameter_count': param_count,
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
                'granularity': 'method',
            }

        except Exception as e:
            print(f"[Warning] Failed to extract method '{m.get('name', '?')}': {e}")
            return None

    # ------------------------------------------------------------------
    # Metric helpers
    # ------------------------------------------------------------------

    def _count_loc(self, code: str) -> int:
        """Count non-blank, non-comment lines of code."""
        lines = code.split('\n')
        loc = 0
        in_multiline = False
        for line in lines:
            stripped = line.strip()
            if '/*' in stripped:
                in_multiline = True
            if '*/' in stripped:
                in_multiline = False
                continue
            if in_multiline:
                continue
            if stripped and not stripped.startswith('//') and not stripped.startswith('#'):
                loc += 1
        return loc

    def _estimate_complexity(self, code: str) -> int:
        """Estimate cyclomatic complexity via decision-point counting."""
        complexity = 1
        keywords = ['if', 'else', 'for', 'while', 'case', 'catch', '&&', '||', '?']
        for kw in keywords:
            if kw in ('&&', '||', '?'):
                complexity += code.count(kw)
            else:
                complexity += len(re.findall(r'\b' + kw + r'\b', code))
        return complexity

    def _count_external_calls(self, code: str) -> int:
        """Approximate count of external method calls (object.method())."""
        clean = re.sub(r'/\*.*?\*/', '', code, flags=re.S)
        clean = re.sub(r'//.*', '', clean)
        clean = re.sub(r'#.*', '', clean)
        return len(re.findall(r'\w+\.\w+\(', clean))

    def _count_getters_setters(self, methods: List[Dict[str, Any]]) -> int:
        """Count methods that appear to be getters or setters."""
        count = 0
        for m in methods:
            name = m.get('name', '')
            if (name.startswith('get') or name.startswith('set') or
                    name.startswith('is') or name.startswith('Get') or
                    name.startswith('Set') or name.startswith('Is')):
                if m.get('metrics', {}).get('loc', 0) <= 5:
                    count += 1
        return count

    def _is_abstract(self, cls: Dict[str, Any]) -> bool:
        """Check whether the class is abstract."""
        attrs = cls.get('attributes', {}) or {}
        modifiers = attrs.get('modifiers', []) or []
        defn = cls.get('definition', '') or ''
        return 'abstract' in modifiers or 'abstract' in defn.lower()

    # ------------------------------------------------------------------
    # Relationship metric helpers
    # ------------------------------------------------------------------

    def _extract_extends(self, definition: str) -> Optional[str]:
        """Extract the parent class name from a class definition string."""
        m = re.search(r'\bextends\s+(\w+)', definition)
        if m:
            return m.group(1)
        # C# / Python style
        m = re.search(r':\s*(\w+)', definition)
        if m and m.group(1) not in ('public', 'private', 'protected', 'internal'):
            return m.group(1)
        return None

    def _extract_implements(self, definition: str) -> List[str]:
        """Extract implemented interface names from a class definition string."""
        m = re.search(r'\bimplements\s+([\w,\s]+?)(?:\s*\{|$)', definition)
        if m:
            return [i.strip() for i in m.group(1).split(',') if i.strip()]
        return []

    def _count_overrides_from_schema(self, cls: Dict[str, Any]) -> int:
        """
        Count methods likely to be overrides using source_parser schema.
        Checks for @Override annotations in method definition strings.
        """
        count = 0
        common_overridable = {'toString', 'equals', 'hashCode', 'compareTo', 'clone',
                              'finalize', 'run', 'call', 'iterator', 'close',
                              'ToString', 'Equals', 'GetHashCode'}  # C# variants
        for m in cls.get('methods', []):
            name = m.get('name', '')
            defn = m.get('definition', '') or ''
            code = m.get('original_string', '') or ''
            if '@Override' in defn or '@Override' in code[:200] or 'override ' in defn.lower():
                count += 1
            elif name in common_overridable:
                count += 1
        return count

    def _estimate_inherited_methods(self, class_code: str, parent_name: Optional[str]) -> int:
        """Estimate the number of overridable methods from the parent class."""
        if not parent_name:
            return 0
        known_parents = {
            'Object': 11, 'AbstractList': 15, 'AbstractMap': 14,
            'AbstractSet': 8, 'Thread': 20, 'Observable': 5,
            'Component': 30, 'JComponent': 40, 'JPanel': 10,
            'JFrame': 15, 'HttpServlet': 8, 'ArrayList': 25,
            'HashMap': 20, 'Vector': 25, 'LinkedList': 25,
            'AbstractCollection': 12, 'InputStream': 6, 'OutputStream': 5,
            'Reader': 6, 'Writer': 5,
        }
        return known_parents.get(parent_name, 8)

    def _extract_coupled_classes(self, class_code: str, own_class_name: str) -> List[str]:
        """
        Extract names of other domain classes referenced in this class.
        Filters out the class's own name and common JDK / framework types.
        """
        clean_code = re.sub(r'/\*.*?\*/', '', class_code, flags=re.S)
        clean_code = re.sub(r'//.*', '', clean_code)
        clean_code = re.sub(r'#.*', '', clean_code)

        type_pattern = r'\b([A-Z][a-zA-Z0-9]+)\b'
        all_types = set(re.findall(type_pattern, clean_code))

        jdk_types = {
            'String', 'Integer', 'Long', 'Double', 'Float', 'Boolean', 'Byte',
            'Short', 'Character', 'Object', 'Class', 'System', 'Math',
            'List', 'ArrayList', 'LinkedList', 'Map', 'HashMap', 'TreeMap',
            'Set', 'HashSet', 'TreeSet', 'Queue', 'Deque', 'Stack', 'Vector',
            'Collection', 'Collections', 'Arrays', 'Iterator', 'Iterable',
            'Optional', 'Stream', 'Collectors',
            'Exception', 'RuntimeException', 'Error', 'Throwable',
            'IOException', 'IllegalArgumentException', 'NullPointerException',
            'Override', 'Deprecated', 'SuppressWarnings', 'FunctionalInterface',
            'Comparable', 'Serializable', 'Cloneable', 'Runnable', 'Callable',
            'Thread', 'StringBuilder', 'StringBuffer', 'Date',
            'Logger', 'Level', 'Console',
        }

        return sorted(
            t for t in all_types
            if t != own_class_name and t not in jdk_types and len(t) > 1
        )


# ------------------------------------------------------------------
# Convenience functions (backwards compatible)
# ------------------------------------------------------------------

def slice_java_file(file_path: str) -> Dict[str, Any]:
    return ProgramSlicerAgent().slice_file(file_path)


def slice_java_code(source_code: str, filename: str = "snippet.java") -> Dict[str, Any]:
    return ProgramSlicerAgent().slice_code(source_code, filename)
