import logging
from mysql.connector import Error
from mysql.connector import pooling

from conf.config import Config

logger = logging.getLogger(Config.__mysql__)
logger.setLevel(logging.DEBUG)


class des_connector:

    def __init__(self, pool_name, db_name, user_name, host_name, host_port, pass_word):

        self.target_cnxpool = pooling.MySQLConnectionPool(pool_name=pool_name,
                                                          pool_size=3,
                                                          pool_reset_session=False,
                                                          host=host_name,
                                                          database=db_name,
                                                          port=host_port,
                                                          autocommit=True,
                                                          user=user_name,
                                                          password=pass_word)

    def get_last_id(self, table):
        try:
            sql = '''select id from %s order by id desc limit 1''' % table
            conn = self.target_cnxpool.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return int(rows[0][0])
        except Error as err:
            logger.error("Error: %d:%s" % (err.args[0], err.args[1]))
        finally:
            cursor.close()
            conn.close()
