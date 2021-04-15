import sys
import os
import argparse
import time
import numpy as np 
import subprocess
from datetime import datetime
from utils.minio_access import Minio
from conf.config import Config
from utils.logger import upload_logger as logger
import cv2
from capture import CapOptions, CapState
from capture.opencv_capture import CaptureProcess


def parse_args():
    # Parse input arguments
    desc = 'Capture and display live camera video on Jetson TX2/TX1'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--rtsp', dest='use_rtsp',
                        help='use IP CAM (remember to also set --uri)',
                        action='store_true')
    parser.add_argument('--uri', dest='rtsp_uri',
                        help='RTSP URI, e.g. rtsp://192.168.1.64:554',
                        default=None, type=str)
    parser.add_argument('--latency', dest='rtsp_latency',
                        help='latency in ms for RTSP [200]',
                        default=200, type=int)
    parser.add_argument('--usb', dest='use_usb',
                        help='use USB webcam (remember to also set --vid)',
                        action='store_true')
    parser.add_argument('--vid', dest='video_dev',
                        help='device # of USB webcam (/dev/video?) [1]',
                        default=0, type=int)
    parser.add_argument('--width', dest='image_width',
                        help='image width [1920]',
                        default=VIDEO_SIZE[0], type=int)
    parser.add_argument('--height', dest='image_height',
                        help='image height [1080]',
                        default=VIDEO_SIZE[1], type=int)
    parser.add_argument('--display',
                        help='if True, a window will show stream in real-time, else not show.',
                        action='store_true')                    
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    options_1 = CapOptions(
        'rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov', 
        duration=5,
        output_folder='videos/cam1'
    )
    options_2 = CapOptions(
        'rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov', 
        duration=5,
        output_folder='videos/cam2'
    )
    options_3 = CapOptions(
        'rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov', 
        duration=5,
        output_folder='videos/cam3'
    )
    options_4 = CapOptions(
        'rtsp://admin:abcd1234@10.124.70.76/channel1', 
        duration=5,
        output_folder='videos/cam4'
    )
    capture_instance_1 = CaptureProcess(options_1, 'Camera 1')
    capture_instance_2 = CaptureProcess(options_2, 'Camera 2')
    capture_instance_3 = CaptureProcess(options_3, 'Camera 3')
    # capture_instance_4 = CaptureProcess(options_4, 'Camera 4')
    capture_instance_1.start()
    print("Start capture process 1")
    capture_instance_2.start()
    print("Start capture process 2")
    capture_instance_3.start()
    print("Start capture process 3")
    # capture_instance_4.start()
    # print("Start capture process 4")

    

    

