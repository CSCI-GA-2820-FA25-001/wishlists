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
from datetime import date
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

    def test_update_wishlist(self):
        """It should update an existing wishlist"""
        wishlist = WishlistsFactory()
        wishlist.create()
        self.assertIsNotNone(wishlist.id)
        original_id = wishlist.id
        
        payload = {
            "customer_id": CUSTOMER_ID,
            "name": "Updated Wishlist Name",
            "description": "Updated description",
            "category": "Updated category",
            "created_date": wishlist.created_date.isoformat()
        }
        
        resp = self.client.put(
            f"/wishlists/{wishlist.id}",
            json=payload,
            content_type="application/json"
        )
        
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data["id"], original_id)
        self.assertEqual(data["name"], payload["name"])
        self.assertEqual(data["description"], payload["description"])
        self.assertEqual(data["category"], payload["category"])
        self.assertEqual(data["customer_id"], payload["customer_id"])
        
    def test_update_wishlist_not_found(self):
        """It should return 404 when updating a wishlist that does not exist"""
        payload = {
            "customer_id": CUSTOMER_ID,
            "name": "Updated Name",
            "created_date": date.today().isoformat()
        }
        
        resp = self.client.put(
            "/wishlists/9999",
            json=payload,
            content_type="application/json"
        )
        
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIsNotNone(data)
        self.assertIn("error", data)
        
    def test_update_wishlist_forbidden(self):
        """It should return 403 when updating a wishlist that belongs to another customer"""
        wishlist = WishlistsFactory()
        wishlist.customer_id = 999
        wishlist.create()
        
        payload = {
            "customer_id": 999,
            "name": "Updated Name",
            "created_date": wishlist.created_date.isoformat()
        }
        
        resp = self.client.put(
            f"/wishlists/{wishlist.id}",
            json=payload,
            content_type="application/json"
        )
        
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        data = resp.get_json()
        self.assertIsNotNone(data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Forbidden")
        
    def test_update_wishlist_bad_request(self):
        """It should return 400 when updating with invalid data"""
        wishlist = WishlistsFactory()
        wishlist.create()
        
        payload = {
            "customer_id": "not_an_integer",
            "name": "Updated Name"
        }
        
        resp = self.client.put(
            f"/wishlists/{wishlist.id}",
            json=payload,
            content_type="application/json"
        )
        
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIsNotNone(data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Bad Request")
