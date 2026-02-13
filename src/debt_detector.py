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
        self.base_url = agent_config.get('base_url', 'http://localhost:11434')
        self.api_key = agent_config.get('api_key', 'ollama')
        self.shot_type = agent_config.get('shot', 'few')
        self.temperature = agent_config.get('temperature', 0.1)
        #self.timeout = agent_config.get('timeout', 300)
        
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
        import config
        
        code = class_info.get('code', '')
        class_name = class_info.get('name', 'Unknown')
        metrics = class_info.get('metrics', {})
        
        # Build detection prompt
        task_prompt = config.TASK_PROMPT_CLASS_DETECTION
        message = f"{task_prompt}```java\n{code}\n```"
        
        # Get agent and perform detection
        agent = self._get_agent()
        response = agent.generate_reply(messages=[{"content": message, "role": "user"}])
        
        if response and "content" in response:
            raw_label = response["content"].strip()
            label = self._normalize_label(raw_label)
            
            # Calculate confidence based on metrics
            confidence = self._calculate_confidence(label, metrics)
            
            return {
                'type': 'class',
                'name': class_name,
                'label': label,
                'debt_type': self._label_to_debt_type(label),
                'confidence': confidence,
                'metrics': metrics,
                'raw_response': raw_label,
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
        self.model = agent_config.get('model', 'qwen2.5-coder:7b')
        self.base_url = agent_config.get('base_url', 'http://localhost:11434')
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
        
        if response and "content" in response:
            raw_label = response["content"].strip()
            label = self._normalize_label(raw_label)
            
            # Calculate confidence
            confidence = self._calculate_confidence(label, metrics)
            
            return {
                'type': 'method',
                'name': method_name,
                'label': label,
                'debt_type': self._label_to_debt_type(label),
                'confidence': confidence,
                'metrics': metrics,
                'raw_response': raw_label,
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
        """Normalize agent response to valid label"""
        # Extract digit (0, 3, or 4)
        if '3' in text:
            return '3'
        elif '4' in text:
            return '4'
        elif '0' in text:
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
        self.base_url = agent_config.get('base_url', 'http://localhost:11434')
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
        
        if response and "content" in response:
            explanation = response["content"].strip()
            debt_result['explanation'] = explanation
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
        self.base_url = agent_config.get('base_url', 'http://localhost:11434')
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
        
        if response and "content" in response:
            suggestion = response["content"].strip()
            debt_result['fix_suggestion'] = suggestion
        else:
            debt_result['fix_suggestion'] = "Could not generate fix suggestion"
        
        return debt_result