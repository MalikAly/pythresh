import numpy as np
import scipy.stats as stats
from sklearn.utils import check_array
from .base import BaseThresholder
from .thresh_utility import normalize, cut

# https://github.com/bhattbhavesh91/outlier-detection-grubbs-test-and-generalized-esd-test-python/blob/master/generalized-esd-test-for-outliers.ipynb

class GESD(BaseThresholder):
    """GESD class for Generalized Extreme Studentized Deviate thresholder.

       Use the generalized extreme studentized deviate to evaluate a
       non-parametric means to threshold scores generated by the decision_scores
       where outliers are set to any less than the smallest detected outlier
       
       Paramaters
       ----------

       max_outliers : int, optional (default='native')
            mamiximum number of outliers that the dataset may have. Default sets 
            max_outliers to be set to half the size of the dataset

       alpha : float, optional (default=0.05)
            significance level

       Attributes
       ----------

       eval_: numpy array of binary labels of the training data. 0 stands
           for inliers and 1 for outliers/anomalies.

    """

    def __init__(self, max_outliers='native', alpha=0.05):

        self.max_outliers = max_outliers
        self.alpha = alpha


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

        arr = decision.copy()

        limit = 1.1

        if self.max_outliers=='native':
            self.max_outliers = int(len(decision)/2)

        for i in range(self.max_outliers):
            Gc = self._calc_crit(len(arr), self.alpha)
            Gs, max_index = self._grubbs_stat(arr)
            
            if (Gs>Gc) & (arr[max_index]<limit):
                limit = arr[max_index]
            arr = np.delete(arr, max_index)

        self.thresh_ = limit

        return cut(decision, limit)
    
    def _grubbs_stat(self, y):
    
        dev = np.abs(y - y.mean())
        max_ind = np.argmax(dev)
        Gcal = np.max(dev)/ y.std()

        return Gcal, max_ind

    def _calc_crit(self, size, alpha):
    
        t_dist = stats.t.ppf(1 - alpha / (2 * size), size - 2)
        numerator = (size - 1) * np.sqrt(np.square(t_dist))
        denominator = np.sqrt(size) * np.sqrt(size - 2 + np.square(t_dist))
        critical_value = numerator / denominator

        return critical_value
