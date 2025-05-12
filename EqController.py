import numpy as np
from scipy import signal


class EQController:
    def __init__(self, fs,
                 low_cut=300.0, mid_center=2000.0, mid_bandwidth=800.0,
                 high_cut=10000, order=2, limiter_threshold_db=-1.0):
        self.fs = fs
        self.low_cut = low_cut
        self.mid_center = mid_center
        self.mid_bandwidth = mid_bandwidth
        self.high_cut = high_cut if high_cut is not None else mid_center + mid_bandwidth/2
        self.order = order

        self.limiter_enabled = True
        self.limiter_threshold = self.db_to_linear(limiter_threshold_db)

        self.gain_low = 1.0
        self.gain_mid = 1.0
        self.gain_high = 1.0

        self._design_filters()

    @staticmethod
    def db_to_linear(db):
        return 10 ** (db / 20.0)

    def _design_filters(self):
        # Ensure band edges are valid
        low_edge = max(0.0, self.mid_center - self.mid_bandwidth/2)
        high_edge = min(self.fs/2, self.mid_center + self.mid_bandwidth/2)
        # Clip low_cut and high_cut within (0, fs/2)
        lc = np.clip(self.low_cut, 0.0, self.fs/2)
        hc = np.clip(self.high_cut, 0.0, self.fs/2)

        # Lowpass for low band
        self.sos_low = signal.butter(self.order, lc,
                                     btype='low', fs=self.fs, output='sos')
        # Bandpass for mid band
        self.sos_mid = signal.butter(self.order, [low_edge, high_edge],
                                     btype='band', fs=self.fs, output='sos')
        # Highpass for high band
        self.sos_high = signal.butter(self.order, hc,
                                      btype='high', fs=self.fs, output='sos')

    def set_gain(self, low_db=0.0, mid_db=0.0, high_db=0.0):
        self.gain_low = self.db_to_linear(low_db)
        self.gain_mid = self.db_to_linear(mid_db)
        self.gain_high = self.db_to_linear(high_db)

    def set_low_cut(self, low_cut):
        self.low_cut = low_cut
        self._design_filters()

    def set_mid_bandwidth(self, mid_center=None, mid_bandwidth=None):
        if mid_center is not None:
            self.mid_center = mid_center
        if mid_bandwidth is not None:
            self.mid_bandwidth = mid_bandwidth
        # Update high_cut based on new mid upper edge
        self.high_cut = self.mid_center + self.mid_bandwidth/2
        self._design_filters()

    def set_high_cut(self, high_cut):
        self.high_cut = high_cut
        self._design_filters()

    def set_limiter(self, threshold_db=-1.0, enabled=True):
        self.limiter_threshold = self.db_to_linear(threshold_db)
        self.limiter_enabled = enabled

    def apply_limiter(self, x):
        if not self.limiter_enabled:
            return x
        return np.clip(x, -self.limiter_threshold, self.limiter_threshold)

    def process(self, x):
        x = np.asarray(x, dtype=np.float64)

        low = signal.sosfilt(self.sos_low, x)
        mid = signal.sosfilt(self.sos_mid, x)
        high = signal.sosfilt(self.sos_high, x)

        out = self.gain_low * low + self.gain_mid * mid + self.gain_high * high

        return self.apply_limiter(out)
