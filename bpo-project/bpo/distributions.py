import pandas
import random
import scipy
import numpy as np
from enum import Enum, auto
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder
from sklearn.neural_network import MLPRegressor


class DistributionType(Enum):
    """An enumeration for different types of probability distribution."""
    CATEGORICAL = auto()
    """A categorical distribution.

    :meta hide-value:"""

    GAMMA = auto()
    """A gamma distribution.

    :meta hide-value:"""

    NORMAL = auto()
    """A normal distribution.

    :meta hide-value:"""

    BETA = auto()
    """A beta distribution.

    :meta hide-value:"""

    ERLANG = auto()
    """An Erlang distribution.

    :meta hide-value:"""

    UNIFORM = auto()
    """A uniform distribution.

    :meta hide-value:"""


class CategoricalDistribution:

    def __init__(self):
        self._values = []
        self._weights = []

    def learn(self, values, counts):
        self._values = values
        self._weights = counts

    def sample(self):
        return random.choices(self._values, weights=self._weights)[0]


class UniformDistribution:

    def __init__(self, minimum=0, maximum=0):
        self.minimum = minimum
        self.maximum = maximum

    def learn(self, values):
        self.minimum = min(values)
        self.maximum = max(values)

    def sample(self):
        return random.uniform(self.minimum, self.maximum)


class GammaDistribution:

    def __init__(self):
        self._alpha = 0
        self._loc = 0
        self._scale = 0

    def learn(self, values):
        fit_alpha, fit_loc, fit_scale = scipy.stats.gamma.fit(values)
        self._alpha = fit_alpha
        self._loc = fit_loc
        self._scale = fit_scale

    def sample(self):
        return scipy.stats.gamma.rvs(self._alpha, loc=self._loc, scale=self._scale)

class GammaDistributionPO:

    def __init__(self):
        self._alpha = 0
        self._loc = 0
        self._scale = 0

    def learn(self, values):
        fit_alpha, fit_loc, fit_scale = scipy.stats.gamma.fit(values, method='MM', floc=0)
        self._alpha = fit_alpha
        self._loc = fit_loc
        self._scale = fit_scale

    def sample(self):
        return scipy.stats.gamma.rvs(self._alpha, loc=self._loc, scale=self._scale)


class ErlangDistribution:

    def __init__(self):
        self._shape = 0
        self._rate = 0

    def __init__(self, shape, scale):
        self._shape = shape
        self._rate = scale

    def learn(self, values):
        shape, loc, scale = scipy.stats.erlang.fit(values)
        self._shape = shape
        self._rate = scale

    def sample(self):
        return scipy.stats.erlang.rvs(self._shape, scale=self._rate)

    def mean(self):
        return scipy.stats.erlang.mean(self._shape, scale=self._rate)

    def std(self):
        return scipy.stats.erlang.std(self._shape, scale=self._rate)

    def var(self):
        return scipy.stats.erlang.var(self._shape, scale=self._rate)


class NormalDistribution:

    def __init__(self, mu = 0, std = 0):
        self.mu = mu
        self.std = std

    def learn(self, values):
        fit_mu, fit_std = scipy.stats.norm.fit(values)
        self.mu = fit_mu
        self.std = fit_std

    def sample(self):
        return scipy.stats.norm.rvs(self.mu, self.std)


class BetaDistribution:

    def __init__(self):
        self._a = 0
        self._b = 0
        self._loc = 0
        self._scale = 0

    def learn(self, values):
        fit_a, fit_b, fit_loc, fit_scale = scipy.stats.beta.fit(values)
        self._a = fit_a
        self._b = fit_b
        self._loc = fit_loc
        self._scale = fit_scale

    def sample(self):
        return scipy.stats.beta.rvs(self._a, self._b, self._loc, self._scale)


