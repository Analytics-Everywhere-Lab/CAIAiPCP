from mcp.server.fastmcp import FastMCP
from util.async_db import execute_sql
from typing import List
from util import settings
import logging
import datetime


# Create an MCP server
mcp = FastMCP("Demo")


@mcp.tool()
async def get_provider_names() -> List[dict]:
    """returns a list of available providers"""
    logging.info('Getting list of providers ....')
    res = await execute_sql("SELECT DISTINCT provider_name, role FROM AVAILABILITY", True)
    providers = [{"provider_name": e["provider_name"], "role": e["role"]} for e in res]
    return providers


@mcp.tool()
async def get_provider_roles() -> List[dict]:
    """returns a list of available provider roles"""
    logging.info('Getting list of provider roles')
    res = await execute_sql("SELECT DISTINCT role FROM AVAILABILITY", True)
    roles = [{"role": e["role"]} for e in res]
    return roles


@mcp.tool()
async def get_available_booking_slots_for_provider(provider_name: str) -> List[dict]:
    """
    Returns booking 5 earliest time slots for a provider.

    Output is ALWAYS JSON with fields:
      - slot_number (integer, sorted ascending)
      - provider_name (string)
      - time_slot (string, format 'YYYY-MM-DD HH24:MI:SS')
    """
    logging.info(f'Getting open slots for {provider_name}')
    res = await execute_sql(
            """
            SELECT provider_name, slot_number, TO_CHAR(dt_time_slot, 'YYYY-MM-DD HH24:MI:SS') as time_slot FROM AVAILABILITY 
            WHERE lower(provider_name) = %s 
            and 
            is_available = True 
            order by slot_number asc limit (5)""", 
            True, provider_name.lower())
    open_slots = [{"provider_name": e["provider_name"],"slot_number": e["slot_number"], "time_slot": e["time_slot"]} for e in res]
    return open_slots


@mcp.tool()
async def book_slot_for_provider(provider_name: str, time_slot: str, client_id: str) -> int:
    """books a client appoinment with a provider at specified time slot. Time slot is expressed as 'YYYY-MM-DD HH24:MI:SS'"""
    logging.info(f'Booking appointment with : {provider_name} for client : {client_id} on {time_slot}')
    affected = await execute_sql("""
                            UPDATE availability 
                            SET 
                                client_to_attend = %s, is_available = False 
                            WHERE 
                                dt_time_slot = TO_TIMESTAMP(%s, 'YYYY-MM-DD HH24:MI:SS')
                            AND
                                LOWER(provider_name) = %s
                            """, False, client_id, time_slot, provider_name.lower())
    print(f'Rows affected : {affected}')
    return affected


if __name__ == "__main__":
    config_json = settings.get_logging_config(settings.LOG_SETTING_FILE)
    logging.config.dictConfig(config_json)
    logging.info('Running application as main ...')

    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8000
    mcp.settings.stateless_http = True
    mcp.run(transport="sse")
