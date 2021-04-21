import logging
from logging.handlers import RotatingFileHandler

formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')

minio_handler = RotatingFileHandler('logs/minio.log', backupCount=8, maxBytes=5*1024*1024)
minio_handler.setFormatter(formatter)
minio_logger = logging.getLogger('minio')
minio_logger.propagate = False
minio_logger.setLevel(logging.INFO)
minio_logger.addHandler(minio_handler)


 # file handler
recorder_handler = logging.handlers.RotatingFileHandler('logs/recorder.log', maxBytes=5*1024*1024, backupCount=10)
recorder_handler.setFormatter(formatter)
recorder_logger = logging.getLogger('recorder')
recorder_logger.setLevel(logging.INFO)
recorder_logger.addHandler(recorder_handler)




