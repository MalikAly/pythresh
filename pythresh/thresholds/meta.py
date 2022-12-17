import os
from os.path import dirname as up

import joblib
import numpy as np
import pandas as pd
import scipy.stats as stats
from sklearn.utils import check_array

from .base import BaseThresholder
from .thresh_utility import normalize


class META(BaseThresholder):
    r"""META class for Meta-modelling thresholder.

       Use a trained meta-model to evaluate a non-parametric means
       to threshold scores generated by the decision_scores where outliers
       are set based on the trained meta-model classifier.
       See :cite:`zhao2022meta` for details.

       Parameters
       ----------

       method : {'LIN', 'GNB'}, optional (default='GNB')
           select

           - 'LIN': RidgeCV trained linear classifier meta-model
           - 'GNB': Gaussian Naive Bayes trained classifier meta-model

       Attributes
       ----------

       thresh_ : threshold value that separates inliers from outliers

       Notes
       -----

       Meta-modelling is the creation of a model of models. If a dataset
       that contains only the explanatory variables (X), yet no response
       variable (y), it can still be predicted by using a meta-model. This
       is done by modelling datasets with known response variables that
       are similar to the dataset that is missing the response variable.

       The META thresholder was trained using the ``PyOD`` outlier
       detection methods ``LODA, QMCD, CD, MCD, GMM, KNN, KDE, PCA, Sampling`` and ``IForest``
       on the AD benchmark datasets: ``ALOI, annthyroid, breastw, campaign, cardio, 
       Cardiotocography, fault, glass, Hepatitis, Ionosphere, landsat, letter, Lymphography, 
       magic.gamma, mammography, mnist, musk, optdigits, PageBlocks, pendigits, Pima, 
       satellite, satimage-2, shuttle, smtp, SpamBase, speech, Stamps, thyroid, vertebral, 
       vowels, Waveform,  WBC, WDBC, Wilt, wine, WPBC, yeast`` available at
       `ADBench dataset <https://github.com/Minqi824/ADBench/tree/main/datasets/Classical>`_.
       META uses a majority vote of all the trained models to determine the
       inlier/outlier labels.

    """

    def __init__(self, method='GNB'):

        self.method = method

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

        clf = 'meta_model_LIN.pkl' if self.method == 'LIN' else 'meta_model_GNB.pkl'

        contam = []
        counts = len(decision)
        parent = up(up(__file__))
        model = joblib.load(os.path.join(parent, 'models', clf))

        for i in range(380):

            df = pd.DataFrame()
            df['scores'] = decision
            df['groups'] = i
            labels = model.predict(df)
            outlier_ratio = np.sum(labels)/counts

            if (outlier_ratio < 0.5) & (outlier_ratio > 0):

                contam.append(labels)

        contam = np.array(contam)
        lbls = stats.mode(contam, axis=0)
        lbls = np.squeeze(lbls[0])

        self.thresh_ = None

        return lbls
