from mcp.server.fastmcp import FastMCP
from util.async_db import execute_sql
from typing import List
from util import settings
import logging


# Create an MCP server
mcp = FastMCP("Demo")


@mcp.prompt()
def configure_assistant() -> list[dict]:
    prompt = """
        You are a scheduling assistant. You must ONLY interact with the environment using the following tools:
        - list_booked_appointments_for_client → returns a list booked appointments for a client id
        - cancel_booked_appointment_for_client → cancels booked appointment for a specific client_id, provider_name and slot_number combination
        - get_provider_names → returns a list of available providers
        - get_provider_roles → returns a list of provider roles
        - get_available_booking_slots_for_provider → returns list of 5 earliest available time slots for a provider. 
          response is JSON with a top-level "result" field.
          "result" is a list of dicts, each with:
            - slot_number (integer, sorted ascending)
            - provider_name (string)
            - time_slot (string in 'YYYY-MM-DD HH24:MI:SS' format).

        - book_slot_for_provider → books a client appointment with a provider at a specified slot number.

        STRICT RULES:
        1. NEVER invent, summarize, analyze, or describe provider names, roles, or time slots. 
        2. NEVER generate your own list. ONLY return exactly what the tool output provides inside the "result" field. 
        3. If asked about availability, ALWAYS call get_available_booking_slots_for_provider once per request. 
        4. When booking, ALWAYS use the exact slot_number and provider_name from the tool output.
           ALWAYS call the book_slot_for_provider when booking an appointment. Check that affected return parameter (number of rows updated) from 
           the function call is correct and is 1. Do not circumvent the tool call. Ensure that the database is really updated.
        5. You must not provide totals, summaries, statistics, distributions, or "observations" about slots. 
        6. If asked for a specific slot (e.g. "what is the slot_number for 2024-08-20 10:00:00?"), 
           search the tool output JSON for that exact time_slot and return its slot_number exactly as-is.
    """
    messages = [
        {
            "role": "assistant",
            "content": prompt,
        }
    ]
    return messages


@mcp.tool()
async def cancel_booked_appointment_for_client(
    client_id: str, provider_name: str, slot_number: str
) -> int:
    """
    Cancels a client appointment with a provider at a specific slot number.

    RULES:
    - Inputs (client_id provider_name and slot_number) may come from free-text user input.
    - Ensure that the database is updated"""
    logging.info(
        f"Canceling appointment with : {provider_name} for client : {client_id} at slot : {slot_number}"
    )
    affected = await execute_sql(
        """
                            UPDATE availability
                            SET
                                client_to_attend = '', is_available = True
                            WHERE
                                slot_number = ?
                            AND
                                LOWER(provider_name) = ?
                            AND
                                client_to_attend = ?
                            """,
        False,
        slot_number,
        provider_name.lower(),
        client_id,
    )

    logging.info(f"Rows affected : {affected}")
    return affected


@mcp.tool()
async def get_provider_names() -> List[dict]:
    """returns a list of available providers"""
    logging.info("Getting list of providers ....")
    res = await execute_sql(
        "SELECT DISTINCT provider_name, role FROM AVAILABILITY", True
    )
    providers = [{"provider_name": e["provider_name"], "role": e["role"]} for e in res]
    return providers


@mcp.tool()
async def get_provider_roles() -> List[dict]:
    """returns a list of available provider roles"""
    logging.info("Getting list of provider roles")
    res = await execute_sql("SELECT DISTINCT role FROM AVAILABILITY", True)
    roles = [{"role": e["role"]} for e in res]
    return roles


