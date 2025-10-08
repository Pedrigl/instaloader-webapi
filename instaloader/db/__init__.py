"""Database package initializer.

Import model modules here so that importing ``instaloader.db`` will register
all SQLAlchemy models with ``Base.metadata``. This avoids needing ad-hoc
pkgutil scans elsewhere.
"""
from .database import Base

# Import model modules (idempotent) so their classes are registered with Base
from . import items_models
from . import fetched_models
from . import models

__all__ = ["Base", "items_models", "fetched_models", "models"]
