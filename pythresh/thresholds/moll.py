import numpy as np
import scipy.signal as signal
from scipy import integrate
from sklearn.utils import check_array
from .base import BaseThresholder
from .thresh_utility import normalize, cut, gen_kde

#https://github.com/geomdata/gda-public/blob/master/timeseries/curve_geometry.pyx

class MOLL(BaseThresholder):
    """MOLL class for Friedrichs' mollifier thresholder.

       Use the Friedrichs' mollifier to evaluate a non-parametric means
       to threshold scores generated by the decision_scores where outliers
       are set to any value beyond one minus the  maximum of the smoothed
       dataset via convolution
       
       Paramaters
       ----------

       Attributes
       ----------

       eval_: numpy array of binary labels of the training data. 0 stands
           for inliers and 1 for outliers/anomalies.

    """

    def __init__(self):

        pass

    def eval(self, decision):
        """Outlier/inlier evaluation process for decision scores.

        Parameters
        ----------
        
        Returns
        -------
        outlier_labels : numpy array of shape (n_samples,)
            For each observation, tells whether or not
            it should be considered as an outlier according to the
            fitted model. 0 stands for inliers and 1 for outliers.
        """

        decision = check_array(decision, ensure_2d=False)
        dat_range = np.linspace(0,1,len(decision))

        decision = normalize(decision)

        # Set the inliers to be where the 1-max(smoothed scores)
        limit = 1-np.max(self._mollifier(dat_range, np.sort(decision)))

        self.thresh_ = limit

        return cut(decision, limit)
    
    def _mollifier(self, time, position, refinement=5, width=1.0):

        N = len(position)

        delta = (time[-1]-time[0])/(N-1)

        ### compute boundary space padding
        left_pad = np.arange(time[0],time[0]-(width+delta),step=-delta)
        left_pad = np.flipud(left_pad)[:-1]
        left_pad_num = left_pad.shape[0]
        right_pad = np.arange(time[-1],time[-1]+(width+delta),step=delta)[1:]
        right_pad_num = right_pad.shape[0]
        time_pad = np.concatenate((left_pad,time,right_pad))

        ### compute boundary score padding
        position_pad = np.pad(position,(left_pad_num,right_pad_num),'edge')

        ### Define a new smaller space scale s, ds (here we a evenly spaced)
        s, ds = np.linspace(time_pad[0],time_pad[-1],
                            (refinement)*time_pad.shape[0],
                            retstep=True)
        right_pad_num = (refinement)*right_pad_num
        left_pad_num = (refinement)*left_pad_num
        position_interp = np.interp(s,time_pad,position_pad)

        ### Compute the mollifier kernel
        norm_const,err = integrate.quad(lambda x: np.exp(1.0/(x**2-1.0)),-1.0,1.0)
        norm_const = 1.0/norm_const

        ### Compute the mollifier rho
        p = np.abs((s - (s[0]+s[-1])/2.0)/width)
        r = np.zeros_like(s)
        q = p[p<1.0]
        r[p<1.0] = np.exp(1.0/(q**2-1.0))
        rho = (norm_const/width)*r

        ### Perform convolution to make smooth reconstruction
        if s.shape[0] > 500:
            smooth = signal.fftconvolve(ds*position_interp,rho,mode='same')
        else:
            smooth = np.convolve(ds*position_interp,rho,mode='same')

        ### remove padding
        s = s[left_pad_num:-right_pad_num]
        smooth = smooth[left_pad_num:-(right_pad_num)]

        return np.asarray(smooth)
