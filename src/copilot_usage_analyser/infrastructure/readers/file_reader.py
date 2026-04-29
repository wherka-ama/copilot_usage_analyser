"""File reader for log files."""

import json
from typing import Dict, Iterator, Tuple


class LogFileReader:
    """Reader for Copilot debug log files."""

    def read_file(self, file_path: str) -> Iterator[Dict]:
        """Read a JSONL or JSON file and yield JSON objects."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try JSONL format first (line-delimited JSON)
        try:
            for line in content.strip().split("\n"):
                if line.strip():
                    yield json.loads(line)
            return
        except json.JSONDecodeError:
            pass

        # Fall back to single JSON file
        try:
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    yield item
            else:
                yield data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in file {file_path}: {e}")

    def read_directory(self, directory_path: str) -> Iterator[Tuple[str, Dict]]:
        """Read all log files in a directory."""
        import os

        for filename in os.listdir(directory_path):
            if filename.endswith((".json", ".jsonl")):
                file_path = os.path.join(directory_path, filename)
                for data in self.read_file(file_path):
                    yield (file_path, data)
