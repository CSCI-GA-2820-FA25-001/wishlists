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
        """It should Create a new Wishlist"""
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

    def test_list_wishlists(self):
        """It should Get a list of Wishlists"""
        self._create_wishlists(5)
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 5)

    def test_list_wishlists_empty(self):
        """It should return an empty list when no wishlists exist"""
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 0)
        self.assertEqual(data, [])

    def test_list_wishlists_by_customer_id(self):
        """It should Get a list of Wishlists filtered by customer_id"""
        # Create wishlists with the default customer_id
        self._create_wishlists(3)

        # Query for wishlists by customer_id
        resp = self.client.get(BASE_URL, query_string={"customer_id": CUSTOMER_ID})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 3)
        # Verify all wishlists have the correct customer_id
        for wishlist in data:
            self.assertEqual(wishlist["customer_id"], CUSTOMER_ID)

    ######################################################################
    #  I T E M S   T E S T   C A S E S
    ######################################################################

    def test_get_wishlist_item(self):
        """It should Read a Wishlist Item"""
        # Create a wishlist first
        wishlist = self._create_wishlists(1)[0]

        # Create a wishlist item
        # TODO: Wait until create_wishlist_items is implemented
        wishlist_item = WishlistItemsFactory()
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/wishlist_items",
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

    def test_delete_wishlist_item(self):
        """It should Delete a wishlist item"""
        wishlist = self._create_wishlists(1)[0]
        wishlist_item = WishlistItemsFactory()
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/wishlist_items",
            json=wishlist_item.serialize(),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.get_json()
        logging.debug(data)
        wishlist_item_id = data["product_id"]

        # send delete request
        resp = self.client.delete(
            f"{BASE_URL}/{wishlist.id}/wishlist_items/{wishlist_item_id}",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
