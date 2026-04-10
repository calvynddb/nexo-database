"""
CSV import/export helpers for entity data.
"""

import csv
from pathlib import Path


_READ_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def read_csv_rows(file_path: str) -> tuple[list[dict], list[str]]:
    """Read a CSV file and return (rows, fieldnames) with trimmed string values."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    last_error = None
    for encoding in _READ_ENCODINGS:
        try:
            with path.open("r", newline="", encoding=encoding) as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    return [], []

                fieldnames = [str(name).strip() for name in reader.fieldnames if name is not None]
                rows = []
                for raw_row in reader:
                    if raw_row is None:
                        continue

                    row = {}
                    for key, value in raw_row.items():
                        if key is None:
                            continue
                        row[str(key).strip()] = str(value or "").strip()

                    # Ignore fully empty rows.
                    if any(value for value in row.values()):
                        rows.append(row)

                return rows, fieldnames
        except UnicodeDecodeError as exc:
            last_error = exc

    raise ValueError(f"Unable to decode CSV file: {file_path}") from last_error


def write_csv_rows(file_path: str, fieldnames: list[str], rows: list[dict]) -> int:
    """Write CSV rows using UTF-8 BOM and return number of written rows."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    normalized_fields = [str(name).strip() for name in fieldnames if str(name).strip()]
    if not normalized_fields:
        raise ValueError("CSV export requires at least one field name")

    written = 0
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=normalized_fields)
        writer.writeheader()
        for raw_row in rows:
            if not isinstance(raw_row, dict):
                continue
            writer.writerow({field: str(raw_row.get(field, "")) for field in normalized_fields})
            written += 1

    return written
