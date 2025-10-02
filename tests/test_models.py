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

# pylint: disable=duplicate-code
import os
import logging
import random
from unittest import TestCase
from pytest import warns
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
        db.session.query(Wishlists).delete()  # clean up the last tests
        db.session.query(WishlistItems).delete()
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_wishlist_repr(self):
        """It should return a string representation of a Wishlists"""
        wishlist = WishlistsFactory()
        logging.debug(wishlist)
        self.assertIsInstance(repr(wishlist), str)
        wishlist.name = "My Wishlist"
        self.assertEqual(
            f"<Wishlists {wishlist.name} id=[{wishlist.id}]>", repr(wishlist)
        )

    def test_wishlist_items_repr(self):
        """It should return a string representation of a WishlistItems"""
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
        self.assertIsNone(wishlist.updated_date)

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
        SIZE = 5
        # Create items with non-sequential positions
        positions = random.sample(range(1, SIZE * 1000, 1000), 3)
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
