import subprocess
from datetime import datetime
import time
import logging
import os
import json
import shlex
import signal
import threading
from urllib.parse import urlparse
from utils.logger import recorder_logger as logger


class RecorderConfig:
    Container = 'auto'
    Duration = 300  # in seconds
    FPS = 10
    Width = 1920
    Height = 1080


class CreateOptions:
    def __init__(self, filename, cam_info, settings, duration=None):
        self.output_filename = filename
        self.cam_id = cam_info['id']
        self.rtsp_url = cam_info['url']
        self.fps = cam_info['fps']
        self.metadata = cam_info['metadata']
        self.container = settings['container']
        self.width = settings['width']
        self.height = settings['height']

        if duration is None:
            self.duration = settings['duration']
        else:
            self.duration = duration


class MyRecorder:
    def __init__(self, cam_info, redis_client, minio_client, settings):

        self.cam_info = cam_info
        self.redis_client = redis_client
        self.minio_client = minio_client
        self.engine = None
        self.last_created_time = None
        self.duration = settings['duration']
        self.folder = os.getcwd()
        self.start_time = time.time()
        self.settings = settings
        self.upload_filename = None
        self.timer = None 

    def stop(self):
        if not self.engine:
            return

        self.upload_filename = self.engine.stop()
        self.engine = None
        network_thread = threading.Thread(target=self.postprocess, args=())
        network_thread.start()
        
    def postprocess(self):
        if self.check_video_file(self.upload_filename):
            # upload video to minio
            filename = os.path.basename(self.upload_filename)
            minio_path = os.path.join(self.settings['minio_prefix_path'],datetime.now().strftime("%Y/%m/%d/"), "cam_" + self.cam_info['id'], filename)
            self.minio_uploader(self.upload_filename, minio_path)
        
            # send notification to redis
            header = {'camera_id': self.cam_info['id'], 'video_path': minio_path}
            self.redis_notifier(header)
            
        elif os.path.isfile(self.upload_filename):
            logger.error("Camera %s: file [%s] invalid size", self.cam_info['id'], self.upload_filename)
            

    def create_task(self, folder):
        # cancel old timer of previous capture process.
        self.cancel_timer()
        self.start_time = time.time()
        self.folder = folder
        self.run(self.duration)
        logger.info("total run: %s", time.time() - self.start_time)
        
    def run(self, duration):
        # stop current job
        self.stop()

        # create new job
        self.last_created_time = datetime.now().strftime("%d-%m-%Y:%H-%M-%S")

        # filename without extension
        filename = 'cam_' + str(self.cam_info['id']) + '_' + self.last_created_time
        filename = os.path.join(self.make_folder_by_date(), filename)

        options = CreateOptions(filename, self.cam_info, self.settings, duration)

        # create capture engine
        try:
            self.timer = threading.Timer(self.duration, self.stop, [self])
            self.engine = GStreamerCaptureEngine(options)
            self.engine.run()
            self.timer.start()
            
            self.upload_filename = filename
            
        except ValueError as ex:
            logger.error('Create engine error: %s. Do you register all engines ?', str(ex))
            self.engine = None
            self.upload_filename = None 
            self.cancel_timer(True)

    def check_alive(self):
        if self.engine is None:
            # logger.debug('Process is None')
            return

        # check process is terminated
        if not self.engine.is_running():
            run_time = time.time() - self.start_time
            remaining_time = self.duration - run_time
            # logger.debug('Process is terminated, remain ', remaining_time)
            if remaining_time >= 60:
                logger.debug('Camera %s: Remain %s seconds, try to reconnect', self.cam_info['id'], remaining_time)
                # avoid Recorder push noti to server when process breaking in the middle process
                self.upload_filename = None 
                
                self.run(remaining_time)

        else:
            logger.debug('Camera %s: Engine is running', self.cam_info['id'])

    def check_video_file(self, file_path):
        try:
            file_size = os.path.getsize(file_path)
            if file_size < 2048:
                os.remove(file_path)
                return False
            else:
                return True
        except Exception:
            return False

    def make_folder_by_date(self):
        # today = datetime.now().strftime('%Y:%m:%d').split(':')
        today = datetime.now().strftime('%d-%m-%Y')
        try:
            cam_name = 'cam_' + str(self.cam_info['id'])
            folder_save = os.path.join(self.folder, today, cam_name)
            if not os.path.isdir(folder_save):
                os.makedirs(folder_save)
            return folder_save
        except Exception:
            return ''
        
    def cancel_timer(self, is_exception=None):
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
            self.timer = None
            if not is_exception:
                logger.info('Camera %s: Cancel timer', self.cam_info['id'])
            else:
                logger.error('Camera %s: Cancel timer in FileNotFoundError exception.', self.cam_info['id'])
        self.timer = None 

    def minio_uploader(self, video_path, minio_path):
        if not self.minio_client.upload_file(video_path, minio_path):
            logger.error("Camera %s: cannot upload video [%s] to minio storage.", self.cam_info['id'], video_path)
        else:
            logger.info("Camera %s: Upload video [%s] to minio storage successfully.", self.cam_info['id'], minio_path)
            self.upload_filename = None
        os.remove(video_path)
    
    def redis_notifier(self, header):
        try:
            if self.redis_client:
                self.redis_client.rpush('capture_video_event', json.dumps(header))
                logger.info("Camera %s - rPush event: " + json.dumps(header), self.cam_info['id'])
            else:
                logger.error('Camera %s: No redis client.', self.cam_info['id'])
        except Exception as ex:
            logger.error('Camera %s - Push to redis failed: %s', self.cam_info['id'], str(ex))
            

