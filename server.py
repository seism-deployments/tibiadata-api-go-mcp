from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn
from fastmcp import FastMCP
import httpx
import os
from typing import Optional

mcp = FastMCP("TibiaData API")

BASE_URL = "https://api.tibiadata.com/v4"


@mcp.tool()
async def get_character(name: str) -> dict:
    """Retrieve detailed information about a specific Tibia character by name. Use this when the user wants to look up a player's character stats, level, vocation, guild, achievements, deaths, or other profile information."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/character/{name}", timeout=30.0)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_world(name: str) -> dict:
    """Retrieve information about a specific Tibia game world/server. Use this when the user wants to know about a world's status, player count, location, PvP type, or other world details."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/world/{name}", timeout=30.0)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def list_worlds() -> dict:
    """Retrieve a list of all available Tibia game worlds/servers. Use this when the user wants to browse all worlds, compare worlds, or find which worlds are currently online."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/worlds", timeout=30.0)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_guild(name: str) -> dict:
    """Retrieve detailed information about a specific Tibia guild including members, ranks, description, and war history. Use this when the user wants to look up a guild's details."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/guild/{name}", timeout=30.0)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def list_guilds_on_world(world: str) -> dict:
    """Retrieve all guilds that exist on a specific Tibia world. Use this when the user wants to browse guilds on a particular server or find active guilds."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/guilds/{world}", timeout=30.0)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_highscores(
    world: str,
    category: str,
    vocation: Optional[str] = "all",
    page: Optional[int] = 1
) -> dict:
    """Retrieve the highscores/leaderboard for a specific Tibia world and category. Use this when the user wants to find top-ranked players by experience, skill, achievements, or other metrics."""
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/highscores/{world}/{category}/{vocation}/{page}"
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_creature(race: str) -> dict:
    """Retrieve information about a specific Tibia creature/monster including stats, loot, and description. Use this when the user wants to look up details about a monster in the game."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/creature/{race}", timeout=30.0)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_api_info() -> dict:
    """Retrieve metadata and version information about the TibiaData API itself. Use this when the user wants to know the current API version, build details, or to verify the API is running correctly."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/info", timeout=30.0)
        response.raise_for_status()
        return response.json()




async def health(request):
    return JSONResponse({"status": "ok", "server": mcp.name})

async def tools(request):
    registered = await mcp.list_tools()
    tool_list = [{"name": t.name, "description": t.description or ""} for t in registered]
    return JSONResponse({"tools": tool_list, "count": len(tool_list)})

mcp_app = mcp.http_app(transport="streamable-http")

class _FixAcceptHeader:
    """Ensure Accept header includes both types FastMCP requires."""
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            accept = headers.get(b"accept", b"").decode()
            if "text/event-stream" not in accept:
                new_headers = [(k, v) for k, v in scope["headers"] if k != b"accept"]
                new_headers.append((b"accept", b"application/json, text/event-stream"))
                scope = dict(scope, headers=new_headers)
        await self.app(scope, receive, send)

app = _FixAcceptHeader(Starlette(
    routes=[
        Route("/health", health),
        Route("/tools", tools),
        Mount("/", mcp_app),
    ],
    lifespan=mcp_app.lifespan,
))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
