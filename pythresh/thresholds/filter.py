import numpy as np
import scipy.stats as stats
from scipy import signal
from scipy.ndimage import gaussian_filter
from sklearn.utils import check_array
from .base import BaseThresholder
from .thresh_utility import normalize, cut


class FILTER(BaseThresholder):
    """FILTER class for Filtering based thresholders.

       Use the filtering based methods to evaluate a non-parametric means
       to threshold scores generated by the decision_scores where outliers
       are set to any value beyond the maximum filter value.
       See :cite:`hashemi2019filter` for details.

       Parameters
       ----------

       method : {'gaussian', 'savgol', 'hilbert', 'wiener', 'medfilt', 'decimate','detrend', 'resample'}, optional (default='wiener')
            Method to filter the scores

            - 'gaussian': use a gaussian based filter
            - 'savgol':   use the savgol based filter
            - 'hilbert':  use the hilbert based filter
            - 'wiener':   use the wiener based filter
            - 'medfilt:   use a median based filter
            - 'decimate': use a decimate based filter
            - 'detrend':  use a detrend based filter
            - 'resample': use a resampling based filter


       sigma : int, optional (default='auto')
            Variable specific to each filter type, default sets sigma to len(scores)*np.std(scores)

            - 'gaussian': standard deviation for Gaussian kernel
            - 'savgol':   savgol filter window size
            - 'hilbert':  number of Fourier components
            - 'medfilt:   kernel size
            - 'decimate': downsampling factor
            - 'detrend':  number of break points
            - 'resample': resampling window size

       Attributes
       ----------

       thresh_ : threshold value that separates inliers from outliers

    """

    def __init__(self, method='wiener', sigma='auto'):

        super(FILTER, self).__init__()
        self.method = method
        self.method_funcs = {'gaussian': self._GAU_fltr, 'savgol': self._SAV_fltr,
                             'hilbert': self._HIL_fltr, 'wiener': self._WIE_fltr,
                             'medfilt': self._MED_fltr, 'decimate': self._DEC_fltr,
                             'detrend': self._DET_fltr, 'resample': self._RES_fltr}

        self.sigma = sigma

    def eval(self, decision):
        """Outlier/inlier evaluation process for decision scores.

        Parameters
        ----------
        decision : np.array or list of shape (n_samples)
                   which are the decision scores from a
                   outlier detection.

        Returns
        -------
        outlier_labels : numpy array of shape (n_samples,)
            For each observation, tells whether or not
            it should be considered as an outlier according to the
            fitted model. 0 stands for inliers and 1 for outliers.
        """

        decision = check_array(decision, ensure_2d=False)

        decision = normalize(decision)

        # Get sigma variables for various applications for each filter
        sig = self.sigma
        if self.sigma=='auto':
            sig = len(decision)*np.std(decision)

        # Filter scores
        fltr = self.method_funcs[str(self.method)](decision, sig)
        limit = np.max(fltr)

        self.thresh_ = limit

        return cut(decision, limit)

    def _GAU_fltr(self, decision, sig):
        """Gaussian filter scores"""

        return gaussian_filter(decision, sigma=sig)

    def _SAV_fltr(self, decision, sig):
        """Savgol filter scores"""

        if self.sigma=='auto':
            sig = round(0.5*sig)

        if sig%2==0:
            sig+=1

        return signal.savgol_filter(decision, window_length=round(sig),
                                        polyorder=1)

    def _HIL_fltr(self, decision, sig):
        """Hilbert filter scores"""

        return signal.hilbert(decision, N=round(sig))

    def _WIE_fltr(self, decision, sig):
        """Wiener filter scores"""

        return signal.wiener(decision, mysize=len(decision))

    def _MED_fltr(self, decision, sig):
        """Medfilt filter scores"""

        sig = round(sig)

        if sig%2==0:
            sig+=1

        return signal.medfilt(decision, kernel_size=[sig])


    def _DEC_fltr(self, decision, sig):
        """Decimate filter scores"""

        return signal.decimate(decision, q=round(sig), ftype='fir')

    def _DET_fltr(self, decision, sig):
        """Detrend filter scores"""

        return signal.detrend(decision, bp=np.linspace(0,len(decision)-1,round(sig)).astype(int))

    def _RES_fltr(self, decision, sig):
        """Resampling filter scores"""

        if self.sigma=='auto':
            return signal.resample(decision, num=round(np.sqrt(len(decision))),
                                window=round(np.sqrt(sig)))
        else:
            return signal.resample(decision, num=round(np.sqrt(len(decision))),
                                window=round(sig))
