"""Cross-platform return values."""

import os

EX_CONFIG = getattr(os, "EX_CONFIG", 78)
EX_OK = getattr(os, "EX_OK", 0)
EX_SOFTWARE = getattr(os, "EX_SOFTWARE", 70)
