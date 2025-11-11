# 📚 PyPoE Examples

This directory contains practical examples of using PyPoE library features.

## 🚀 Available Examples

### `di_usage_example.py` - Dependency Injection

Demonstrates the DI container usage patterns:

- **Example 1:** Basic DI container usage
- **Example 2:** Using DI with game path
- **Example 3:** Creating custom services with DI
- **Example 4:** Manual provider registration
- **Example 5:** Using global container singleton
- **Example 6:** Testing patterns with DI
- **Example 7:** Comparing singleton vs transient lifecycles

**Run:**
```bash
uv run python examples/di_usage_example.py
```

**Note:** Some examples require:
- Path of Exile installation (for FileSystem examples)
- Specification database (run `python scripts/migrate_specs_to_db.py`)

---

## 📖 Documentation

For detailed documentation, see:
- [DI Integration Guide](../docs/DI_INTEGRATION_GUIDE.md)
- [Architecture Analysis](../ARCHITECTURE_ANALYSIS.md)
- [Refactoring Roadmap](../REFACTORING_ROADMAP.md)

---

## 🎯 Purpose

These examples serve as:
1. **Learning resources** for new contributors
2. **Reference implementations** for best practices
3. **Integration tests** for core features
4. **Documentation supplements** with working code

---

## 🤝 Contributing

To add a new example:
1. Create a descriptive filename (e.g., `feature_example.py`)
2. Add docstrings and comments
3. Ensure code quality (Ruff + MyPy clean)
4. Update this README

---

**Happy Learning! 📖**

