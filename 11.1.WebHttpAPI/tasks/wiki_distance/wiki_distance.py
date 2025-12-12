import typing as tp
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
import requests
import bs4


# Directory to save your .json files to
# NB: create this directory if it doesn't exist
SAVED_JSON_DIR = Path(__file__).parent / 'visited_paths'

def _name(url: str) -> str:
    p = urlparse(url).path
    return unquote(p.split("/wiki/", 1)[-1] if "/wiki/" in p else p.lstrip("/"))


def _soup(url: str) -> tp.Optional[bs4.BeautifulSoup]:
    try:
        r = requests.get(url)
        r.raise_for_status()
        return bs4.BeautifulSoup(r.text, "html.parser")
    except requests.exceptions.RequestException:
        return None

def _first_p(s: bs4.BeautifulSoup) -> tp.Optional[bs4.Tag]:
    root = s.find("div", id="mw-content-text")
    root = (root.find("div", class_="mw-parser-output") if root else None) or root
    if not root:
        return None

    def good(p: bs4.Tag) -> bool:
        return ("mw-empty-elt" not in (p.get("class") or [])) and (p.get_text(" ", strip=True) != "")

    for p in root.find_all("p", recursive=False):
        if good(p):
            return p
    return None

def _wiki_links(paragraph: bs4.Tag, base: str) -> list[str]:
    out = []
    for a in paragraph.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("/wiki/"):
            continue
        href = href.split("#", 1)[0]
        if href and ":" not in href[6:]:
            out.append(urljoin(base, href))
    return out

def _title(s: bs4.BeautifulSoup) -> str:
    t = s.title.string if s.title else ""
    return (t.split(" — ")[0].strip() if t else "")


def distance(source_url: str, target_url: str) -> int | None:
    """Amount of wiki articles which should be visited to reach the target one
    starting from the source url. Assuming that the next article is choosing
    always as the very first link from the first article paragraph (tag <p>).
    If the article does not have any paragraph tags or any links in the first
    paragraph then the target is considered unreachable and None is returned.
    If the next link is pointing to the already visited article, it should be
    discarded in favor of the second link from this paragraph. And so on
    until the first not visited link will be found or no links left in paragraph.
    NB. The distance between neighbour articles (one is pointing out to the other)
    assumed to be equal to 1.
    :param source_url: the url of source article from wiki
    :param target_url: the url of target article from wiki
    :return: the distance calculated as described above
    """
    source_url = source_url.split("#", 1)[0]
    target_url = target_url.split("#", 1)[0]
    base = f"{urlparse(source_url).scheme}://{urlparse(source_url).netloc}"

    seen = set()
    trail = []
    curr = source_url
    dist = 0

    while curr not in seen:
        s = _soup(curr)
        if not s:
            return None

        seen.add(curr)

        trail.append({"title" : _title(s)})

        if curr == target_url:
            try:
                SAVED_JSON_DIR.mkdir(parents=True, exist_ok=True)
                (SAVED_JSON_DIR / f"{_name(source_url)}-{_name(target_url)}.json").write_text(
                    json.dumps(trail, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
            except OSError:
                pass
            return dist

        p = _first_p(s)
        if not p:
            return None

        curr = next((u for u in _wiki_links(p, base) if u not in seen), "")
        if not curr:
            return None

        dist += 1

    return None
