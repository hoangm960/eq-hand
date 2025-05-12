import multiprocessing
import threading
from PyQt6 import uic
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox, QFileDialog
from PyQt6.QtGui import QPixmap, QImage

from AudioPlayer import AudioPlayer
from EqController import EQController


class UI_Window(QMainWindow):

    def __init__(self, camera=None):
        super().__init__()
        uic.loadUi("GUI.ui", self)
        self.camera = camera
        # Create a timer.
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)

        self.initialized = False
        self.initialize_button.clicked.connect(self.start)

        self.audio_file = ""
        self.eq_controller = EQController()
        self.player = None
        self.insert_button.clicked.connect(self.insertAudio)

        self.is_played = False
        self.play_thread = None
        self.play_button.clicked.connect(self.playAudio)

    def start(self):
        if self.initialized:
            self.initialized = False
            return

        if not self.camera.open():
            print('failure')
            msgBox = QMessageBox()
            msgBox.setText("Failed to open camera.")
            msgBox.exec_()
            return

        self.timer.start(int(1000/24))

    def insertAudio(self):
        self.audio_file = QFileDialog.getOpenFileName(self, 'Open file',
         'c:\\',"Audio files (*.mp3)")[0]
        if not self.audio_file:
            return

        self.player = AudioPlayer(self.audio_file, self.eq_controller)

    def playAudio(self):
        if not self.player:
            return

        if self.is_played:
            self.player.stop()
        elif not self.play_thread:
            self.play_thread = threading.Thread(target=self.player.play, daemon=True)
            self.play_thread.start()
        self.is_played = not self.is_played

    def nextFrameSlot(self):
        frame = self.camera.read()
        if frame is not None:
            if not self.initialized:
                self.initialized = self.camera.initializeHandDetection(frame)
                if self.initialized:
                    self.initialize_button.setText("ReInitialize?")
            elif self.player:
                frame, freq_band, gain, volume, adjust_mode = self.camera.handDetection(
                    frame)

                if adjust_mode and self.activated_label.text() == "OFF":
                    self.activated_label.setText("ON")
                elif not adjust_mode and self.activated_label.text() == "ON":
                    self.activated_label.setText("OFF")

                if not freq_band in ["none", "toggle"]:
                    if freq_band == "all":
                        self.player.set_volume(volume)
                        self.player.get_volume()

                        self.volume_slider.setValue(int(volume*100))
                    else:
                        self.eq_controller.set_band(freq_band)
                        self.eq_controller.set_gain(gain)

                        UI_SLIDER_BANDS = {
                            "bass": self.low_gain_slider,
                            "mid": self.band_gain_slider,
                            "treble": self.high_gain_slider,
                        }
                        UI_SLIDER_BANDS[freq_band].setValue(int(-20 + (gain / 100.0) * 30))

            image = QImage(
                frame, frame.shape[1], frame.shape[0], QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.cam_display.setPixmap(pixmap)



if __name__ == '__main__':
    app = QApplication([])
    window = UI_Window()
    window.show()
