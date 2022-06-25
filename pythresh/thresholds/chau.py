import numpy as np
import scipy.stats as stats
from scipy.special import erfc 
from sklearn.utils import check_array
from .base import BaseThresholder
from .thresh_utility import normalize, cut


class CHAU(BaseThresholder):
    """CHAU class for Chauvenet's criterion thresholder.

       Use the Chauvenet's criterion to evaluate a non-parametric
       means to threshold scores generated by the decision_scores
       where outliers are set to any value below the Chauvenet's
       criterion

       Paramaters
       ----------

       method : {'mean', 'median', 'gmean'}, optional (default='mean')
            Calculate the area normal to distance using a scaler
       
            - 'mean':  Construct a scaler with the the mean of the scores
            - 'median: Construct a scaler with the the median of the scores
            - 'gmean': Construct a scaler with the geometric mean of the scores

       Attributes
       ----------

       eval_: numpy array of binary labels of the training data. 0 stands
           for inliers and 1 for outliers/anomalies.

    """

    def __init__(self, method='mean'):

        super(CHAU, self).__init__()
        stat = {'mean':np.mean, 'median':np.median, 'gmean':stats.gmean}
        self.method = stat[method]

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

        # Calculate Chauvenet's criterion for one tail
        Pz = 1/(4*len(decision))
        criterion = 1/abs(stats.norm.ppf(Pz))

        # Get area normal to distance
        prob = erfc(np.abs(decision-self.method(decision))/decision.std())

        self.thresh_ = criterion * (1-np.min(prob))/np.max(prob)

        return cut(prob, criterion)

