import math
import os
import pickle
import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np

CALIBRATION_FILE = "hand_range.calib"


class Camera:
    GESTURE = {
        "bass": [0, 0, 0, 0, 0],
        "mid": [0, 1, 0, 0, 0],
        "treble": [0, 0, 0, 0, 1],
        "all": [1, 1, 1, 1, 1],
        "toggle": [1, 1, 0, 0, 1]  # gesture to turn on/off adjustment mode
    }

    EQ_RANGE = [0, 100]
    VOLUME_RANGE = (-50, 50)
    INITIAL_VOLUME_ANGLE = 60

    def __init__(self, camera):
        self.camera = camera
        self.detector = HandDetector(detectionCon=0.6, maxHands=2)

        self.adjust_mode = False
        self.prev_toggle_state = False
        self.toggle_cooldown = 0
        self.right_hand_range = [0, 0]
        self.palm_size = 0

    def open(self, width=720, height=480):
        self.vc = cv2.VideoCapture(self.camera)

        self.width = width
        self.height = height
        self.vc.set(3, width)
        self.vc.set(4, height)

        return self.vc.isOpened()

    def read(self, negative=False):
        rval, frame = self.vc.read()
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if negative:
                frame = cv2.bitwise_not(frame)

            self.current_frame = frame
            return frame

    def initializeHandDetection(self, frame):
        hands, frame_copy = self.detector.findHands(frame)

        INIT_CONTROL_GESTURES = {
            "[1, 1, 1, 1, 1]": "max",
            "[1, 0, 0, 0, 0]": "min",
            "[0, 0, 0, 0, 0]": "done"
        }

        if len(hands) == 2:
            hand1, hand2 = hands
            if hand1["center"][0] < hand2["center"][0]:
                left_hand = hand2
                right_hand = hand1
            else:
                left_hand = hand1
                right_hand = hand2

            fingers_left = self.detector.fingersUp(left_hand)
            if str(fingers_left) not in INIT_CONTROL_GESTURES.keys():
                return False

            gesture = INIT_CONTROL_GESTURES[str(fingers_left)]

            if gesture == "done":
                return True

            thumb_index_distance, _, frame_copy = self.detector.findDistance(
                right_hand["lmList"][8][:-1],
                right_hand["lmList"][4][:-1],
                frame_copy
            )

            self.palm_size, _, _ = self.detector.findDistance(
                right_hand["lmList"][0][:-1],
                right_hand["lmList"][5][:-1],
                frame_copy
            )

            if gesture == "min":
                self.right_hand_range[0] = thumb_index_distance
            else:
                self.right_hand_range[1] = thumb_index_distance

        return False

    def handDetection(self, frame):
        hands, frame_copy = self.detector.findHands(frame)

        freq_band = "none"
        gain = 0.5
        volume = 0.5

        if len(hands) == 2:
            hand1, hand2 = hands
            if hand1["center"][0] < hand2["center"][0]:
                left_hand = hand2
                right_hand = hand1
            else:
                left_hand = hand1
                right_hand = hand2

            fingers_left = self.detector.fingersUp(left_hand)
            # == Adjustment Mode ==
            if fingers_left == self.GESTURE["toggle"]:
                if not self.prev_toggle_state and self.toggle_cooldown == 0:
                    self.adjust_mode = not self.adjust_mode
                    self.toggle_cooldown = 20
                self.prev_toggle_state = True
            else:
                self.prev_toggle_state = False

            if self.toggle_cooldown > 0:
                self.toggle_cooldown -= 1

            # == EQ and Volume Control ==

            if self.adjust_mode:
                for control, gesture in self.GESTURE.items():
                    if fingers_left == gesture:
                        freq_band = control

                        if control == "all":  # adjust the volume
                            wrist = np.array(right_hand['lmList'][0])
                            middle_tip = np.array(right_hand['lmList'][12])

                            dx = middle_tip[0] - wrist[0]
                            dy = middle_tip[1] - wrist[1]
                            angle = - \
                                math.degrees(math.atan2(dy, dx)) - \
                                self.INITIAL_VOLUME_ANGLE
                            angle_clamped = max(
                                self.VOLUME_RANGE[0], min(self.VOLUME_RANGE[1], angle))

                            volume = (
                                angle_clamped - self.VOLUME_RANGE[0]) / (self.VOLUME_RANGE[1] - self.VOLUME_RANGE[0])

                        else:  # adjust the eq
                            thumb_index_distance, info, frame_copy = self.detector.findDistance(
                                right_hand["lmList"][8][:-1],
                                right_hand["lmList"][4][:-1],
                                frame_copy
                            )

                            palm_size, _, _ = self.detector.findDistance(
                                right_hand["lmList"][0][:-1],
                                right_hand["lmList"][5][:-1],
                                frame_copy
                            )
                            scale = palm_size / self.palm_size
                            resized_range = [x*scale for x in self.right_hand_range]
                            gain = self.EQ_RANGE[0]+((thumb_index_distance-resized_range[0])*(
                                self.EQ_RANGE[1]-self.EQ_RANGE[0]))/(resized_range[1]-resized_range[0])
                        break

        return frame_copy, freq_band, gain, volume, self.adjust_mode
