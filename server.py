import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from html2text import html2text

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request 
from starlette.routing import Route, Mount

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError 
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS
from mcp.server.sse import SseServerTransport

mcp = FastMCP("wiki")

@mcp.tool()
def read_wikipedia_article(url: str) -> str:
    """
    Fetch a Wikipedia article at the provided URL, parse its main content, 
    convert it to Markdown, and return it.

    Usage:
        read_wikipedia_article("https://en.wikipedia.org/wiki/Example")
    """
    try:
        if not url.startswith("http"):
            raise ValueError("URL must start with http or https.")

        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            raise McpError(
                ErrorData(
                    INTERNAL_ERROR,
                    f"Failed to fetch the article. HTTP Status code: {response.status_code}"
                )
            )

        soup = BeautifulSoup(response.content, "html.parser")
        content = soup.find("div", {"id": "mw-content-text"})
        if not content:
            raise McpError(
                    ErrorData(
                        INVALID_PARAMS,
                        "Could not find the main content of the article. Please check the URL."
                    )
                )
        markdown_text = html2text(str(content))
        return markdown_text

    except ValueError as e:
        raise McpError(ErrorData(INVALID_PARAMS, str(e))) from e 
    except RequestException as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Request error: {str(e)}")) from e
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e

# Set up the SSE Transport for MCP Communication
sse = SseServerTransport("/messages")

async def handle_sse(request: Request) -> None:
    _server = mcp._mcp_server
    async with sse.connect_sse(
        request.scope,      # HTTP request information
        request.receive,    # Receive msg from client
        request._send,      # Send msg to client
    ) as (reader, writer):  # reader - read from client, writer - send to client
        await _server.run(reader, writer, _server.create_initialization_options())

# Create the Starlette app with two endpoints:
# - "/sse": for SSE connection from clients.
# - "/messages/": for handling incoming POST messages.
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages", app=sse.handle_post_message),
    ],
)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000, log_level="info")