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
Model class for Wishlists
"""

import logging
from datetime import date
from .persistent_base import db, PersistentBase, DataValidationError
from .wishlist_items import WishlistItems

logger = logging.getLogger("flask.app")


class Wishlists(db.Model, PersistentBase):
    """Class that represents a Wishlist"""

    __tablename__ = "wishlists"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(63), nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(63))
    created_date = db.Column(db.Date, nullable=False, default=date.today())
    updated_date = db.Column(db.Date, onupdate=date.today())

    wishlist_items = db.relationship(
        "WishlistItems",
        backref="wishlists",
        lazy=True,
        order_by="WishlistItems.position",
    )

    def __repr__(self):
        return f"<Wishlists {self.name} id=[{self.id}]>"

    def serialize(self) -> dict:
        """Convert a Wishlist into a dictionary"""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "created_date": self.created_date.isoformat(),
            "updated_date": (
                self.updated_date.isoformat() if self.updated_date else None
            ),
            "wishlist_items": [item.serialize() for item in self.wishlist_items],
        }

    def deserialize(self, data: dict) -> None:
        """Convert a dictionary into a Wishlist"""
        # pylint: disable=duplicate-code
        try:
            if not isinstance(data["customer_id"], int):
                raise TypeError("customer_id must be an integer")
            if not isinstance(data["name"], str):
                raise TypeError("name must be a string")
            self.customer_id = data["customer_id"]
            self.name = data["name"]
            self.description = data.get("description")
            self.category = data.get("category")
            if self.created_date is None:
                self.created_date = (
                    date.fromisoformat(data["created_date"])
                    if "created_date" in data
                    else date.today()
                )
            self.updated_date = date.today()
        except AttributeError as e:
            raise DataValidationError(f"Invalid attribute: {e.args[0]}") from e
        except KeyError as e:
            raise DataValidationError(f"Missing key: {e.args[0]}") from e
        except TypeError as e:
            raise DataValidationError(f"Invalid type: {e}") from e
        return self

    @classmethod
    def find_by_id(cls, wishlist_id: int):
        """Find a Wishlist by its ID"""
        return db.session.get(cls, wishlist_id)

    @classmethod
    def find_all_by_customer_id(cls, customer_id: int):
        """Find all Wishlists for a given customer ID"""
        return cls.query.filter(cls.customer_id == customer_id).all()

    @classmethod
    def find_all_by_customer_id_and_name_like(cls, customer_id: int, name: str):
        """Find all Wishlists for a given customer where the name contains the given substring (case-insensitive)."""
        pattern = f"%{name}%"
        return cls.query.filter(
            cls.customer_id == customer_id, cls.name.ilike(pattern)
        ).all()

    @classmethod
    def find_by_category(cls, category: str):
        """Find all Wishlists by category only (case-insensitive, global)."""
        return cls.query.filter(cls.category.ilike(category)).all()

    @classmethod
    def find_by_name_like(cls, name: str):
        """Find all Wishlists by name like."""
        pattern = f"%{name}%"
        return cls.query.filter(cls.name.ilike(pattern)).all()

    @classmethod
    def find_by_customer_and_category(cls, customer_id: int, category: str):
        """Find all Wishlists by customer_id AND category (case-insensitive)."""
        return cls.query.filter(
            cls.customer_id == customer_id, cls.category.ilike(category)
        ).all()

    @classmethod
    def find_by_customer_category_name_like(
        cls, customer_id: int, category: str, name: str
    ):
        """Find all Wishlists by customer_id AND category AND name-like (case-insensitive)."""
        pattern = f"%{name}%"
        return cls.query.filter(
            cls.customer_id == customer_id,
            cls.category.ilike(category),
            cls.name.ilike(pattern),
        ).all()

    @classmethod
    def reposition(cls, wishlist_id: int):
        """Reposition items in a Wishlist to ensure positions are sequential starting from 1000, with increments of 1000"""
        wishlist = cls.find_by_id(wishlist_id)
        if not wishlist:
            raise DataValidationError(f"Wishlist with id {wishlist_id} not found")
        for index, item in enumerate(wishlist.wishlist_items):
            item.position = (index + 1) * 1000
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        return wishlist.wishlist_items

    @classmethod
    def _find_item_and_before(
        cls, wishlist_items, product_id: int, before_position: int
    ):
        """Locate the moving item and the 'before' item and its index.

        Returns a tuple (item, before, before_index).
        """
        item = None
        before = None
        before_index = -1
        for index, i_item in enumerate(wishlist_items):
            if i_item.product_id == product_id:
                item = i_item
                continue

            if i_item.position >= before_position and before is None:
                before = i_item
                before_index = index

        return item, before, before_index

    @classmethod
    def _compute_new_position(cls, wishlist_items, before, before_index: int):
        """Compute a new position for an item given the located `before` item.

        Returns a tuple (new_position, prev_position).
        """
        new_position = None
        prev_position = None
        if before is None:
            # Item moved to the end
            new_position = wishlist_items[-1].position + 1000
        elif before_index == 0:
            # Item moved to the front
            new_position = before.position // 2
        else:
            prev = wishlist_items[before_index - 1]
            new_position = (before.position + prev.position) // 2
            prev_position = prev.position

        return new_position, prev_position

    @classmethod
    def move_item(cls, wishlist_id: int, product_id: int, before_position: int):
        """Move an item to a new position in the Wishlist"""
        wishlist = cls.find_by_id(wishlist_id)
        if not wishlist:
            raise DataValidationError(f"Wishlist with id {wishlist_id} not found")

        wishlist_items = wishlist.wishlist_items

        if not wishlist_items:
            raise DataValidationError(f"Wishlist with id {wishlist_id} has no items")

        if len(wishlist_items) == 1:
            # Only one item, no need to move
            return wishlist_items[0]

        item, before, before_index = cls._find_item_and_before(
            wishlist_items, product_id, before_position
        )

        if item is None:
            raise DataValidationError(
                f"Item with product_id {product_id} not found in wishlist {wishlist_id}"
            )

        new_position, prev_position = cls._compute_new_position(
            wishlist_items, before, before_index
        )

        if before is not None and (
            new_position <= 0
            or new_position == before.position
            or new_position == prev_position
        ):
            # Positions are too close or invalid: renumber and retry using the
            # new 'before' position after repositioning.
            cls.reposition(wishlist_id)
            before = WishlistItems.find_by_wishlist_and_product(
                wishlist_id, before.product_id
            )
            return cls.move_item(wishlist_id, product_id, before.position)

        item.position = new_position
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        return item
