from util import settings
import logging
import aiosqlite
from util.settings import SQLITE_DB_PATH


async def execute_sql(sql_str: str, fetch=False, *args):
    logging.info("Opening a connection...")
    logging.info(f"SQLite DB path: {SQLITE_DB_PATH}")  # update your settings accordingly
    res = None

    try:
        async with aiosqlite.connect(SQLITE_DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row  # so results come back as dict-like
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
