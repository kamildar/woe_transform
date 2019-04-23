# Author: Kamaldinov Ildar (kamildraf@gmail.com)
# MIT License
from woevidence.one_feature_tree import OneFeatureTree
import numpy as np
from joblib import Parallel, delayed


class WoeTree:

    def __init__(self,
                 criterion,
                 min_samples_leaf=2,
                 min_samples_class=0,
                 max_depth=None,
                 na_strategy='own',
                 smooth_woe=0.001,
                 smooth_entropy=1,
                 max_bins=255,
                 n_jobs=1,
                 dtype=None):
        """Weight Of Evidence encoder

        This estimator build trees for features based
        on criterion and apply WOE transformation
        to terminal lists defined as

        WOE = log(number of positive obs. / n. of negative)

        Parameters
        ----------
        criterion : str, default='entropy'
            Criterion for building a tree,
            supported: 'gini' and 'entropy'.

        min_samples_leaf : int, default=2
            Minimum number of observation in
            leaf for splitting.

        min_samples_class : int, default=0,
            Minimum number of observation per class
            for calculating woe.

        max_depth : int or None, default=None
            Maximum depth of three, None means
            unbouded tree.

        max_bins : int, default=255
            Number of bins for continious variable.self
            Smaller value speep up computations.

        na_strategy : str, float, default='own'
            Determine value for missing values.
            if float set na_strategy value to
            woe of NA, 'own' calculate woe for missing
            values or set to zero if there is no missings,
            'min', 'max' stratigies set min and max
            woe value respectively.

        smooth_woe : float, default=0.001
            Constant for avoiding division on zero
            and log(0) in homoscedasticity leaf.

        smooth_entropy : float, defalut=0.001
            Constant for avoiding log(0).

        n_jobs : int, default=1
            number of threads for fit and
            transform methods

        """
        self._criterion = criterion
        self._min_samples_leaf = min_samples_leaf
        self._min_samples_class = min_samples_class
        self._max_depth = max_depth
        self._na_strategy = na_strategy
        self._max_bins = max_bins
        self._smooth_woe = smooth_woe
        self._smooth_entropy = smooth_entropy
        self._n_jobs = n_jobs
        self._dtype = np.float32 if dtype is None else dtype

        self._trees = []

    def _to_array(self, X, y):
        if not isinstance(X, np.ndarray):
            X = np.array(X, dtype=self._dtype)
        if not isinstance(X, np.ndarray):
            y = np.array(y, dtype=self._dtype)
        return X, y

    @staticmethod
    def _to_arglist(arg, shape):
        """make list of argument from argument of len = 1"""
        if isinstance(arg, list):
            return arg
        else:
            return [arg] * shape

    def fit(self, X, y):
        """building woe tree for each feature"""
        X, y = self._to_array(X, y)
        n_features = X.shape[1]

        # make lists from arguments
        criterion = self._to_arglist(self._criterion, n_features)
        max_depth = self._to_arglist(self._max_depth, n_features)
        min_samples_leaf = self._to_arglist(self._min_samples_leaf, n_features)
        min_samples_class = self._to_arglist(
            self._min_samples_class, n_features)
        na_strategy = self._to_arglist(self._na_strategy, n_features)
        smooth_woe = self._to_arglist(self._smooth_woe, n_features)
        smooth_entropy = self._to_arglist(self._smooth_entropy, n_features)

        for feature in range(n_features):
            self._trees.append(
                OneFeatureTree(
                    criterion=criterion[feature],
                    max_depth=max_depth[feature],
                    min_samples_leaf=min_samples_leaf[feature],
                    min_samples_class=min_samples_class[feature],
                    na_strategy=na_strategy[feature],
                    smooth_woe=smooth_woe[feature],
                    smooth_entropy=smooth_entropy[feature],
                    dtype=self._dtype
                )
            )

        self._trees = (Parallel(n_jobs=self._n_jobs)
                       (delayed(self._trees[feature].fit)(X[:, feature], y)
                        for feature in range(n_features)))
        return self

    def transform(self, X):
        if not isinstance(X, np.ndarray):
            X = np.array(X, dtype=self._dtype)
        transformed = (Parallel(n_jobs=self._n_jobs)
                       (delayed(self._trees[ind].transform)(X[:, ind])
                        for ind in range(X.shape[1])))
        return np.array(transformed).T

    def fit_transform(self, X, y):
        self.fit(X, y)
        return self.transform(X)
