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

    def test_update_wishlist(self):
        """It should update an existing wishlist"""

    def test_create_wishlist(self):
        """It should Create a new Wishlist"""
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

        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_wishlist_bad_request(self):
        """It should not create a wishlist with missing data"""
        resp = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_wishlist_method_not_allowed(self):
        """It should not allow an illegal method"""
        resp = self.client.put(BASE_URL, json={"not": "today"})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_wishlist(self):
        """It should Get a single Wishlist"""
        # get the id of a wishlist
        wishlist = self._create_wishlists(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/{wishlist.id}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], wishlist.id)
        self.assertEqual(data["name"], wishlist.name)
        self.assertEqual(data["description"], wishlist.description)
        self.assertEqual(data["category"], wishlist.category)
        self.assertEqual(data["created_date"], wishlist.created_date.isoformat())

    def test_get_wishlist_not_found(self):
        """It should not Get a Wishlist that is not found"""
        resp = self.client.get(f"{BASE_URL}/0", content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_wishlist(self):
        """It should delete a wishlist"""
        # get the id of a wishlist
        wishlist = self._create_wishlists(1)[0]
        resp = self.client.delete(f"{BASE_URL}/{wishlist.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Delete the same id again, still return 204
        resp = self.client.delete(f"{BASE_URL}/{wishlist.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    ######################################################################
    #  I T E M S   T E S T   C A S E S
    ######################################################################

    def test_add_wishlist_item(self):
        """It should Add a wishlist item to a wishlist"""
        wishlist = self._create_wishlists(1)[0]
        wishlist_item = WishlistItemsFactory()
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/wishlist_items",
            json=wishlist_item.serialize(),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)

        data = resp.get_json()
        logging.debug(data)
        self.assertEqual(data["wishlist_id"], wishlist.id)
        self.assertEqual(data["product_id"], wishlist_item.product_id)
        self.assertEqual(data["description"], wishlist_item.description)
        self.assertEqual(data["position"], wishlist_item.position)

        # TODO: Uncomment once GET wishlist_item endpoint is implemented
        # Check that the location header was correct by getting it
        # resp = self.client.get(location, content_type="application/json")
        # self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # new_wishlist_item = resp.get_json()
        # self.assertEqual(
        #     new_wishlist_item["wishlist_id"],
        #     wishlist_item.wishlist_id,
        #     "Wishlist ID does not match",
        # )

