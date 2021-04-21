import cv2
import sys
import os
import ffmpeg
import threading
import subprocess
import shlex
import signal


cameras = [
    {
        "id": "192.168.1.100",
        "url": "rtsp://admin:123456aA@192.168.1.100/channel",
        "fps": 10,
        "codec": "h265"
    },
    {
        "id": "192.168.100.101",
        "url": "rtsp://admin:123456aA@192.168.1.101/channel",
        "fps": 10,
        "codec": "h265"
    }
]


def probe_stream(rtsp_url):
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


def stop_recorder(process):
    print("Terminal process:", process)
    try:
        process.send_signal(signal.SIGINT)
        process.wait(20)
    except subprocess.TimeoutExpired:
        process.kill()


if __name__ == '__main__':

    for camera in cameras:
        stream = probe_stream(camera['url'])
        if stream is not None:
            print(str(camera))
            print('Metadata: {}x{}, {}, {} fps\n'.format(stream['width'], stream['height'], stream['codec'], stream['frame_rate']))
        else:
            print('Camera {}: {}, NO metadata\n'.format(cameras[0]['id'], cameras[0]['url']))

    command_template = """gst-launch-1.0 rtspsrc location=%s latency=300 ! \
                        queue ! rtph264depay ! h264parse ! omxh264dec ! nvvidconv ! videorate ! \'video/x-raw,width=(int)%d,height=(int)%d,framerate=%d/1\' ! \
                        omxh265enc ! \'video/x-h265, stream-format=(string)byte-stream\' ! h265parse ! qtmux ! \
                        filesink location=%s -e"""
    command = command_template % ("rtsp://admin:123456aA@192.168.1.100/channel", 1920, 1080, 10, 'test-stream.mp4')
    command = 'bash -c "%s"' % command
    print("command:", command)
    process = subprocess.Popen(shlex.split(command))
    timer = threading.Timer(30, stop_recorder, [process])
    timer.start()
    print("Done main function.")



