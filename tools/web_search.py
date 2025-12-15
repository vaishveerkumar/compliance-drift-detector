"""
Web search tool - restricted to official government sources only
"""

from ddgs import DDGS


# Only allow official sources
ALLOWED_DOMAINS = [
    "irs.gov",
    "dol.gov",
    "federalregister.gov",
    "congress.gov",
    "ecfr.gov",
    "govinfo.gov"
]


def search_official_sources(query: str, max_results: int = 5) -> list[dict]:
    site_filter = " OR ".join([f"site:{domain}" for domain in ALLOWED_DOMAINS])
    restricted_query = f"{query} ({site_filter})"

    sources = []

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(restricted_query, max_results=max_results))

        for r in results:
            url = r.get("href", "")
            if any(domain in url for domain in ALLOWED_DOMAINS):
                sources.append({
                    "title": r.get("title", "Official source"),
                    "url": url,
                    "snippet": r.get("body", "")
                })

        return sources

    except Exception as e:
        return [{
            "title": "Web search error",
            "url": "",
            "snippet": str(e)
        }]
