# NDJSON Event Reader

Process bounded event lines while isolating malformed records.

All bundled examples use synthetic data.

## Run

Requires Python 3.9 or later; no third-party packages or network access are needed.

```sh
python3 main.py
python3 main.py --help
python3 -m unittest -v
```

Run these commands from this repository's directory. The demo can also be launched from any directory by passing the absolute path to `main.py`.

## How it works

The binary reader uses bounded `readline()` calls. An oversized physical line is drained in bounded chunks and reported once, allowing the next event to be read. Each nonblank line must decode as UTF-8 and contain a JSON object with nonempty `event_id` and `type`, a nonnegative integer `timestamp`, and an object `payload`.

Duplicate JSON keys and non-finite numbers are rejected, including numbers that overflow to infinity. Bad records become results instead of aborting later lines. Physical line numbers include skipped blanks. Processing is O(input bytes), with memory bounded by the configured line size and its parsed object.

## Reuse

```python
import io
from main import read_events

stream = io.BytesIO(b'{"event_id":"demo","type":"created","timestamp":1,"payload":{}}\n')
result = next(read_events(stream))
assert result.error is None
assert result.event["event_id"] == "demo"
```

## Demo behavior

The bundled `sample.ndjson` contains valid events, a blank line, an invalid timestamp, and malformed JSON. `python3 main.py --strict` returns 1 because that fixture includes errors. Use `--file events.ndjson --max-line-bytes 4096` for another stream. The default fixture resolves from the script's directory.

## Boundaries

The byte limit includes LF or CRLF terminators. Unknown event fields are preserved, and event IDs are not deduplicated. The input must be a binary file-like object that honors `readline(size)`; text-mode streams are rejected. There is no schema registry, persistence, queue acknowledgment, or network ingestion. Extremely deep JSON is reported as a parsing failure when Python reaches its recursion limit.

## Verification

`test_main.py` exercises boundary conditions, invalid inputs, and meaningful behavior specific to this implementation. The default demo is deterministic and completes without external services. See the collection's verification report for the recorded run; run the commands above to verify this repository independently.

## Repository checks

```sh
python3 verify.py
```

This runs the isolated test suite, synthetic example, and CLI help. The included GitHub Actions workflow repeats these checks when the repository is published. No hosted CI result is claimed by the local verification report.
