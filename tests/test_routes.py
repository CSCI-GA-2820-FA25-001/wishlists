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
TestYourResourceModel API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db
from service.models import Wishlists, WishlistItems
from tests.factories import WishlistsFactory, WishlistItemsFactory
from tests.factories import CUSTOMER_ID


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestWishlistsService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Wishlists).delete()  # clean up the last tests
        db.session.query(WishlistItems).delete()
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_get_wishlists_empty(self):
        """It should get an empty list of Wishlists"""
        resp = self.client.get("/wishlists")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json), 0)

    def test_get_wishlists(self):
        """It should get a list of Wishlists"""
        wishlist = WishlistsFactory()
        wishlist.create()
        resp = self.client.get("/wishlists")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["name"], wishlist.name)
        self.assertEqual(resp.json[0]["customer_id"], CUSTOMER_ID)

    def test_create_wishlist(self):
        """It should create a new wishlist"""
        # should not use factory to create wishlist
        new_wishlist = {
            "customer_id": CUSTOMER_ID,
            "name": "My Wishlist",
            "description": "A description",
            "category": "SHOPPING_LIST",
        }
        resp = self.client.post("/wishlists", json=new_wishlist)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("Location", resp.headers)
        expected_location = f"/wishlists/{resp.json['id']}"
        self.assertTrue(resp.headers["Location"].endswith(expected_location))
        data = resp.json
        self.assertEqual(data["name"], new_wishlist["name"])
        self.assertEqual(data["customer_id"], new_wishlist["customer_id"])
        self.assertEqual(data["description"], new_wishlist["description"])
        self.assertEqual(data["category"], new_wishlist["category"])
        self.assertIsNotNone(data["id"])
        self.assertIsNotNone(data["created_date"])
        self.assertIsNone(data["updated_date"])
        self.assertEqual(data["wishlist_items"], [])

    def test_create_wishlist_invalid(self):
        """It should not create a wishlist with missing data"""
        resp = self.client.post("/wishlists", data="Hello World!")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        resp = self.client.post("/wishlists", json={"name": "Missing customer_id"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_wishlist(self):
        """It should get a single wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        resp = self.client.get(f"/wishlists/{wishlist.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json["name"], wishlist.name)
        self.assertEqual(resp.json["customer_id"], CUSTOMER_ID)

    def test_get_wishlist_not_found(self):
        """It should not get a wishlist that is not found"""
        resp = self.client.get("/wishlists/12345")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_wishlist_forbidden(self):
        """It should not get a wishlist that belongs to a different customer"""
        wishlist = WishlistsFactory(customer_id=CUSTOMER_ID + 1)
        wishlist.create()
        resp = self.client.get(f"/wishlists/{wishlist.id}")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_wishlist(self):
        """It should update a wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        updated_wishlist = {
            "customer_id": CUSTOMER_ID,
            "name": "Updated Wishlist",
            "description": "An updated description",
            "category": "GIFT_LIST",
        }
        resp = self.client.put(f"/wishlists/{wishlist.id}", json=updated_wishlist)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json
        self.assertEqual(data["name"], updated_wishlist["name"])
        self.assertEqual(data["customer_id"], updated_wishlist["customer_id"])
        self.assertEqual(data["description"], updated_wishlist["description"])
        self.assertEqual(data["category"], updated_wishlist["category"])
        self.assertEqual(data["id"], wishlist.id)
        self.assertIsNotNone(data["created_date"])
        self.assertIsNotNone(data["updated_date"])
        self.assertEqual(data["wishlist_items"], [])

    def test_update_wishlist_invalid(self):
        """It should not update a wishlist with invalid body"""
        wishlist = WishlistsFactory()
        wishlist.create()
        wishlist_snapshot = wishlist.serialize()
        # Test with a non-JSON body
        resp = self.client.put(f"/wishlists/{wishlist.id}", data="Hello World!")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Request body must be JSON", resp.get_data(as_text=True))
        # Test with missing customer_id
        resp = self.client.put(
            f"/wishlists/{wishlist.id}", json={"name": "Missing customer_id"}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing key: customer_id", resp.get_data(as_text=True))
        # Test non-existent wishlist
        resp = self.client.put(
            "/wishlists/9999", json={"name": "Non-existent", "customer_id": CUSTOMER_ID}
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Wishlist with id 9999 not found", resp.get_data(as_text=True))

        # no changes should be made
        data = Wishlists.find_by_id(wishlist.id)
        self.assertEqual(data.serialize(), wishlist_snapshot)

    def test_update_wishlist_forbidden(self):
        """It should not update a wishlist that belongs to a different customer"""
        wishlist = WishlistsFactory(customer_id=CUSTOMER_ID + 1)
        wishlist.create()
        wishlist_snapshot = wishlist.serialize()
        updated_wishlist = {
            "customer_id": CUSTOMER_ID + 1,
            "name": "Updated Wishlist",
            "description": "An updated description",
            "category": "GIFT_LIST",
        }
        resp = self.client.put(f"/wishlists/{wishlist.id}", json=updated_wishlist)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(
            f"Access to wishlist id {wishlist.id} is forbidden",
            resp.get_data(as_text=True),
        )
        updated_wishlist["customer_id"] = CUSTOMER_ID
        resp = self.client.put(f"/wishlists/{wishlist.id}", json=updated_wishlist)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(
            f"Access to wishlist id {wishlist.id} is forbidden",
            resp.get_data(as_text=True),
        )

        # no changes should be made
        data = Wishlists.find_by_id(wishlist.id)
        self.assertEqual(data.serialize(), wishlist_snapshot)

    def test_add_wishlist_item(self):
        """It should add an item to a wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        new_item = {
            "product_id": 123,
            "description": "Gift for a friend",
        }
        resp = self.client.post(f"/wishlists/{wishlist.id}/items", json=new_item)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("Location", resp.headers)
        expected_location = f"/wishlists/{wishlist.id}/items/{resp.json['product_id']}"
        self.assertTrue(resp.headers["Location"].endswith(expected_location))
        data = resp.json
        self.assertEqual(data["product_id"], new_item["product_id"])
        self.assertEqual(data["wishlist_id"], wishlist.id)
        self.assertEqual(data["description"], new_item["description"])
        self.assertEqual(data["position"], 1000)

        new_item = {
            "product_id": 456,
            "description": "Another gift",
        }
        resp = self.client.post(f"/wishlists/{wishlist.id}/items", json=new_item)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.json
        self.assertEqual(data["position"], 2000)
        self.assertEqual(data["product_id"], new_item["product_id"])
        self.assertEqual(data["wishlist_id"], wishlist.id)
        self.assertEqual(data["description"], new_item["description"])

        # check get wishlist includes items
        resp = self.client.get(f"/wishlists/{wishlist.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json["wishlist_items"]), 2)
        self.assertEqual(resp.json["wishlist_items"][0]["position"], 1000)
        self.assertEqual(resp.json["wishlist_items"][1]["position"], 2000)
        self.assertEqual(resp.json["wishlist_items"][0]["product_id"], 123)
        self.assertEqual(resp.json["wishlist_items"][1]["product_id"], 456)
        self.assertEqual(
            resp.json["wishlist_items"][0]["description"], "Gift for a friend"
        )
        self.assertEqual(resp.json["wishlist_items"][1]["description"], "Another gift")
        self.assertEqual(resp.json["wishlist_items"][0]["wishlist_id"], wishlist.id)
        self.assertEqual(resp.json["wishlist_items"][1]["wishlist_id"], wishlist.id)

    def test_add_wishlist_item_duplicate(self):
        """It should not add a duplicate item to a wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        new_item = {
            "product_id": 123,
            "description": "Gift for a friend",
        }
        resp = self.client.post(f"/wishlists/{wishlist.id}/items", json=new_item)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Try to add the same product_id again
        new_item["description"] = "Gift for another friend"
        resp = self.client.post(f"/wishlists/{wishlist.id}/items", json=new_item)
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertIn(
            f"Product ID {new_item['product_id']} is already in wishlist id {wishlist.id}",
            resp.get_data(as_text=True),
        )

        # Only one item should be present
        resp = self.client.get(f"/wishlists/{wishlist.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json["wishlist_items"]), 1)

    def test_add_wishlist_item_invalid(self):
        """It should not add an item to a wishlist with invalid body"""
        wishlist = WishlistsFactory()
        wishlist.create()
        # Test with a non-JSON body
        resp = self.client.post(f"/wishlists/{wishlist.id}/items", data="Hello World!")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Request body must be JSON", resp.get_data(as_text=True))
        # Test with missing product_id
        resp = self.client.post(
            f"/wishlists/{wishlist.id}/items",
            json={"description": "Missing product_id"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Product ID is required", resp.get_data(as_text=True))
        # Test non-existent wishlist
        resp = self.client.post(
            "/wishlists/9999/items", json={"product_id": 123, "description": "Test"}
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Wishlist with id 9999 not found", resp.get_data(as_text=True))

        # no data should be added
        data = WishlistItems.find_all_by_wishlist_id(wishlist.id)
        self.assertEqual(len(data), 0)

    def test_add_wishlist_item_forbidden(self):
        """It should not add an item to a wishlist that belongs to a different customer"""
        wishlist = WishlistsFactory(customer_id=CUSTOMER_ID + 1)
        wishlist.create()
        new_item = {
            "product_id": 123,
            "description": "Gift for a friend",
        }
        resp = self.client.post(f"/wishlists/{wishlist.id}/items", json=new_item)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(
            f"Access to wishlist id {wishlist.id} is forbidden",
            resp.get_data(as_text=True),
        )

        # no data should be added
        data = WishlistItems.find_all_by_wishlist_id(wishlist.id)
        self.assertEqual(len(data), 0)

    def test_get_wishlist_item(self):
        """It should get a single wishlist item"""
        wishlist = WishlistsFactory()
        wishlist.create()
        item = WishlistItemsFactory(wishlist_id=wishlist.id)
        item.create()
        resp = self.client.get(f"/wishlists/{wishlist.id}/items/{item.product_id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json["product_id"], item.product_id)
        self.assertEqual(resp.json["wishlist_id"], wishlist.id)
        self.assertEqual(resp.json["description"], item.description)
        self.assertEqual(resp.json["position"], item.position)

    def test_get_wishlist_invalid(self):
        """It should not get a wishlist item that is not found, or for a non-existent wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        resp = self.client.get(f"/wishlists/{wishlist.id}/items/12345")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn(
            f"Product ID 12345 not found in wishlist id {wishlist.id}",
            resp.get_data(as_text=True),
        )
        resp = self.client.get("/wishlists/9999/items/12345")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Wishlist with id 9999 not found", resp.get_data(as_text=True))

    def test_get_wishlist_item_forbidden(self):
        """It should not get a wishlist item that belongs to a different customer's wishlist"""
        wishlist = WishlistsFactory(customer_id=CUSTOMER_ID + 1)
        wishlist.create()
        item = WishlistItemsFactory(wishlist_id=wishlist.id)
        item.create()
        resp = self.client.get(f"/wishlists/{wishlist.id}/items/{item.product_id}")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(
            f"Access to wishlist id {wishlist.id} is forbidden",
            resp.get_data(as_text=True),
        )
