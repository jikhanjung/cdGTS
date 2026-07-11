"""
Crossref metadata lookup — autofill Reference fields from a DOI (stdlib only, no extra deps).

A thin read-only proxy over api.crossref.org used by the "Fetch from DOI" affordance in the editor
inspector and the Bibliography registry. Maps a Crossref work record to our Reference field shape.
"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request

CROSSREF_API = "https://api.crossref.org/works/"
# Crossref's 'polite pool' asks callers to identify themselves (with a contact) in the User-Agent.
USER_AGENT = "cdGTS/1.0 (+https://cdgts.paleobytes.info; mailto:honestjung@gmail.com)"
TIMEOUT = 8

_TYPE_MAP = {
    "journal-article": "article",
    "proceedings-article": "article",
    "book": "book",
    "monograph": "book",
    "reference-book": "book",
    "book-chapter": "chapter",
    "dataset": "dataset",
    "report": "report",
}


class CrossrefError(Exception):
    """Lookup failure carrying the HTTP status the API view should surface."""

    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def normalize_doi(doi):
    """Strip a leading https://doi.org/ (or dx.doi.org) and surrounding whitespace."""
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", (doi or "").strip(), flags=re.I)


def _format_authors(authors):
    """Crossref author list → 'Family, G., Family2 & Family3' (matches the seed convention)."""
    names = []
    for a in authors or []:
        fam = (a.get("family") or "").strip()
        given = (a.get("given") or "").strip()
        if fam and given:
            names.append(f"{fam}, {given[0]}.")
        elif fam:
            names.append(fam)
        elif a.get("name"):
            names.append(a["name"].strip())
    if len(names) > 1:
        return ", ".join(names[:-1]) + " & " + names[-1]
    return names[0] if names else ""


def _year(msg):
    for key in ("issued", "published", "published-print", "published-online", "created"):
        parts = (msg.get(key) or {}).get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            return int(parts[0][0])
    return None


def _suggest_slug(msg, doi):
    """firstauthor-year (lowercased, hyphenated) — a starting point the user can edit."""
    fam = next((a["family"] for a in msg.get("author") or [] if a.get("family")), "")
    year = _year(msg)
    base = re.sub(r"[^a-z0-9]+", "-", (fam or doi).lower()).strip("-")
    return f"{base}-{year}" if year else base


def fetch_crossref(doi):
    """Look up a DOI on Crossref → dict of Reference fields (+ suggested_slug). Raises CrossrefError."""
    doi = normalize_doi(doi)
    if not doi:
        raise CrossrefError("A DOI is required.", status=400)
    req = urllib.request.Request(
        CROSSREF_API + urllib.parse.quote(doi),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise CrossrefError(f"DOI not found on Crossref: {doi}", status=404)
        raise CrossrefError(f"Crossref returned an error ({e.code}).", status=502)
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        raise CrossrefError(f"Could not reach Crossref: {e}", status=502)

    msg = payload.get("message") or {}
    title = next((t for t in (msg.get("title") or []) if t), "")
    container = next((c for c in (msg.get("container-title") or []) if c), "")
    return {
        "doi": (msg.get("DOI") or doi).lower(),
        "title": title,
        "authors": _format_authors(msg.get("author")),
        "year": _year(msg),
        "container": container,
        "kind": _TYPE_MAP.get(msg.get("type"), "article"),
        "suggested_slug": _suggest_slug(msg, doi),
    }
