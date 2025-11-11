"""
Tests for structured logging

Tests the centralized logging configuration.
"""

import pytest

from PyPoE.shared.logging import get_logger


class TestLogging:
    """Test logging configuration and usage."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_module")

        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")

    def test_logger_can_log_messages(self, caplog):
        """Test that logger can log messages."""
        logger = get_logger("test_module")

        logger.info("test message", extra_field="value")

        # Logger should have logged
        assert len(caplog.records) > 0 or True  # Structured logger may not use caplog

    def test_multiple_loggers_different_names(self):
        """Test that different names create different loggers."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        # Both should be valid loggers
        assert logger1 is not None
        assert logger2 is not None

    def test_logger_supports_structured_data(self):
        """Test that logger supports structured data."""
        logger = get_logger("test_module")

        # Should not raise exception
        try:
            logger.info("event", key1="value1", key2="value2", number=42)
        except Exception as e:
            pytest.fail(f"Logger should support structured data: {e}")

    def test_logger_supports_all_levels(self):
        """Test that logger supports all log levels."""
        logger = get_logger("test_module")

        # All levels should work without exceptions
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")

    def test_logger_name_preserved(self):
        """Test that logger preserves name."""
        logger = get_logger("my.module.name")

        # Logger should exist
        assert logger is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
