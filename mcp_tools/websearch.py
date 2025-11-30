import utils
import asyncio
import urllib

from mcp_tools import reader

async def search_web(query: str, purpose: str, memory: str, limit: int = 4):
    """
    search the web for a query. uses read_path internally to process the resulting page.

    use the "purpose" argument to describe the purpose of this request.
    use the "memory" argument for details that must be remembered by the LLM after parsing all the data, such as details about the user.
    use the "limit" argument to specify how many results to fetch. defaults to 4.
    """

    url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"

    html = await utils.http_request(url)

    output = []

    import re
    from bs4 import BeautifulSoup

    soup = await asyncio.to_thread(BeautifulSoup, html, "html.parser")

    urls = []

    headers = []
    for header in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        headers.append(header.get_text().strip())

    for a in soup.find_all("a", href=True):
        urls.append(a["href"])

    urls = utils.remove_duplicates(urls)

    processed_urls = []
    for url in urls:
        # get rid of duckduckgo's garbage
        url = url.replace("//duckduckgo.com", "")
        url = url.replace("/l/?uddg=", "")

        url = urllib.parse.unquote(url)

        # more garbage
        url = url.split("&rut")[0]

        if (
            url in ["/html/", "/feedback.html"] or
            "/duckduckgo-help-pages/" in url or
            url.startswith("https://duckduckgo.com")
        ):
            # seriously wtf duckduckgo why all the spam?
            continue

        processed_urls.append(url)

    searchresults = await reader.read_multiple_files_or_urls(
        # limit amount of results returned
        processed_urls[:limit], purpose, memory
    )

    return {
        "results": searchresults,
        "important_details": memory,
        "purpose_of_request": purpose
    }

def register_mcp(mcp):
    mcp.tool(search_web)
