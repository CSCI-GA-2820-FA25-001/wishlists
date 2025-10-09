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

BASE_URL = "/wishlists"


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
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_wishlists(self, count):
        """Factory method to create wishlists in bulk"""
        wishlists = []
        for _ in range(count):
            wishlist = WishlistsFactory()
            resp = self.client.post(
                BASE_URL, json=wishlist.serialize(), content_type="application/json"
            )
            self.assertEqual(
                resp.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Wishlist",
            )
            new_wishlist = resp.get_json()
            wishlist.id = new_wishlist["id"]
            wishlists.append(wishlist)
        return wishlists

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_wishlist(self):
        """It should Create a new Account"""
        wishlist = WishlistsFactory()
        resp = self.client.post(
            BASE_URL, json=wishlist.serialize(), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_wishlist = resp.get_json()
        self.assertEqual(new_wishlist["name"], wishlist.name, "Names do not match")
        self.assertEqual(
            new_wishlist["description"],
            wishlist.description,
            "Descriptions do not match",
        )
        self.assertEqual(
            new_wishlist["category"], wishlist.category, "Categories do not match"
        )
        self.assertEqual(
            new_wishlist["created_date"],
            str(wishlist.created_date),
            "Created date is not set",
        )

        # **TODO** Uncomment once get_wishlists is implemented

        # Check that the location header was correct by getting it
        # resp = self.client.get(location, content_type="application/json")
        # self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # new_wishlist = resp.get_json()
        # self.assertEqual(new_wishlist["name"], wishlist.name, "Names do not match")
        # self.assertEqual(
        #     new_wishlist["description"], wishlist.description, "Descriptions do not match"
        # )
        # self.assertEqual(
        #     new_wishlist["category"], wishlist.category, "Categories do not match"
        # )
        # self.assertEqual(
        #     new_wishlist["created_date"], str(wishlist.created_date), "Created date is not set"
        # )

    def test_create_wishlist_unsupported_media_type(self):
        """It should reject non-JSON Content-Type with 415"""
        wishlist = WishlistsFactory()
        resp = self.client.post(
            BASE_URL, json=wishlist.serialize(), content_type="text/plain"
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_wishlist_item(self):
        """It should Read a Wishlist Item"""
        # Create a wishlist first
        wishlist = self._create_wishlists(1)[0]

        # Create a wishlist item
        # TODO: Wait until create_wishlist_items is implemented
        wishlist_item = WishlistItemsFactory()
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items",
            json=wishlist_item.serialize(),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.get_json()
        wishlist_item.product_id = data["product_id"]

        # retrieve it back
        resp = self.client.get(
            f"{BASE_URL}/{wishlist.id}/items/{wishlist_item.product_id}",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        self.assertEqual(data["wishlist_id"], wishlist.id)
        self.assertEqual(data["description"], wishlist_item.description)
        self.assertEqual(data["position"], wishlist_item.position)
        self.assertEqual(data["product_id"], wishlist_item.product_id)

    def test_get_wishlist_item_not_found(self):
        """It should return 404 for a non-existent Wishlist Item"""
        wishlist = self._create_wishlists(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/{wishlist.id}/items/9999",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_wishlist_item_wishlist_not_found(self):
        """It should return 404 for a non-existent Wishlist"""
        resp = self.client.get(
            f"{BASE_URL}/9999/items/1",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
