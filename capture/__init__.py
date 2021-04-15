import cv2 
import os
from datetime import datetime
from conf.config import Config

class CapState:
    INIT = 0
    OPENED = 1
    REOPENED = 2
    CLOSED = 3

    names = {
        0: 'INIT',
        1: 'OPENED',
        2: 'REOPENED',
        3: 'CLOSED'
    }


class CapOptions:
    def __init__(self, url, fps=30, output_folder='videos', video_extension='avi', duration=5, frame_width=1920, frame_height=1080, max_cannot_upload=3):
        self.rtsp_url = url
        self.fps = fps
        self.output_folder = output_folder
        self.video_extension = video_extension
        self.duration = duration
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.max_cannot_upload = max_cannot_upload

class AbstractCaptureProcess:
    def __init__(self):
        self.options = None

    def stop(self):
        raise NotImplementedError()

    def get_options(self):
        return self.options

def get_file_name(video_extension, output_folder):
    time_string = datetime.now().strftime('%d%m%y_%H%M%S.' + video_extension)
    return os.path.join(output_folder, time_string)

def init_capture_rtsp(uri, fps=30, width=1920, height=1080, latency=200):
    gst_str = ('rtspsrc location={} latency={} ! '
               'rtph264depay ! h264parse ! omxh264dec ! '
               'nvvidconv ! videorate ! '
               'video/x-raw, framerate={}/1, width=(int){}, height=(int){},'
               'format=(string)BGRx ! '
               'videoconvert ! appsink').format(uri, latency, fps, width, height)
    # return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
    return cv2.VideoCapture(uri)

def create_writer(options):
        video_path = get_file_name(options.video_extension, options.output_folder)
        writer = cv2.VideoWriter()
        writer.open(
            f"appsrc ! videoconvert ! omxh265enc ! h265parse ! qtmux ! filesink location={video_path}", 
            cv2.CAP_GSTREAMER, 
            0, 
            float(options.fps), 
            (options.frame_width,options.frame_height))
        minio_path = os.path.join(Config.MINIO_FREFIX_PATH, datetime.now().strftime('20%y/%m/%d'), os.path.basename(video_path))
        
        return video_path, minio_path, writer

def get_paths(options):
    video_path = get_file_name(options.video_extension, options.output_folder)
    minio_path = os.path.join(Config.MINIO_FREFIX_PATH, datetime.now().strftime('20%y/%m/%d'), os.path.basename(video_path))
    return video_path, minio_path