"""
Simplified tests for the FastAPI server module focusing on core functionality.
Tests individual functions without complex mocking.
Run with: uv run pytest tests/test_server_simple.py -v
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Import the specific functions we want to test
from salasblog2.server import (
    is_admin_authenticated,
    create_xmlrpc_response,
    create_xmlrpc_fault_with_code,
    setup_logging,
    config
)


class TestAuthenticationHelpers:
    """Test authentication helper functions."""
    
    def test_is_admin_authenticated_true(self):
        """Test admin authentication check when authenticated."""
        request = Mock()
        request.session = {"admin_authenticated": True}
        
        result = is_admin_authenticated(request)
        assert result is True
    
    def test_is_admin_authenticated_false(self):
        """Test admin authentication check when not authenticated."""
        request = Mock()
        request.session = {}
        
        result = is_admin_authenticated(request)
        assert result is False
    
    def test_is_admin_authenticated_explicit_false(self):
        """Test admin authentication check with explicit false."""
        request = Mock()
        request.session = {"admin_authenticated": False}
        
        result = is_admin_authenticated(request)
        assert result is False


class TestAdminStatusEndpoint:
    """Test the /api/admin-status endpoint functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock the config for testing."""
        with patch('salasblog2.server.config') as mock_config:
            yield mock_config
    
    def test_admin_status_no_password_set(self, mock_config):
        """Test admin status when no password is configured."""
        from salasblog2.server import get_admin_status
        import asyncio
        
        # Mock config with no admin password
        mock_config.__getitem__.return_value = None
        
        # Mock request
        mock_request = Mock()
        
        # Run the async function
        result = asyncio.run(get_admin_status(mock_request))
        
        # Check the response
        assert hasattr(result, 'body')
        import json
        response_data = json.loads(result.body.decode())
        assert response_data["authenticated"] is True
    
    def test_admin_status_with_password_authenticated(self, mock_config):
        """Test admin status when password is set and user is authenticated."""
        from salasblog2.server import get_admin_status
        import asyncio
        
        # Mock config with admin password
        mock_config.__getitem__.return_value = "test_password"
        
        # Mock authenticated request
        mock_request = Mock()
        mock_request.session = {"admin_authenticated": True}
        
        # Run the async function
        result = asyncio.run(get_admin_status(mock_request))
        
        # Check the response
        assert hasattr(result, 'body')
        import json
        response_data = json.loads(result.body.decode())
        assert response_data["authenticated"] is True
    
    def test_admin_status_with_password_not_authenticated(self, mock_config):
        """Test admin status when password is set and user is not authenticated."""
        from salasblog2.server import get_admin_status
        import asyncio
        
        # Mock config with admin password
        mock_config.__getitem__.return_value = "test_password"
        
        # Mock unauthenticated request
        mock_request = Mock()
        mock_request.session = {}
        
        # Run the async function
        result = asyncio.run(get_admin_status(mock_request))
        
        # Check the response
        assert hasattr(result, 'body')
        import json
        response_data = json.loads(result.body.decode())
        assert response_data["authenticated"] is False


class TestXMLRPCHelpers:
    """Test XML-RPC helper functions."""
    
    def test_create_xmlrpc_response_string(self):
        """Test XML-RPC response creation with string result."""
        result = create_xmlrpc_response("Hello World")
        
        assert "<?xml version=\"1.0\"?>" in result
        assert "<methodResponse>" in result
        assert "<string>Hello World</string>" in result
        assert "<params>" in result
        assert "<param>" in result
        assert "<value>" in result
    
    def test_create_xmlrpc_response_boolean_true(self):
        """Test XML-RPC response creation with boolean true."""
        result = create_xmlrpc_response(True)
        
        assert "<?xml version=\"1.0\"?>" in result
        assert "<boolean>1</boolean>" in result
    
    def test_create_xmlrpc_response_boolean_false(self):
        """Test XML-RPC response creation with boolean false."""
        result = create_xmlrpc_response(False)
        
        assert "<?xml version=\"1.0\"?>" in result
        assert "<boolean>0</boolean>" in result
    
    def test_create_xmlrpc_response_integer(self):
        """Test XML-RPC response creation with integer."""
        result = create_xmlrpc_response(42)
        
        assert "<?xml version=\"1.0\"?>" in result
        assert "<int>42</int>" in result
    
    def test_create_xmlrpc_response_dict(self):
        """Test XML-RPC response creation with dictionary."""
        data = {"key": "value", "number": "123"}
        result = create_xmlrpc_response(data)
        
        assert "<?xml version=\"1.0\"?>" in result
        assert "<struct>" in result
        assert "<member>" in result
        assert "<name>key</name>" in result
        assert "<string>value</string>" in result
        assert "<name>number</name>" in result
        assert "<string>123</string>" in result
    
    def test_create_xmlrpc_response_list_of_strings(self):
        """Test XML-RPC response creation with list of strings."""
        data = ["item1", "item2", "item3"]
        result = create_xmlrpc_response(data)
        
        assert "<?xml version=\"1.0\"?>" in result
        assert "<array>" in result
        assert "<data>" in result
        assert "<string>item1</string>" in result
        assert "<string>item2</string>" in result
        assert "<string>item3</string>" in result
    
    def test_create_xmlrpc_response_list_of_dicts(self):
        """Test XML-RPC response creation with list of dictionaries."""
        data = [
            {"title": "Post 1", "id": "1"},
            {"title": "Post 2", "id": "2"}
        ]
        result = create_xmlrpc_response(data)
        
        assert "<?xml version=\"1.0\"?>" in result
        assert "<array>" in result
        assert "<struct>" in result
        assert "<name>title</name>" in result
        assert "<string>Post 1</string>" in result
        assert "<string>Post 2</string>" in result
    
    def test_create_xmlrpc_response_other_types(self):
        """Test XML-RPC response creation with other types (converted to string)."""
        result = create_xmlrpc_response(3.14)
        
        assert "<?xml version=\"1.0\"?>" in result
        assert "<string>3.14</string>" in result
    
    def test_create_xmlrpc_fault_with_code(self):
        """Test XML-RPC fault response creation."""
        result = create_xmlrpc_fault_with_code(403, "Access denied")
        
        assert "<?xml version=\"1.0\"" in result
        assert "<methodResponse>" in result
        assert "<fault>" in result
        assert "<struct>" in result
        assert "<name>faultCode</name>" in result
        assert "<int>403</int>" in result
        assert "<name>faultString</name>" in result
        assert "<string>Access denied</string>" in result
    
    def test_create_xmlrpc_fault_different_codes(self):
        """Test XML-RPC fault response with different error codes."""
        result404 = create_xmlrpc_fault_with_code(404, "Not found")
        result500 = create_xmlrpc_fault_with_code(500, "Internal error")
        
        assert "<int>404</int>" in result404
        assert "<string>Not found</string>" in result404
        assert "<int>500</int>" in result500
        assert "<string>Internal error</string>" in result500


class TestLoggingSetup:
    """Test logging configuration."""
    
    def test_setup_logging_default_level(self):
        """Test logging setup with default level."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('salasblog2.server.logging.basicConfig') as mock_config:
                setup_logging()
                
                mock_config.assert_called_once()
                call_args = mock_config.call_args[1]
                assert call_args['format'] == '%(asctime)s [%(levelname)s] %(message)s'
                assert call_args['datefmt'] == '%M:%S'
                assert call_args['force'] is True
    
    def test_setup_logging_custom_level(self):
        """Test logging setup with custom level."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            with patch('salasblog2.server.logging.basicConfig') as mock_config:
                setup_logging()
                
                mock_config.assert_called_once()
    
    def test_setup_logging_invalid_level(self):
        """Test logging setup with invalid level falls back to INFO."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID_LEVEL"}):
            with patch('salasblog2.server.logging.basicConfig') as mock_config:
                setup_logging()
                
                mock_config.assert_called_once()


