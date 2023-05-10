from PoseTrackingModule import PoseDetector
import cv2

def isPoseCorrect(ref_img_address,img, threshold=10):
    #lmList is the list of landmarks that we want to use for the comparison of angles
    lmList = ['head', 'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_knee', 'right_knee'] 
    min_correct_angles = 4 #minimum number of correct angles to be in the correct position

    # reference image for comparison of angles
    ref_detector = PoseDetector()
    ref_image = cv2.imread(ref_img_address)
    ref_image = ref_detector.findPose(ref_image)
    _,_,ref_angles = ref_detector.findPosition(ref_image, bboxWithHands=False, ret_angles=True, angleLandmarks=lmList) 
    # print("Reference angles", ref_angles)

    detector = PoseDetector()
    img = detector.findPose(img)
    try:
        _,_,angles = detector.findPosition(img,draw=True, bboxWithHands=True, ret_angles=True, angleLandmarks=lmList) 
    except TypeError:
        pass
    # print('liveImg angles',angles)
    
    #this if else block is to check if the user is in the correct position or not 
    incorrect_angles = []
    for i in range(len(angles[0])):
        angle, ref_angle = angles[0][i], ref_angles[0][i]
        if abs(angle - ref_angle) / ref_angle * 100 > threshold:
            incorrect_angles.append(i)
            # print("incorrect angles", lmList[i])
    # print("incorrect angles list", incorrect_angles)

    if (len(angles[0]) - len(incorrect_angles)) >= min_correct_angles:
        #if the minimum number of correct angles is met, user is in correct position
        cv2.putText(img,"User is in the correct position" , (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        return True
    else:
        cv2.putText(img,"User is not in the correct position" , (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        return False    


def main():
    pass
    

if __name__ == "__main__":
    main()