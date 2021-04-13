import cv2
import os 
import numpy as np
import traceback
import boto3
from botocore.client import Config as BotoConfig
from conf.config import Config
from utils.logger import minio_logger as logger


MINIO_ENDPOINT_URL = Config.MINIO_ENDPOINT_URL
MINIO_ACCESS_KEY_ID = Config.MINIO_ACCESS_KEY_ID
MINIO_SECRET_ACCESS_KEY = Config.MINIO_SECRET_KEY
MINIO_SIGNATURE_VERSION = Config.MINIO_SIGNATURE_VERSION
MINIO_REGION_NAME = Config.MINIO_REGION_NAME
MINIO_BUCKET = Config.MINIO_BUCKET

class Minio:
    def __init__(self):

        self.s3_object = boto3.client('s3', endpoint_url=MINIO_ENDPOINT_URL, aws_access_key_id=MINIO_ACCESS_KEY_ID,
                                      aws_secret_access_key=MINIO_SECRET_ACCESS_KEY,
                                      config=BotoConfig(signature_version=MINIO_SIGNATURE_VERSION),
                                      region_name=MINIO_REGION_NAME)

        self.s3_file = boto3.resource('s3',
                                      endpoint_url=MINIO_ENDPOINT_URL,
                                      aws_access_key_id=MINIO_ACCESS_KEY_ID,
                                      aws_secret_access_key=MINIO_SECRET_ACCESS_KEY,
                                      config=BotoConfig(signature_version=MINIO_SIGNATURE_VERSION),
                                      region_name=MINIO_REGION_NAME)

    def put(self, buf, minio_path):
        try:
            self.s3_object.put_object(Bucket=MINIO_BUCKET, Key=minio_path, Body=buf)

        except:
            logger.debug(traceback.format_exc())
            return False

    def get(self, minio_path):
        try:
            response = self.s3_object.get_object(Bucket=MINIO_BUCKET, Key=minio_path)
            return response['Body'].read()
        except:
            logger.debug(traceback.format_exc())
            return False

    def get_opencv_img(self, path):
        try:
            response = self.s3_object.get_object(Bucket=MINIO_BUCKET, Key=path)
            byte_data = response['Body'].read()
            img_as_np = np.frombuffer(byte_data, dtype=np.uint8)
            return cv2.imdecode(img_as_np, flags=1)
        except:
            logger.debug(traceback.format_exc())
            return None

    def write_opencv_img(self, img, path):
        _, buf = cv2.imencode('.jpg', img)
        return self.put(buf.tobytes(), path)

    def upload_file(self, file_path, minio_path):
        try:
            self.s3_file.Bucket(MINIO_BUCKET).upload_file(file_path, minio_path)
            return True
        except:
            logger.debug(traceback.format_exc())
            return False

    def download_file(self, minio_path, file_path):
        try:
            self.s3_file.Bucket(MINIO_BUCKET).download_file(minio_path, file_path)
        except:
            logger.debug(traceback.format_exc())
            return False

    def copy(self, src_path, dest_path):
        copy_source = {'Bucket': MINIO_BUCKET, 'Key': src_path}
        self.s3_object.copy_object(CopySource=copy_source, Bucket=MINIO_BUCKET, Key=dest_path)

    def move(self, src_path, dest_path):
        self.copy(src_path, dest_path)
        self.s3_object.delete_object(Bucket=MINIO_BUCKET, Key=src_path)


if __name__ == '__main__':
    minio_instance = Minio()
    video_path = '/home/nano/workplace/video-capture/videos/041321_143807.avi'
    minio_path = 'uploads/2021/4/13/' + os.path.basename(video_path)
    minio_instance.upload_file(video_path, minio_path)
