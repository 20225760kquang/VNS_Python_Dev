from __future__ import annotations

import argparse
import csv
from pathlib import Path

from handle_json import load_json, transform_records


DEFAULT_CSV_PATH = "bongdaplus_news.csv"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JSON_PATH = str(PROJECT_ROOT / "bongdaplus_crawled.json")

def format_timestamp(dt) -> str:
	return dt.strftime("%Y-%m-%d %H:%M:%S")


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Export crawled Bongdaplus records to CSV with DB-like columns.")
	parser.add_argument("--json-path", default=DEFAULT_JSON_PATH, help="Path to crawler JSON file.")
	parser.add_argument("--csv-path", default=DEFAULT_CSV_PATH, help="Destination CSV file path.")
	parser.add_argument("--start-id", type=int, default=1, help="Starting id value for CSV rows.")
	return parser


def export_csv(json_path: Path, csv_path: Path, start_id: int) -> int:
	payload = load_json(json_path)
	records = transform_records(payload)

	fieldnames = [
		"id",
		"title",
		"url",
		"published_time",
		"author",
		"tag",
		"content",
		"fetched_at",
	]

	with csv_path.open("w", encoding="utf-8-sig", newline="") as file_obj:
		writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
		writer.writeheader()

		for index, record in enumerate(records, start=start_id):
			writer.writerow(
				{
					"id": index,
					"title": record["title"],
					"url": record["url"],
					"published_time": format_timestamp(record["published_time"]),
					"author": record["author"],
					"tag": record["tag"],
					"content": record["content"],
					"fetched_at": format_timestamp(record["fetched_at"]),
				}
			)

	return len(records)


def main() -> int:
	parser = build_parser()
	args = parser.parse_args()

	count = export_csv(Path(args.json_path), Path(args.csv_path), args.start_id)
	print(f"Exported {count} rows to {args.csv_path}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
