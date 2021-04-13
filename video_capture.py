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


minio_instance = Minio()

WINDOW_NAME = 'capture_camera'
FPS = Config.FPS
DURATION = Config.DURATION
OUTPUT_EXTENSION = Config.EXTENSION
VIDEO_SIZE = Config.VIDEO_SIZE

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


def open_cam_rtsp(uri, fps, width, height, latency):
    gst_str = ('rtspsrc location={} latency={} ! '
               'rtph264depay ! h264parse ! omxh264dec ! '
               'nvvidconv ! videorate ! '
               'video/x-raw, framerate={}/1, width=(int){}, height=(int){},'
               'format=(string)BGRx ! '
               'videoconvert ! appsink').format(uri, latency, fps, width, height)
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)


def open_cam_usb(dev, width, height):
    # We want to set width and height here, otherwise we could just do:
    #     return cv2.VideoCapture(dev)
    gst_str = ('v4l2src device=/dev/video{} ! '
               'video/x-raw, width=(int){}, height=(int){}, format=RGB, framerate=30/1 !'
               'videoconvert ! appsink').format(dev, width, height)
    # return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
    return cv2.VideoCapture(dev)


def open_cam_onboard(width, height):
    gst_elements = str(subprocess.check_output('gst-inspect-1.0'))
    if 'nvcamerasrc' in gst_elements:
        # On versions of L4T prior to 28.1, add 'flip-method=2' into gst_str
        gst_str = ('nvcamerasrc ! '
                   'video/x-raw(memory:NVMM), '
                   'width=(int)2592, height=(int)1458, '
                   'format=(string)I420, framerate=(fraction)30/1 ! '
                   'nvvidconv ! '
                   'video/x-raw, width=(int){}, height=(int){}, '
                   'format=(string)BGRx ! '
                   'videoconvert ! appsink').format(width, height)
    elif 'nvarguscamerasrc' in gst_elements:
        gst_str = ('nvarguscamerasrc '
                   'awblock=false saturation=1 gainrange="1 8" aeantibanding=2 '
                   'exposurecompensation=0 '
                   'ee-mode=1  ee-strength=0 tnr-mode=2 tnr-strength=1 wbmode=3 '
                   'ispdigitalgainrange="1 256" exposuretimerange="34000 358733000" aelock=true ! '
                   'video/x-raw(memory:NVMM), '
                   'width=(int)1920, height=(int)1080, '
                   'format=(string)NV12, framerate=(fraction)15/1 ! '
                   'nvvidconv flip-method=2 ! '
                   'video/x-raw, width=(int){}, height=(int){}, '
                   'format=(string)BGRx ! '
                   'videoconvert ! appsink ').format(width, height)
    else:
        raise RuntimeError('onboard camera source not found!')
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)


def open_window(width, height):
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, width, height)
    cv2.moveWindow(WINDOW_NAME, 0, 0)
    cv2.setWindowTitle(WINDOW_NAME, 'Camera Demo for Jetson TX2/TX1')

def get_file_name():
    time_string = datetime.now().strftime('%d%m%y_%H%M%S.' + OUTPUT_EXTENSION)
    return os.path.join('videos', time_string)

def read_cam(cap, width, height, display):
    show_help = True
    full_scrn = False
    help_text = '"Esc" to Quit, "H" for Help, "F" to Toggle Fullscreen'
    font = cv2.FONT_HERSHEY_PLAIN
  
    if OUTPUT_EXTENSION == 'mp4':
        fourcc = cv2.VideoWriter_fourcc(*'MPEG')
    elif OUTPUT_EXTENSION == 'avi':
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
    else:
        fourcc = cv2.VideoWriter_fourcc(*'XVID')

    _, frame = cap.read()
    h, w, d = frame.shape
    if h < height or w < width:
        height = h
        width = w
    
    out_file_name = get_file_name()
    out = cv2.VideoWriter(out_file_name, fourcc, FPS, (width, height))
    frame_total = 0
    start_time = None

    while True:
        if start_time is None:
            start_time = time.time()

        if display:
            if cv2.getWindowProperty(WINDOW_NAME, 0) < 0:
            # Check to see if the user has closed the window
            # If yes, terminate the program
                break

        _, img = cap.read() # grab the next image frame from camera
        
        if display:
            if show_help:
                cv2.putText(img, help_text, (11, 20), font,
                            1.0, (32, 32, 32), 4, cv2.LINE_AA)
                cv2.putText(img, help_text, (10, 20), font,
                        1.0, (240, 240, 240), 1, cv2.LINE_AA)
            cv2.imshow(WINDOW_NAME, img)

        out.write(img)
        frame_total += 1

        if frame_total == FPS * DURATION * 60:
            total_time = time.time() - start_time
            start_time = None
            print('Total time is {:.3f} s for 1 file in {} minutes'.format(total_time, DURATION))
            frame_total = 0
            out.release()

            # upload video file to Minio storage
            time_upload = time.time()
            video_path = out_file_name
            minio_path = os.path.join(config.MINIO_FREFIX_PATH, datetime.now().strftime('20%y/%m/%d'), os.path.basename(video_path))
            upload_response = minio_instance.upload_file(video_path, minio_path)
            if upload_response:
                logger.debug(f"File {out_file_name} was uploaded successfully at {datetime.now().strftime('%y/%m/%d-%H/%M/%S')}")
                os.remove(video_path)

            else:
                logger.debug(f"Cannot upload file: {out_file_name} at {datetime.now().strftime('%y/%m/%d-%H/%M/%S')}")
            print("Uploaded time:", time.time() - time_upload)
            
            # create new video writer for next video
            out_file_name = get_file_name()
            out = cv2.VideoWriter(out_file_name, fourcc, FPS, (width,height))

        if display:
            key = cv2.waitKey(10)
            if key == 27: # ESC key: quit program
                out.release()
                break
            elif key == ord('H') or key == ord('h'): # toggle help message
                show_help = not show_help
            elif key == ord('F') or key == ord('f'): # toggle fullscreen
                full_scrn = not full_scrn
                if full_scrn:
                    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN,
                                        cv2.WINDOW_FULLSCREEN)
                else:
                    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_NORMAL)
    out.release()

def main():
    args = parse_args()
    print('Called with args:')
    print(args)
    print('OpenCV version: {}'.format(cv2.__version__))

    if args.use_rtsp:
        cap = open_cam_rtsp(args.rtsp_uri,
                            FPS,
                            VIDEO_SIZE[0],
                            VIDEO_SIZE[1],
                            args.rtsp_latency)
    elif args.use_usb:
        print('Use Usb cam', args.video_dev, VIDEO_SIZE[0], VIDEO_SIZE[1])
        cap = open_cam_usb(args.video_dev,
                           VIDEO_SIZE[0],
                           VIDEO_SIZE[1])
    else: # by default, use the Jetson onboard camera
        cap = open_cam_onboard(args.image_width,
                               args.image_height)

    if not cap.isOpened():
        sys.exit('Failed to open camera!')

    open_window(VIDEO_SIZE[0], VIDEO_SIZE[1])
    read_cam(cap, VIDEO_SIZE[0], VIDEO_SIZE[1], args.display)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()


