import sys
from pathlib import Path

# let the tests import the scripts in src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
