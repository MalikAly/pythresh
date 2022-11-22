import numpy as np
from sklearn.metrics import auc
from sklearn.utils import check_array

from .base import BaseThresholder
from .thresh_utility import cut, gen_kde, normalize


class AUCP(BaseThresholder):
    r"""AUCP class for Area Under Curve Precentage thresholder.

       Use the area under the curve to evaluate a non-parametric means
       to threshold scores generated by the decision_scores where outliers
       are set to any value beyond where the auc of the kde is less
       than the (mean + abs(mean-median)) percent of the total kde auc.
       See :cite:`ren2018aucp` for details

       Parameters
       ----------

       Attributes
       ----------

       thresh_ : threshold value that separates inliers from outliers

       Notes
       -----

       The area under the curve (AUC) is defined as follows:

       .. math::

          AUC = \mathrm{lim}_{x\rightarrow\inf} \sum_{i=1}^{n} f(x) \delta x \mathrm{,}

       where :math:`f(x)` is the curve and :math:`\delta x` is the incremental step size
       of the rectangles whose areas will be summed up. The AUCP method generates a
       curve using the pdf of the normalized decision scores over a range of 0-1.
       This is done with a kernel density estimation. The incremental size step is
       :math:`1/2n`, with :math:`n` being the number of points of the decision scores.

       The AUC is continuously calculated in steps from the left to right of the data
       range starting from 0. The stopping limit is set to
       :math:`\mathrm{lim} = \bar{x} + \lvert \bar{x}-\tilde{x} \rvert`, where :math:`\bar{x}`
       is the mean decision score, and :math:`\tilde{x}` is the median decision score.

       The first AUC that is greater than the total AUC of the pdf multiplied by the
       :math:`\mathrm{lim}` is set as the threshold between inliers and outliers.


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

        # Generate KDE
        val, dat_range = gen_kde(decision, 0, 1, len(decision)*2)
        val = normalize(val)

        # Get the total area under the curve
        tot_area = auc(dat_range, val)

        # Get area percentage limit
        mean = np.mean(decision)
        perc = mean+abs(mean-np.median(decision))

        # Apply the limit to where the area is less than that limit percentage
        # of the total area under the curve
        limit = 1
        for i in range(len(dat_range)):

            splt_area = auc(dat_range[i:], val[i:])

            if splt_area < perc*tot_area:
                limit = dat_range[i]
                break

        self.thresh_ = limit

        return cut(decision, limit)
