"""
Models for Wishlists

All of the models are stored in this package
"""

from .persistent_base import db, DataValidationError
from .wishlists import Wishlists
from .wishlist_items import WishlistItems
