import pyodbc
import pandas as pd
import time
from conf.config import Config
import logging

logger = logging.getLogger(Config.__mysql__)
logger.setLevel(logging.DEBUG)


class SQLServer():
    def __init__(self, SERVER, DATABASE, UID, PWD, DRIVER='ODBC Driver 17 for SQL Server'):
        self.SERVER = SERVER
        self.DATABASE = DATABASE
        self.DRIVER = DRIVER
        self.UID = UID
        self.PWD = PWD
        self.connection = self.connect()

    def getDrivers(self):
        return pyodbc.drivers()

    def setDriver(self):
        for index, driver in enumerate(self.getDrivers()):
            print('{}.  {}\n'.format(index, driver))
        driverSelect = input('Enter Driver Number : ')
        self.DRIVER = self.getDrivers()[int(driverSelect)]
        print('Driver Selected : {}'.format(self.DRIVER))
        print('[LOG] Reconnecting')
        self.connect()

    def connect(self):

        print('[LOG] Connecting to SQL Server')
        print('      Driver:   {}'.format(self.DRIVER))
        print('      Server:   {}'.format(self.SERVER))
        print('      Database: {}'.format(self.DATABASE))
        str_conn = "DRIVER={" + self.DRIVER + "};" \
                   + "SERVER=" + self.SERVER + ";" \
                   + "DATABASE=" + self.DATABASE + ";" \
                   + "UID=" + self.UID + ";" \
                   + "PWD=" + self.PWD
        conn = None
        try:
            conn = pyodbc.connect(str_conn)
            return conn
        except Exception as e:
            print(e)
            return conn

    def get_connection(self):
        for retry in range(30):
            try:
                sql = '''SELECT CAST( GETDATE() AS Date )'''
                conn = self.connection
                cursor = conn.cursor()
                cursor.execute(sql)
                # Stop on success
                return conn
            except Exception as e:
                time.sleep(1)
                self.connection = self.connect()
                continue
            logger.error("import pyodbc: cannot communicate with sql server")
        logger.error("_____Error: try to communicate with sql server failed")
        return None  # throw if the retry fails too often

    def get_last_id(self, table):
        try:
            sql = '''select top 1 id from %s order by id desc''' % table
            conn = self.connection
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            if len(rows) > 0:
                return int(rows[0][0])
            return 0
        except Exception as err:
            logger.error("Error: %s" % err)