@mcp.tool()
async def get_available_booking_slots_by_roles(role: str) -> List[dict]:
    """
    Returns the 5 earliest available booking slots for a given provider role.

    Output always includes:
      - slot_number (int, sorted ascending)
      - provider_name (str)
      - time_slot (str in 'YYYY-MM-DD HH24:MI:SS')

    The query is case-insensitive on the role name.
    """
    logging.info(f"Getting open slots for role {role}")
    # Query availability by role, ensuring only open slots are considered
    res = await execute_sql(
        """
        SELECT provider_name,
               slot_number,
               strftime('%Y-%m-%d %H:%M:%S', dt_time_slot) AS time_slot
        FROM AVAILABILITY
        WHERE lower(role) = ?
          AND is_available = True
        ORDER BY slot_number ASC
        LIMIT 5
        """,
        True,
        role.lower(),
    )
    # Normalize to list of dicts
    return [
        {
            "provider_name": row["provider_name"],
            "slot_number": row["slot_number"],
            "time_slot": row["time_slot"],
        }
        for row in res
    ]


@mcp.tool()
async def get_available_booking_slots_for_provider(provider_name: str) -> List[dict]:
    """
    Returns booking 5 earliest time slots for a provider.

    Output is ALWAYS JSON with fields:
      - slot_number (integer, sorted ascending)
      - provider_name (string)
      - time_slot (string, format 'YYYY-MM-DD HH24:MI:SS')
    """
    logging.info(f"Getting open slots for {provider_name}")
    res = await execute_sql(
        """
            SELECT provider_name, slot_number, strftime('%Y-%m-%d %H:%M:%S', dt_time_slot) as time_slot FROM AVAILABILITY
            WHERE lower(provider_name) = ?
            and
            is_available = True
            order by slot_number asc limit (5)""",
        True,
        provider_name.lower(),
    )
    open_slots = [
        {
            "provider_name": e["provider_name"],
            "slot_number": e["slot_number"],
            "time_slot": e["time_slot"],
        }
        for e in res
    ]
    return open_slots


@mcp.tool()
async def book_slot_for_provider(
    provider_name: str, slot_number: str, client_id: str
) -> int:
    """
    Books a client appointment with a provider at a specific slot number.

    RULES:
    - Inputs (provider_name and slot_number) may come from free-text user input.
    - Only book the slot if the inputs exactly match a valid slot returned by
      get_available_booking_slots_for_provider.
    - Ensure that the database is updated"""
    logging.info(
        f"Booking appointment with : {provider_name} for client : {client_id} at slot: {slot_number}"
    )
    affected = await execute_sql(
        """
                            UPDATE availability
                            SET
                                client_to_attend = ?, is_available = False
                            WHERE
                                slot_number = ?
                            AND
                                LOWER(provider_name) = ?
                            """,
        False,
        client_id,
        slot_number,
        provider_name.lower(),
    )
    print(f"Rows affected : {affected}")
    return affected


@mcp.tool()
async def list_booked_appointments_for_client(client_id: str) -> List[dict]:
    """
    Returns a list of booked appointments for a client.
    The list of appointments may be empty if the client has no bookings.

    When the results are not empty, output is always a list of JSON objects with the following fields:
      - client_id: string representing the client's identification number
      - slot_number: integer, sorted in ascending order
      - provider_name: string
      - time_slot: string in the format 'YYYY-MM-DD HH24:MI:SS'
    """
    logging.info(f"Getting booked appointments for client id : {client_id}")
    res = await execute_sql(
        """
            SELECT
                client_to_attend as client_id,
                slot_number,
                provider_name,
                strftime('%Y-%m-%d %H:%M:%S', dt_time_slot) as time_slot
            FROM
                AVAILABILITY
            WHERE
                lower(client_to_attend) = ?
            order by
                slot_number
            asc
                limit (25)""",
        True,
        client_id.lower(),
    )
    booked_list = [
        {
            "client_id": e["client_id"],
            "slot_number": e["slot_number"],
            "provider_name": e["provider_name"],
            "time_slot": e["time_slot"],
        }
        for e in res
    ]
    logging.info(f"Size of booked appointments list: {len(booked_list)}")
    return booked_list


if __name__ == "__main__":
    config_json = settings.get_logging_config(settings.LOG_SETTING_FILE)
    logging.config.dictConfig(config_json)
    logging.info("Running application as main ...")

    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8000
    mcp.settings.stateless_http = True
    mcp.run(transport="sse")
