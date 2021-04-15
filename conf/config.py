# HD: (1920,1080)
# Full HD: (1280,720)

class Config:
    VIDEO_SIZE = (1920,1080)
    DURATION = 5 # in minutes
    FPS = 30
    EXTENSION = 'avi' # [avi, mp4]
    
    # MINIO_ENDPOINT_URL = 'http://10.124.64.120:9000'
    MINIO_ENDPOINT_URL = 'http://210.211.99.8:9000'
    MINIO_ACCESS_KEY_ID = 'BIGDATA'
    MINIO_SECRET_KEY = 'KLFDSAJKFJEWOkhjfkdashfkjafiowe'
    MINIO_SIGNATURE_VERSION = 's3v4'
    MINIO_REGION_NAME = 'ap-southeast-1'
    MINIO_BUCKET = 'vinmart' 
    MINIO_FREFIX_PATH = 'uploads'

    RTSP = [

    ]