from pydub import AudioSegment
import sounddevice as sd
import numpy as np
import threading


class AudioPlayer:
    def __init__(self, filename, eq_controller):
        self.eq_controller = eq_controller
        self.audio = AudioSegment.from_mp3(
            filename).set_channels(1).set_frame_rate(44100)
        self.samples = np.array(self.audio.get_array_of_samples()).astype(
            np.float32) / 32768.0
        self.fs = 44100
        self.volume = 1.0  # default volume 100%
        self.buffer_pos = 0
        self.stop_playback = False
        self.buffer_lock = threading.Lock()

    def callback(self, outdata, frames, time, status):
        if self.stop_playback or self.buffer_pos + frames > len(self.samples):
            outdata[:] = np.zeros((frames, 1))
            raise sd.CallbackStop()

        with self.buffer_lock:
            chunk = self.samples[self.buffer_pos:self.buffer_pos + frames]
            self.buffer_pos += frames
        # apply eq
        eq_chunk = self.eq_controller.process(chunk)
        # adjust volume
        eq_chunk *= self.volume
        eq_chunk = np.clip(eq_chunk, -1.0, 1.0)

        outdata[:] = eq_chunk.reshape(-1, 1)

    def set_volume(self, new_volume):
        with self.buffer_lock:
            self.volume = max(0.0, min(new_volume, 1.0))

    def get_volume(self):
        return self.volume

    def play(self):
        with sd.OutputStream(callback=self.callback,
                             channels=1, samplerate=self.fs,
                             blocksize=1024):
            sd.sleep(int(len(self.samples) / self.fs * 1000))

    def stop(self):
        self.stop_playback = True