class StratifiedNumericDistribution:

    def __init__(self):
        self._target_column = ''
        self._feature_columns = []
        self._onehot_columns = []
        self._standardization_columns = []
        self._rest_columns = []

        self._normalizer = None
        self._standardizer = None
        self._encoder = None
        self._regressor = None

        self._stratifier = ''
        self._stratified_errors = dict()
        self._overall_mean = 0

    # onehot_columns will be onehot encoded, standardization_columns will be Z-Score normalized
    # all other features will be minmax normalized.
    # The maximum standard deviation of the error can be given as a fraction to the mean predicted value.
    # If the mean predicted value is m, the standard deviation of the error will be the min(actual error std, mean * max_error_std).
    # The max_error_std is given as a distribution itself, from which the max error is drawn for each strata.
    # For a max_error_std of None, no maximum will be set.
    def learn(self, data, target_column, feature_columns, onehot_columns, standardization_columns, stratifier, max_error_std):
        x = data[feature_columns]
        y = data[target_column]

        self._normalizer = MinMaxScaler()
        self._standardizer = StandardScaler()
        self._encoder = OneHotEncoder(sparse=False)

        self._target_column = target_column
        self._feature_columns = feature_columns
        self._onehot_columns = onehot_columns
        self._standardization_columns = standardization_columns
        self._rest_columns = [col for col in feature_columns if
                              col not in standardization_columns and col not in onehot_columns]

        self._overall_mean = y.mean()

        # handling empty columns
        if self._standardization_columns:
            standardized_data = self._standardizer.fit_transform(x[self._standardization_columns])
        else:
            standardized_data = np.empty((x.shape[0], 0))
        
        if self._rest_columns:
            normalized_data = self._normalizer.fit_transform(x[self._rest_columns])
        else:
            normalized_data = np.empty((x.shape[0], 0))
        
        if self._onehot_columns:
            onehot_data = self._encoder.fit_transform(x[self._onehot_columns])
        else:
            onehot_data = np.empty((x.shape[0], 0))

        x = np.concatenate([standardized_data, normalized_data, onehot_data], axis=1)

        self._regressor = MLPRegressor(hidden_layer_sizes=(x.shape[1], int(x.shape[1] / 2), int(x.shape[1] / 4)),
                                       activation='relu', solver='adam').fit(x, y)

        # now calculate the errors
        self._stratifier = stratifier
        df_error = data[[self._stratifier]].copy()
        df_error['y'] = data[target_column]
        df_error['y_hat'] = list(self._regressor.predict(x))
        df_error['error'] = df_error['y'] - df_error['y_hat']

        overall_value = NormalDistribution()
        overall_value.learn(list(df_error['error']))

        possible_values = data[stratifier].unique()
        for pv in possible_values:
            self._stratified_errors[pv] = NormalDistribution()
            stratified_errors = list(df_error[df_error[self._stratifier] == pv]['error'])
            if len(stratified_errors) > 50:
                self._stratified_errors[pv].learn(stratified_errors)
            else:
                self._stratified_errors[pv] = overall_value
            if max_error_std is not None:
                pv_mean = float(df_error[df_error[self._stratifier] == pv]['y'].mean())
                pv_max_error_std = max_error_std.sample() * pv_mean
                if self._stratified_errors[pv].std > pv_max_error_std:
                    self._stratified_errors[pv] = NormalDistribution(0, pv_max_error_std)

    # features is a dictionary that maps feature labels to lists of values
    def sample(self, features):
        data = pandas.DataFrame(features, index=[1])

        # handling empty colums
        if self._standardization_columns:
            standardized_data = self._standardizer.transform(data[self._standardization_columns])
        else:
            standardized_data = np.empty((1, 0))
        
        if self._rest_columns:
            normalized_data = self._normalizer.transform(data[self._rest_columns])
        else:
            normalized_data = np.empty((1, 0))
        
        if self._onehot_columns:
            onehot_data = self._encoder.transform(data[self._onehot_columns])
        else:
            onehot_data = np.empty((1, 0))

        x = np.concatenate([standardized_data, normalized_data, onehot_data], axis=1)

        processing_time = self._regressor.predict(x)[0]
        if processing_time <= 0:
            processing_time = self._overall_mean
        error = self._stratified_errors[features[self._stratifier]].sample()
        max_retries = 10
        retry = 0
        while retry < max_retries and processing_time + error <= 0:
            error = self._stratified_errors[features[self._stratifier]].sample()
            retry += 1
        if processing_time + error > 0:
            return processing_time + error
        else:
            return processing_time