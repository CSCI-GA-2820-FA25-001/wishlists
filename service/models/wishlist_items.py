######################################################################
# Copyright 2025 Dingwen Wang. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
# cspell: ignore= userid, backref
"""
Model class for WishlistItems
"""

import logging
from .persistent_base import db, PersistentBase, DataValidationError

# from .wishlists import Wishlists

logger = logging.getLogger("flask.app")


class WishlistItems(db.Model, PersistentBase):
    """Class that represents an item in a Wishlist"""

    __tablename__ = "wishlist_items"

    wishlist_id = db.Column(
        db.Integer, db.ForeignKey("wishlists.id", ondelete="CASCADE"), primary_key=True
    )
    product_id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255))
    position = db.Column(db.Integer, nullable=False)

    # wishlist = db.relationship('Wishlists', backref=db.backref('wishlist_items', lazy=True))

    def __repr__(self):
        return f"<WishlistItems {self.product_id} in Wishlist {self.wishlist_id} at position {self.position}>"

    def serialize(self) -> dict:
        """Convert a WishlistItem into a dictionary"""
        return {
            "wishlist_id": self.wishlist_id,
            "product_id": self.product_id,
            "description": self.description,
            "position": self.position,
        }

    def deserialize(self, data: dict) -> None:
        """Convert a dictionary into a WishlistItem"""
        # pylint: disable=duplicate-code
        try:
            if not isinstance(data["product_id"], int):
                raise TypeError("product_id must be an integer")
            self.wishlist_id = data.get("wishlist_id")
            self.product_id = data["product_id"]
            self.description = data.get("description")
            if self.position is None:
                self.position = data.get("position", 0)
        except AttributeError as e:
            raise DataValidationError(f"Invalid attribute: {e.args[0]}") from e
        except KeyError as e:
            raise DataValidationError(f"Missing key: {e.args[0]}") from e
        except TypeError as e:
            raise DataValidationError(f"Invalid type: {e}") from e
        return self

    @classmethod
    def find_all_by_wishlist_id(cls, wishlist_id: int):
        """Find all WishlistItems for a given wishlist ID"""
        return (
            cls.query.filter(cls.wishlist_id == wishlist_id)
            .order_by(cls.position.asc())
            .all()
        )

    @classmethod
    def find_by_wishlist_and_product(cls, wishlist_id: int, product_id: int):
        """Find a WishlistItem by its wishlist ID and product ID"""
        return cls.query.filter(
            cls.wishlist_id == wishlist_id, cls.product_id == product_id
        ).first()

    @classmethod
    def find_last_position(cls, wishlist_id: int):
        """Find the last position number in a given wishlist"""
        item = (
            cls.query.filter(cls.wishlist_id == wishlist_id)
            .order_by(cls.position.desc())
            .first()
        )
        return item.position if item else 0
