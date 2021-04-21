import logging
from mysql.connector import Error
from mysql.connector import pooling

from conf.config import Config

logger = logging.getLogger(Config.__mysql__)
logger.setLevel(logging.DEBUG)


class connector:

    def __init__(self, pool_name, db_name, user_name, host_name, host_port, pass_word):
        self.cnxpool = pooling.MySQLConnectionPool(pool_name=pool_name,
                                                   pool_size=2,
                                                   pool_reset_session=False,
                                                   host=host_name,
                                                   port=host_port,
                                                   database=db_name,
                                                   autocommit=True,
                                                   user=user_name,
                                                   password=pass_word)
        print('Connect to sql success full')

    def get_camera_url(self, cam_id):
        conn = self.cnxpool.get_connection()
        try:
            cursor = conn.cursor()
            sql = "select url from camera where id = %s"
            cursor.execute(sql, (cam_id,))
            results = cursor.fetchall()
            if not results:
                return results[0]

        except Error as err:
            logger.debug(sql + "\t Something went wrong: {}".format(err))
        finally:
            conn.close()
        return None
