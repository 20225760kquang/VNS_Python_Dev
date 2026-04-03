from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


BASE_URL = "https://bongdaplus.vn"
DEFAULT_SECTION_URL = "https://bongdaplus.vn/bong-da-viet-nam"
DEFAULT_OUTPUT = "bongdaplus_crawled.json"
DEFAULT_MAX_VIEWMORE_PAGES = 1
HEADERS = {
	"User-Agent": (
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
		"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
	),
	"Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}


def normalize_text(value: str | None) -> str:
	if not value:
		return ""
	return re.sub(r"\s+", " ", value).strip()


def absolute_url(url: str, base_url: str = BASE_URL) -> str:
	return urljoin(base_url, url)


def fetch_html(url: str, timeout: int = 30) -> str:
	request = Request(url, headers=HEADERS)
	with urlopen(request, timeout=timeout) as response:
		charset = response.headers.get_content_charset() or "utf-8"
		return response.read().decode(charset, errors="replace")


def get_meta_content(soup: BeautifulSoup, *, name: str | None = None, property: str | None = None) -> str:
	attributes: dict[str, str] = {}
	if name:
		attributes["name"] = name
	if property:
		attributes["property"] = property

	meta = soup.find("meta", attrs=attributes)
	return normalize_text(meta.get("content") if meta else "")


def extract_article_text(article_soup: BeautifulSoup) -> str:
	content = article_soup.select_one("div.content")
	if not content:
		return ""

	paragraphs: list[str] = []
	for block in content.select("p, h2, h3"):
		text = normalize_text(block.get_text(" ", strip=True))
		if text:
			paragraphs.append(text)
	return "\n\n".join(paragraphs)


def extract_breadcrumbs(article_soup: BeautifulSoup) -> list[str]:
	for selector in ("div.bread-crums a", "div.chain-navs a"):
		anchors = article_soup.select(selector)
		if anchors:
			breadcrumbs = []
			for anchor in anchors:
				text = normalize_text(anchor.get_text(" ", strip=True))
				if text and text != "/":
					breadcrumbs.append(text)
			if breadcrumbs:
				return breadcrumbs
	return []


def parse_section_page(html: str, source_url: str) -> list[dict[str, Any]]:
	soup = BeautifulSoup(html, "html.parser")
	items: list[dict[str, Any]] = []
	seen_urls: set[str] = set()
	section = soup.select_one("section.cat-news") or soup

	card_selectors = (
		"div.sld-lst div.sld-itm.news",
		"div.news-lst li.news",
		"div.col.m12.w3 > div.news",
	)

	def append_card(card: Any) -> None:
		anchors = card.find_all("a", href=True)
		if not anchors:
			return

		title_anchor = None
		for anchor in anchors:
			text = normalize_text(anchor.get_text(" ", strip=True))
			if text:
				title_anchor = anchor
				break

		if not title_anchor:
			return

		title = normalize_text(title_anchor.get_text(" ", strip=True))
		article_url = absolute_url(title_anchor["href"], source_url)
		if article_url in seen_urls:
			return
		seen_urls.add(article_url)

		items.append(
			{
				"title": title,
				"url": article_url,
			}
		)

	for selector in card_selectors:
		for card in section.select(selector):
			append_card(card)

	return items


def parse_viewmore_page(html: str, source_url: str) -> list[dict[str, Any]]:
	soup = BeautifulSoup(html, "html.parser")
	items: list[dict[str, Any]] = []

	for card in soup.select("div.col.m12.w3"):
		anchors = card.find_all("a", href=True)
		if not anchors:
			continue

		title_anchor = None
		for anchor in anchors:
			text = normalize_text(anchor.get_text(" ", strip=True))
			if text:
				title_anchor = anchor
				break

		if not title_anchor:
			continue

		title = normalize_text(title_anchor.get_text(" ", strip=True))
		article_url = absolute_url(title_anchor["href"], source_url)

		items.append(
			{
				"title": title,
				"url": article_url,
			}
		)

	return items


def parse_article_page(html: str, article_url: str) -> dict[str, Any]:
	soup = BeautifulSoup(html, "html.parser")

	author_link = soup.select_one('a[href*="/tac-gia/"]')
	author = normalize_text(author_link.get_text(" ", strip=True) if author_link else "")

	editor = soup.select_one("div.editor")
	published_time = ""
	if editor:
		parts = [normalize_text(part) for part in editor.get_text("•", strip=True).split("•")]
		parts = [part for part in parts if part]
		if len(parts) >= 2:
			published_time = parts[-1]
		elif parts:
			published_time = parts[0]

	description = get_meta_content(soup, name="description") or get_meta_content(soup, property="og:description")

	breadcrumbs = extract_breadcrumbs(soup)

	content = extract_article_text(soup)

	return {
		"author": author,
		"published_time": published_time,
		"description": description,
		"breadcrumbs": breadcrumbs,
		"content": content,
	}


def crawl_section(section_url: str, *, max_items: int | None = None, crawl_details: bool = True, delay: float = 0.0, max_viewmore_pages: int = DEFAULT_MAX_VIEWMORE_PAGES) -> dict[str, Any]:
	section_html = fetch_html(section_url)
	section_items = parse_section_page(section_html, section_url)
	section_soup = BeautifulSoup(section_html, "html.parser")
	viewmore_type = normalize_text((section_soup.select_one("#viewmore_type") or {}).get("value") if section_soup.select_one("#viewmore_type") else "")
	viewmore_id = normalize_text((section_soup.select_one("#viewmore_id") or {}).get("value") if section_soup.select_one("#viewmore_id") else "")
	viewmore_page = section_soup.select_one("#viewmore_page")
	viewmore_current_page = 1
	if viewmore_page:
		try:
			viewmore_current_page = int(normalize_text(viewmore_page.get("value")) or "1")
		except ValueError:
			viewmore_current_page = 1

	if viewmore_type and viewmore_id and max_viewmore_pages > 0:
		for offset in range(1, max_viewmore_pages + 1):
			page_number = viewmore_current_page + offset
			try:
				viewmore_html = fetch_html(f"{BASE_URL}/loadviewmore/{viewmore_type}/{viewmore_id}/{page_number}")
			except Exception:
				break
			more_items = parse_viewmore_page(viewmore_html, section_url)
			if not more_items:
				break
			section_items.extend(more_items)

	if max_items is not None:
		section_items = section_items[:max_items]

	crawled_items: list[dict[str, Any]] = []
	for index, item in enumerate(section_items, 1):
		merged_item = dict(item)
		if crawl_details:
			try:
				detail_html = fetch_html(item["url"])
				detail = parse_article_page(detail_html, item["url"])
				merged_item.update(detail)
			except Exception as exc:  # pragma: no cover - defensive network handling
				merged_item["author"] = ""
				merged_item["published_time"] = ""
				merged_item["description"] = ""
				merged_item["breadcrumbs"] = []
				merged_item["content"] = ""

			if delay and index < len(section_items):
				time.sleep(delay)

		crawled_items.append(merged_item)

	section_title_node = section_soup.select_one("h1") or section_soup.title
	section_title = normalize_text(section_title_node.get_text(" ", strip=True) if section_title_node else "")

	return {
		"source_url": section_url,
		"section_title": section_title,
		"fetched_at": datetime.now(timezone.utc).isoformat(),
		"item_count": len(crawled_items),
		"items": crawled_items,
	}


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Crawl Bongdaplus section pages and article details.")
	parser.add_argument("--section-url", default=DEFAULT_SECTION_URL, help="Section URL to crawl.")
	parser.add_argument("--max-items", type=int, default=None, help="Limit the number of list items to crawl.")
	parser.add_argument("--max-viewmore-pages", type=int, default=DEFAULT_MAX_VIEWMORE_PAGES, help="Number of Xem thêm pages to request after the first page.")
	parser.add_argument("--no-details", action="store_true", help="Skip fetching article detail pages.")
	parser.add_argument("--delay", type=float, default=0.0, help="Delay in seconds between article requests.")
	parser.add_argument("--stdout", action="store_true", help="Print JSON to stdout instead of writing file.")
	return parser


def write_output(data: dict[str, Any], output_path: Path, *, to_stdout: bool = False) -> None:
	if to_stdout:
		json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
		sys.stdout.write("\n")
		return

	output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
	if hasattr(sys.stdout, "reconfigure"):
		sys.stdout.reconfigure(encoding="utf-8")

	parser = build_parser()
	args = parser.parse_args()

	result = crawl_section(
		args.section_url,
		max_items=args.max_items,
		crawl_details=not args.no_details,
		delay=args.delay,
		max_viewmore_pages=args.max_viewmore_pages,
	)
	output_path = Path(__file__).resolve().parent.parent / DEFAULT_OUTPUT
	write_output(result, output_path, to_stdout=args.stdout)

	if not args.stdout:
		print(f"Saved {result['item_count']} items to {output_path}")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
