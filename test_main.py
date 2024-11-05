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








if __name__ == '__main__':
    unittest.main()
