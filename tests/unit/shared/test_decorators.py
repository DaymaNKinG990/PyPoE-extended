"""
Tests for shared decorators

Tests utility decorators from PyPoE.shared.decorators.
"""

import pytest

from PyPoE.shared.decorators import doc


class TestDocDecorator:
    """Test the doc decorator for docstring manipulation."""

    def test_doc_decorator_appends_docstring(self):
        """Test that doc decorator appends to existing docstring."""

        @doc(append="Additional documentation.")
        def test_func():
            """Original docstring."""
            pass

        assert "Original docstring." in test_func.__doc__
        assert "Additional documentation." in test_func.__doc__

    def test_doc_decorator_prepends_docstring(self):
        """Test that doc decorator prepends to existing docstring."""

        @doc(prepend="Prepended documentation.")
        def test_func():
            """Original docstring."""
            pass

        assert "Prepended documentation." in test_func.__doc__
        assert "Original docstring." in test_func.__doc__
        assert test_func.__doc__.index("Prepended") < test_func.__doc__.index("Original")

    def test_doc_decorator_replaces_docstring(self):
        """Test that doc decorator can replace docstring."""

        @doc(doc="Completely new docstring.")
        def test_func():
            """Original docstring."""
            pass

        assert test_func.__doc__ == "Completely new docstring."
        assert "Original" not in test_func.__doc__

    def test_doc_decorator_on_function_without_docstring(self):
        """Test doc decorator on function without existing docstring."""

        @doc(append="New documentation.")
        def test_func():
            pass

        assert "New documentation." in test_func.__doc__

    def test_doc_decorator_with_class(self):
        """Test that doc decorator works on classes."""

        @doc(append="Class documentation.")
        class TestClass:
            """Original class doc."""

            pass

        assert "Original class doc." in TestClass.__doc__
        assert "Class documentation." in TestClass.__doc__

    def test_doc_decorator_preserves_function_name(self):
        """Test that doc decorator preserves function name."""

        @doc(append="Documentation.")
        def my_function():
            """Original."""
            pass

        assert my_function.__name__ == "my_function"

    def test_doc_decorator_empty_append(self):
        """Test doc decorator with empty append."""

        @doc(append="")
        def test_func():
            """Original."""
            pass

        assert test_func.__doc__ == "Original."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
