import os
import re
import html
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit

import requests
import markdown
import bleach

OWNER = "hofman0107-cell"
REPO = "window-repair-journal-cloudflare"
SITE_NAME = "Window Repair Journal"

# Temporary domain until the new Cloudflare Pages
# project receives its final address.
SITE_URL = os.getenv(
    "SITE_URL",
    "https://window-repair-journal-cloudflare.pages.dev"
).rstrip("/")

API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
    "X-GitHub-Api-Version": "2022-11-28",
}

OUTPUT = Path("site")
ARTICLES = OUTPUT / "articles"
ARTICLES.mkdir(parents=True, exist_ok=True)


def escape(value):
    return html.escape(str(value or ""), quote=True)


def valid_attribute(tag, name, value):
    allowed = {
        "a": {"href", "title"},
        "img": {"src", "alt", "title", "width", "height"},
        "td": {"colspan", "rowspan"},
        "th": {"colspan", "rowspan"},
    }

    if name not in allowed.get(tag, set()):
        return False

    if name in ("href", "src"):
        parsed = urlsplit(value.strip())
        return parsed.scheme.lower() in ("http", "https") or (
            not parsed.scheme
            and not parsed.netloc
            and (
                value.startswith("/")
                and not value.startswith("//")
                or value.startswith("#")
            )
        )

    return True


def render_content(body):
    rendered = markdown.markdown(
        body or "",
        extensions=["extra", "sane_lists", "nl2br"],
    )

    return bleach.clean(
        rendered,
        tags=[
            "p", "br", "h1", "h2", "h3", "h4",
            "strong", "b", "em", "i", "a", "img",
            "ul", "ol", "li", "blockquote",
            "code", "pre", "hr", "table", "thead",
            "tbody", "tr", "td", "th", "del",
        ],
        attributes=valid_attribute,
        protocols=["http", "https"],
        strip=True,
    )


