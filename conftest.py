"""Make the `subtraction` package importable when running pytest from code/."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
