import numpy as np
from pyclustering.cluster.agglomerative import agglomerative
from pyclustering.cluster.bang import bang
from pyclustering.cluster.bsas import bsas
from pyclustering.cluster.dbscan import dbscan
from pyclustering.cluster.ema import ema
from pyclustering.cluster.mbsas import mbsas
from pyclustering.cluster.optics import optics
from pyclustering.cluster.somsc import somsc
from pyclustering.cluster.xmeans import xmeans
from scipy.spatial.distance import cityblock
from sklearn.cluster import (
    Birch,
    KMeans,
    MeanShift,
    SpectralClustering,
    estimate_bandwidth
)
from sklearn.mixture import BayesianGaussianMixture
from sklearn.utils import check_array

from .base import BaseThresholder
from .thresh_utility import normalize


class CLUST(BaseThresholder):
    """CLUST class for clustering type thresholders.

       Use the clustering methods to evaluate a non-parametric means to
       threshold scores generated by the decision_scores where outliers
       are set to any value not labelled as part of the main cluster.
       See :cite:`klawonn2008clust` for details.

       Parameters
       ----------

       method : {'agg', 'birch', 'bang', 'bgm', 'bsas', 'dbscan', 'ema', 'kmeans', 'mbsas', 'mshift', 'optics', 'somsc', 'spec', 'xmeans'}, optional (default='spec')
            Clustering method

            - 'agg':    Agglomerative
            - 'birch':  Balanced Iterative Reducing and Clustering using Hierarchies
            - 'bang':   BANG
            - 'bgm':    Bayesian Gaussian Mixture
            - 'bsas':   Basic Sequential Algorithmic Scheme
            - 'dbscan': Density-based spatial clustering of applications with noise
            - 'ema':    Expectation-Maximization clustering algorithm for Gaussian Mixture Model
            - 'kmeans': K-means
            - 'mbsas':  Modified Basic Sequential Algorithmic Scheme
            - 'mshift': Mean shift
            - 'optics': Ordering Points To Identify Clustering Structure
            - 'somsc':  Self-organized feature map
            - 'spec':   Clustering to a projection of the normalized Laplacian
            - 'xmeans': X-means

       random_state : int, optional (default=1234)
            Random seed for the BayesianGaussianMixture clustering (method='bgm'). Can
            also be set to None.

       Attributes
       ----------

       thresh_ : threshold value that separates inliers from outliers

    """

    def __init__(self, method='spec', random_state=1234):

        super(CLUST, self).__init__()
        self.method = method
        self.method_funcs = {'agg': self._AGG_clust, 'birch': self._BIRCH_clust,
                             'bang': self._BANG_clust, 'bgm': self._BGM_clust,
                             'bsas': self._BSAS_clust, 'dbscan': self._DBSCAN_clust,
                             'ema': self._EMA_clust, 'kmeans': self._KMEANS_clust,
                             'mbsas': self._MBSAS_clust, 'mshift': self._MSHIFT_clust,
                             'optics': self._OPTICS_clust, 'somsc': self._SOMSC_clust,
                             'spec': self._SPEC_clust, 'xmeans': self._XMEANS_clust}
        self.random_state = random_state

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

        decision = normalize(decision).reshape(-1, 1)

        labels = self.method_funcs[str(self.method)](decision)

        self.thresh_ = None

        return labels

    def _pyclust_eval(self, cl, decision):
        """ Evaluate cluster labels from pyclustering methods """

        cl.process()

        pred = np.squeeze(np.array(cl.get_clusters(), dtype=object))

        if type(pred[0]) == list:
            pred = np.array(pred[0])

        labels = np.ones(len(decision))
        labels[pred.astype(int)] = 0

        # Flip if outliers were clustered
        if sum(labels) > np.ceil(len(decision)/2):
            labels = 1-labels

        return labels

    def _sklearn_eval(self, cl, decision):
        """ Evaluate cluster labels from sklearn methods """

        cl.fit(decision)
        labels = cl.labels_

        # Flip if outliers were clustered
        if sum(labels) > np.ceil(len(decision)/2):
            labels = 1-labels

        return labels

    def _AGG_clust(self, decision):
        """ Agglomerative algorithm for cluster analysis """

        cl = agglomerative(data=decision, number_clusters=2,
                           link=2, ccore=True)

        return self._pyclust_eval(cl, decision)

    def _BIRCH_clust(self, decision):
        """ BIRCH (Balanced Iterative Reducing and Clustering using
            Hierarchies) algorithm for cluster analysis
        """

        cl = Birch(n_clusters=2, threshold=np.std(decision)/np.sqrt(2))

        return self._sklearn_eval(cl, decision)

    def _BANG_clust(self, decision):
        """ BANG clustering algorithm for cluster analysis """

        cl = bang(data=decision, levels=8, ccore=True)

        return self._pyclust_eval(cl, decision)

    def _BGM_clust(self, decision):
        """ Bayesian Gaussian Mixture algorithm for cluster analysis """

        cl = BayesianGaussianMixture(n_components=2,
                                     covariance_type='tied',
                                     random_state=self.random_state).fit(decision)

        labels = cl.predict(decision)

        # Flip if outliers were clustered
        if sum(labels) > np.ceil(len(decision)/2):
            labels = 1-labels

        return labels

    def _BSAS_clust(self, decision):
        """ BSAS (Basic Sequential Algorithmic Scheme)
            algorithm for cluster analysis
        """

        cl = bsas(data=decision, maximum_clusters=2,
                  threshold=np.std(decision), ccore=True)

        return self._pyclust_eval(cl, decision)

    def _DBSCAN_clust(self, decision):
        """ DBSCAN (Density-based spatial clustering of applications with
            noise) algorithm for cluster analysis
        """

        cl = dbscan(data=decision, eps=np.std(decision) /
                    np.sqrt(2), neighbors=len(decision) // 2, ccore=True)

        return self._pyclust_eval(cl, decision)

    def _EMA_clust(self, decision):
        """ Expectation-Maximization clustering algorithm for Gaussian
            Mixture Models
        """

        cl = ema(data=decision, amount_clusters=2)

        return self._pyclust_eval(cl, decision)

    def _KMEANS_clust(self, decision):
        """ K-means algorithm for cluster analysis """

        cl = KMeans(n_clusters=2)

        return self._sklearn_eval(cl, decision)

    def _MBSAS_clust(self, decision):
        """ MBSAS (Modified Basic Sequential Algorithmic Scheme)
            algorithm for cluster analysis
        """

        cl = mbsas(data=decision, maximum_clusters=2,
                   threshold=np.std(decision), ccore=True)

        return self._pyclust_eval(cl, decision)

    def _MSHIFT_clust(self, decision):
        """ Mean shift algorithm for cluster analysis"""

        # Get quantile value for bandwidth estimation
        dat = np.squeeze(decision)
        q = cityblock(dat, np.sort(dat))/np.sum(dat)

        q = min(q, 1.0)

        # Estimate bandwidth
        try:
            bw = estimate_bandwidth(decision, quantile=q)
        except ValueError:
            bw = estimate_bandwidth(decision)

        cl = MeanShift(bandwidth=bw, cluster_all=True, max_iter=500)
        cl.fit(decision)
        lbls = cl.labels_

        mode = np.bincount(lbls).argmax()
        labels = np.ones(len(lbls))
        labels[lbls == mode] = 0

        return labels

    def _OPTICS_clust(self, decision):
        """ OPTICS (Ordering Points To Identify Clustering Structure)
            algorithm for cluster analysis
        """

        cl = optics(sample=decision, eps=np.std(decision) / np.sqrt(2),
                    minpts=len(decision) // 2, amount_clusters=1, ccore=True)

        return self._pyclust_eval(cl, decision)

    def _SOMSC_clust(self, decision):
        """ Self-organized feature map algorithm for cluster analysis """

        cl = somsc(data=decision, amount_clusters=2, ccore=True)

        return self._pyclust_eval(cl, decision)

    def _SPEC_clust(self, decision):
        """ Clustering to a projection of the normalized Laplacian """

        cl = SpectralClustering(n_clusters=2)

        return self._sklearn_eval(cl, decision)

    def _XMEANS_clust(self, decision):
        """ X-means algorithm for cluster analysis """

        cl = xmeans(data=decision, kmax=2, ccore=True)

        return self._pyclust_eval(cl, decision)
