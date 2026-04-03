from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from dotenv import load_dotenv

from sqlalchemy import Column, DateTime, Integer, MetaData, Table, Text, create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

from handle_json import load_json, transform_records




DEFAULT_TABLE_NAME = "data"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JSON_PATH = str(PROJECT_ROOT / "bongdaplus_crawled.json")


def load_environment() -> None:
	load_dotenv(PROJECT_ROOT / ".env")


def build_database_url(cli_database_url: str = "") -> str:
	if cli_database_url:
		return cli_database_url

	user = os.getenv("DB_USER", "")
	password = os.getenv("DB_PASSWORD", "")
	host = os.getenv("DB_HOST", "localhost")
	port = os.getenv("DB_PORT", "5432")
	db_name = os.getenv("DB_NAME", "")

	if not user or not db_name:
		return ""

	user_safe = quote_plus(user)
	password_safe = quote_plus(password)
	auth = f"{user_safe}:{password_safe}" if password else user_safe

	# Same style as requested: postgresql+psycopg2://user:pass@host:port/db
	return f"postgresql+psycopg2://{auth}@{host}:{port}/{db_name}"


def ensure_table(engine: Engine, table_name: str) -> Table:
	metadata = MetaData()
	table = Table(
		table_name,
		metadata,
		Column("id", Integer, primary_key=True, autoincrement=True),
		Column("title", Text, nullable=False),
		Column("url", Text, nullable=False, unique=True),
		Column("published_time", DateTime(timezone=True), nullable=False),
		Column("author", Text, nullable=True),
		Column("tag", Text, nullable=True),
		Column("content", Text, nullable=True),
		Column("fetched_at", DateTime(timezone=True), nullable=False),
	)
	metadata.create_all(engine)
	return table


def upsert_records(engine: Engine, table: Table, records: list[dict[str, Any]]) -> int:
	if not records:
		return 0

	stmt = pg_insert(table).values(records)
	stmt = stmt.on_conflict_do_update(
		index_elements=[table.c.url],
		set_={
			"title": stmt.excluded.title,
			"published_time": stmt.excluded.published_time,
			"author": stmt.excluded.author,
			"tag": stmt.excluded.tag,
			"content": stmt.excluded.content,
			"fetched_at": stmt.excluded.fetched_at,
		},
	)

	with engine.begin() as connection:
		result = connection.execute(stmt)
	return int(result.rowcount or 0)

def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Save crawled Bongdaplus data into PostgreSQL via SQLAlchemy.")
	parser.add_argument("--json-path", default=DEFAULT_JSON_PATH, help="Path to the crawler JSON file.")
	parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", ""), help="PostgreSQL SQLAlchemy URL.")
	parser.add_argument("--table-name", default=DEFAULT_TABLE_NAME, help="Destination PostgreSQL table name.")
	parser.add_argument("--dry-run", action="store_true", help="Only parse and show stats without writing to DB.")
	return parser


def main() -> int:
	load_environment()
	parser = build_parser()
	args = parser.parse_args()

	payload = load_json(Path(args.json_path))
	records = transform_records(payload)

	if args.dry_run:
		print(f"Parsed {len(records)} records from {args.json_path}")
		if records:
			preview = records[0]
			print("Sample record:")
			print(json.dumps({
				"title": preview["title"],
				"url": preview["url"],
				"published_time": preview["published_time"].isoformat(),
				"author": preview["author"],
				"tag": preview["tag"],
				"fetched_at": preview["fetched_at"].isoformat(),
			}, ensure_ascii=False, indent=2))
		return 0

	database_url = build_database_url(args.database_url)
	if not database_url:
		raise ValueError(
			"Missing DB config. Set DATABASE_URL or DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME in .env"
		)

	engine = create_engine(database_url, future=True)
	table = ensure_table(engine, args.table_name)
	affected_rows = upsert_records(engine, table, records)
	print(f"Upserted {affected_rows} rows into table '{args.table_name}'")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
