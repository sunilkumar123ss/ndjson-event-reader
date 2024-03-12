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


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError("non-finite JSON number")


def _validate_json_numbers(value):
    # json.loads accepts 1e999 as infinity even with parse_constant configured.
    import math
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite JSON number")
    if isinstance(value, dict):
        for child in value.values():
            _validate_json_numbers(child)
    elif isinstance(value, list):
        for child in value:
            _validate_json_numbers(child)


def read_events(stream, max_line_bytes=8192, skip_blank=True):
    if type(max_line_bytes) is not int or max_line_bytes < 1:
        raise ValueError("max_line_bytes must be a positive integer")
    line_number = 0
    while True:
        raw = stream.readline(max_line_bytes + 1)
        if not raw:
            return
        if not isinstance(raw, bytes):
            raise TypeError("stream must be opened in binary mode")
        line_number += 1
        if len(raw) > max_line_bytes:
            while raw and not raw.endswith(b"\n"):
                raw = stream.readline(max_line_bytes + 1)
            yield EventResult(line_number, None, "line exceeds max_line_bytes (including newline)")
            continue
        if not raw.strip() and skip_blank:
            continue
        try:
            text = raw.decode("utf-8")
            event = json.loads(text, object_pairs_hook=_object, parse_constant=_invalid_constant)
            _validate_json_numbers(event)
            if not isinstance(event, dict):
                raise ValueError("event must be a JSON object")
            for name in ("event_id", "type"):
                if not isinstance(event.get(name), str) or not event[name].strip():
                    raise ValueError(name + " must be a nonempty string")
            if type(event.get("timestamp")) is not int or event["timestamp"] < 0:
                raise ValueError("timestamp must be a nonnegative integer")
            if not isinstance(event.get("payload"), dict):
                raise ValueError("payload must be a JSON object")
        except (UnicodeError, ValueError, RecursionError) as exc:
            yield EventResult(line_number, None, "{}: {}".format(type(exc).__name__, str(exc)))
            continue
        yield EventResult(line_number, event, None)
