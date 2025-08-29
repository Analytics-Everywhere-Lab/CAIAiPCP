import logging
import aiosqlite
from util.settings import SQLITE_DB_PATH


def expand_sql(sql_str, params):
    """
    Safely expand SQL string with parameters for debugging/logging only.
    """
    parts = sql_str.split("?")
    out = []
    for i, part in enumerate(parts[:-1]):
        out.append(part)
        val = params[i]
        if val is None:
            out.append("NULL")
        elif isinstance(val, str):
            out.append("'" + val.replace("'", "''") + "'")
        else:
            out.append(str(val))
    out.append(parts[-1])
    return "".join(out)


async def execute_sql(sql_str: str, fetch=False, *args):
    logging.info("Opening a connection...")
    logging.info(f"SQLite DB path: {SQLITE_DB_PATH}")  # update your settings accordingly
    res = None

    try:
        async with aiosqlite.connect(SQLITE_DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row  # so results come back as dict-like
            logging.info(f'SQL string : {expand_sql(sql_str, args)}')

            async with conn.execute(sql_str, args) as cursor:
                logging.getLogger().info("Executing SQL command ...")

                if fetch:
                    logging.getLogger().info("Assembling results ...")
                    rows = await cursor.fetchall()
                    res = [dict(row) for row in rows]
                else:
                    res = cursor.rowcount

            await conn.commit()
    except BaseException as e:
        logging.getLogger().error(f"Exception occurred {e}. Rolling back transaction.")
        # Rollback only makes sense inside the context manager
        async with aiosqlite.connect(SQLITE_DB_PATH) as conn:
            await conn.rollback()
    finally:
        logging.getLogger().info("Closing connection")

    return res


if __name__ == '__main__':
    pass
