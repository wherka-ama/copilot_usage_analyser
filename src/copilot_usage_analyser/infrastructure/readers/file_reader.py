"""File reader for log files."""

import json
from typing import Any, Dict, Iterator, List, Tuple, Union


class LogFileReader:
    """Reader for Copilot debug log files."""

    def read_file(self, file_path: str) -> Union[Dict, List[Dict]]:
        """Read a JSON or JSONL file and return the data.

        Returns a dict for single-JSON files, or a list of dicts for JSONL files.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Try JSONL first if the file has .jsonl extension or contains newline-delimited JSON
        if file_path.endswith(".jsonl"):
            return self._parse_jsonl(content, file_path)

        # Try single JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Fall back to JSONL (some files lack the extension)
        return self._parse_jsonl(content, file_path)

    def _parse_jsonl(self, content: str, file_path: str) -> List[Dict]:
        """Parse newline-delimited JSON."""
        records = []
        for i, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {i} of {file_path}: {e}")
        if not records:
            raise ValueError(f"No records found in JSONL file {file_path}")
        return records

    def detect_format(self, file_path: str) -> str:
        """Detect the log file format.

        Returns one of: 'chatreplay', 'copilot_cli_otel', 'otlp'.
        """
        data = self.read_file(file_path)

        # JSONL list → could be Copilot CLI OTel format
        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                first = data[0]
                # Copilot CLI OTel has type='span'|'metric' with gen_ai attributes
                if first.get("type") in ("span", "metric"):
                    return "copilot_cli_otel"
                # Generic JSONL with spans
                if "traceId" in first or "spanId" in first:
                    return "copilot_cli_otel"
            return "copilot_cli_otel"

        # Dict-based formats
        if isinstance(data, dict):
            # Check for ChatReplay format
            if "exportedAt" in data and "prompts" in data:
                return "chatreplay"

            # Check for OTLP format
            if "resourceSpans" in data:
                return "otlp"

        # Default to chatreplay
        return "chatreplay"

    def read_directory(self, directory_path: str) -> Iterator[Tuple[str, Any]]:
        """Read all log files in a directory."""
        import os

        for filename in sorted(os.listdir(directory_path)):
            if filename.endswith((".json", ".jsonl")):
                file_path = os.path.join(directory_path, filename)
                try:
                    data = self.read_file(file_path)
                    yield (file_path, data)
                except (ValueError, OSError):
                    pass
