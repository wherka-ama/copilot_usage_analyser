"""File reader for log files."""

import json
from typing import Dict, Iterator, Tuple


class LogFileReader:
    """Reader for Copilot debug log files."""

    def read_file(self, file_path: str) -> Dict:
        """Read a JSON file and return the data."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse as single JSON file
        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in file {file_path}: {e}")

    def detect_format(self, file_path: str) -> str:
        """Detect the log file format."""
        data = self.read_file(file_path)
        
        # Check for ChatReplay format
        if "exportedAt" in data and "prompts" in data:
            return "chatreplay"
        
        # Check for OTLP format
        if "resourceSpans" in data:
            return "otlp"
        
        # Default to chatreplay as it's the current VS Code format
        return "chatreplay"

    def read_directory(self, directory_path: str) -> Iterator[Tuple[str, Dict]]:
        """Read all log files in a directory."""
        import os

        for filename in os.listdir(directory_path):
            if filename.endswith((".json", ".jsonl")):
                file_path = os.path.join(directory_path, filename)
                data = self.read_file(file_path)
                yield (file_path, data)
