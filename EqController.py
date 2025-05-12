import numpy as np
from scipy import signal


class EQController:
    def __init__(self, fs,
                 low_cut=200.0, mid_center=1000.0, mid_bandwidth=800.0,
                 high_cut=None, order=2, limiter_threshold_db=-1.0):
        """
        fs: Sampling frequency in Hz.
        low_cut: Upper edge of low band in Hz (default 200).
        mid_center: Center frequency of mid band in Hz.
        mid_bandwidth: Bandwidth of mid band in Hz (full width) around center.
        high_cut: Lower edge of high band in Hz; if None, computed as mid_center + mid_bandwidth/2.
        order: Filter order per section (default 2).
        limiter_threshold_db: Threshold in dBFS for the built-in limiter (default -1 dB).
        """
        self.fs = fs
        self.low_cut = low_cut
        self.mid_center = mid_center
        self.mid_bandwidth = mid_bandwidth
        self.high_cut = high_cut if high_cut is not None else mid_center + mid_bandwidth/2
        self.order = order

        # Limiter parameters
        self.limiter_enabled = True
        self.limiter_threshold = self.db_to_linear(limiter_threshold_db)

        # Default gains (linear scale)
        self.gain_low = 1.0
        self.gain_mid = 1.0
        self.gain_high = 1.0

        # Initialize filters
        self._design_filters()

    @staticmethod
    def db_to_linear(db):
        """Convert gain in dB to linear scale."""
        return 10 ** (db / 20.0)

    def _design_filters(self):
        """Design the SOS filters based on current band edges."""
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
        """
        Set boost/cut for each band in dB. Positive = boost, negative = cut.
        """
        self.gain_low = self.db_to_linear(low_db)
        self.gain_mid = self.db_to_linear(mid_db)
        self.gain_high = self.db_to_linear(high_db)

    def set_low_cut(self, low_cut):
        """
        Set new cutoff frequency for the low band (Hz) and redesign filters.
        """
        self.low_cut = low_cut
        self._design_filters()

    def set_mid_bandwidth(self, mid_center=None, mid_bandwidth=None):
        """
        Adjust mid band center frequency and/or bandwidth (Hz), then redesign filters.
        mid_center: new center freq in Hz.
        mid_bandwidth: new full bandwidth in Hz.
        """
        if mid_center is not None:
            self.mid_center = mid_center
        if mid_bandwidth is not None:
            self.mid_bandwidth = mid_bandwidth
        # Update high_cut based on new mid upper edge
        self.high_cut = self.mid_center + self.mid_bandwidth/2
        self._design_filters()

    def set_high_cut(self, high_cut):
        """
        Set new cutoff frequency for the high band (Hz) and redesign filters.
        """
        self.high_cut = high_cut
        self._design_filters()

    def set_limiter(self, threshold_db=-1.0, enabled=True):
        """
        Configure limiter threshold in dBFS and enable/disable it.
        """
        self.limiter_threshold = self.db_to_linear(threshold_db)
        self.limiter_enabled = enabled

    def apply_limiter(self, x):
        """
        Simple peak limiter: hard clip at +/- threshold.
        x: numpy array of samples.
        """
        if not self.limiter_enabled:
            return x
        return np.clip(x, -self.limiter_threshold, self.limiter_threshold)

    def process(self, x):
        """
        Apply the 3-band EQ and limiter to input signal x (1D numpy array).
        Returns equalized and limited signal.
        """
        # Ensure input is float
        x = np.asarray(x, dtype=np.float64)

        # Filter each band
        low = signal.sosfilt(self.sos_low, x)
        mid = signal.sosfilt(self.sos_mid, x)
        high = signal.sosfilt(self.sos_high, x)

        # Sum bands with gains
        out = self.gain_low * low + self.gain_mid * mid + self.gain_high * high

        # Apply limiter
        return self.apply_limiter(out)
