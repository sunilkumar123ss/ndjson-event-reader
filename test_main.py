import io
import json
import unittest
from main import read_events


def event(**changes):
    data = {"event_id": "demo-1", "type": "created", "timestamp": 1, "payload": {}}
    data.update(changes)
    return json.dumps(data, separators=(',', ':')).encode()


class NDJSONTests(unittest.TestCase):
    def read(self, data, **kwargs):
        return list(read_events(io.BytesIO(data), **kwargs))

    def test_valid_final_line_without_newline(self):
        results = self.read(event())
        self.assertIsNone(results[0].error)
        self.assertEqual(results[0].event['event_id'], 'demo-1')

    def test_bad_line_does_not_abort_good_line(self):
        results = self.read(b'not-json\n' + event() + b'\n')
        self.assertIsNotNone(results[0].error)
        self.assertIsNone(results[1].error)
        self.assertEqual(results[1].line_number, 2)

    def test_blank_lines_preserve_physical_line_numbers(self):
        results = self.read(b'\n  \n' + event())
        self.assertEqual(results[0].line_number, 3)
        self.assertIsNotNone(self.read(b'\n', skip_blank=False)[0].error)

    def test_oversized_line_drains_and_recovers(self):
        results = self.read(b'x' * 300 + b'\n' + event(), max_line_bytes=100)
        self.assertEqual(len(results), 2)
        self.assertIn('exceeds', results[0].error)
        self.assertIsNone(results[1].error)
        self.assertEqual(results[1].line_number, 2)

    def test_byte_limit_includes_newline(self):
        raw = event()
        self.assertIsNone(self.read(raw, max_line_bytes=len(raw))[0].error)
        self.assertIsNotNone(self.read(raw + b'\n', max_line_bytes=len(raw))[0].error)

    def test_invalid_utf8_duplicate_keys_and_nonfinite_numbers(self):
        for data in (b'\xff\n', b'{"a":1,"a":2}\n', event(payload={"x": float('nan')}),
                     event().replace(b'"payload":{}', b'"payload":{"x":1e999}')):
            with self.subTest(data=data): self.assertIsNotNone(self.read(data)[0].error)




if __name__ == '__main__':
    unittest.main()
