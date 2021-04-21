import logging
from mysql.connector import Error
from mysql.connector import pooling

from conf.config import Config

logger = logging.getLogger(Config.__mysql__)
logger.setLevel(logging.DEBUG)


class src_connector:

    def __init__(self, pool_name, user_name, host_name, host_port, pass_word):
        self.src_cnxpool = pooling.MySQLConnectionPool(pool_name=pool_name,
                                                       pool_size=2,
                                                       pool_reset_session=False,
                                                       host=host_name,
                                                       port=host_port,
                                                       autocommit=True,
                                                       user=user_name,
                                                       password=pass_word,
                                                       charset="utf8")

    def is_employee(self, dossier_id, confidence):
        try:
            conn = self.src_cnxpool.get_connection()
            query = '''select count(1) from vcrtimes.face_dossier fd WHERE fd.id = %s 
                and fd.group_id = (select id from vcrtimes.face_dossier_group fdg where fdg.type = 'vcr_employee') 
                and %s >= (select value from vcrtimes.configurations where name = 'FACE_MATCH_THRESHOLD')''' \
                % (dossier_id, confidence)
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            if rows[0][0] > 0:
                logger.debug("_____face_events\t %s \t_____%s" % (dossier_id, confidence))
                return True
            else:
                return False
        except Error as err:
            logger.debug(query + "\t Something went wrong: {}".format(err))
        finally:
            conn.close()
        return None
