#!/usr/bin/python3
import sys
import os
import json
import redis
from datetime import datetime, date, timedelta
import time
import signal
import ffmpeg
from capture.capture import MyRecorder, RecorderConfig
from utils.minio_access import Minio
from utils.logger import recorder_logger as logger
# from dao.connector import connector

user_interrupt = False


class RecorderService:
    def __init__(self, config_file_name):
        self.config_file_name = config_file_name
        self.settings = {}
        self.camera_list = []
        self.folder = os.getcwd()
        self.recorder_list = []
        self.redis_client = None
        self.minio_client = None 

    def read_config_file(self):
        # read config file
        try:
            fin = open(self.config_file_name)
            self.settings = json.load(fin)
            fin.close()

        except Exception:
            logger.exception('Read config file error')
            return False

        # Connect redis
        try:
            self.redis_client = redis.StrictRedis(host=self.settings['redis_host'], port=self.settings['redis_port'],
                                                  password=self.settings['redis_pass'], decode_responses=True)
        except Exception as e:
            logger.error(e)
            return False
            
        # Connect minio
        try: 
            self.minio_client = Minio(
                endpoint = self.settings['minio_endpoint_url'],
                access_key_id = self.settings['minio_access_key_id'],
                secret_key = self.settings['minio_secret_key'],
                signature_version = self.settings['minio_signature_version'],
                region_name = self.settings['minio_region_name'],
                bucket = self.settings['minio_bucket']
            )
        except Exception as e:
            logger.error(e)
            return False

        # load list of camera
        self.camera_list = self.settings['camera_info_list']

        # load url from db
        enable_database = False
        if 'enable_database' in self.settings:
            enable_database = self.settings["enable_database"]

        if enable_database:
            # connect to database
            mysql_conn = connector().cnxpool

            # read database to find camera id
            for camera in self.camera_list:
                cam_id = camera['id']
                url = mysql_conn.get_camera_url(cam_id)
                if url:
                    camera['url'] = url
                else:
                    logger.info('Camera %s not valid', cam_id)

        # global settings of capture
        if 'container' not in self.settings:
            self.settings['container'] = RecorderConfig.Container
        
        if 'folder' in self.settings:
            if os.path.isdir(self.settings['folder']):
                self.folder = self.settings['folder']

        if 'duration' not in self.settings:
            self.settings['duration'] = RecorderConfig.Duratio

        if 'width' not in self.settings:
            self.settings['width'] = RecorderConfig.Width

        if 'height' not in self.settings:
            self.settings['height'] = RecorderConfig.Height
            
        if 'minio_prefix_path' not in self.settings:
            self.settings['minio_prefix_path'] = 'uploads'

        return True

    def probe_stream(self, rtsp_url):
        probe = ffmpeg.probe(rtsp_url)
        stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if stream:
            return {
                'width': int(stream['width']),
                'height': int(stream['height']),
                'codec': stream['codec_name'],
                'frame_rate': int(stream['avg_frame_rate'].split('/')[0])
            }
        else:
            return None

    def get_metadata(self):
        for i, camera in enumerate(self.camera_list):
            try:
                probe = self.probe_stream(camera['url'])
                if probe:
                    logger.info(str(camera))
                    logger.info('Metadata: {}x{}, {}, {} fps\n'.format(probe['width'], probe['height'], probe['codec'], probe['frame_rate']))
                    camera['metadata'] = probe
                else:
                    logger.info('Camera {}: {}, NO metadata\n'.format(camera['id'], camera['url']))
                    self.camera_list.pop(i)
            except Exception as ex:
                logger.info('Camera {}: {}, GET metadata failed\n'.format(camera['id'], camera['url']))
                continue

    def init_service(self):
        try:
            # 1. read config file
            if not self.read_config_file():
                return False

            # 2. check stream metadata
            self.get_metadata()
            print(self.camera_list)

            # 3. Exit if cannot connect to any camera.
            if len(self.camera_list) == 0:
                logger.error("Cannot connect to any camera. Exit process.")
                return False
 
            # 4. create job
            for cam in self.camera_list:
                self.recorder_list.append(MyRecorder(cam, self.redis_client, self.minio_client,self.settings))

            return True
        except Exception:
            logger.exception('Init service error')
            return False

    def stop(self):
        logger.info('Stop recorder service')
        for recorder in self.recorder_list:
            recorder.stop()

    def run(self):
        logger.info('Start recorder')

        count_check = 30
        start_time = datetime.now()
        is_first_running = True

        while not user_interrupt:
            timestamp = datetime.now()

            if count_check == 0:
                for recorder in self.recorder_list:
                    recorder.check_alive()
                count_check = 30
            else:
                count_check -= 1
            
            if (timestamp-start_time).total_seconds() >= self.settings['duration'] or is_first_running:
                is_first_running = False

                for recorder in self.recorder_list:
                    recorder.create_task(self.folder)

                start_time = datetime.now()

            time.sleep(0.1)

        self.stop()


def signal_terminate_handler(signum, frame):
    global user_interrupt
    user_interrupt = True
    logger.info("Received signal: %s", signum)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_terminate_handler)
    signal.signal(signal.SIGTERM, signal_terminate_handler)

    if len(sys.argv) < 2:
        config_file_name = "conf/config.json"
    else:
        config_file_name = sys.argv[1]

    try:
        service = RecorderService(config_file_name)
        if service.init_service():
            service.run()

    except KeyboardInterrupt:
        logger.info('Main process interrupted')
        service.stop()

    except Exception as ex:
        logger.exception(ex)
        service.stop()

    logger.info('Exit recorder')
