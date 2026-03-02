#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import time
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ATCODER_BASE = "https://atcoder.jp"
HISTORY_ENDPOINT = "/users/{username}/history/json"
USER_PAGE = "/users/{username}"

JST = dt.timezone(dt.timedelta(hours=9), name="JST")

def warn(message: str) -> None:
	yellow = "\033[33m"
	end_color = "\033[0m"
	print(f"{yellow}Warning:{end_color} {message}", file=sys.stderr)

def load_users(users_file: Path) -> list[str]:
	if not users_file.exists():
		raise FileNotFoundError(f"users list not found: {users_file}")

	users: list[str] = []
	for raw_line in users_file.read_text(encoding="utf-8").splitlines():
		# "#"以降の文字列をコメントとして扱うため、最も前にある"#"から先を削除する。
		line = raw_line.split("#", 1)[0].strip()
		if not line:
			continue
		# AtCoderのユーザ名は3 文字以上 16 文字以下の半角英数字とアンダースコアのみで構成されるため、これら以外の文字が含まれる行は無視する。
		if not re.fullmatch(r"[A-Za-z0-9_]{3,16}", line):
			warn(f"Invalid username skipped: \"{line}\"")
			continue
		users.append(line)
	return users


def safe_widget_filename(username: str) -> str:
	# Prevent path traversal and keep filenames portable.
	safe = re.sub(r"[^A-Za-z0-9_-]", "_", username)
	if safe in {"", ".", ".."}:
		safe = "user"
	return f"{safe}.html"


def fetch_json(url: str) -> Any:
	req = urllib.request.Request(
		url,
		headers={
			"User-Agent": "AtCoder-Rating-Widget/1.0 (+https://github.com/r-1317/AtCoder-Rating-Widget)",
			"Accept": "application/json",
		},
	)
	with urllib.request.urlopen(req, timeout=30) as resp:
		data = resp.read()
	return json.loads(data.decode("utf-8"))


def get_latest_rating(history_json: Any) -> int | None:
	if not isinstance(history_json, list) or len(history_json) == 0:
		return None
	last = history_json[-1]
	if not isinstance(last, dict):
		return None
	new_rating = last.get("NewRating")
	if isinstance(new_rating, int):
		return new_rating
	return None


def rating_to_class(rating: int | None) -> str:
	if rating is None:
		return "acrw-rating--black"
	# "任意色"の扱いが不明瞭なため、範囲外は赤扱い。
	if rating >= 2800:
		return "acrw-rating--red"
	if rating >= 2400:
		return "acrw-rating--orange"
	if rating >= 2000:
		return "acrw-rating--yellow"
	if rating >= 1600:
		return "acrw-rating--blue"
	if rating >= 1200:
		return "acrw-rating--cyan"
	if rating >= 800:
		return "acrw-rating--green"
	if rating >= 400:
		return "acrw-rating--brown"
	if rating >= 0:
		return "acrw-rating--gray"
	return "acrw-rating--red"


def rating_text(rating: int | None) -> str:
	return "No Rating" if rating is None else str(rating)


def rating_to_chevron_src(rating: int | None, chevrons_href: str) -> str | None:
	"""Return chevron image src for the given rating.

	Rules (per 何がしたいか.md):
	- Show chevrons for gray/brown/green/cyan/blue/yellow/orange only.
	- Do not show for black (None/0) and red (>=2800 or out-of-range treated as red).
	- Increment chevron number every 100 rating points within each color band.
	"""
	if rating is None:
		return None
	if rating < 0:
		return None
	if rating >= 2800:
		return None

	color: str
	base: int
	if rating >= 2400:
		color, base = "orange", 2400
	elif rating >= 2000:
		color, base = "yellow", 2000
	elif rating >= 1600:
		color, base = "blue", 1600
	elif rating >= 1200:
		color, base = "cyan", 1200
	elif rating >= 800:
		color, base = "green", 800
	elif rating >= 400:
		color, base = "brown", 400
	elif rating >= 0:
		# Gray band is 0..399.
		color, base = "gray", 0
	else:
		return None

	number = (rating - base) // 100 + 1
	if number < 1:
		return None
	if number > 4:
		number = 4
	return f"{chevrons_href}/user-{color}-{number}.png"


def build_history_url(username: str, contest_type: str | None) -> str:
	url = f"{ATCODER_BASE}{HISTORY_ENDPOINT.format(username=username)}"
	if contest_type is None:
		return url
	return f"{url}?contestType={contest_type}"


def build_user_url(username: str, contest_type: str | None) -> str:
	url = f"{ATCODER_BASE}{USER_PAGE.format(username=username)}"
	if contest_type is None:
		return url
	return f"{url}?contestType={contest_type}"


