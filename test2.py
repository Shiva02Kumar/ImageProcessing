import numpy as np
import cv2
import cv2.aruco as aruco
import sys
import time
import math


marker_size = 10

def isRotationMatrix(R):
    Rt = np.transpose(R)
    shouldBeIdentity = np.dot(Rt, R)
    I = np.identity(3, dtype=R.dtype)
    n = np.linalg.norm(I - shouldBeIdentity)
    return n < 1e-6

def rotationMatrixToEulerAngles(R):
    assert (isRotationMatrix(R))

    sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])

    singular = sy < 1e-6

    if not singular:
        x = math.atan2(R[2, 1], R[2, 2])
        y = math.atan2(-R[2, 0], sy)
        z = math.atan2(R[1, 0], R[0, 0])
    else:
        x = math.atan2(-R[1, 2], R[1, 1])
        y = math.atan2(-R[2, 0], sy)
        z = 0

    return np.array([x, y, z])

def detect_marker(id_to_find):
    # --- Get the camera calibration path
    calib_path = ""
    camera_matrix = np.loadtxt(calib_path+'cameraMatrix_webcam.txt', delimiter=',')
    camera_distortion = np.loadtxt(calib_path+'cameraDistortion_webcam.txt', delimiter=',')

    # --- 180 deg rotation matrix around the x axis
    R_flip = np.zeros((3, 3), dtype=np.float32)
    R_flip[0, 0] = 1.0
    R_flip[1, 1] = -1.0
    R_flip[2, 2] = -1.0

    # --- Define the aruco dictionary
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_ARUCO_ORIGINAL)
    parameters = aruco.DetectorParameters_create()


    # --- Capture the videocamera (this may also be a video or a picture)
    cap = cv2.VideoCapture(0)
    # -- Set the camera size as the one it was calibrated with
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # -- Font for the text in the image
    font = cv2.FONT_HERSHEY_PLAIN

    while True:

        # -- Read the camera frame
        ret, frame = cap.read()

        # -- Convert in gray scale
        # -- remember, OpenCV stores color images in Blue, Green, Red
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # -- Find all the aruco markers in the image
        corners, ids, rejected = aruco.detectMarkers(image=gray, dictionary=aruco_dict, parameters=parameters, cameraMatrix=camera_matrix, distCoeff=camera_distortion)

        if ids is not None and ids[0] == id_to_find:

            # -- ret = [rvec, tvec, ?]
            # -- array of rotation and position of each marker in camera frame
            # -- rvec = [[rvec_1], [rvec_2], ...]    attitude of the marker respect to camera frame
            # -- tvec = [[tvec_1], [tvec_2], ...]    position of the marker in camera frame
            ret = aruco.estimatePoseSingleMarkers(corners, marker_size, camera_matrix, camera_distortion)

            # -- Unpack the output, get only the first
            rvec, tvec = ret[0][0, 0, :], ret[1][0, 0, :]

            # -- Draw the detected marker and put a reference frame over it
            aruco.drawDetectedMarkers(frame, corners)
            aruco.drawAxis(frame, camera_matrix, camera_distortion, rvec, tvec, 10)

            # -- Print the tag position in camera frame
            str_position = "MARKER Position x=%4.0f  y=%4.0f  z=%4.0f" % (tvec[0], tvec[1], tvec[2])
            cv2.putText(frame, str_position, (0, 100), font, 1, (0, 255, 0), 2, cv2.LINE_AA)

            # -- Obtain the rotation matrix tag->camera
            R_ct = np.matrix(cv2.Rodrigues(rvec)[0])
            R_tc = R_ct.T

            # -- Get the attitude in terms of euler 321 (Needs to be flipped first)
            roll_marker, pitch_marker, yaw_marker = rotationMatrixToEulerAngles(R_flip*R_tc)

            # -- Print the marker's attitude respect to camera frame
            str_attitude = "MARKER Attitude r=%4.0f  p=%4.0f  y=%4.0f" % (math.degrees(roll_marker), math.degrees(pitch_marker), math.degrees(yaw_marker))
            cv2.putText(frame, str_attitude, (0, 150), font, 1, (0, 255, 0), 2, cv2.LINE_AA)

            # -- Now get Position and attitude f the camera respect to the marker
            pos_camera = -R_tc*np.matrix(tvec).T

            str_position = "CAMERA Position x=%4.0f  y=%4.0f  z=%4.0f" % (pos_camera[0], pos_camera[1], pos_camera[2])
            cv2.putText(frame, str_position, (0, 200), font,1, (0, 255, 0), 2, cv2.LINE_AA)

            # -- Get the attitude of the camera respect to the frame
            roll_camera, pitch_camera, yaw_camera = rotationMatrixToEulerAngles(R_flip*R_tc)
            str_attitude = "CAMERA Attitude r=%4.0f  p=%4.0f  y=%4.0f" % (math.degrees(roll_camera), math.degrees(pitch_camera), math.degrees(yaw_camera))
            cv2.putText(frame, str_attitude, (0, 250), font, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # --- Display the frame
        cv2.imshow('frame', frame)

        '''
        marker positions
        x = tvec[0]
        y = tvec[1]
        z = tvec[2]
        if required to move with live camera add code here to move the location of drone 
        as per the position given in the frame 
        frames are change per millisecond so move drone accordingly
        '''

        # --- use 'q' to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            break


if __name__ == "__main__" :
    ''' 
    done by kunal
    take the initial position by lifting the drone and positioning it to center of the grond
    '''
    ''' 
    round 1:
    object1 to be detected
    '''
    detect_marker(1)
    '''
    done by kunal
    after detection, pickup the object and return to the center position of the ground 
    to detect the next location (drop zone) to drop the object
    drop zone detection
    '''
    detect_marker(2)
    '''
    done by kunal
    after droping the object and return to the center position of the ground 
    to detect the next location (landing pad) to drop the object
    landing pad
    '''
    # if required else direct round 2
    detect_marker(0)
    '''
    
    '''