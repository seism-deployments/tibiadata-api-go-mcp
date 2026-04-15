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
async def get_character(character_name: str) -> dict:
    """Retrieve detailed information about a specific Tibia character by name, including their level, vocation, world, guild membership, achievements, and other profile data. Use this when the user asks about a specific player or character in Tibia."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/character/{character_name}",
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_world(world_name: str) -> dict:
    """Retrieve information about a specific Tibia game world, including online player count, world type (PvP/non-PvP), location, and other world details. Use this when the user asks about a particular Tibia game server or world."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/world/{world_name}",
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def list_worlds() -> dict:
    """Retrieve a list of all available Tibia game worlds, including their status, player counts, and world types. Use this when the user wants to see all game servers or compare worlds."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/worlds",
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_guild(guild_name: str) -> dict:
    """Retrieve detailed information about a specific Tibia guild, including its members, ranks, description, and founding date. Use this when the user asks about a guild or organization in Tibia."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/guild/{guild_name}",
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_highscores(
    world: str,
    category: str,
    vocation: Optional[str] = "all",
    page: Optional[int] = 1
) -> dict:
    """Retrieve highscore rankings for a specific Tibia world and category such as experience, magic level, skills, achievements, or other leaderboards. Use this when the user wants to see top-ranked players.

    Args:
        world: The Tibia world name to get highscores for, or 'all' for global rankings
        category: The highscore category (e.g., 'experience', 'magiclevel', 'fist', 'club', 'sword', 'axe', 'distance', 'shielding', 'fishing', 'achievements', 'loyalty')
        vocation: Filter by vocation: 'all', 'knight', 'paladin', 'sorcerer', 'druid', or 'none' (rookgaard)
        page: Page number for paginated results (each page contains 50 entries)
    """
    voc = vocation if vocation else "all"
    pg = page if page else 1
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/highscores/{world}/{category}/{voc}/{pg}",
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_news(
    news_id: Optional[int] = None,
    days: Optional[int] = 90
) -> dict:
    """Retrieve the latest Tibia news articles, tickers, or news archive entries from the official Tibia website. Use this when the user wants to know about recent Tibia game updates, events, or announcements.

    Args:
        news_id: Specific news article ID to retrieve. If omitted, returns a list of recent news.
        days: Number of past days to include in the news archive list (used when news_id is not specified)
    """
    async with httpx.AsyncClient() as client:
        if news_id is not None:
            response = await client.get(
                f"{BASE_URL}/news/id/{news_id}",
                timeout=30.0
            )
        else:
            d = days if days else 90
            response = await client.get(
                f"{BASE_URL}/news/archive/{d}",
                timeout=30.0
            )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_creature(creature_name: str) -> dict:
    """Retrieve information about a specific Tibia creature or monster from the creature library, including hit points, experience, loot, and other stats. Use this when the user asks about a monster or creature in Tibia."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/creature/{creature_name}",
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_spell(spell_identifier: str) -> dict:
    """Retrieve information about a specific Tibia spell, including its mana cost, level requirement, vocation restrictions, and effect. Use this when the user asks about spells or magic in Tibia."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/spell/{spell_identifier}",
            timeout=30.0
        )
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
