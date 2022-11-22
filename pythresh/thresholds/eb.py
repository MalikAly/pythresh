import numpy as np
from sklearn.utils import check_array

from .base import BaseThresholder
from .thresh_utility import cut, gen_kde, normalize


class EB(BaseThresholder):
    r"""EB class for Elliptical Boundary thresholder.

       Use pseudo-random elliptical boundaries to evaluate a non-parametric means
       to threshold scores generated by the decision_scores where outliers
       are set to any value beyond a pseudo-random elliptical boundary set
       between inliers and outliers. See :cite:`friendly2013eb` for details.

       Parameters
       ----------

       Attributes
       ----------

       thresh_ : threshold value that separates inliers from outliers

       Notes
       -----

       Pseudo-random eccentricities are used to generate elliptical boundaries
       and threshold the decision scores. This is done by using the farthest
       point on the perimeter of an ellipse from its center and is defined as:

       .. math::

          A=a(1+e) \mathrm{,}

       where :math:`e` is the eccentricity and :math:`a` is the semi-major axis.
       If the decision scores are normalized the farthest point on the perimeter
       of an ellipse from its center is equal to 1, and the semi-major
       axis can be solved. The threshold is then set as the closest point on the
       perimeter of an ellipse from its center.

       This is repeated with Monte Carlo simulations and the median number of inliers
       is selected from these thresholds. The pseudo-random eccentricity that produces
       a threshold that is closest to median sampled inlier count is applied as the
       output threshold.

    """

    def __init__(self):

        pass

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

        # Generate random set of eccentricities to test
        np.random.seed(1234)
        rnd = np.random.uniform(0, 1, 5000)

        # Create pseudo-random elliptical boundaries using each eccentricity
        # and compute the inlier/outlier labels
        counts = []  # Get number of inliers
        for i in range(5000):
            e = rnd[i]
            a = 1/(1+e)
            lb = cut(decision, a*(1-e))
            counts.append(len(decision)-np.sum(lb))

        # Calculate the median count of expected inliers
        med = np.round(np.median(counts))
        ec = np.linspace(0, 1, 5000)

        # Randomly find eccentricity that generates
        # the closest value to the median inliers
        close = 0
        for i in range(5000):
            e = ec[i]
            a = 1/(1+e)
            lb = cut(decision, a*(1-e))
            count = len(decision)-np.sum(lb)
            if abs(med-count) < abs(med-close):
                close = count
                limit = a*(1-e)

        self.thresh_ = limit

        return cut(decision, limit)
