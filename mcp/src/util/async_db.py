import psycopg
from util import settings
import logging
from pgvector.psycopg import register_vector_async


async def execute_sql(sql_str: str, fetch=False, *args):
    logging.info('Opening a connection...')
    logging.info(f'Connection string : {settings.PSYCOPG_DB_CONN_STR}')
    conn = await psycopg.AsyncConnection.connect(settings.PSYCOPG_DB_CONN_STR)
    # Enable the pgvector extension and register vector types
    await register_vector_async(conn)
    res = None
    try:
        # use the connection
        logging.getLogger().info('Executing SQL command ...')
        cursor = conn.cursor()
        await cursor.execute(sql_str, args)
        if fetch :
            logging.getLogger().info('Assembling results ...')
            res = [
                    dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in await cursor.fetchall()
            ]
        else:
            res = cursor.rowcount

        await cursor.close()
        # commit the transaction
        await conn.commit()
    except BaseException as e:
        logging.getLogger().error(f'Exception occured {e}. Rolling back transaction.')
        await conn.rollback()
    finally:
        logging.getLogger().info('Closing connection')
        # We must always close our connection
        await conn.close()
    return res


if __name__ == '__main__':
    pass
