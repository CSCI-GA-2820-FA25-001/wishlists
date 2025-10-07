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
BASE_URL = "/wishlist_items"


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

    def test_create_wishlist_item(self):
        """It should Create a new Wishlist Item"""

        # Todo: Delete these two lines of code after create_wishlist is implemented
        test_wishlist = WishlistsFactory()
        test_wishlist.create()

        test_wishlist_item = WishlistItemsFactory()

        # Todo: Delete this line of code after create_wishlist is implemented
        test_wishlist_item.wishlist_id = test_wishlist.id

        logging.debug("Test Wishlist Item: %s", test_wishlist_item.serialize())
        response = self.client.post(BASE_URL, json=test_wishlist_item.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_wishlist_item = response.get_json()
        self.assertEqual(
            new_wishlist_item["wishlist_id"], test_wishlist_item.wishlist_id
        )
        self.assertEqual(new_wishlist_item["product_id"], test_wishlist_item.product_id)
        self.assertEqual(
            new_wishlist_item["description"], test_wishlist_item.description
        )
        self.assertEqual(new_wishlist_item["position"], test_wishlist_item.position)

        # Todo: Uncomment this code when get_wishlist_items is implemented
        # Check that the location header was correct
        # response = self.client.get(location)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # new_wishlist_item = response.get_json()
        # self.assertEqual(
        #     new_wishlist_item["wishlist_id"], test_wishlist_item.wishlist_id
        # )
        # self.assertEqual(new_wishlist_item["product_id"], test_wishlist_item.product_id)
        # self.assertEqual(
        #     new_wishlist_item["description"], test_wishlist_item.description
        # )
        # self.assertEqual(new_wishlist_item["position"], test_wishlist_item.position)
