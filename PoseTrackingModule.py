"""
Pose Module
By: Computer Vision Zone
Website: https://www.computervision.zone/
"""
import cv2
import mediapipe as mp
import numpy as np

class PoseDetector:
    """
    Estimates Pose points of a human body using the mediapipe library.
    """
    def __init__(self, mode=False, smooth=True, detectionCon=0.5, trackCon=0.5):
        """
        :param mode: In static mode, detection is done on each image:
        slower
        :param upBody: Upper boy only flag
        :param smooth: Smoothness Flag
        :param detectionCon: Minimum Detection Confidence Threshold
        :param trackCon: Minimum Tracking Confidence Threshold
        """
        self.mode = mode
        self.smooth = smooth
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(
            static_image_mode=self.mode,
            smooth_landmarks=self.smooth,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon,
        )

    def findPose(self, img, draw=True):
        """
        Find the pose landmarks in an Image of BGR color space.
        :param img: Image to find the pose in.
        :param draw: Flag to draw the output on the image.
        :return: Image with or without drawings
        """
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        if self.results.pose_landmarks:
            if draw:
                self.mpDraw.draw_landmarks(
                    img, self.results.pose_landmarks, self.mpPose.POSE_CONNECTIONS
                )
        return img

    #added the (ret_angles and angleLandmarks parameters) 
    # and extra lanmark point "center_shoulder", also added calcAngles function
    def findPosition(self, img, draw=True, bboxWithHands=False, ret_angles = False, angleLandmarks = []):
        '''ret_angles = True will return angles of the body parts that are in angleLandmarks list,
           angleLandmarks is the list of body parts for which angles are to be calculated'''
        self.lmList = []
        self.bboxInfo = {}
        if self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = img.shape
                cx, cy, cz = int(lm.x * w), int(lm.y * h), int(lm.z * w)
                self.lmList.append([id, cx, cy, cz])

            # Bounding Box
            ad = abs(self.lmList[12][1] - self.lmList[11][1]) // 2
            if bboxWithHands:
                x1 = self.lmList[16][1] - ad
                x2 = self.lmList[15][1] + ad
            else:
                x1 = self.lmList[12][1] - ad
                x2 = self.lmList[11][1] + ad
            y2 = self.lmList[29][2] + ad
            y1 = self.lmList[1][2] - ad
            bbox = (x1, y1, x2 - x1, y2 - y1)
            cx, cy = bbox[0] + (bbox[2] // 2), bbox[1] + bbox[3] // 2
            self.bboxInfo = {"bbox": bbox, "center": (cx, cy)}

            # center_shoulder is the center of the line joining the two shoulders
            center_shoulder = (self.lmList[11][1] + self.lmList[12][1])//2, (self.lmList[11][2] + self.lmList[12][2])//2 

            """angleLandmarksMapping is a dictionary that maps body parts to the list of landmarks that are used to calculate the angles"""
            angleLandmarksMapping = {'right_shoulder':("extra_point",11,13), #extra_point is the center_shoulder landmark which we created.
                                     'left_shoulder':("extra_point",12,14),
                                     'right_elbow':(11,13,15),
                                     'left_elbow':(12,14,16), 
                                     'right_knee':(23,25,27),
                                     'left_knee':(24,26,28),
                                     'head':(0,"extra_point",12)} 

            def calcAngles(bodyPartLandmarks):
                """bodyPartLandmarks is a list of body parts for which angles are to be calculated 
                This function returns a list of angles in degrees for the body parts in bodyPartLandmarks"""
                angles_list = []
                for part in bodyPartLandmarks:
                    line_coordinates = [] #list of coordinates of the points on the body part
                    if part in angleLandmarksMapping: #check if the body part is in the dictionary
                        listLandmarks = angleLandmarksMapping[part] #list of landmarks that are used to calculate the angle
                        for landmark in listLandmarks:
                            if landmark == "extra_point":
                                line_coordinates.append(center_shoulder)
                            else:
                                line_coordinates.append((self.lmList[landmark][1],self.lmList[landmark][2]))
                        
                        #making every line coordinate as numpy arrays 
                        A = np.array(line_coordinates[0])
                        B = np.array(line_coordinates[1])
                        C = np.array(line_coordinates[2])

                        AB = B-A #vector AB = B-A
                        BC = C-B #vector BC = C-B

                        cosine_angle = np.dot(AB, BC) / (np.linalg.norm(AB) * np.linalg.norm(BC)) #cosine of the angle between AB and BC
                        angle = np.arccos(cosine_angle)
                        angle_degrees = np.degrees(angle)
                        angles_list.append(angle_degrees)
                    else:
                        raise Exception("Please provide valid body part")#if the body part is not in the dictionary
                return angles_list  #return list of angles in degrees       
                

            if ret_angles:
                if angleLandmarks == []:
                    raise Exception("Please provide angleLandmarks")
                else:
                    angles = []
                    angles.append(calcAngles(angleLandmarks))
                
            if draw:
                cv2.circle(img, center_shoulder,5, (255, 0, 0), cv2.FILLED) #drawing a circle on center_shoulder point
                cv2.line(img, center_shoulder,(self.lmList[0][1],self.lmList[0][2]), (0, 255, 0), thickness=3, lineType=8) #drawing a line from center_shoulder to nose
                cv2.rectangle(img, bbox, (255, 0, 255), 3) #drawing a bounding box
                cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED) #center of the bounding box

                # #displaying angles on the image
                # text =''
                # for i in angleLandmarks:
                #     text += str(i) + " : " + str(angles[0][angleLandmarks.index(i)]) + "\n"
                # lines = text.split("\n")
                # x_pos, y_pos = 20,20
                # for line in lines:
                #     cv2.putText(img, line, (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                #     y_pos += 20 #line_height
                
                #returning the list of angles in degrees, bounding box info and landmark list
                if ret_angles:
                    return self.lmList, self.bboxInfo, angles 
                return self.lmList, self.bboxInfo
                