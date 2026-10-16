"""Runs the test functions without pytest, for machines where pytest is not installed."""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "tests"))
sys.path.insert(0, str(Path(__file__).parent))

passed = failed = 0
for mod_name in ["test_quote", "test_extractor", "test_triage"]:
    mod = importlib.import_module(mod_name)
    for name in dir(mod):
        if name.startswith("test_"):
            try:
                getattr(mod, name)()
                passed += 1
                print(f"PASS {mod_name}.{name}")
            except Exception as e:
                failed += 1
                print(f"FAIL {mod_name}.{name}: {e!r}")
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
