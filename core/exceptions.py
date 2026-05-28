"""MarkovLens custom exceptions."""


class MarkovLensError(Exception):
    """Base exception for all MarkovLens errors."""


class DatasetNotFoundError(MarkovLensError):
    """Raised when a requested dataset_id is not in the DB."""


class DatasetTooSparseError(MarkovLensError):
    """Raised when a dataset has too few observations for valid modelling."""


class InvalidTransitionMatrixError(MarkovLensError):
    """Raised when a matrix fails validation."""


class UnsupportedModelError(MarkovLensError):
    """Raised when an unknown model_type is requested."""
