from mcp.server.fastmcp import FastMCP
from util.async_db import execute_sql
from typing import List
from util import settings
import logging


# Create an MCP server
mcp = FastMCP("Demo")


@mcp.tool()
async def get_provider_names() -> List[dict]:
    """returns a list of available providers"""
    res = await execute_sql("SELECT DISTINCT provider_name, role FROM AVAILABILITY", True)
    providers = [{"provider_name": e["provider_name"], "role": e["role"]} for e in res]
    return providers


@mcp.tool()
async def get_provider_roles() -> List[dict]:
    """returns a list of available provider roles"""
    res = await execute_sql("SELECT DISTINCT role FROM AVAILABILITY", True)
    roles = [{"role": e["role"]} for e in res]
    return roles


@mcp.tool()
async def get_available_slots_by_provider(provider_name: str) -> List[dict]:
    """returns a list of available / open provider time slots"""
    res = await execute_sql("SELECT dt_time_slot FROM AVAILABILITY WHERE lower(provider_name) = %s and is_available = True", True, provider_name.lower())
    roles = [{"available_time_slot": e["dt_time_slot"]} for e in res]
    return roles


@mcp.tool()
async def book_slot_for_provider(provider_name: str, time_slot: str, client_id: str) -> int:
    """books client appoinment with provider at specified time slot"""
    affected = await execute_sql("""
                            UPDATE availability 
                            SET 
                                patient_to_attend = %s, is_available = False 
                            WHERE 
                                dt_time_slot = TO_TIMESTAMP(%s, 'YYYY-MM-DD HH24:MI:SS')
                            AND
                                LOWER(provider_name) = %s
                            """, False, client_id, time_slot, provider_name.lower())
    print(f'Rows affected : {affected}')
    return 1
    # return affected


if __name__ == "__main__":
    config_json = settings.get_logging_config(settings.LOG_SETTING_FILE)
    logging.config.dictConfig(config_json)
    logging.info('Running application as main ...')

    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8000
    mcp.settings.stateless_http = True
    mcp.run(transport="sse")
