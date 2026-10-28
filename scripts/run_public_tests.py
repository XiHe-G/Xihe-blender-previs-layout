"""Run only the self-contained tests distributed with the public source package."""
from pathlib import Path
import sys, unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
raise SystemExit(0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1)
