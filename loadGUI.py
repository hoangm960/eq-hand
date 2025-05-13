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
        self.eq_controller = None
        self.player = None
        self.insert_button.clicked.connect(self.insertAudio)

        self.is_played = False
        self.play_thread = None
        self.play_button.clicked.connect(self.playAudio)

        self.volume_slider.valueChanged.connect(self.setVolume)
        self.high_freq_slider.valueChanged.connect(self.setHighFrequency)
        self.high_gain_slider.valueChanged.connect(self.setHighGain)
        self.band_freq_slider.valueChanged.connect(self.setMidFrequency)
        self.band_bandwidth_slider.valueChanged.connect(self.setMidBandwidth)
        self.band_gain_slider.valueChanged.connect(self.setMidGain)
        self.low_freq_slider.valueChanged.connect(self.setLowFrequency)
        self.low_gain_slider.valueChanged.connect(self.setLowGain)

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
        self.audio_file = QFileDialog.getOpenFileName(
            self,
            'Open file',
            '${HOME}',
            "Audio files (*.mp3)"
        )[0]

        if not self.audio_file:
            return

        self.pauseAudio()
        self.eq_controller = EQController(44100)
        self.player = AudioPlayer(self.audio_file, self.eq_controller)

    def pauseAudio(self):
        if self.player:
            self.player.stop()
            if self.play_thread:
                self.play_thread = None

    def playAudio(self):
        if not self.player:
            return

        if self.is_played:
            self.pauseAudio()
        elif not self.play_thread:
            self.play_thread = threading.Thread(
                target=self.player.play, daemon=True)
            self.play_thread.start()
        self.is_played = not self.is_played

    def setVolume(self, value):
        if not self.player:
            return

        self.player.set_volume(value/100)

    def setHighFrequency(self, value):
        if not self.eq_controller:
            return

        self.eq_controller.set_high_cut(value)

    def setHighGain(self, value):
        if not self.eq_controller:
            return

        self.eq_controller.set_gain(high_db=value)

    def setMidFrequency(self, value):
        if not self.eq_controller:
            return

        self.eq_controller.set_mid_bandwidth(value)

    def setMidBandwidth(self, value):
        if not self.eq_controller:
            return

        self.eq_controller.set_mid_bandwidth(mid_bandwidth=value)

    def setMidGain(self, value):
        if not self.eq_controller:
            return

        self.eq_controller.set_gain(mid_db=value)

    def setLowFrequency(self, value):
        if not self.eq_controller:
            return

        self.eq_controller.set_low_cut(value)

    def setLowGain(self, value):
        if not self.eq_controller:
            return

        self.eq_controller.set_gain(low_db=value)

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
                        self.volume_slider.setValue(int(volume*100))
                    else:
                        gain_db = int(-20 + (gain / 100.0) * 30)
                        if freq_band == "bass":
                            self.eq_controller.set_gain(low_db=gain_db)
                        elif freq_band == "mid":
                            self.eq_controller.set_gain(mid_db=gain_db)
                        elif freq_band == "treble":
                            self.eq_controller.set_gain(high_db=gain_db)

                        UI_SLIDER_BANDS = {
                            "bass": self.low_gain_slider,
                            "mid": self.band_gain_slider,
                            "treble": self.high_gain_slider,
                        }
                        UI_SLIDER_BANDS[freq_band].setValue(gain_db)

            image = QImage(
                frame, frame.shape[1], frame.shape[0], QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.cam_display.setPixmap(pixmap)


if __name__ == '__main__':
    app = QApplication([])
    window = UI_Window()
    window.show()
