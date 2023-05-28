import numpy as np
import scipy.stats as stats
from sklearn.utils import check_array

from .base import BaseThresholder
from .thresh_utility import cut, normalize

# https://github.com/vvaezian/modified_thompson_tau_test/blob/main/src/Modified_Thompson_Tau_Test/modified_thompson_tau_test.py


class MTT(BaseThresholder):
    r"""MTT class for Modified Thompson Tau test thresholder.

       Use the modified Thompson Tau test to evaluate a non-parametric means
       to threshold scores generated by the decision_scores where outliers
       are set to any value beyond the smallest outlier detected by the test.
       See :cite:`rengasamy2020mtt` for details.

       Parameters
       ----------

       self.alpha : float, optional (default=0.99)
            Confidence level corresponding to the t-Student distribution map to sample

       Attributes
       ----------

       thresh_ : threshold value that separates inliers from outliers

       Notes
       -----

       The Modified Thompson Tau test is a modified univariate t-test that eliminates outliers
       that are more than a number of standard deviations away from the mean. This method is
       done iteratively with the Tau critical value being recalculated after each outlier removal
       until the dataset no longer has data points that fall outside of the criterion. The Tau
       critical value can be obtained by,

       .. math::

           \tau = \frac{t \cdot (n-1)}{\sqrt{n}\sqrt{n-2+t^2}}  \mathrm{,}

       where :math:`n` is the number of data points and :math:`t` is the student t-value

    """

    def __init__(self, alpha=0.99):

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

        arr = np.sort(decision.copy())

        limit = 1.1

        while True:

            # Calculate the rejection threshold
            n = len(arr)
            t = stats.t.ppf(self.alpha, df=n-2)
            thres = (t * (n - 1))/(np.sqrt(n) * np.sqrt(n - 2 + t**2))
            delta = np.abs(arr[-1] - arr.mean())/arr.std()

            if delta > thres:
                limit = arr[-1]
                arr = np.delete(arr, n-1)

            else:
                break

        self.thresh_ = limit

        return cut(decision, limit)