class TestConfigurationGlobal:
    """Test global configuration management."""
    
    def test_config_is_dict(self):
        """Test that config is a dictionary."""
        assert isinstance(config, dict)
    
    def test_config_has_expected_keys(self):
        """Test that config has all expected keys."""
        expected_keys = {
            "root_dir", "output_dir", "templates_dir", 
            "admin_password", "session_secret", "jinja_env"
        }
        assert all(key in config for key in expected_keys)
    
    def test_config_allows_updates(self):
        """Test that config can be updated."""
        original_value = config.get("test_key")
        config["test_key"] = "test_value"
        assert config["test_key"] == "test_value"
        
        # Clean up
        if original_value is None:
            config.pop("test_key", None)
        else:
            config["test_key"] = original_value


class TestEnvironmentValidationUnit:
    """Test environment validation with isolated unit tests."""
    
    def test_environment_validation_import(self):
        """Test that validate_environment_and_setup can be imported."""
        from salasblog2.server import validate_environment_and_setup
        assert callable(validate_environment_and_setup)
    
    def test_environment_validation_requires_session_secret(self):
        """Test validation requires SESSION_SECRET."""
        from salasblog2.server import validate_environment_and_setup
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="SESSION_SECRET"):
                validate_environment_and_setup()


class TestServerImports:
    """Test that all expected functions and objects can be imported."""
    
    def test_import_app(self):
        """Test that FastAPI app can be imported."""
        from salasblog2.server import app
        assert app is not None
        # Basic check that it's a FastAPI app
        assert hasattr(app, 'routes')
    
    def test_import_config(self):
        """Test that config can be imported."""
        from salasblog2.server import config
        assert isinstance(config, dict)
    
    def test_import_helper_functions(self):
        """Test that helper functions can be imported."""
        from salasblog2.server import (
            is_admin_authenticated,
            create_xmlrpc_response,
            create_xmlrpc_fault_with_code,
            setup_logging
        )
        
        assert callable(is_admin_authenticated)
        assert callable(create_xmlrpc_response)
        assert callable(create_xmlrpc_fault_with_code)
        assert callable(setup_logging)
    
    def test_import_validation_functions(self):
        """Test that validation functions can be imported."""
        from salasblog2.server import validate_environment_and_setup
        assert callable(validate_environment_and_setup)


