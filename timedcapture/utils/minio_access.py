import cv2
import os 
import numpy as np
import traceback
import boto3
from botocore.client import Config as BotoConfig
from utils.logger import minio_logger as logger
import time 

class Minio:
    def __init__(self, endpoint, access_key_id, secret_key, signature_version='s3v4', region_name='ap-southeast-1', bucket='vinmart'):
        
        self.endpoint = endpoint
        self.access_key_id = access_key_id
        self.secret_key = secret_key
        self.signature_version = signature_version
        self.region_name = region_name
        self.bucket = bucket

        self.s3_object = boto3.client('s3', endpoint_url=endpoint, aws_access_key_id=access_key_id,
                                      aws_secret_access_key=secret_key,
                                      config=BotoConfig(signature_version=signature_version),
                                      region_name=region_name)

        self.s3_file = boto3.resource('s3',
                                      endpoint_url=endpoint,
                                      aws_access_key_id=access_key_id,
                                      aws_secret_access_key=secret_key,
                                      config=BotoConfig(signature_version=signature_version),
                                      region_name=region_name)
        
        logger.info("Init minio instance.")

    def put(self, buf, minio_path):
        try:
            self.s3_object.put_object(Bucket=self.bucket, Key=minio_path, Body=buf)

        except:
            logger.debug(traceback.format_exc())
            return False

    def get(self, minio_path):
        try:
            response = self.s3_object.get_object(Bucket=self.bucket, Key=minio_path)
            return response['Body'].read()
        except:
            logger.debug(traceback.format_exc())
            return False

    def get_opencv_img(self, path):
        try:
            response = self.s3_object.get_object(Bucket=self.bucket, Key=path)
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
            start_time = time.time()
            self.s3_file.Bucket(self.bucket).upload_file(file_path, minio_path)
            end_time = time.time()
            logger.info("Upload file %s to server take total: %s s", minio_path,end_time-start_time)
            return True
        except:
            logger.debug(traceback.format_exc())
            return False

    def download_file(self, minio_path, file_path):
        try:
            self.s3_file.Bucket(self.bucket).download_file(minio_path, file_path)
        except:
            logger.debug(traceback.format_exc())
            return False

    def copy(self, src_path, dest_path):
        copy_source = {'Bucket': self.bucket, 'Key': src_path}
        self.s3_object.copy_object(CopySource=copy_source, Bucket=self.bucket, Key=dest_path)

    def move(self, src_path, dest_path):
        self.copy(src_path, dest_path)
        self.s3_object.delete_object(Bucket=self.bucket, Key=src_path)


if __name__ == '__main__':
    minio_instance = Minio()
    video_path = '/home/nano/workplace/video-capture/videos/041321_143807.avi'
    minio_path = 'uploads/2021/4/13/' + os.path.basename(video_path)
    minio_instance.upload_file(video_path, minio_path)