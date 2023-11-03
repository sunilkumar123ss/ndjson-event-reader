"""Read and validate bounded NDJSON event lines while reporting per-line failures."""
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys


@dataclass(frozen=True)
class EventResult:
    line_number: int
    event: object
    error: object
