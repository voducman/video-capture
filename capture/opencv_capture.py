import sys
import os
import multiprocessing as mp 
import subprocess
import time 
import ctypes
import cv2
from datetime import datetime
from capture import AbstractCaptureProcess, CapState
from capture import create_writer, init_capture_rtsp, get_paths
from utils.minio_access import Minio 
from utils.logger import capture_logger as logger 
from utils.logger import upload_logger 

class CaptureProcess(mp.Process, AbstractCaptureProcess):
    def __init__(self, options, name=None):
        super(mp.Process, self).__init__()
        super(CaptureProcess, self).__init__(name=name)

        self.options = options
        self.state = CapState.INIT
        self.running = mp.Value(ctypes.c_bool, True)  
        self.video_total_frame = 0 
        self.minio_instance = Minio()
        self.capture = None 
        self.writer = None   
        self.current_file_path = None
        self.minio_path = None 
        self.count_cannot_upload = 0
        if not os.path.isdir(options.output_folder):
            os.makedirs(options.output_folder)
        logger.debug(f'[{self.name}] Init capture processor')

    def run(self):
        # init capture
        logger.debug(f'[{self.name}] Start to run capture processor')
        rtsp_url = self.options.rtsp_url
        fps = self.options.fps
        frame_width = self.options.frame_width
        frame_height = self.options.frame_height
        # self.capture = init_capture_rtsp(self.options.rtsp_url, fps, frame_width, frame_height)
        
        # if not self.capture.isOpened():
        #     self.state = CapState.CLOSED
        #     time.sleep(5)
        #     if not self.capture.isOpened():
        #         self.stop()

        # self.capture.release()
        self.capture = None
        self.state = CapState.OPENED

        while self.running.value:
            # write frame to video to prepare for upload
            self.current_file_path, self.minio_path = get_paths(self.options)
            # self.writer.release()
            start_time = time.time()
            logger.debug(f'[{self.name}] Begin to capture new video with length {self.options.duration}m')

            count_frame = 0
            # timestamp = time.time()
            # while count_frame <  int(self.options.fps * self.options.duration * 60) or time.time() - timestamp <= self.options.duration * 60:
            # while time.time() - timestamp <= self.options.duration * 60:
            #     ret, frame = self.capture.read()
            #     if not ret:
            #         continue
            #     if self.options.frame_width != frame.shape[1] or self.options.frame_height != frame.shape[0]:
            #         frame = cv2.resize(frame, (self.options.frame_width, self.options.frame_height))
            #     self.writer.write(frame)
            #     count_frame += 1
            cmd = 'ffmpeg -y -i {} -c:a copy -c:v libx265 -t 0:{}:0 {}'.format(self.options.rtsp_url, self.options.duration, self.current_file_path)
            result = subprocess.call(cmd.split(), shell=False) 
            print(result)
            if result != 0:
                # fail
                logger.debug(f'Record video {os.path.basename(self.current_file_path)} is fail.')
                os.remove(self.current_file_path)
            else:
                # upload video to minio storage
                write_time = time.time()
                # self.writer.release()
                # self.writer = None
                self.upload_video()
                end_time = time.time()
                file_name = os.path.basename(self.current_file_path)
                upload_logger.debug(f'[{self.name}] Upload file {file_name} is success. Total time: {(end_time-start_time)/60}m | {self.options.duration}m, write time: {(write_time-start_time)/60}m, upload time: {(end_time-write_time)/60}m.')
                self.current_file_path = None

    def stop(self):
        logger.debug(f'[{self.name}] Stop capture processor')
        if self.writer is not None:
            self.writer.release()

        if self.capture is not None:
            self.capture.release()
            self.state = CapState.CLOSED

        self.running.value = False
        self.join()

    def upload_video(self):
        result = self.minio_instance.upload_file(self.current_file_path, self.minio_path)
        if result:
            os.remove(self.current_file_path)
            logger.debug(f'[{self.name}] Upload file to minio successfully.')
        else:
            self.count_cannot_upload += 1
            if self.count_cannot_upload >= self.options.max_cannot_upload:
                # stop process if cout cannot upload exceed max cannot upload
                logger.debug(f'Total file cannot upload exceed maximum setting --> Exit this process: {self.options.rtsp_url}.')
                self.stop()

    def get_cap_state(self):
        return self.state
                
    
    


        


    