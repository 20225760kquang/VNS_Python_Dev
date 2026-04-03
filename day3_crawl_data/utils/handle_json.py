from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


VIETNAM_TZ = timezone(timedelta(hours=7))


def parse_iso_datetime(value: str) -> datetime:
	text = value.strip()
	if text.endswith("Z"):
		text = text.replace("Z", "+00:00")
	return datetime.fromisoformat(text)


def convert_fetched_at_to_vn(fetched_at_utc: str) -> datetime:
	dt = parse_iso_datetime(fetched_at_utc)
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=timezone.utc)
	return dt.astimezone(VIETNAM_TZ)


def parse_published_time(raw_time: str, fetched_at_vn: datetime) -> datetime:
	text = (raw_time or "").strip()
	if not text:
		return fetched_at_vn

	relative_match = re.fullmatch(r"(\d{1,2})\s*giờ\s*trước", text)
	if relative_match:
		hours = int(relative_match.group(1))
		return fetched_at_vn - timedelta(hours=hours)

	absolute_match = re.fullmatch(r"(\d{1,2}):(\d{2})\s*ngày\s*(\d{2})/(\d{2})/(\d{4})", text)
	if absolute_match:
		hour, minute, day, month, year = map(int, absolute_match.groups())
		return datetime(year, month, day, hour, minute, 0, tzinfo=VIETNAM_TZ)

	return fetched_at_vn


def build_tag(breadcrumbs: Any) -> str:
	if not isinstance(breadcrumbs, list):
		return ""
	cleaned = [str(item).strip() for item in breadcrumbs if str(item).strip()]
	return ", ".join(cleaned)


def load_json(path: Path) -> dict[str, Any]:
	return json.loads(path.read_text(encoding="utf-8"))


def transform_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
	fetched_at_raw = str(payload.get("fetched_at", "")).strip()
	if not fetched_at_raw:
		raise ValueError("Missing root field 'fetched_at' in JSON payload")

	fetched_at_vn = convert_fetched_at_to_vn(fetched_at_raw)
	records: list[dict[str, Any]] = []

	for item in payload.get("items", []):
		detail = item.get("detail") or {}

		title = str(item.get("title", "")).strip()
		url = str(item.get("url", "")).strip()
		author = str(detail.get("author", "")).strip()
		content = str(detail.get("content", "")).strip()
		tag = build_tag(detail.get("breadcrumbs", []))

		published_raw = str(detail.get("published_text") or item.get("time_text") or "").strip()
		published_time = parse_published_time(published_raw, fetched_at_vn)

		if not title or not url:
			continue

		records.append(
			{
				"title": title,
				"url": url,
				"published_time": published_time,
				"author": author,
				"tag": tag,
				"content": content,
				"fetched_at": fetched_at_vn,
			}
		)

	return records
