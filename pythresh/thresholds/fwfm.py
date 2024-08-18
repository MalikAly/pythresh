from scipy.signal import find_peaks, peak_widths

from .base import BaseThresholder
from .thresh_utility import check_scores, cut, gen_kde, normalize


class FWFM(BaseThresholder):
    """FWFM class for Full Width at Full Minimum thresholder.

       Use the full width at full minimum (aka base width) to evaluate
       a non-parametric means to threshold scores generated by the
       decision_scores where outliers are set to any value beyond the base
       width. See :cite:`joneidi2013fwfm` for details.

       Parameters
       ----------

       random_state : int, optional (default=1234)
            Random seed for the random number generators of the thresholders. Can also
            be set to None.

       Attributes
       ----------

       thresh_ : threshold value that separates inliers from outliers

       dscores_ : 1D array of decomposed decision scores

       Notes
       -----

       The outlier detection scores are assumed to be a mixture of Gaussian
       distributions. The probability density function of this Gaussian mixture
       is approximated using kernel density estimation. The highest peak within the
       PDF is used to find the base width of the mixture and the threshold is set
       to the base width divided by the number of scores.
    """

    def __init__(self, random_state=1234):

        self.random_state = random_state

    def eval(self, decision):
        """Outlier/inlier evaluation process for decision scores.

        Parameters
        ----------
        decision : np.array or list of shape (n_samples)
                   or np.array of shape (n_samples, n_detectors)
                   which are the decision scores from a
                   outlier detection.

        Returns
        -------
        outlier_labels : numpy array of shape (n_samples,)
            For each observation, tells whether or not
            it should be considered as an outlier according to the
            fitted model. 0 stands for inliers and 1 for outliers.
        """

        decision = check_scores(decision, random_state=self.random_state)

        decision = normalize(decision)

        self.dscores_ = decision

        # Generate KDE
        val, _ = gen_kde(decision, -1, 1, len(decision)*3)
        val = normalize(val)

        # Find the greatest peak of the KDE
        peaks, _ = find_peaks(val, prominence=0.75)

        # Find the base width of the peak
        base_width = peak_widths(val, peaks, rel_height=0.99)[0]

        # Normalize and set limit
        limit = base_width[0]/len(val) if len(base_width) > 0 else 1.1

        self.thresh_ = limit

        return cut(decision, limit)
