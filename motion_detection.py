# based on https://www.pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/
# added area of interest monitoring
# todo:
# - check xmin xmax of selection

import argparse
import datetime
import imutils
from imutils.video import VideoStream
from time import sleep
import cv2
import math


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser(description='Process a video file or stream to check when motion appears in a pre defined area of interest.')
ap.add_argument("-v", "--video", help="path to the video file, if not set assumes video camera stream")
ap.add_argument("-a", "--min-area", type=int, default=3, help="minimum area size in pixels")
args = vars(ap.parse_args())

def select_and_show_rectangle(event, x, y, flags, data):
    global rectangle_corners
    global btn_down

    if event == cv2.EVENT_LBUTTONDOWN:
        rectangle_corners = [(x, y)]
        btn_down = True
    
    # during dragging show selection rectangle
    elif event == cv2.EVENT_MOUSEMOVE and btn_down:
        image = data.copy()
        cv2.rectangle(image, rectangle_corners[0], (x, y), (0,255,0), 2)
        cv2.imshow("image", image)
 
    elif event == cv2.EVENT_LBUTTONUP:
        rectangle_corners.append((x, y))
        btn_down = False


cv2.namedWindow("image")
is_cam_stream = False
rectangle_corners = []
btn_down = False
base_frame = None
frame_i = -1

# if the video argument is None, then we are reading from webcam
if args.get("video", None) is None:
    vs = imutils.video.VideoStream(src=0).start()
    is_cam_stream = True
    frame_rate = 10 # assume 10 fps 
    sleep(2.0)
# otherwise, we are reading from a video file
else:
    vs = cv2.VideoCapture(args["video"])
    frame_rate = vs.get(cv2.CAP_PROP_FPS)

# loop over the frames of the video
while True:
    frame_i = frame_i + 1
    frame = vs.read()
    frame = frame if is_cam_stream else frame[1]

    # frame could not be grabbed, end of video
    if frame is None:
        break

    if base_frame is None:
        # display the image and wait for a keypress
        print("Select area of interest and press Enter afterwards.")
        data = frame.copy()
        cv2.setMouseCallback("image", select_and_show_rectangle, data)
        cv2.imshow("image", frame)
        key = cv2.waitKey(0) & 0xFF # 0: wait forever

    # resize the frame, convert it to grayscale, and blur it
    frame = frame[rectangle_corners[0][1]:rectangle_corners[1][1],
                  rectangle_corners[0][0]:rectangle_corners[1][0]]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    if frame_i % frame_rate == 0: # select a base frame for comparisson every second
        base_frame = gray
        continue

    # compute the absolute difference between the current frame and base_frame
    frameDelta = cv2.absdiff(base_frame, gray)
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
 
    # dilate the thresholded image to fill in holes, then find contours
    # on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
 
    # loop over the contours
    found_motion = False
    for c in cnts:
        # if the contour is too small, ignore it
        if cv2.contourArea(c) < args["min_area"]:
            continue

        found_motion = True
        # compute the bounding box for the contour, draw it on the frame,
        # and update the text
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imshow("image", frame)

    if found_motion:
        if args.get("video", None) is None:
            # for cam video stream output time
            print("Motion detected at " + str(datetime.datetime.now().time()))
        else:
            # for video file output time and frame
            print("Motion detected at %2d:%02d (frame %4d)" 
                  %(math.floor(frame_i/(frame_rate*60)),
                  math.floor(frame_i/frame_rate%60), frame_i))  

    # show the frame and record if the user presses a key
    key = cv2.waitKey(1) & 0xFF

    # if the "q" key is pressed, break from the loop
    if key == ord("q"):
        break

# show last motion
print("Processing done, press Enter to leave.")
cv2.waitKey(0)

# cleanup the camera and close any open windows
vs.stop() if is_cam_stream else vs.release()
cv2.destroyAllWindows()
