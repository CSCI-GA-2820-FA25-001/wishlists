######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
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

"""
Test cases for Pet Model
"""

# pylint: disable=duplicate-code,ungrouped-imports
import os
import logging
import random
from datetime import date
from unittest import TestCase
from unittest.mock import patch
from pytest import warns
from service.models.persistent_base import PersistentBase
from wsgi import app
from service.models import DataValidationError, db
from service.models import Wishlists, WishlistItems
from .factories import WishlistsFactory, WishlistItemsFactory
from .factories import CUSTOMER_ID

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  Wishlists   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestWishlistsModel(TestCase):
    """Test Cases for Wishlists Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.rollback()
        db.session.query(WishlistItems).delete()
        db.session.query(Wishlists).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_persistent_base_init(self):
        """PersistentBase should initialize a model with id=None"""
        data = PersistentBase()
        self.assertIsInstance(data, PersistentBase)
        self.assertIsNone(data.id)

    def test_persistent_base_update(self):
        """PersistentBase should update a model in the database"""
        wishlist = WishlistsFactory()
        self.assertIsNotNone(wishlist)
        wishlist.create()
        self.assertIsNotNone(wishlist.id)
        old_name = wishlist.name
        wishlist.name = "New Name"
        wishlist.update()
        self.assertNotEqual(old_name, wishlist.name)
        data = Wishlists.find(wishlist.id)
        self.assertEqual(data.name, "New Name")

    def test_persistent_base_update_db_error(self):
        """PersistentBase should raise Exception when a database error occurs during update"""
        wishlist = WishlistsFactory()
        self.assertIsNotNone(wishlist)
        wishlist.create()
        self.assertIsNotNone(wishlist.id)
        old_name = wishlist.name
        wishlist.name = "New Name"

        with patch.object(db.session, "commit", side_effect=Exception("DB Error")):
            with self.assertRaises(Exception) as context:
                wishlist.update()
            self.assertTrue("DB Error" in str(context.exception))
        # Verify the name was not changed in the database
        data = Wishlists.find(wishlist.id)
        self.assertEqual(data.name, old_name)

    def test_persistent_base_update_no_id(self):
        """PersistentBase should raise DataValidationError when updating with no id"""
        wishlist = WishlistsFactory()
        wishlist.create()
        wishlist.id = None
        wishlist.name = "New Name"
        with self.assertRaises(DataValidationError):
            wishlist.update()

    def test_persistent_base_delete_db_error(self):
        """PersistentBase should raise Exception when a database error occurs during delete"""
        wishlist = WishlistsFactory()
        self.assertIsNotNone(wishlist)
        wishlist.create()
        self.assertIsNotNone(wishlist.id)

        with patch.object(db.session, "commit", side_effect=Exception("DB Error")):
            with self.assertRaises(Exception) as context:
                wishlist.delete()
            self.assertTrue("DB Error" in str(context.exception))
        # Verify the wishlist was not deleted from the database
        data = Wishlists.find(wishlist.id)
        self.assertIsNotNone(data)

    def test_wishlist_repr(self):
        """Wishlists should return a string representation of a Wishlists"""
        wishlist = WishlistsFactory()
        logging.debug(wishlist)
        self.assertIsInstance(repr(wishlist), str)
        wishlist.name = "My Wishlist"
        self.assertEqual(
            f"<Wishlists {wishlist.name} id=[{wishlist.id}]>", repr(wishlist)
        )

    def test_wishlist_items_repr(self):
        """WishlistItems should return a string representation of a WishlistItems"""
        wishlist = WishlistsFactory()
        item = WishlistItemsFactory(wishlist_id=wishlist.id)
        logging.debug(item)
        self.assertIsInstance(repr(item), str)
        item.wishlist_id = wishlist.id
        item.product_id = 42
        item.position = 1000
        self.assertEqual(
            f"<WishlistItems {item.product_id} in Wishlist {item.wishlist_id} at position {item.position}>",
            repr(item),
        )

    def test_wishlist_serialize(self):
        """It should serialize a Wishlists"""
        wishlist = WishlistsFactory()
        data = wishlist.serialize()
        self.assertIsInstance(data, dict)
        self.assertEqual(wishlist.id, data["id"])
        self.assertEqual(wishlist.customer_id, data["customer_id"])
        self.assertEqual(wishlist.name, data["name"])
        self.assertEqual(wishlist.description, data["description"])
        self.assertEqual(wishlist.category, data["category"])
        self.assertEqual(wishlist.created_date.isoformat(), data["created_date"])
        self.assertIsNone(data["updated_date"])
        self.assertEqual(data["wishlist_items"], [])

    def test_wishlist_serialize_with_items(self):
        """It should serialize a Wishlists with WishlistItems"""
        wishlist = WishlistsFactory()
        wishlist.create()
        item1 = WishlistItemsFactory(wishlist_id=wishlist.id)
        item1.position = 2000
        item1.create()
        item2 = WishlistItemsFactory(wishlist_id=wishlist.id)
        item2.position = 1000
        item2.create()
        data = wishlist.serialize()
        self.assertIsInstance(data, dict)
        self.assertEqual(len(data["wishlist_items"]), 2)
        self.assertEqual(data["wishlist_items"][0]["product_id"], item2.product_id)
        self.assertEqual(data["wishlist_items"][1]["product_id"], item1.product_id)

    def test_wishlist_deserialize(self):
        """It should deserialize a Wishlists"""
        data = {
            "customer_id": CUSTOMER_ID,
            "name": "My Wishlist",
            "description": "This is my wishlist",
            "category": "General",
            "created_date": "2023-01-01",
        }
        wishlist = Wishlists()
        wishlist.deserialize(data)
        self.assertIsInstance(wishlist, Wishlists)
        self.assertEqual(wishlist.customer_id, data["customer_id"])
        self.assertEqual(wishlist.name, data["name"])
        self.assertEqual(wishlist.description, data["description"])
        self.assertEqual(wishlist.category, data["category"])
        self.assertEqual(wishlist.created_date.isoformat(), data["created_date"])
        self.assertEqual(wishlist.updated_date, date.today())

    def test_wishlist_deserialize_with_invalid_data(self):
        """It should raise DataValidationError on bad data"""
        with self.assertRaises(DataValidationError):
            # code that should raise the exception
            Wishlists().deserialize({"customer_id": "not-an-int", "name": 123})
        with self.assertRaises(DataValidationError):
            Wishlists().deserialize({"customer_id": 1, "name": 123})
        with self.assertRaises(DataValidationError):
            Wishlists().deserialize({"customer_id": "not an int", "name": "Valid Name"})
        with self.assertRaises(DataValidationError):
            Wishlists().deserialize({"name": "Valid Name"})  # Missing customer_id

    def test_wishlist_deserialize_bad_getitem(self):
        """It should raise DataValidationError on bad data"""

        class BadData:
            """A dict-like object that works with [] but raises AttributeError when .get() is called."""

            def __getitem__(self, key):
                # Return normal values like a dict would
                if key == "customer_id":
                    return 123
                if key == "name":
                    return "Test Wishlist"
                if key == "created_date":
                    return "2025-10-09"
                if key == "updated_date":
                    return None
                raise KeyError(key)

            def __contains__(self, key):
                # So `"created_date" in data` works
                return key in {"customer_id", "name", "created_date", "updated_date"}

            def get(self, key, default=None):
                """Simulate a broken .get() method that always raises an error"""
                raise AttributeError(
                    f"Simulated broken .get() method for key: {key}, default: {default}"
                )

        bad_data = BadData()
        with self.assertRaises(DataValidationError):
            Wishlists().deserialize(bad_data)

    def test_wishlist_items_deserialize(self):
        """It should deserialize a WishlistItems"""
        data = {
            "wishlist_id": 1,
            "product_id": 42,
            "description": "This is a product",
            "position": 1000,
        }
        item = WishlistItems()
        item.deserialize(data)
        self.assertIsInstance(item, WishlistItems)
        self.assertEqual(item.wishlist_id, data["wishlist_id"])
        self.assertEqual(item.product_id, data["product_id"])
        self.assertEqual(item.description, data["description"])
        self.assertEqual(item.position, data["position"])

    def test_wishlist_items_deserialize_with_invalid_data(self):
        """It should raise DataValidationError if product_id is missing or invalid"""
        data = {
            "wishlist_id": 1,
            "description": "This is a product",
            "position": 1000,
        }
        item = WishlistItems()
        with self.assertRaises(DataValidationError):
            item.deserialize(data)
        data["product_id"] = "not-an-int"
        with self.assertRaises(DataValidationError):
            item.deserialize(data)

    def test_wishlist_items_deserialize_bad_getitem(self):
        """It should raise DataValidationError on bad data"""

        class BadData:
            """A dict-like object that works with [] but raises AttributeError when .get() is called."""

            def __getitem__(self, key):
                # Return normal values like a dict would
                if key == "wishlist_id":
                    return 1
                if key == "product_id":
                    return 42
                if key == "description":
                    return "This is a product"
                if key == "position":
                    return 1000
                raise KeyError(key)

            def __contains__(self, key):
                # So `"created_date" in data` works
                return key in {
                    "wishlist_id",
                    "product_id",
                    "description",
                    "position",
                }

            def get(self, key, default=None):
                """Simulate a broken .get() method that always raises an error"""
                raise AttributeError(
                    f"Simulated broken .get() method for key: {key}, default: {default}"
                )

        bad_data = BadData()
        with self.assertRaises(DataValidationError):
            WishlistItems().deserialize(bad_data)

    def test_wishlist_items_foreign_key_constraint(self):
        """It should enforce foreign key constraint on WishlistItems"""
        item = WishlistItemsFactory()
        item.wishlist_id = 9999  # Non-existent wishlist_id
        item.product_id = 1
        item.position = 1000
        with self.assertRaises(Exception) as context:
            item.create()
        self.assertTrue("foreign key constraint" in str(context.exception).lower())

    def test_wishlist_items_primary_key_constraint(self):
        """It should enforce primary key constraint on WishlistItems"""
        wishlist = WishlistsFactory()
        wishlist.create()
        item1 = WishlistItemsFactory(wishlist_id=wishlist.id)
        item1.product_id = 1
        item1.position = 1000
        item1.create()
        item2 = WishlistItemsFactory(wishlist_id=wishlist.id)
        item2.product_id = 1  # Same product_id as item1
        item2.position = 2000
        with self.assertRaises(DataValidationError) as context:
            with warns(Warning, match="conflicts"):
                item2.create()
        self.assertTrue(
            "duplicate key value violates unique constraint"
            in str(context.exception).lower()
        )

    def test_create_wishlist(self):
        """It should create a Wishlists"""
        resource = WishlistsFactory()
        resource.create()
        self.assertIsNotNone(resource.id)
        found = Wishlists.all()
        self.assertEqual(len(found), 1)
        data = Wishlists.find(resource.id)
        self.assertEqual(data.name, resource.name)

    def test_find_wishlist(self):
        """It should find a Wishlists by ID"""
        resource = WishlistsFactory()
        resource.create()
        found = Wishlists.find_by_id(resource.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.id, resource.id)
        self.assertEqual(found.name, resource.name)
        self.assertEqual(found.customer_id, resource.customer_id)

    def test_find_wishlist_by_customer_id(self):
        """It should find Wishlists by customer_id"""
        for _ in range(5):
            resource = WishlistsFactory()
            resource.create()
        found = Wishlists.find_all_by_customer_id(CUSTOMER_ID)
        self.assertEqual(len(found), 5)

    def test_find_wishlist_by_customer_id_and_name_like(self):
        """It should find Wishlists by customer_id and name containing a substring"""

        # Create 5 Wishlists with names containing "My Wishlist"
        for i in range(5):
            resource = WishlistsFactory(name=f"My Wishlist {i}")
            resource.create()

        # Create 2 Wishlists with names containing "Other Wishlist"
        for i in range(2):
            resource = WishlistsFactory(name=f"Other Wishlist {i}")
            resource.create()

        # Find Wishlists by customer_id and name containing "My Wishlist"
        found = Wishlists.find_all_by_customer_id_and_name_like(
            CUSTOMER_ID, "My Wishlist"
        )
        self.assertEqual(len(found), 5)

        # Find Wishlists by customer_id and name containing "Other Wishlist"
        found = Wishlists.find_all_by_customer_id_and_name_like(
            CUSTOMER_ID, "Other Wishlist"
        )
        self.assertEqual(len(found), 2)

    def test_find_all_by_wishlist_id(self):
        """It should find all WishlistItems by wishlist_id"""
        wishlists = []
        for _ in range(3):
            wishlist = WishlistsFactory()
            wishlist.create()
            wishlists.append(wishlist)
            for _ in range(3):
                item = WishlistItemsFactory(wishlist_id=wishlist.id)
                item.create()
        for wishlist in wishlists:
            found_items = WishlistItems.find_all_by_wishlist_id(wishlist.id)
            self.assertEqual(len(found_items), 3)
            for item in found_items:
                self.assertEqual(item.wishlist_id, wishlist.id)

    def test_find_by_wishlist_and_product(self):
        """It should find a WishlistItem by wishlist_id and product_id"""
        wishlist = WishlistsFactory()
        wishlist.create()
        item = WishlistItemsFactory(wishlist_id=wishlist.id)
        item.product_id = 42
        item.position = 1000
        item.create()
        found_item = WishlistItems.find_by_wishlist_and_product(wishlist.id, 42)
        self.assertIsNotNone(found_item)
        self.assertEqual(found_item.wishlist_id, wishlist.id)
        self.assertEqual(found_item.product_id, 42)

    def test_find_last_position(self):
        """It should find the last position in a Wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        positions = [1000, 3000, 2000, 500]
        for pos in positions:
            item = WishlistItemsFactory(wishlist_id=wishlist.id)
            item.position = pos
            item.create()
        last_position = WishlistItems.find_last_position(wishlist.id)
        self.assertEqual(last_position, max(positions))

    def test_wishlist_not_found(self):
        """It should not find a Wishlist"""
        resource = WishlistsFactory()
        resource.create()
        found = Wishlists.find_by_id(resource.id + 1)
        self.assertIsNone(found)

    def test_update_wishlist(self):
        """It should update a Wishlists"""
        resource = WishlistsFactory()
        resource.create()
        self.assertIsNotNone(resource.id)
        data = Wishlists.find(resource.id)
        self.assertEqual(data.name, resource.name)
        old_name = resource.name
        resource.name = "New Name"
        resource.update()
        self.assertEqual(resource.id, data.id)
        self.assertNotEqual(old_name, resource.name)
        data = Wishlists.find(resource.id)
        self.assertEqual(data.name, "New Name")

    def test_add_wishlist_item(self):
        """It should add a WishlistItem to a Wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        self.assertIsNotNone(wishlist.id)
        item = WishlistItemsFactory(wishlist_id=wishlist.id)
        item.create()
        self.assertIsNotNone(item.wishlist_id)
        self.assertIsNotNone(item.product_id)
        self.assertEqual(item.wishlist_id, wishlist.id)
        found_items = WishlistItems.find_all_by_wishlist_id(wishlist.id)
        self.assertEqual(len(found_items), 1)
        self.assertEqual(found_items[0].product_id, item.product_id)

    def test_wishlist_items_reposition(self):
        """It should reposition WishlistItems in a Wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        self.assertIsNotNone(wishlist.id)
        test_size = 5
        # Create items with non-sequential positions
        positions = random.sample(range(1, test_size * 1000, 1000), 3)
        for pos in positions:
            item = WishlistItemsFactory(wishlist_id=wishlist.id)
            item.position = pos
            item.create()
        found_items = WishlistItems.find_all_by_wishlist_id(wishlist.id)
        self.assertEqual(len(found_items), 3)
        # Reposition items
        Wishlists.reposition(wishlist.id)
        found_items = sorted(
            WishlistItems.find_all_by_wishlist_id(wishlist.id), key=lambda x: x.position
        )
        expected_positions = [(i + 1) * 1000 for i in range(len(found_items))]
        actual_positions = [item.position for item in found_items]
        self.assertEqual(actual_positions, expected_positions)

    def test_wishlist_items_reposition_no_wishlist(self):
        """It should raise DataValidationError when repositioning items in a non-existent Wishlist"""
        with self.assertRaises(DataValidationError):
            Wishlists.reposition(9999)  # Non-existent wishlist_id

    def test_wishlist_items_reposition_db_error(self):
        """It should raise Exception when a database error occurs during repositioning"""
        wishlist = WishlistsFactory()
        wishlist.create()
        wishlist_items = WishlistItemsFactory(wishlist_id=wishlist.id)
        wishlist_items.create()

        with patch.object(db.session, "commit", side_effect=Exception("DB Error")):
            with self.assertRaises(Exception) as context:
                Wishlists.reposition(wishlist.id)
            self.assertTrue("DB Error" in str(context.exception))

    def test_move_wishlist_item(self):
        """It should move a WishlistItem to a new position in the Wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        self.assertIsNotNone(wishlist.id)
        test_size = 5
        # Create items with sequential positions
        for i in range(test_size):
            item = WishlistItemsFactory(wishlist_id=wishlist.id)
            item.position = (i + 1) * 1000
            item.create()
        found_items = sorted(
            WishlistItems.find_all_by_wishlist_id(wishlist.id), key=lambda x: x.position
        )
        self.assertEqual(len(found_items), test_size)

        # Move the last item to the second position
        item_to_move = found_items[-1]
        before_position = found_items[1].position
        moved_item = Wishlists.move_item(
            wishlist.id, item_to_move.product_id, before_position
        )
        self.assertEqual(moved_item.product_id, item_to_move.product_id)
        # Verify the new order of items
        new_positions = [
            item.position for item in WishlistItems.find_all_by_wishlist_id(wishlist.id)
        ]
        self.assertEqual(new_positions, [1000, 1500, 2000, 3000, 4000])

        # Move the 4th item (3rd item in found_items) before 2000 (2nd item in found_items)
        item_to_move = found_items[2]
        before_position = found_items[1].position
        moved_item = Wishlists.move_item(
            wishlist.id, item_to_move.product_id, before_position
        )
        self.assertEqual(moved_item.product_id, item_to_move.product_id)
        # Verify the new order of items
        new_positions = [
            item.position for item in WishlistItems.find_all_by_wishlist_id(wishlist.id)
        ]
        self.assertEqual(new_positions, [1000, 1500, 1750, 2000, 4000])

    def test_move_wishlist_item_reposition(self):
        """It should trigger repositioning when moving an item to a conflicting position"""
        wishlist = WishlistsFactory()
        wishlist.create()
        self.assertIsNotNone(wishlist.id)
        test_size = 3
        # Create items with sequential positions
        for i in range(test_size):
            item = WishlistItemsFactory(wishlist_id=wishlist.id)
            item.position = i + 1
            item.create()
        found_items = sorted(
            WishlistItems.find_all_by_wishlist_id(wishlist.id), key=lambda x: x.position
        )
        self.assertEqual(len(found_items), test_size)

        # Move the last item to the position of the first item, causing a conflict
        item_to_move = found_items[-1]
        before_position = found_items[0].position
        moved_item = Wishlists.move_item(
            wishlist.id, item_to_move.product_id, before_position
        )

        new_positions = [
            item.position for item in WishlistItems.find_all_by_wishlist_id(wishlist.id)
        ]

        self.assertEqual(new_positions, [500, 1000, 2000])
        self.assertEqual(moved_item.position, 500)

    def test_move_wishlist_item_first(self):
        """It should move a WishlistItem to the front of the Wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        self.assertIsNotNone(wishlist.id)
        test_size = 2
        # Create items with sequential positions
        for i in range(test_size):
            item = WishlistItemsFactory(wishlist_id=wishlist.id)
            item.position = (i + 1) * 1000
            item.create()
        found_items = sorted(
            WishlistItems.find_all_by_wishlist_id(wishlist.id), key=lambda x: x.position
        )
        self.assertEqual(len(found_items), test_size)

        # Move the last item to the front
        item_to_move = found_items[-1]
        before_position = found_items[0].position
        moved_item = Wishlists.move_item(
            wishlist.id, item_to_move.product_id, before_position
        )

        new_positions = [
            item.position for item in WishlistItems.find_all_by_wishlist_id(wishlist.id)
        ]
        self.assertEqual(new_positions, [500, 1000])
        self.assertEqual(moved_item.position, 500)

    def test_move_wishlist_item_last(self):
        """It should move a WishlistItem to the end of the Wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        self.assertIsNotNone(wishlist.id)
        test_size = 2
        # Create items with sequential positions
        for i in range(test_size):
            item = WishlistItemsFactory(wishlist_id=wishlist.id)
            item.position = i + 1
            item.create()
        found_items = sorted(
            WishlistItems.find_all_by_wishlist_id(wishlist.id), key=lambda x: x.position
        )
        self.assertEqual(len(found_items), test_size)

        # Move the first item to the end
        item_to_move = found_items[0]
        before_position = 9999  # A position greater than any existing position
        moved_item = Wishlists.move_item(
            wishlist.id, item_to_move.product_id, before_position
        )

        new_positions = [
            item.position for item in WishlistItems.find_all_by_wishlist_id(wishlist.id)
        ]
        self.assertEqual(new_positions, [2, 1002])
        self.assertEqual(moved_item.position, 1002)

    def test_move_wishlist_item_no_wishlist(self):
        """It should raise DataValidationError when moving an item in a non-existent Wishlist"""
        with self.assertRaises(DataValidationError):
            Wishlists.move_item(9999, 1, 1000)  # Non-existent wishlist_id

    def test_move_wishlist_item_no_items(self):
        """It should raise DataValidationError when moving an item in a Wishlist with no items"""
        wishlist = WishlistsFactory()
        wishlist.create()
        with self.assertRaises(DataValidationError):
            Wishlists.move_item(wishlist.id, 1, 1000)  # Wishlist has no items

    def test_move_wishlist_item_one_item(self):
        """It should return the single item when moving in a Wishlist with one item"""
        wishlist = WishlistsFactory()
        wishlist.create()
        item = WishlistItemsFactory(wishlist_id=wishlist.id)
        item.position = 1000
        item.create()
        moved_item = Wishlists.move_item(wishlist.id, item.product_id, 500)
        self.assertEqual(moved_item.product_id, item.product_id)
        self.assertEqual(moved_item.position, item.position)

    def test_move_wishlist_item_not_found(self):
        """It should raise DataValidationError when the item to move is not found in the Wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        item = WishlistItemsFactory(wishlist_id=wishlist.id)
        item.position = 1000
        item.create()
        item_2 = WishlistItemsFactory(wishlist_id=wishlist.id)
        item_2.position = 2000
        item_2.create()
        with self.assertRaises(DataValidationError):
            Wishlists.move_item(wishlist.id, 9999, 500)  # Non-existent product_id

    def test_move_wishlist_item_db_error(self):
        """It should raise Exception when a database error occurs during move_item"""
        wishlist = WishlistsFactory()
        wishlist.create()
        item = WishlistItemsFactory(wishlist_id=wishlist.id)
        item.position = 1000
        item.create()
        item_2 = WishlistItemsFactory(wishlist_id=wishlist.id)
        item_2.position = 2000
        item_2.create()

        with patch.object(db.session, "commit", side_effect=Exception("DB Error")):
            with self.assertRaises(Exception) as context:
                Wishlists.move_item(wishlist.id, item_2.product_id, 500)
            self.assertTrue("DB Error" in str(context.exception))

    def test_update_wishlist_item_with_empty_wishlist_id(self):
        """It should raise DataValidationError when updating with empty wishlist_id"""
        item = WishlistItems()
        item.wishlist_id = None
        item.product_id = 123
        item.description = "test"
        item.position = 1000

        with self.assertRaises(DataValidationError):
            item.update()

    def test_update_wishlist_item_with_empty_product_id(self):
        """It should raise DataValidationError when updating with empty product_id"""
        item = WishlistItems()
        item.wishlist_id = 1
        item.product_id = None
        item.description = "test"
        item.position = 1000

        with self.assertRaises(DataValidationError):
            item.update()
