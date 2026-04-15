"""
Debt Detector Module
Contains all specialized agents for technical debt detection at different granularities
"""
import re
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from agent_utils import create_agent
import config

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class DebtType(Enum):
    """Technical debt categories"""
    NO_SMELL = 0
    BLOB = 1
    DATA_CLASS = 2
    FEATURE_ENVY = 3
    LONG_METHOD = 4
    REFUSED_BEQUEST = 5
    SHOTGUN_SURGERY = 6
    INAPPROPRIATE_INTIMACY = 7
    HARDCODED_SECRETS = 8
    SQL_COMMAND_INJECTION = 9


class ClassDebtDetector:
    """
    Specialized agent for detecting class-level code smells.
    Optimized for Blob and Data Class detection.
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        """
        Initialize class-level detector.
        
        Args:
            agent_config: Configuration from config.AGENT_CONFIGS['class_detector']
        """
        self.config = agent_config
        self.model = agent_config.get('model', 'codestral:22b')
        self.base_url = agent_config.get('base_url', 'http://localhost:11434/v1')
        self.api_key = agent_config.get('api_key', 'ollama')
        self.shot_type = agent_config.get('shot', 'few')
        self.temperature = agent_config.get('temperature', 0.1)
        self.timeout = agent_config.get('timeout', 300)
        
        # Build LLM config
        self.llm_config = {
            "config_list": [{
                "model": self.model,
                "base_url": self.base_url,
                "api_key": self.api_key,
            }],
            "temperature": self.temperature,
            "timeout": self.timeout,
            "cache_seed": None,
        }
        
        # Agent will be created lazily
        self._agent = None
    
    def _get_agent(self):
        if self._agent is None:
            
            # Select system prompt based on shot type
            if self.shot_type == 'few':
                sys_prompt = config.SYS_MSG_CLASS_DETECTOR_FEW_SHOT
            else:
                sys_prompt = config.SYS_MSG_CLASS_DETECTOR_ZERO_SHOT
            
            self._agent = create_agent(
                agent_type="assistant",
                name="class_debt_detector",
                llm_config=self.llm_config,
                sys_prompt=sys_prompt,
                description="Detects class-level code smells (Blob, Data Class)"
            )
        return self._agent
    
    def detect(self, class_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect class-level technical debt.
        
        Args:
            class_info: Dictionary with 'code', 'name', 'metrics', etc.
            
        Returns:
            Detection result with label, confidence, and metadata
        """
        
        code = class_info.get('code', '')
        class_name = class_info.get('name', 'Unknown')
        metrics = class_info.get('metrics', {})
        
        # Build detection prompt
        task_prompt = config.TASK_PROMPT_CLASS_DETECTION
        message = f"{task_prompt}```java\n{code}\n```"
        
        # Get agent and perform detection
        agent = self._get_agent()
        response = agent.generate_reply(messages=[{"content": message, "role": "user"}])
        #print(f"Class-level Detector Agent response for class '{class_name}': {response}")
        if response:
            label = self._normalize_label(response)
            #print(f"Normalized label for class '{class_name}': '{label}'")
            # Calculate confidence based on metrics
            confidence = self._calculate_confidence(label, metrics)
            
            return {
                'type': 'class',
                'name': class_name,
                'label': label,
                'debt_type': self._label_to_debt_type(label),
                'confidence': confidence,
                'metrics': metrics,
                'raw_response': response,
                'granularity': 'class'
            }
        else:
            return {
                'type': 'class',
                'name': class_name,
                'label': 'UNKNOWN',
                'debt_type': None,
                'confidence': 0.0,
                'error': 'No response from agent'
            }
    
    def _normalize_label(self, text: str) -> str:
        """Normalize agent response to valid label"""
        # Extract first digit
        match = re.search(r'[0-2]', text)
        if match:
            return match.group(0)
        return 'UNKNOWN'
    
    def _label_to_debt_type(self, label: str) -> Optional[str]:
        """Convert numeric label to debt type name"""
        mapping = {
            '0': 'No Smell',
            '1': 'Blob',
            '2': 'Data Class',
        }
        return mapping.get(label)
    
    def _calculate_confidence(self, label: str, metrics: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on metrics alignment with detected smell.
        """
        if label == '0':
            return 0.9  # High confidence for clean code
        
        elif label == '1':  # Blob
            loc = metrics.get('loc', 0)
            method_count = metrics.get('method_count', 0)
            
            # Stronger evidence = higher confidence
            if loc > 500 or method_count > 20:
                return 0.9
            elif loc > 300 or method_count > 15:
                return 0.75
            else:
                return 0.6
        
        elif label == '2':  # Data Class
            getter_setter_ratio = metrics.get('getter_setter_ratio', 0.0)
            
            if getter_setter_ratio > 0.8:
                return 0.9
            elif getter_setter_ratio > 0.6:
                return 0.75
            else:
                return 0.6
        
        return 0.5  # Default confidence


class MethodDebtDetector:
    """
    Specialized agent for detecting method-level code smells.
    Optimized for Feature Envy and Long Method detection.
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        """
        Initialize method-level detector.
        
        Args:
            agent_config: Configuration from config.AGENT_CONFIGS['method_detector']
        """
        self.config = agent_config
        self.model = agent_config.get('model', 'qwen2.5-coder:7b-instruct')
        self.base_url = agent_config.get('base_url', 'http://localhost:11434/v1')
        self.api_key = agent_config.get('api_key', 'ollama')
        self.shot_type = agent_config.get('shot', 'few')
        self.temperature = agent_config.get('temperature', 0.1)
        self.timeout = agent_config.get('timeout', 300)
        
        # Build LLM config
        self.llm_config = {
            "config_list": [{
                "model": self.model,
                "base_url": self.base_url,
                "api_key": self.api_key,
            }],
            "temperature": self.temperature,
            "timeout": self.timeout,
            "cache_seed": None,
        }
        
        self._agent = None
    
    def _get_agent(self):
        if self._agent is None:
            from agent_utils import create_agent
            import config
            
            # Select system prompt
            if self.shot_type == 'few':
                sys_prompt = config.SYS_MSG_METHOD_DETECTOR_FEW_SHOT
            else:
                sys_prompt = config.SYS_MSG_METHOD_DETECTOR_ZERO_SHOT
            
            self._agent = create_agent(
                agent_type="assistant",
                name="method_debt_detector",
                llm_config=self.llm_config,
                sys_prompt=sys_prompt,
                description="Detects method-level code smells (Feature Envy, Long Method)"
            )
        return self._agent
    
    def detect(self, method_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect method-level technical debt.
        
        Args:
            method_info: Dictionary with 'code', 'name', 'metrics', etc.
            
        Returns:
            Detection result with label, confidence, and metadata
        """
        
        code = method_info.get('code', '')
        method_name = method_info.get('name', 'Unknown')
        metrics = method_info.get('metrics', {})
        
        # Build detection prompt
        task_prompt = config.TASK_PROMPT_METHOD_DETECTION
        message = f"{task_prompt}```java\n{code}\n```"
        
        # Get agent and perform detection
        agent = self._get_agent()
        response = agent.generate_reply(messages=[{"content": message, "role": "user"}])
        #print(f"Method-level Detector Agent response for method '{method_name}': {response}")
        if response:
            label = self._normalize_label(response)
            #print(f"Normalized label for method '{method_name}': '{label}'")
            
            # Calculate confidence
            confidence = self._calculate_confidence(label, metrics)
            
            return {
                'type': 'method',
                'name': method_name,
                'label': label,
                'debt_type': self._label_to_debt_type(label),
                'confidence': confidence,
                'metrics': metrics,
                'raw_response': response,
                'granularity': 'method'
            }
        else:
            return {
                'type': 'method',
                'name': method_name,
                'label': 'UNKNOWN',
                'debt_type': None,
                'confidence': 0.0,
                'error': 'No response from agent'
            }
    
    def _normalize_label(self, text: str) -> str:
        """Normalize agent response to valid label (0, 3, or 4)"""
        text = str(text).strip()
        
        # First try: exact single-digit response
        if text in ('0', '3', '4'):
            return text
        
        # Second try: find a standalone digit using word boundaries.
        for target in ['3', '4']:
            if re.search(r'(?:^|\b|\s)' + target + r'(?:$|\b|\s|[,;.!?)])', text):
                return target
        if re.search(r'(?:^|\b|\s)0(?:$|\b|\s|[,;.!?)])', text):
            return '0'
        
        # Last resort: any digit 3 or 4 found anywhere
        match = re.search(r'[34]', text)
        if match:
            return match.group(0)
        if '0' in text:
            return '0'
        return 'UNKNOWN'
    
    def _label_to_debt_type(self, label: str) -> Optional[str]:
        """Convert numeric label to debt type name"""
        mapping = {
            '0': 'No Smell',
            '3': 'Feature Envy',
            '4': 'Long Method',
        }
        return mapping.get(label)
    
    def _calculate_confidence(self, label: str, metrics: Dict[str, Any]) -> float:
        """Calculate confidence based on metrics alignment"""
        if label == '0':
            return 0.9
        
        elif label == '3':  # Feature Envy
            external_calls = metrics.get('external_calls', 0)
            
            if external_calls >= 7:
                return 0.9
            elif external_calls >= 5:
                return 0.75
            else:
                return 0.6
        
        elif label == '4':  # Long Method
            loc = metrics.get('loc', 0)
            complexity = metrics.get('cyclomatic_complexity', 0)
            
            if loc >= 25 or complexity >= 15:
                return 0.9
            elif loc >= 15 or complexity >= 10:
                return 0.75
            else:
                return 0.6
        
        return 0.5


class LocalizationAgent:
    """
    Localizes detected technical debt within the source file.
    Provides precise line numbers for the problematic code.
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        """
        Initialize localization agent.
        
        Args:
            agent_config: Configuration from config.AGENT_CONFIGS['localization']
        """
        self.config = agent_config
        self.use_ast = agent_config.get('use_ast', True)
    
    def localize(self, debt_result: Dict[str, Any], 
                 source_file_content: str) -> Dict[str, Any]:
        """
        Find exact line numbers for detected debt.
        
        Args:
            debt_result: Detection result from ClassDebtDetector or MethodDebtDetector
            source_file_content: Full source file content
            
        Returns:
            Enhanced debt_result with 'location' field containing line numbers
        """
        code_snippet = debt_result.get('code', '')
        name = debt_result.get('name', '')
        
        if not code_snippet or not source_file_content:
            debt_result['location'] = {'error': 'Missing code or source file'}
            return debt_result
        
        # Find the code snippet in the source file
        lines = source_file_content.split('\n')
        
        # Try to find exact match
        snippet_lines = code_snippet.strip().split('\n')
        first_line = snippet_lines[0].strip()
        
        start_line = None
        for i, line in enumerate(lines):
            if first_line in line.strip():
                # Found potential match
                start_line = i + 1  # 1-indexed
                break
        
        if start_line:
            end_line = start_line + len(snippet_lines) - 1
            debt_result['location'] = {
                'start_line': start_line,
                'end_line': end_line,
                'file_path': debt_result.get('file_path', 'unknown')
            }
        else:
            # Fallback: search for class/method declaration
            if debt_result.get('type') == 'class':
                pattern = rf'class\s+{re.escape(name)}'
            else:
                pattern = rf'\s+{re.escape(name)}\s*\('
            
            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    start_line = i + 1
                    # Estimate end line (rough)
                    end_line = start_line + len(snippet_lines)
                    debt_result['location'] = {
                        'start_line': start_line,
                        'end_line': end_line,
                        'file_path': debt_result.get('file_path', 'unknown'),
                        'approximate': True
                    }
                    break
        
        if 'location' not in debt_result:
            debt_result['location'] = {
                'error': 'Could not localize code',
                'file_path': debt_result.get('file_path', 'unknown')
            }
        
        return debt_result


class ExplanationAgent:
    """
    Generates human-readable explanations for detected technical debt.
    Helps developers understand why the code is problematic.
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        """
        Initialize explanation agent.
        
        Args:
            agent_config: Configuration from config.AGENT_CONFIGS['explanation']
        """
        self.config = agent_config
        self.model = agent_config.get('model', 'codestral:22b')
        self.base_url = agent_config.get('base_url', 'http://localhost:11434/v1')
        self.api_key = agent_config.get('api_key', 'ollama')
        self.temperature = agent_config.get('temperature', 0.1)
        self.max_tokens = agent_config.get('max_tokens', 1000)
        
        self.llm_config = {
            "config_list": [{
                "model": self.model,
                "base_url": self.base_url,
                "api_key": self.api_key,
            }],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "cache_seed": None,
        }
        
        self._agent = None
    
    def _get_agent(self):
        if self._agent is None:     
            self._agent = create_agent(
                agent_type="assistant",
                name="explanation_agent",
                llm_config=self.llm_config,
                sys_prompt=config.SYS_MSG_EXPLANATION_AGENT,
                description="Explains detected technical debt"
            )
        return self._agent
    
    def explain(self, debt_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanation for detected debt.
        
        Args:
            debt_result: Detection result with label and debt_type
            
        Returns:
            Enhanced debt_result with 'explanation' field
        """
        debt_type = debt_result.get('debt_type')
        code = debt_result.get('code', '')
        name = debt_result.get('name', 'Unknown')
        metrics = debt_result.get('metrics', {})
        
        if not debt_type or debt_type == 'No Smell':
            debt_result['explanation'] = None
            return debt_result
        
        # Build explanation prompt
        prompt = f"""
        Explain why the following code is classified as '{debt_type}':

        **Code Element:** {name}
        **Metrics:** {metrics}

        **Code:**
        ```java
        {code}
        ```

        Provide a concise explanation (3-5 sentences) covering:
        1. WHY it's considered technical debt (symptoms)
        2. CONSEQUENCES of leaving it unaddressed
        3. IMPACT on code quality (readability, maintainability, testability)
        """
        
        agent = self._get_agent()
        response = agent.generate_reply(messages=[{"content": prompt, "role": "user"}])
        #print(f"Explanation Agent response for '{name}': {response}")
        if response:
            #explanation = response["content"].strip()
            #print(f"Generated explanation for '{name}': {response}")
            debt_result['explanation'] = response
        else:
            debt_result['explanation'] = "Could not generate explanation"
        
        return debt_result


class FixSuggestionAgent:
    """
    Suggests practical refactoring steps to address detected technical debt.
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        """
        Initialize fix suggestion agent.
        
        Args:
            agent_config: Configuration from config.AGENT_CONFIGS['fix_suggestion']
        """
        self.config = agent_config
        self.model = agent_config.get('model', 'codestral:22b')
        self.base_url = agent_config.get('base_url', 'http://localhost:11434/v1')
        self.api_key = agent_config.get('api_key', 'ollama')
        self.temperature = agent_config.get('temperature', 0.1)
        self.max_tokens = agent_config.get('max_tokens', 2000)
        self.validate_fixes = agent_config.get('validate_fixes', False)
        
        self.llm_config = {
            "config_list": [{
                "model": self.model,
                "base_url": self.base_url,
                "api_key": self.api_key,
            }],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "cache_seed": None,
        }
        
        self._agent = None
    
    def _get_agent(self):
        if self._agent is None:
            self._agent = create_agent(
                agent_type="assistant",
                name="fix_suggestion_agent",
                llm_config=self.llm_config,
                sys_prompt=config.SYS_MSG_FIX_SUGGESTION_AGENT,
                description="Suggests refactoring for technical debt"
            )
        return self._agent
    
    def suggest_fix(self, debt_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate refactoring suggestions.
        
        Args:
            debt_result: Detection result with debt_type and code
            
        Returns:
            Enhanced debt_result with 'fix_suggestion' field
        """
        debt_type = debt_result.get('debt_type')
        code = debt_result.get('code', '')
        name = debt_result.get('name', 'Unknown')
        
        if not debt_type or debt_type == 'No Smell':
            debt_result['fix_suggestion'] = None
            return debt_result
        
        # Build fix prompt
        prompt = f"""
        Suggest refactoring for this '{debt_type}' code smell:

        **Code Element:** {name}

        **Code:**
        ```java
        {code}
        ```

        Provide:
        1. The refactoring pattern to apply (e.g., Extract Method, Move Method, etc.)
        2. Concrete refactoring steps
        3. A brief code example showing the improved structure (if appropriate)

        Keep suggestions practical and focused on the most impactful improvements.
        """
        
        agent = self._get_agent()
        response = agent.generate_reply(messages=[{"content": prompt, "role": "user"}])
        #print(f"Fix Suggestion Agent response for '{name}': {response}")
        if response:
            #suggestion = response["content"].strip()
            #print(f"Generated fix suggestion for '{name}': {response}")
            debt_result['fix_suggestion'] = response
        else:
            debt_result['fix_suggestion'] = "Could not generate fix suggestion"
        
        return debt_result


class RelationshipDebtDetector:
    """
    Specialized agent for detecting relationship-level code smells.
    Optimized for Refused Bequest, Shotgun Surgery, and Inappropriate Intimacy detection.
    These smells require semantic understanding of class relationships — inheritance hierarchies,
    cross-class coupling patterns, and bidirectional dependencies — making them well-suited
    for LLM-based detection rather than purely metric-driven approaches.
    """

    def __init__(self, agent_config: Dict[str, Any]):
        self.config = agent_config
        self.model = agent_config.get('model', config.LLM_MODEL)
        self.base_url = agent_config.get('base_url', 'http://localhost:11434/v1')
        self.api_key = agent_config.get('api_key', 'ollama')
        self.shot_type = agent_config.get('shot', 'few')
        self.temperature = agent_config.get('temperature', 0.1)
        self.timeout = agent_config.get('timeout', 300)

        self.llm_config = {
            "config_list": [{
                "model": self.model,
                "base_url": self.base_url,
                "api_key": self.api_key,
            }],
            "temperature": self.temperature,
            "timeout": self.timeout,
            "cache_seed": None,
        }
        self._agent = None

    def _get_agent(self):
        if self._agent is None:
            if self.shot_type == 'few':
                sys_prompt = config.SYS_MSG_RELATIONSHIP_DETECTOR_FEW_SHOT
            else:
                sys_prompt = config.SYS_MSG_RELATIONSHIP_DETECTOR_ZERO_SHOT

            self._agent = create_agent(
                agent_type="assistant",
                name="relationship_debt_detector",
                llm_config=self.llm_config,
                sys_prompt=sys_prompt,
                description="Detects relationship-level code smells (Refused Bequest, Shotgun Surgery, Inappropriate Intimacy)"
            )
        return self._agent

    def detect(self, class_info: Dict[str, Any]) -> Dict[str, Any]:
        code = class_info.get('code', '')
        class_name = class_info.get('name', 'Unknown')
        metrics = class_info.get('metrics', {})
        related_code = class_info.get('related_code', '')

        task_prompt = config.TASK_PROMPT_RELATIONSHIP_DETECTION

        # Include relationship metrics as context for the LLM
        context_parts = []
        if metrics.get('extends'):
            context_parts.append(f"Extends: {metrics['extends']}")
        if metrics.get('implements'):
            context_parts.append(f"Implements: {', '.join(metrics['implements'])}")
        if metrics.get('override_ratio') is not None:
            context_parts.append(f"Override ratio: {metrics['override_ratio']:.2f}")
        if metrics.get('coupled_classes'):
            context_parts.append(f"Coupled to classes: {', '.join(metrics['coupled_classes'])}")
        if metrics.get('coupled_class_count', 0) > 0:
            context_parts.append(f"Number of coupled domain classes: {metrics['coupled_class_count']}")
        if metrics.get('bidirectional_dependencies'):
            context_parts.append(f"Bidirectional dependencies with: {', '.join(metrics['bidirectional_dependencies'])}")

        context_str = "\n".join(context_parts)

        message = f"{task_prompt}"
        if context_str:
            message += f"Relationship context:\n{context_str}\n\n"
        message += f"```java\n{code}\n```"
        if related_code:
            message += f"\n\nRelated class code for context:\n```java\n{related_code}\n```"

        agent = self._get_agent()
        response = agent.generate_reply(messages=[{"content": message, "role": "user"}])

        if response:
            label = self._normalize_label(response)
            confidence = self._calculate_confidence(label, metrics)

            return {
                'type': 'class',
                'name': class_name,
                'label': label,
                'debt_type': self._label_to_debt_type(label),
                'confidence': confidence,
                'metrics': metrics,
                'raw_response': response,
                'granularity': 'class'
            }
        else:
            return {
                'type': 'class',
                'name': class_name,
                'label': 'UNKNOWN',
                'debt_type': None,
                'confidence': 0.0,
                'error': 'No response from agent'
            }

    def _normalize_label(self, text: str) -> str:
        text = str(text).strip()
        if text in ('0', '5', '6', '7'):
            return text
        for target in ['5', '6', '7']:
            if re.search(r'(?:^|\b|\s)' + target + r'(?:$|\b|\s|[,;.!?)])', text):
                return target
        if re.search(r'(?:^|\b|\s)0(?:$|\b|\s|[,;.!?)])', text):
            return '0'
        match = re.search(r'[567]', text)
        if match:
            return match.group(0)
        if '0' in text:
            return '0'
        return 'UNKNOWN'

    def _label_to_debt_type(self, label: str) -> Optional[str]:
        mapping = {
            '0': 'No Smell',
            '5': 'Refused Bequest',
            '6': 'Shotgun Surgery',
            '7': 'Inappropriate Intimacy',
        }
        return mapping.get(label)

    def _calculate_confidence(self, label: str, metrics: Dict[str, Any]) -> float:
        if label == '0':
            return 0.9
        elif label == '5':  # Refused Bequest
            override_ratio = metrics.get('override_ratio', None)
            has_extends = bool(metrics.get('extends'))
            if not has_extends:
                return 0.4
            if override_ratio is not None:
                if override_ratio < 0.2:
                    return 0.85
                elif override_ratio < 0.3:
                    return 0.7
                else:
                    return 0.55
            return 0.6
        elif label == '6':  # Shotgun Surgery
            coupled_count = metrics.get('coupled_class_count', 0)
            fan_out = metrics.get('fan_out', 0)
            if coupled_count >= 7 or fan_out >= 12:
                return 0.85
            elif coupled_count >= 5 or fan_out >= 8:
                return 0.7
            else:
                return 0.55
        elif label == '7':  # Inappropriate Intimacy
            bidirectional_count = len(metrics.get('bidirectional_dependencies', []))
            if bidirectional_count >= 5:
                return 0.85
            elif bidirectional_count >= 3:
                return 0.7
            else:
                return 0.55
        return 0.5


class SecurityDebtDetector:
    """
    Specialized agent for detecting security-related technical debt.
    Detects Hardcoded Secrets and SQL/Command Injection vulnerabilities.
    Combines LLM semantic analysis with metric-based heuristics for confidence scoring.
    """

    def __init__(self, agent_config: Dict[str, Any]):
        self.config = agent_config
        self.model = agent_config.get('model', config.LLM_MODEL)
        self.base_url = agent_config.get('base_url', 'http://localhost:11434/v1')
        self.api_key = agent_config.get('api_key', 'ollama')
        self.shot_type = agent_config.get('shot', 'few')
        self.temperature = agent_config.get('temperature', 0.1)
        self.timeout = agent_config.get('timeout', 300)

        self.llm_config = {
            "config_list": [{
                "model": self.model,
                "base_url": self.base_url,
                "api_key": self.api_key,
            }],
            "temperature": self.temperature,
            "timeout": self.timeout,
            "cache_seed": None,
        }
        self._agent = None

    def _get_agent(self):
        if self._agent is None:
            if self.shot_type == 'few':
                sys_prompt = config.SYS_MSG_SECURITY_DETECTOR_FEW_SHOT
            else:
                sys_prompt = config.SYS_MSG_SECURITY_DETECTOR_ZERO_SHOT

            self._agent = create_agent(
                agent_type="assistant",
                name="security_debt_detector",
                llm_config=self.llm_config,
                sys_prompt=sys_prompt,
                description="Detects security-related technical debt (Hardcoded Secrets, SQL/Command Injection)"
            )
        return self._agent

    def detect(self, code_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect security-related technical debt.

        Args:
            code_info: Dictionary with 'code', 'name', 'metrics', and optionally
                       'security_metrics' containing heuristic signals.

        Returns:
            Detection result with label, confidence, and metadata
        """
        code = code_info.get('code', '')
        name = code_info.get('name', 'Unknown')
        metrics = code_info.get('metrics', {})
        security_metrics = code_info.get('security_metrics', {})

        task_prompt = config.TASK_PROMPT_SECURITY_DETECTION

        # Include security metric context
        context_parts = []
        if security_metrics.get('hardcoded_string_count', 0) > 0:
            context_parts.append(f"Suspicious hardcoded strings: {security_metrics['hardcoded_string_count']}")
        if security_metrics.get('secret_pattern_matches'):
            context_parts.append(f"Secret-like patterns: {', '.join(security_metrics['secret_pattern_matches'])}")
        if security_metrics.get('sql_concat_count', 0) > 0:
            context_parts.append(f"SQL string concatenations: {security_metrics['sql_concat_count']}")
        if security_metrics.get('exec_calls'):
            context_parts.append(f"Exec/command calls: {', '.join(security_metrics['exec_calls'])}")

        context_str = "\n".join(context_parts)

        message = f"{task_prompt}"
        if context_str:
            message += f"Security context:\n{context_str}\n\n"
        message += f"```\n{code}\n```"

        agent = self._get_agent()
        response = agent.generate_reply(messages=[{"content": message, "role": "user"}])

        if response:
            label = self._normalize_label(response)
            confidence = self._calculate_confidence(label, security_metrics)

            granularity = 'class' if label == '8' else ('method' if label == '9' else code_info.get('granularity', 'class'))

            return {
                'type': code_info.get('type', 'class'),
                'name': name,
                'label': label,
                'debt_type': self._label_to_debt_type(label),
                'confidence': confidence,
                'metrics': metrics,
                'security_metrics': security_metrics,
                'raw_response': response,
                'granularity': granularity
            }
        else:
            return {
                'type': code_info.get('type', 'class'),
                'name': name,
                'label': 'UNKNOWN',
                'debt_type': None,
                'confidence': 0.0,
                'error': 'No response from agent'
            }

    def _normalize_label(self, text: str) -> str:
        text = str(text).strip()
        if text in ('0', '8', '9'):
            return text
        for target in ['8', '9']:
            if re.search(r'(?:^|\b|\s)' + target + r'(?:$|\b|\s|[,;.!?)])', text):
                return target
        if re.search(r'(?:^|\b|\s)0(?:$|\b|\s|[,;.!?)])', text):
            return '0'
        match = re.search(r'[89]', text)
        if match:
            return match.group(0)
        if '0' in text:
            return '0'
        return 'UNKNOWN'

    def _label_to_debt_type(self, label: str) -> Optional[str]:
        mapping = {
            '0': 'No Smell',
            '8': 'Hardcoded Secrets',
            '9': 'SQL/Command Injection',
        }
        return mapping.get(label)

    def _calculate_confidence(self, label: str, security_metrics: Dict[str, Any]) -> float:
        if label == '0':
            return 0.9
        elif label == '8':  # Hardcoded Secrets
            pattern_count = len(security_metrics.get('secret_pattern_matches', []))
            string_count = security_metrics.get('hardcoded_string_count', 0)
            if pattern_count >= 3 or string_count >= 5:
                return 0.9
            elif pattern_count >= 1 or string_count >= 2:
                return 0.75
            else:
                return 0.6
        elif label == '9':  # SQL/Command Injection
            sql_concat = security_metrics.get('sql_concat_count', 0)
            exec_count = len(security_metrics.get('exec_calls', []))
            if sql_concat >= 3 or exec_count >= 2:
                return 0.9
            elif sql_concat >= 1 or exec_count >= 1:
                return 0.75
            else:
                return 0.6
        return 0.5