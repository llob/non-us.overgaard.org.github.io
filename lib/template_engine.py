"""
Template rendering engine for the static blog generator.

This module provides functionality for rendering HTML templates with dynamic
content. It uses Python's built-in string.Template for a simple, dependency-free
approach with custom template tags for better readability.
"""

import os
import re
from string import Template
from typing import Any, Dict, List, Optional, Union


class TemplateEngine:
    """
    Renders HTML templates with dynamic content.
    
    This class loads template files and renders them with provided context data.
    It supports template inheritance and custom template tags for a more
    readable syntax than standard string.Template.
    
    Attributes:
        template_dir: Directory where template files are stored.
        template_cache: Cache of loaded templates.
    """
    
    # Custom template tag pattern - allows for more readable syntax
    # Use {% ... %} for statements, {{ ... }} for variables
    TEMPLATE_TAG_PATTERN = re.compile(
        r'\{\s*%([^%]+)%\s*\}'  # {% ... %} - statements/loops
        r'|\{\s*\{([^}]+)\}\s*\}'  # {{ ... }} - variables
        r'|\$\{([^}]+)\}'  # ${...} - standard string.Template syntax
    )
    
    def __init__(self, template_dir: str = "templates") -> None:
        """
        Initialize the template engine.
        
        Args:
            template_dir: Path to the directory containing template files.
        """
        self.template_dir = template_dir
        self.template_cache: Dict[str, str] = {}
    
    def _load_template(self, template_path: str) -> str:
        """
        Load a template file from disk.
        
        Args:
            template_path: Path to the template file (relative to template_dir).
            
        Returns:
            The template content as a string.
            
        Raises:
            FileNotFoundError: If the template file doesn't exist.
            IOError: If the template file cannot be read.
        """
        if template_path in self.template_cache:
            return self.template_cache[template_path]
        
        full_path = os.path.join(self.template_dir, template_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Template file not found: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Cache the template
        self.template_cache[template_path] = template_content
        return template_content
    
    def _convert_to_string_template(self, template_content: str) -> str:
        """
        Convert custom template syntax to string.Template syntax.
        
        Converts {% ... %} and {{ ... }} syntax to ${...} syntax that
        string.Template can understand. Also handles dot notation by 
        converting {{ obj.attr }} to ${obj_attr}.
        
        Args:
            template_content: The template content with custom syntax.
            
        Returns:
            Template content converted to string.Template syntax.
        """
        # Remove template comments: {# ... #}
        template_content = re.sub(
            r'\{\s*#([^#}]+)#\s*\}',
            '',
            template_content
        )
        
        # Convert {{ variable }} to ${variable} and handle dot notation
        # Convert {{ obj.attr }} to ${obj_attr}
        template_content = re.sub(
            r'\{\s*\{([^}]+)\}\s*\}',
            lambda m: self._convert_variable_ref(m.group(1).strip()),
            template_content
        )
        
        return template_content
    
    def _convert_variable_ref(self, var_ref: str) -> str:
        """
        Convert a variable reference to string.Template syntax.
        
        Handles dot notation by converting obj.attr to obj_attr.
        
        Args:
            var_ref: The variable reference (e.g., 'post.title', 'site_title')
            
        Returns:
            The converted reference (e.g., '${post_title}')
        """
        # Replace dots with underscores for string.Template compatibility
        return '${' + var_ref.replace('.', '_') + '}'
    
    def _handle_template_blocks(self, template_content: str, context: Dict[str, Any], flat_context: Dict[str, Any]) -> str:
        """
        Handle template blocks like loops and conditionals.
        
        This provides basic support for control structures in templates.
        
        Args:
            template_content: Template content with block syntax.
            context: The context data for rendering.
            flat_context: The flattened context for variable substitution.
            
        Returns:
            Template content with blocks processed.
        """
        # Handle {% for ... in ... %} ... {% endfor %} loops
        template_content = self._process_for_loops(template_content, context, flat_context)
        
        # Handle {% if ... %} ... {% endif %} conditionals
        template_content = self._process_if_blocks(template_content, flat_context)
        
        # Handle {% include ... %} for template includes
        template_content = self._process_includes(template_content, context)
        
        return template_content
    
    def _process_for_loops(self, template_content: str, context: Dict[str, Any], flat_context: Dict[str, Any]) -> str:
        """
        Process for loop blocks in template content.
        
        Args:
            template_content: Template content with for loop syntax.
            context: The context data for rendering.
            flat_context: The flattened context for variable substitution.
            
        Returns:
            Template content with for loops processed.
        """
        # Pattern for for loops: {% for item in items %} ... {% endfor %}
        pattern = re.compile(
            r'\{\s*%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\s*\}'
            r'(.*?)'
            r'\{\s*%\s*endfor\s*%\s*\}',
            re.DOTALL
        )
        
        def replace_for_loop(match: re.Match) -> str:
            var_name = match.group(1).strip()
            list_name = match.group(2).strip()
            loop_content = match.group(3).strip()
            
            # Get the list from context
            items = context.get(list_name, [])
            
            if not isinstance(items, (list, tuple)):
                return ""
            
            # For dictionary items (like our flattened post objects), we can merge them directly
            result = []
            for item in items:
                # Create a new context for this iteration
                if isinstance(item, dict):
                    # For dictionaries, merge all key-value pairs directly into the context
                    # This allows templates to use the direct field names (title, description, etc.)
                    loop_context = {**flat_context, **item}
                else:
                    # For other types, just add the variable
                    loop_context = {**flat_context, var_name: item}
                
                # Also add the item itself under the original variable name
                loop_context[var_name] = item
                
                # Process the loop content recursively with the new context
                # This ensures that any blocks (like if statements) inside the loop 
                # have access to the loop variables
                processed_content = self._process_template_content(
                    loop_content, 
                    loop_context, 
                    in_loop=True  # Prevent infinite recursion
                )
                result.append(processed_content)
            
            return '\n'.join(result)
        
        return pattern.sub(replace_for_loop, template_content)
    
    def _process_if_blocks(self, template_content: str, flat_context: Dict[str, Any]) -> str:
        """
        Process if/else/endif blocks in template content.
        
        Args:
            template_content: Template content with if block syntax.
            flat_context: The flattened context for variable evaluation.
            
        Returns:
            Template content with if blocks processed.
        """
        # Pattern for if blocks: {% if condition %} ... {% else %} ... {% endif %}
        # Use a counter-based approach to handle nested if blocks
        
        # First, try to find and process if blocks in multiple passes to handle nesting
        max_passes = 10  # Prevent infinite loops
        for _ in range(max_passes):
            pattern = re.compile(
                r'\{\s*%\s*if\s+([^%]+)%\s*\}'
                r'(.*?)'
                r'(?:\{\s*%\s*else\s*%\s*\}(.*?))?'
                r'\{\s*%\s*endif\s*%\s*\}',
                re.DOTALL
            )
            
            def replace_if_block(match: re.Match) -> str:
                condition = match.group(1).strip()
                if_content = match.group(2)
                # Group 3 is the else content (when present)
                else_content = match.group(3) if match.group(3) else ""
                
                # Evaluate the condition using the flattened context
                condition_met = self._evaluate_condition_with_flat(condition, flat_context)
                
                # Process the content with the flattened context
                if condition_met:
                    return self._process_template_content(if_content, flat_context, in_loop=True)
                else:
                    return self._process_template_content(else_content, flat_context, in_loop=True)
            
            new_content = pattern.sub(replace_if_block, template_content)
            
            # If no changes were made, we're done
            if new_content == template_content:
                break
                
            template_content = new_content
        
        return template_content
    
    def _evaluate_condition_with_flat(self, condition: str, flat_context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition expression using a flattened context.
        
        Args:
            condition: The condition expression.
            flat_context: The flattened context for evaluation.
            
        Returns:
            True if the condition is met, False otherwise.
        """
        # Simple condition handling
        condition = condition.strip()
        
        # Handle 'not' prefix
        if condition.startswith('not '):
            return not self._evaluate_condition_with_flat(condition[4:], flat_context)
        
        # Handle 'and' operator
        if ' and ' in condition:
            parts = [part.strip() for part in condition.split(' and ')]
            return all(self._evaluate_condition_with_flat(part, flat_context) for part in parts)
        
        # Handle 'or' operator
        if ' or ' in condition:
            parts = [part.strip() for part in condition.split(' or ')]
            return any(self._evaluate_condition_with_flat(part, flat_context) for part in parts)
        
        # Handle dot notation by converting obj.attr to obj_attr
        condition_flat = condition.replace('.', '_')
        
        # Handle comparison operators first (before variable existence check)
        # Handle equality check: variable == value
        if '==' in condition:
            left, right = [part.strip() for part in condition.split('==', 1)]
            left_flat = left.replace('.', '_')
            right_value = right.strip('"').strip("'")
            left_value = flat_context.get(left_flat, flat_context.get(left, None))
            return str(left_value) == right_value
        
        # Handle inequality check: variable != value
        if '!=' in condition:
            left, right = [part.strip() for part in condition.split('!=', 1)]
            left_flat = left.replace('.', '_')
            right_value = right.strip('"').strip("'")
            left_value = flat_context.get(left_flat, flat_context.get(left, None))
            return str(left_value) != right_value
        
        # Handle greater than check: variable > value
        if '>' in condition and '>=' not in condition:
            left, right = [part.strip() for part in condition.split('>', 1)]
            left_flat = left.replace('.', '_')
            right_value = right.strip('"').strip("'")
            left_value = flat_context.get(left_flat, flat_context.get(left, None))
            try:
                # Try to convert both to numbers for comparison
                left_num = float(left_value) if left_value is not None else 0
                right_num = float(right_value)
                return left_num > right_num
            except (ValueError, TypeError):
                # If not numbers, compare as strings
                return str(left_value) > right_value
        
        # Handle greater than or equal check: variable >= value
        if '>=' in condition:
            left, right = [part.strip() for part in condition.split('>=', 1)]
            left_flat = left.replace('.', '_')
            right_value = right.strip('"').strip("'")
            left_value = flat_context.get(left_flat, flat_context.get(left, None))
            try:
                left_num = float(left_value) if left_value is not None else 0
                right_num = float(right_value)
                return left_num >= right_num
            except (ValueError, TypeError):
                return str(left_value) >= right_value
        
        # Handle list length check: list_name|length > 0
        if '|length' in condition:
            var_name = condition.split('|length')[0].strip()
            var_name_flat = var_name.replace('.', '_')
            value = flat_context.get(var_name_flat, flat_context.get(var_name, None))
            if value is not None and isinstance(value, (list, tuple)):
                return len(value) > 0
            return False
        
        # Handle variable existence check
        if condition_flat in flat_context:
            value = flat_context[condition_flat]
            return bool(value)
        
        # Also try the original condition in case it's a simple variable
        if condition in flat_context:
            value = flat_context[condition]
            return bool(value)
        
        return False

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition expression in template context.
        
        Args:
            condition: The condition expression.
            context: The context data for evaluation.
            
        Returns:
            True if the condition is met, False otherwise.
        """
        # Simple condition handling
        condition = condition.strip()
        
        # Handle 'not' prefix
        if condition.startswith('not '):
            return not self._evaluate_condition(condition[4:], context)
        
        # Handle dot notation by converting obj.attr to obj_attr
        condition_flat = condition.replace('.', '_')
        
        # Handle variable existence check
        if condition_flat in context:
            value = context[condition_flat]
            return bool(value)
        
        # Also try the original condition in case it's a simple variable
        if condition in context:
            value = context[condition]
            return bool(value)
        
        # Handle equality check: variable == value
        if '==' in condition:
            left, right = [part.strip() for part in condition.split('==', 1)]
            left_value = context.get(left, None)
            right_value = right.strip('"').strip("'")
            return str(left_value) == right_value
        
        # Handle inequality check: variable != value
        if '!=' in condition:
            left, right = [part.strip() for part in condition.split('!=', 1)]
            left_value = context.get(left, None)
            right_value = right.strip('"').strip("'")
            return str(left_value) != right_value
        
        # Handle greater than check: variable > value
        if '>' in condition and '>=' not in condition:
            left, right = [part.strip() for part in condition.split('>', 1)]
            left_value = context.get(left, None)
            right_value = right.strip('"').strip("'")
            try:
                # Try to convert both to numbers for comparison
                left_num = float(left_value) if left_value is not None else 0
                right_num = float(right_value)
                return left_num > right_num
            except (ValueError, TypeError):
                # If not numbers, compare as strings
                return str(left_value) > right_value
        
        # Handle greater than or equal check: variable >= value
        if '>=' in condition:
            left, right = [part.strip() for part in condition.split('>=', 1)]
            left_value = context.get(left, None)
            right_value = right.strip('"').strip("'")
            try:
                left_num = float(left_value) if left_value is not None else 0
                right_num = float(right_value)
                return left_num >= right_num
            except (ValueError, TypeError):
                return str(left_value) >= right_value
        
        # Handle list length check: list_name|length > 0
        if '|length' in condition:
            var_name = condition.split('|length')[0].strip()
            if var_name in context:
                value = context[var_name]
                if isinstance(value, (list, tuple)):
                    return len(value) > 0
            return False
        
        return False
    
    def _process_includes(self, template_content: str, context: Dict[str, Any]) -> str:
        """
        Process template include directives.
        
        Args:
            template_content: Template content with include syntax.
            context: The context data for rendering.
            
        Returns:
            Template content with includes processed.
        """
        # Pattern for includes: {% include template_name %}
        pattern = re.compile(r'\{\s*%\s*include\s+([^%]+)%\s*\}')
        
        def replace_include(match: re.Match) -> str:
            template_name = match.group(1).strip().strip('"').strip("'")
            try:
                include_content = self._load_template(template_name)
                return self._process_template_content(include_content, context)
            except FileNotFoundError:
                return f"<!-- Include error: {template_name} not found -->"
        
        return pattern.sub(replace_include, template_content)
    
    def _process_template_content(self, template_content: str, context: Dict[str, Any], in_loop: bool = False) -> str:
        """
        Process template content with all template features.
        
        Args:
            template_content: The template content to process.
            context: The context data for rendering.
            in_loop: Whether this is being called from within a loop (to prevent infinite recursion)
            
        Returns:
            The fully processed template content.
        """
        # Flatten the context first to handle dot notation throughout
        flat_context = self._flatten_context(context)
        
        # First handle blocks (loops, conditionals, includes) with the flattened context
        # If we're inside a loop, we still need to process if blocks and includes, but not for loops
        if not in_loop:
            template_content = self._handle_template_blocks(template_content, context, flat_context)
        else:
            # Inside a loop, still process if blocks and includes but not for loops
            template_content = self._process_if_blocks(template_content, flat_context)
            template_content = self._process_includes(template_content, context)
        
        # Convert to string.Template syntax and render
        template_content = self._convert_to_string_template(template_content)
        
        try:
            template = Template(template_content)
            return template.substitute(flat_context)
        except (ValueError, KeyError) as e:
            # Handle missing variables gracefully
            return f"<!-- Template error: {e} -->"
    
    def render(self, template_path: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Render a template with the given context.
        
        Args:
            template_path: Path to the template file (relative to template_dir).
            context: Dictionary of variables to use in the template.
            
        Returns:
            The rendered HTML string.
            
        Raises:
            FileNotFoundError: If the template file doesn't exist.
            IOError: If the template file cannot be read.
        """
        if context is None:
            context = {}
        
        # Load the template
        template_content = self._load_template(template_path)
        
        # Process and render the template
        return self._process_template_content(template_content, context)
    
    def render_string(self, template_content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Render a template string with the given context.
        
        This method is useful for rendering template strings directly without
        loading from a file.
        
        Args:
            template_content: The template content as a string.
            context: Dictionary of variables to use in the template.
            
        Returns:
            The rendered HTML string.
        """
        if context is None:
            context = {}
        
        return self._process_template_content(template_content, context)
    
    def _flatten_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten a nested context dictionary to support dot notation in templates.
        
        Converts nested dictionaries and objects with attributes like 
        {'post': Post(title='Hello', slug='hello-world')}
        to flat dictionaries like {'post_title': 'Hello', 'post_slug': 'hello-world'}.
        
        Also keeps the original keys for backward compatibility.
        
        Args:
            context: The nested context dictionary.
            
        Returns:
            A flattened dictionary with underscore-separated keys.
        """
        flat = {}
        
        for key, value in context.items():
            if isinstance(value, dict):
                # Keep the original key with the dictionary value
                flat[key] = value
                # Also flatten nested dictionaries
                nested_flat = self._flatten_context(value)
                for nested_key, nested_value in nested_flat.items():
                    flat[f"{key}_{nested_key}"] = nested_value
            elif hasattr(value, '__dict__'):
                # Handle objects with attributes by treating them like dictionaries
                attrs = {}
                for attr_name in dir(value):
                    if not attr_name.startswith('_') and not callable(getattr(value, attr_name)):
                        try:
                            attr_value = getattr(value, attr_name)
                            if not callable(attr_value):
                                attrs[attr_name] = attr_value
                        except:
                            pass
                # Flatten the attributes
                nested_flat = self._flatten_context(attrs)
                for nested_key, nested_value in nested_flat.items():
                    flat[f"{key}_{nested_key}"] = nested_value
            elif isinstance(value, (list, tuple)):
                # Handle lists by converting them to a space-separated string for simple cases
                flat[key] = value
            else:
                flat[key] = value
        
        return flat
    
    def clear_cache(self) -> None:
        """Clear the template cache."""
        self.template_cache.clear()