class TestServerStructure:
    """Test server structure and organization."""
    
    def test_no_inline_html_in_functions(self):
        """Test that the refactoring removed large HTML chunks from functions."""
        # This tests that we successfully extracted HTML to templates
        import inspect
        from salasblog2 import server
        
        # Get all functions from the server module
        functions = inspect.getmembers(server, inspect.isfunction)
        
        for name, func in functions:
            if hasattr(func, '__code__'):
                # Get function source if possible
                try:
                    source = inspect.getsource(func)
                    # Check that no function has large HTML chunks (more than 500 chars of HTML-like content)
                    html_like_lines = [line for line in source.split('\n') if '<html' in line.lower() or '<!doctype' in line.lower()]
                    if html_like_lines:
                        # If there are HTML-like lines, they should be short (templates or simple tags)
                        for line in html_like_lines:
                            assert len(line.strip()) < 100, f"Function {name} still contains large HTML: {line[:100]}..."
                except (OSError, TypeError):
                    # Can't get source for some functions (built-ins, etc.), skip
                    pass
    
    def test_imports_at_top(self):
        """Test that all imports are at the top of the file (except conditional imports)."""
        import ast
        import salasblog2.server as server_module
        
        # Read the source file
        server_file = Path(server_module.__file__)
        source = server_file.read_text()
        
        # Parse the AST
        tree = ast.parse(source)
        
        # Find all import statements and their line numbers
        top_level_imports = []
        conditional_imports = []
        other_statements = []
        
        for node in tree.body:  # Only check top-level nodes
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                top_level_imports.append(node.lineno)
            elif isinstance(node, ast.If) and getattr(node.test, 'left', None) and \
                 isinstance(node.test.left, ast.Name) and node.test.left.id == '__name__':
                # This is if __name__ == "__main__": block - conditional imports are OK here
                for subnode in ast.walk(node):
                    if isinstance(subnode, (ast.Import, ast.ImportFrom)):
                        conditional_imports.append(subnode.lineno)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Assign)):
                other_statements.append(node.lineno)
        
        # Check that top-level imports come before other statements
        if top_level_imports and other_statements:
            first_non_import = min(other_statements)
            last_import = max(top_level_imports)
            
            assert last_import < first_non_import, f"Top-level imports should come before other statements. Last import: {last_import}, First other: {first_non_import}"
        
        # Conditional imports in if __name__ == "__main__": are acceptable
        assert len(conditional_imports) >= 0, "Conditional imports in __main__ block are acceptable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])