def render_widget_html(
	username: str,
	algorithm_rating: int | None,
	heuristic_rating: int | None,
	updated_at_utc: dt.datetime,
	css_href: str,
	chevrons_href: str,
) -> str:
	updated_at_jst = updated_at_utc.astimezone(JST)
	updated_str = updated_at_jst.strftime("%Y-%m-%d %H:%M JST")
	user_url = build_user_url(username, None)
	about_url = "https://github.com/r-1317/AtCoder-Rating-Widget"
	heur_url = build_user_url(username, "heuristic")

	alg_class = rating_to_class(algorithm_rating)
	heur_class = rating_to_class(heuristic_rating)
	chevron_src = rating_to_chevron_src(algorithm_rating, chevrons_href)
	chevron_html = (
		f'<img class="acrw-chevron" src="{chevron_src}" alt="" width="16" height="16" /> '
		if chevron_src
		else ""
	)

	return """<!doctype html>
<html lang=\"ja\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <link rel=\"stylesheet\" href=\"{css_href}\" />
    <title>AtCoder Rating Widget - {username}</title>
  </head>
  <body>
    <div class=\"acrw-widget\" role=\"group\" aria-label=\"AtCoder rating widget\">

			<a class=\"acrw-user-link\" href=\"{user_url}\" target=\"_blank\" rel=\"noopener noreferrer\" aria-label=\"Open AtCoder user page\">
				<div class=\"acrw-header {alg_class}\">{chevron_html}{username}</div>
			</a>

      <div class=\"acrw-ratings\">

			<a class=\"acrw-alg-link\" href=\"{user_url}\" target=\"_blank\" rel=\"noopener noreferrer\" aria-label=\"Open AtCoder algorithm page\">
				<div class=\"acrw-block\" aria-label=\"Algorithm rating\">
				  <span class=\"acrw-label\">Algorithm</span>
				  <span class=\"acrw-rating {alg_class}\">{alg_text}</span>
				</div>
			</a>

        <a class=\"acrw-heur-link\" href=\"{heur_url}\" target=\"_blank\" rel=\"noopener noreferrer\" aria-label=\"Open AtCoder heuristic page\">
          <div class=\"acrw-block\" aria-label=\"Heuristic rating\">
            <span class=\"acrw-label\">Heuristic</span>
            <span class=\"acrw-rating {heur_class}\">{heur_text}</span>
          </div>
        </a>
      </div>


			<div class=\"acrw-updated\">
				<span>更新日時: {updated_str}</span>
				<a class=\"acrw-about\" href=\"{about_url}\" target=\"_blank\" rel=\"noopener noreferrer\">About</a>
			</div>
    </div>
  </body>
</html>
""".format(
		css_href=css_href,
		username=username,
		user_url=user_url,
		heur_url=heur_url,
		about_url=about_url,
		alg_class=alg_class,
		heur_class=heur_class,
		alg_text=rating_text(algorithm_rating),
		heur_text=rating_text(heuristic_rating),
		updated_str=updated_str,
		chevron_html=chevron_html,
	)


def main() -> int:
	parser = argparse.ArgumentParser(description="Generate AtCoder rating widgets")
	parser.add_argument("--users-file", default="users-list", help="Path to users list file")
	parser.add_argument("--out-dir", default="widgets", help="Output directory")
	parser.add_argument(
		"--css-href",
		default="../widget.css",
		help="CSS href written into widget HTML (relative to each widget file)",
	)
	parser.add_argument(
		"--chevrons-href",
		default="../chevrons",
		help="Chevrons directory href used in widget HTML (relative to each widget file)",
	)
	parser.add_argument(
		"--sleep-seconds",
		type=float,
		default=1.0,
		help="Sleep duration after each request to AtCoder",
	)
	args = parser.parse_args()

	users_file = Path(args.users_file)
	out_dir = Path(args.out_dir)
	out_dir.mkdir(parents=True, exist_ok=True)

	users = load_users(users_file)
	updated_at_utc = dt.datetime.now(dt.UTC)

	for username in users:
		algo_rating: int | None
		heur_rating: int | None

		try:
			algo_json = fetch_json(build_history_url(username, None))
			algo_rating = get_latest_rating(algo_json)
		except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
			algo_rating = None
		time.sleep(args.sleep_seconds)

		try:
			heur_json = fetch_json(build_history_url(username, "heuristic"))
			heur_rating = get_latest_rating(heur_json)
		except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
			heur_rating = None
		time.sleep(args.sleep_seconds)

		html = render_widget_html(
			username=username,
			algorithm_rating=algo_rating,
			heuristic_rating=heur_rating,
			updated_at_utc=updated_at_utc,
			css_href=args.css_href,
			chevrons_href=args.chevrons_href,
		)

		(out_dir / safe_widget_filename(username)).write_text(html, encoding="utf-8")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
