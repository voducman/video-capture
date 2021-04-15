import logging
from logging.handlers import TimedRotatingFileHandler


minio_handler = TimedRotatingFileHandler('logs/minio.log', when="W0", backupCount=8)
minio_logger = logging.getLogger('minio')
minio_logger.propagate = False
minio_logger.setLevel(logging.DEBUG)
minio_logger.addHandler(minio_handler)

upload_handler = TimedRotatingFileHandler('logs/upload.log', when="W0", backupCount=8)
upload_logger = logging.getLogger('upload')
upload_logger.propagate = False
upload_logger.setLevel(logging.DEBUG)
upload_logger.addHandler(upload_handler)

capture_handler = TimedRotatingFileHandler('logs/capture.log', when="W0", backupCount=8)
capture_logger = logging.getLogger('capture')
capture_logger.propagate = False
capture_logger.setLevel(logging.DEBUG)
capture_logger.addHandler(capture_handler)