def plain_text(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def description_for(content, title):
    text = plain_text(content)
    if not text:
        text = title
    return text[:155].rsplit(" ", 1)[0] or text[:155]


CSS = """
:root {
  --navy: #203c57;
  --gold: #d5b27c;
  --paper: #f5f3ef;
  --ink: #24364a;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font: 16px/1.8 Arial, sans-serif;
}
header, footer {
  background: var(--navy);
  color: white;
}
.nav {
  max-width: 1040px;
  margin: auto;
  padding: 22px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}
.nav a { color: white; text-decoration: none; }
.brand { font-size: 20px; font-weight: 700; }
nav a { margin-left: 20px; }
.hero {
  background: var(--navy);
  color: white;
  padding: 75px 24px;
}
.hero-inner { max-width: 1040px; margin: auto; }
.eyebrow {
  color: var(--gold);
  font-weight: bold;
  letter-spacing: 2px;
  font-size: 12px;
}
.hero h1 {
  font-size: clamp(32px, 5vw, 48px);
  line-height: 1.2;
  max-width: 700px;
}
.container {
  max-width: 1040px;
  margin: 45px auto;
  padding: 0 24px;
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}
.card, .article {
  background: white;
  border: 1px solid #e8e2d9;
  border-radius: 12px;
  padding: 28px;
}
.card::before {
  content: "";
  display: block;
  width: 40px;
  height: 3px;
  background: var(--gold);
  margin-bottom: 20px;
}
.card h2 { font-size: 21px; line-height: 1.4; }
.card a, .article a { color: var(--navy); }
.card p { color: #63758a; }
time { color: #66788a; font-size: 14px; }
.article { max-width: 850px; margin: 45px auto; }
.article h1 { font-size: clamp(28px, 4vw, 40px); }
.article img { max-width: 100%; height: auto; }
.article-content { overflow-wrap: anywhere; }
.article-content h2, .article-content h3 {
  margin-top: 30px;
}
.article-content blockquote {
  border-left: 4px solid var(--gold);
  padding: 10px 20px;
  background: var(--paper);
}
.article-content table {
  display: block;
  overflow-x: auto;
  border-collapse: collapse;
}
.article-content td, .article-content th {
  border: 1px solid #ddd;
  padding: 10px;
}
.article-content pre { overflow-x: auto; }
footer { text-align: center; padding: 25px; }
@media(max-width:600px) {
  .nav { flex-direction: column; }
  nav a { margin: 0 10px; }
  .hero { padding: 45px 24px; }
  .article { margin: 15px; padding: 22px; }
}
"""


def layout(title, description, canonical, content,
           page_type="website"):
    full_title = f"{title} | {SITE_NAME}"
    year = datetime.now(timezone.utc).year

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(full_title)}</title>
<meta name="description" content="{escape(description)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{escape(canonical)}">
<meta property="og:type" content="{escape(page_type)}">
<meta property="og:site_name" content="{escape(SITE_NAME)}">
<meta property="og:title" content="{escape(full_title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{escape(canonical)}">
<style>{CSS}</style>
</head>
<body>
<header>
<div class="nav">
<a class="brand" href="{SITE_URL}/">{escape(SITE_NAME)}</a>
<nav>
<a href="{SITE_URL}/">Home</a>
<a href="{SITE_URL}/#articles">Articles</a>
</nav>
</div>
</header>
{content}
<footer>
&copy; {year} {escape(SITE_NAME)} · Practical guides for homeowners
</footer>
</body>
</html>"""


def get_issues():
    issues = []
    page = 1

    while True:
        response = requests.get(
            API_URL,
            headers=HEADERS,
            params={
                "state": "open",
                "per_page": 100,
                "page": page,
                "sort": "created",
                "direction": "desc",
            },
            timeout=30,
        )
        response.raise_for_status()
        batch = response.json()

        if not batch:
            break

        issues.extend(
            item for item in batch
            if "pull_request" not in item
        )
        page += 1

    return issues


def publish():
    issues = get_issues()
    cards = []
    urls = [f"{SITE_URL}/"]
    active = set()

    for issue in issues:
        number = issue["number"]
        title = issue.get("title") or "Untitled"
        body = issue.get("body") or ""
        date = issue["created_at"][:10]
        filename = f"issue-{number}.html"
        active.add(filename)

        url = f"{SITE_URL}/articles/{filename}"
        content = render_content(body)
        desc = description_for(content, title)

        article = f"""
<main class="article">
<article>
<h1>{escape(title)}</h1>
<p><time datetime="{date}">{date}</time></p>
<div class="article-content">{content}</div>
</article>
</main>
"""

        page_html = layout(
            title, desc, url, article, "article"
        )

        (ARTICLES / filename).write_text(
            page_html, encoding="utf-8"
        )

        cards.append(f"""
<article class="card">
<time datetime="{date}">{date}</time>
<h2>{escape(title)}</h2>
<p>{escape(desc)}</p>
<a href="articles/{filename}">Read article →</a>
</article>
""")
        urls.append(url)

    for old in ARTICLES.glob("issue-*.html"):
        if old.name not in active:
            old.unlink()

    homepage = f"""
<section class="hero">
<div class="hero-inner">
<p class="eyebrow">WINDOW CARE &amp; MAINTENANCE</p>
<h1>Practical Window Care &amp; Repair Guides</h1>
<p>Clear, useful articles on window repair,
glass maintenance, and everyday home comfort.</p>
</div>
</section>
<main class="container" id="articles">
<h2>Latest Articles</h2>
<div class="cards">
{''.join(cards) if cards else '<p>No articles published yet.</p>'}
</div>
</main>
"""

    (OUTPUT / "index.html").write_text(
        layout(
            "Home",
            "Practical window repair, glass care, and maintenance guides.",
            f"{SITE_URL}/",
            homepage,
        ),
        encoding="utf-8",
    )

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap.append(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    )

    for url in urls:
        sitemap.append(
            f"<url><loc>{escape(url)}</loc></url>"
        )

    sitemap.append("</urlset>")

    (OUTPUT / "sitemap.xml").write_text(
        "\n".join(sitemap),
        encoding="utf-8",
    )

    (OUTPUT / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )

    print(f"Published {len(issues)} articles.")


if __name__ == "__main__":
    publish()
