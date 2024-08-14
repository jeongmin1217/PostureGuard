import cv2
import mediapipe as mp
import numpy as np

# MediaPipe 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

def calculate_angle_3d(point1, point2, point3):
    """세 점의 3D 좌표를 받아 각도를 계산하는 함수"""
    a = np.array(point1)
    b = np.array(point2)
    c = np.array(point3)

    ba = a - b
    bc = c - b

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)
    
    return round(np.degrees(angle), 2)

def analyze_posture(image):
    """이미지를 받아서 자세 분석 결과를 반환하는 함수"""
    results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark

        left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y,
                         landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].z]
        right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                          landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y,
                          landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].z]
        left_ear = [landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].y,
                    landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].z]
        right_ear = [landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value].x,
                     landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value].y,
                     landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value].z]
        
        c7 = [(left_shoulder[0] + right_shoulder[0]) / 2,
              (left_shoulder[1] + right_shoulder[1]) / 2,
              (left_shoulder[2] + right_shoulder[2]) / 2]
        
        fhs_midpoint = [(left_shoulder[0] + right_shoulder[0]) / 2,
                        (left_shoulder[1] + right_shoulder[1]) / 2,
                        (left_shoulder[2] + right_shoulder[2]) / 2]
        
        # CVA 계산
        cva_left = calculate_angle_3d(left_ear, c7, [c7[0], c7[1], c7[2] - 0.1])
        cva_right = calculate_angle_3d(right_ear, c7, [c7[0], c7[1], c7[2] - 0.1])

        # FHA 계산
        fha_left = calculate_angle_3d(left_ear, fhs_midpoint, [fhs_midpoint[0] + 0.1, fhs_midpoint[1], fhs_midpoint[2]])
        fha_right = calculate_angle_3d(right_ear, fhs_midpoint, [fhs_midpoint[0] + 0.1, fhs_midpoint[1], fhs_midpoint[2]])
        
        # 자세가 올바른지 여부 판단
        posture_correct = (cva_left >= 50 or cva_right >= 50) and (fha_left >= 80 or fha_right >= 80)

        return cva_left, cva_right, fha_left, fha_right, "Yes" if posture_correct else "No"
    
    return None, None, None, None, "No"