class CaptureEngine:
    def __init__(self, options: CreateOptions):
        self.command = ''
        self.process = None
        self.terminate_signal = signal.SIGINT

        self.cam_id = options.cam_id
        self.container = options.container
        self.metadata = options.metadata
        self.duration = options.duration
        self.rtsp_url = options.rtsp_url
        self.fps = options.fps
        self.output_filename = options.output_filename

    def is_running(self):
        if self.process is None:
            return False
        else:
            return self.process.poll() is None
    

    def stop(self):
        if self.process is None:
            return

        if self.is_running():
            try:
                self.process.send_signal(self.terminate_signal)
                self.process.wait(20)
            except subprocess.TimeoutExpired:
                self.process.kill()

            logger.info('Camera %s: Stop record %s', self.cam_id, self.output_filename)
        else:
            logger.info('Camera %s: Stop record2 %s', self.cam_id, self.output_filename)
        
        return self.output_filename

    def get_last_file_name(self):
        return self.output_filename

    def run(self,**kwargs):
        logger.info('Camera %s: %s', self.cam_id, self.command)
        try:
            self.process = subprocess.Popen(shlex.split(self.command), **kwargs)
            return True
        except FileNotFoundError:
            logger.info('Camera %s: Command not found', self.cam_id)
            self.output_filename = None
            return False


class GStreamerCaptureEngine(CaptureEngine):
    def __init__(self, options: CreateOptions):
        CaptureEngine.__init__(self, options)

        # output file name
        if self.container == 'auto':
            self.container = 'mkv'
  
        self.output_filename += '.' + self.container

        if self.metadata is not None:
            src_width = self.metadata['width']
            src_height = self.metadata['height']
            src_fps = self.metadata['frame_rate']
            src_codec = self.metadata['codec'].lower()

            if src_codec == 'h264' or src_codec == 'avc':
                if src_width == options.width and src_height == options.height:
                    command_template = """gst-launch-1.0 rtspsrc location=%s latency=300 ! \
                            queue ! rtph264depay ! h264parse ! omxh264dec ! nvvidconv ! videorate ! \'video/x-raw, framerate=%d/1\' ! \
                            omxh265enc ! 'video/x-h265, stream-format=(string)byte-stream' ! h265parse ! qtmux ! \
                            filesink location=%s -e"""
                    if src_fps >= options.fps:
                        self.command = command_template % (options.rtsp_url, options.fps, self.output_filename)
                    else:
                        self.command = command_template % (options.rtsp_url, src_fps, self.output_filename)
                else:
                    command_template = """gst-launch-1.0 rtspsrc location=%s latency=300 ! \
                        queue ! rtph264depay ! h264parse ! omxh264dec ! nvvidconv ! videorate ! \'video/x-raw,width=(int)%d,height=(int)%d,framerate=%d/1\' ! \
                        omxh265enc ! 'video/x-h265, stream-format=(string)byte-stream' ! h265parse ! qtmux ! \
                        filesink location=%s -e"""
                    if src_fps >= options.fps:
                        self.command = command_template % (options.rtsp_url, options.width, options.height, options.fps, self.output_filename)
                    else:
                        self.command = command_template % (options.rtsp_url, options.width, options.height, src_fps, self.output_filename)

            elif src_codec == 'hevc' or src_codec == 'h265':
                if src_width == options.width and src_height == options.height:
                    command_template = """gst-launch-1.0 rtspsrc location=%s latency=300 ! \
                    queue ! rtph265depay ! h265parse ! omxh265dec ! nvvidconv ! videorate ! \'video/x-raw, framerate=%d/1\' ! \
                    omxh265enc ! \'video/x-h265, stream-format=(string)byte-stream\' ! h265parse ! qtmux ! \
                    filesink location=%s -e"""
                    if src_fps > options.fps:
                        self.command = command_template % (options.rtsp_url, options.fps, self.output_filename)
                    else:
                        self.command = command_template % (options.rtsp_url, src_fps, self.output_filename)
                else:
                    command_template = """gst-launch-1.0 rtspsrc location=%s latency=300 ! \
                    queue ! rtph265depay ! h265parse ! omxh265dec ! nvvidconv ! videorate ! \'video/x-raw,width=(int)%d,height=(int)%d,framerate=%d/1\' ! \
                    omxh265enc ! \'video/x-h265, stream-format=(string)byte-stream\' ! h265parse ! qtmux ! \
                    filesink location=%s -e"""
                    if src_fps >= options.fps:
                        self.command = command_template % (options.rtsp_url, options.width, options.height, options.fps, self.output_filename)
                    else:
                        self.command = command_template % (options.rtsp_url, options.width, options.height, src_fps, self.output_filename)
            else:
                logger.error("Codec of RTSP video {} is not supported.".format(options.rtsp_url))
                raise ValueError("Codec of RTSP video is not supported.")

        else:
            logger.error("Cannot probe metadata of RTSP source: {}.".format(options.rtsp_url))
            raise ValueError("Cannot probe metadata of RTSP source.")

       # run pipeline command in bash
        self.command = 'bash -c "' + self.command + '"'

