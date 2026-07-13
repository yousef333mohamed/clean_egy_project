"""Typed ML provider failures; none is a prediction."""


class DataScienceError(RuntimeError):
    pass


class DataScienceUnavailable(DataScienceError):
    pass


class InvalidPredictionRequest(DataScienceError):
    pass


class InvalidPredictionResponse(DataScienceError):
    pass


class CircuitBreakerOpen(DataScienceUnavailable):
    pass
