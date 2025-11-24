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

BASE_URL = "/api/wishlists"


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
        db.session.rollback()
        db.session.query(WishlistItems).delete()
        db.session.query(Wishlists).delete()  # clean up the last tests
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
    #  R O U T E   T E S T S
    ######################################################################

    def test_index(self):
        """It should return the HTML home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.mimetype, "text/html")
        self.assertIn(b"Wishlists REST API Service", resp.data)

    def test_health(self):
        """It should get the health check"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.content_type, "application/json")

        # Get the JSON data
        data = resp.get_json()

        # Verify the response
        self.assertIn("status", data)
        self.assertEqual(data["status"], "OK")

    ######################################################################
    # Wishlist
    ######################################################################

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

    def test_list_wishlists_by_customer_id_and_name_like(self):
        """It should Get a list of Wishlists filtered by customer_id and name containing a substring"""
        # Create wishlists with the default customer_id
        for i in range(3):
            wishlist = WishlistsFactory(name=f"My Wishlist {i}")
            resp = self.client.post(
                BASE_URL, json=wishlist.serialize(), content_type="application/json"
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Create wishlists with the default customer_id
        for i in range(2):
            wishlist = WishlistsFactory(name=f"Other Wishlist {i}")
            resp = self.client.post(
                BASE_URL, json=wishlist.serialize(), content_type="application/json"
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Query for wishlists by customer_id and name containing a substring
        resp = self.client.get(
            BASE_URL, query_string={"customer_id": CUSTOMER_ID, "name": "My Wishlist"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 3)

        for wishlist in data:
            self.assertIn("My Wishlist", wishlist["name"])

        # Query for wishlists by customer_id and name containing a substring
        resp = self.client.get(
            BASE_URL,
            query_string={"customer_id": CUSTOMER_ID, "name": "Other Wishlist"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 2)

        for wishlist in data:
            self.assertIn("Other Wishlist", wishlist["name"])

    def test_list_wishlists_by_customer_and_category(self):
        """It should list by customer_id AND category"""
        for _ in range(3):
            w = WishlistsFactory(customer_id=CUSTOMER_ID, category="gifts", name="A")
            r = self.client.post(
                BASE_URL, json=w.serialize(), content_type="application/json"
            )
            self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        for _ in range(2):
            w = WishlistsFactory(customer_id=CUSTOMER_ID, category="books", name="B")
            r = self.client.post(
                BASE_URL, json=w.serialize(), content_type="application/json"
            )
            self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        for _ in range(2):
            w = WishlistsFactory(customer_id=999, category="gifts", name="C")
            r = self.client.post(
                BASE_URL, json=w.serialize(), content_type="application/json"
            )
            self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        resp = self.client.get(
            BASE_URL, query_string={"customer_id": CUSTOMER_ID, "category": "GIFTS"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 3)
        for wl in data:
            self.assertEqual(wl["customer_id"], CUSTOMER_ID)
        self.assertTrue(all(wl["category"].lower() == "gifts" for wl in data))

    def test_list_wishlists_by_name_like_global(self):
        """It should list by name (global, name-like & case-insensitive)"""
        samples = [
            {"customer_id": CUSTOMER_ID, "name": "Birthday Gifts"},
            {"customer_id": CUSTOMER_ID, "name": "Gift List"},
            {"customer_id": 999, "name": "my gift ideas"},
            {"customer_id": 888, "name": "GIFT registry"},
        ]

        for s in samples:
            w = WishlistsFactory(**s, category="misc")
            r = self.client.post(
                BASE_URL, json=w.serialize(), content_type="application/json"
            )
            self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        w = WishlistsFactory(customer_id=CUSTOMER_ID, name="Holiday", category="misc")
        r = self.client.post(
            BASE_URL, json=w.serialize(), content_type="application/json"
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        resp = self.client.get(BASE_URL, query_string={"name": "GiFt"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 4)
        self.assertTrue(all("gift" in wl["name"].lower() for wl in data))

    def test_list_wishlists_by_customer_category_name_like(self):
        """It should list by customer_id AND category AND name-like"""

        pos = [
            {"customer_id": CUSTOMER_ID, "category": "gifts", "name": "My Gift 1"},
            {"customer_id": CUSTOMER_ID, "category": "GIFTS", "name": "gift ideas 2"},
        ]

        for s in pos:
            w = WishlistsFactory(**s, description="x")
            r = self.client.post(
                BASE_URL, json=w.serialize(), content_type="application/json"
            )
            self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        w = WishlistsFactory(customer_id=CUSTOMER_ID, category="gifts", name="Holiday")
        r = self.client.post(
            BASE_URL, json=w.serialize(), content_type="application/json"
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        w = WishlistsFactory(
            customer_id=CUSTOMER_ID, category="books", name="Gift book"
        )
        r = self.client.post(
            BASE_URL, json=w.serialize(), content_type="application/json"
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        w = WishlistsFactory(customer_id=999, category="gifts", name="Awesome Gift")
        r = self.client.post(
            BASE_URL, json=w.serialize(), content_type="application/json"
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        resp = self.client.get(
            BASE_URL,
            query_string={
                "customer_id": CUSTOMER_ID,
                "category": "gifts",
                "name": "GiFt",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 2)
        for wl in data:
            self.assertEqual(wl["customer_id"], CUSTOMER_ID)
            self.assertEqual(wl["category"].lower(), "gifts")
            self.assertIn("gift", wl["name"].lower())

    def test_list_wishlists_by_category_global(self):
        """It should list wishlists by category globally"""

        for _ in range(3):
            w = WishlistsFactory(customer_id=CUSTOMER_ID, category="gifts")
            resp = self.client.post(
                BASE_URL, json=w.serialize(), content_type="application/json"
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        for _ in range(2):
            w = WishlistsFactory(customer_id=CUSTOMER_ID, category="books")
            resp = self.client.post(
                BASE_URL, json=w.serialize(), content_type="application/json"
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        w = WishlistsFactory(customer_id=CUSTOMER_ID, category="travel")
        resp = self.client.post(
            BASE_URL, json=w.serialize(), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        for _ in range(2):
            w = WishlistsFactory(customer_id=999, category="gifts")
            resp = self.client.post(
                BASE_URL, json=w.serialize(), content_type="application/json"
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.get(BASE_URL, query_string={"category": "gifts"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        self.assertEqual(len(data), 5)
        for wl in data:
            self.assertEqual(wl["category"].lower(), "gifts")

        resp = self.client.get(BASE_URL, query_string={"category": "GIFTS"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data2 = resp.get_json()
        self.assertEqual(len(data2), 5)
        for wl in data2:
            self.assertEqual(wl["category"].lower(), "gifts")

    def test_list_wishlists_by_nonexistent_category(self):
        """It should return an empty list when filtering by a non-existent category for the current user"""
        # Create some wishlists with known categories for the current user
        for _ in range(3):
            wishlist = WishlistsFactory(customer_id=CUSTOMER_ID, category="gifts")
            resp = self.client.post(
                BASE_URL, json=wishlist.serialize(), content_type="application/json"
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Query for a category that doesn't exist for the current user
        resp = self.client.get(BASE_URL, query_string={"category": "nonexistent"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 0)
        self.assertEqual(data, [])

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

    def test_update_wishlist(self):
        """It should Update an existing Wishlist"""
        wishlist = self._create_wishlists(1)[0]
        self.assertIsNotNone(wishlist.id)
        original_id = wishlist.id

        payload = {
            "customer_id": CUSTOMER_ID,
            "name": "Updated Wishlist Name",
            "description": "Updated description",
            "category": "Updated category",
            "created_date": wishlist.created_date.isoformat(),
        }

        resp = self.client.put(
            f"{BASE_URL}/{wishlist.id}",
            json=payload,
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data["id"], original_id, "IDs do not match")
        self.assertEqual(data["name"], payload["name"], "Names do not match")
        self.assertEqual(
            data["description"],
            payload["description"],
            "Descriptions do not match",
        )
        self.assertEqual(
            data["category"],
            payload["category"],
            "Categories do not match",
        )
        self.assertEqual(
            data["customer_id"],
            payload["customer_id"],
            "Customer IDs do not match",
        )

    def test_update_wishlist_not_found(self):
        """It should not Update a Wishlist that is not found"""
        payload = {
            "customer_id": CUSTOMER_ID,
            "name": "Updated Name",
            "created_date": date.today().isoformat(),
        }

        resp = self.client.put(
            f"{BASE_URL}/9999", json=payload, content_type="application/json"
        )

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_wishlist_validates_field_types(self):
        """It should reject PUT when field types are invalid (tests deserialize validation)"""
        wl = self._create_wishlists(1)[0]
        body = {"name": 123}
        resp = self.client.put(
            f"{BASE_URL}/{wl.id}", json=body, content_type="application/json"
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", resp.get_json()["message"].lower())

    def test_update_wishlist_forbidden(self):
        """It should return 403 when updating a Wishlist that belongs to another customer"""
        wishlist = WishlistsFactory()
        wishlist.customer_id = 999
        resp = self.client.post(
            BASE_URL, json=wishlist.serialize(), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        new_wishlist = resp.get_json()
        wishlist.id = new_wishlist["id"]

        payload = {
            "customer_id": 999,
            "name": "Updated Name",
            "created_date": wishlist.created_date.isoformat(),
        }

        resp = self.client.put(
            f"{BASE_URL}/{wishlist.id}", json=payload, content_type="application/json"
        )

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_wishlist_bad_request(self):
        """It should not Update a Wishlist with invalid data"""
        wishlist = self._create_wishlists(1)[0]

        payload = {
            "customer_id": CUSTOMER_ID,
            "name": None,
        }

        resp = self.client.put(
            f"{BASE_URL}/{wishlist.id}", json=payload, content_type="application/json"
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_wishlist_rejects_mismatched_body_id(self):
        """It should reject PUT when body.id mismatches path id"""
        wl = self._create_wishlists(1)[0]
        body = {"id": wl.id + 1, "name": "x"}
        resp = self.client.put(
            f"{BASE_URL}/{wl.id}", json=body, content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_wishlist_rejects_non_integer_id(self):
        """It should reject PUT when body.id is not an integer"""
        wl = self._create_wishlists(1)[0]
        body = {"id": "abc", "name": "x"}
        resp = self.client.put(
            f"{BASE_URL}/{wl.id}", json=body, content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_wishlist_ignores_customer_id_change(self):
        """It should ignore changing customer_id on PUT"""
        wl = self._create_wishlists(1)[0]
        original_owner = wl.customer_id
        body = {"name": "updated", "customer_id": original_owner + 999}
        resp = self.client.put(
            f"{BASE_URL}/{wl.id}", json=body, content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        wl = db.session.get(Wishlists, wl.id)
        self.assertEqual(wl.customer_id, original_owner)

    def test_update_wishlist_accepts_matching_id(self):
        """It should accept PUT when body.id matches path id"""
        wl = self._create_wishlists(1)[0]
        body = {"id": wl.id, "name": "match", "customer_id": wl.customer_id}
        resp = self.client.put(
            f"{BASE_URL}/{wl.id}", json=body, content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["name"], "match")

    def test_update_wishlist_accepts_no_id_in_body(self):
        """It should accept PUT with no id in body"""
        wl = self._create_wishlists(1)[0]
        body = {"name": "no-id", "customer_id": wl.customer_id}
        resp = self.client.put(
            f"{BASE_URL}/{wl.id}", json=body, content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["name"], "no-id")

    def test_update_wishlist_invalid_or_missing_json(self):
        """It should reject PUT with invalid JSON"""
        wl = self._create_wishlists(1)[0]
        resp = self.client.put(
            f"{BASE_URL}/{wl.id}", data="not-json", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_wishlist(self):
        """It should Get a single Wishlist"""
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
        wishlist = self._create_wishlists(1)[0]
        resp = self.client.delete(f"{BASE_URL}/{wishlist.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Delete the same id again, still return 204
        resp = self.client.delete(f"{BASE_URL}/{wishlist.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    ######################################################################
    #  Wishlist Items
    ######################################################################

    def test_get_wishlist_item(self):
        """It should Read a Wishlist Item"""
        wishlist = self._create_wishlists(1)[0]

        wishlist_item = WishlistItemsFactory()
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items",
            json=wishlist_item.serialize(),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.get_json()
        wishlist_item.product_id = data["product_id"]

        resp = self.client.get(
            f"{BASE_URL}/{wishlist.id}/items/{wishlist_item.product_id}",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        self.assertEqual(data["wishlist_id"], wishlist.id)
        self.assertEqual(data["description"], wishlist_item.description)
        # self.assertEqual(data["position"], wishlist_item.position)
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
            f"{BASE_URL}/{wishlist.id}/items",
            json=wishlist_item.serialize(),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)

        data = resp.get_json()
        logging.debug(data)
        self.assertEqual(data["wishlist_id"], wishlist.id)
        self.assertEqual(data["product_id"], wishlist_item.product_id)
        self.assertEqual(data["description"], wishlist_item.description)
        # self.assertEqual(data["position"], wishlist_item.position)

    def test_delete_wishlist_item(self):
        """It should Delete a wishlist item"""
        wishlist = self._create_wishlists(1)[0]
        wishlist_item = WishlistItemsFactory()
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items",
            json=wishlist_item.serialize(),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.get_json()
        logging.debug(data)
        product_id = data["product_id"]

        resp = self.client.delete(
            f"{BASE_URL}/{wishlist.id}/items/{product_id}",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_wishlist_item_wishlist_not_found(self):
        """It should return 404 when deleting an item from a non-existent wishlist"""
        resp = self.client.delete(
            f"{BASE_URL}/9999/items/1",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_wishlist_item_not_found(self):
        """It should return 404 when deleting a non-existent wishlist item"""
        wishlist = self._create_wishlists(1)[0]
        resp = self.client.delete(
            f"{BASE_URL}/{wishlist.id}/items/9999",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_wishlist_items(self):
        """It should List wishlist items for a wishlist"""
        wishlist = self._create_wishlists(1)[0]
        self.assertIsNotNone(wishlist.id)

        # Add 5 items to the wishlist
        for _ in range(5):
            wishlist_item = WishlistItemsFactory()
            resp = self.client.post(
                f"{BASE_URL}/{wishlist.id}/items",
                json=wishlist_item.serialize(),
                content_type="application/json",
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # List all items
        resp = self.client.get(f"{BASE_URL}/{wishlist.id}/items")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 5)

    def test_list_wishlist_items_empty(self):
        """It should return an empty list when wishlist has no items"""
        wishlist = self._create_wishlists(1)[0]
        self.assertIsNotNone(wishlist.id)

        # List all items
        resp = self.client.get(f"{BASE_URL}/{wishlist.id}/items")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 0)
        self.assertEqual(data, [])

    def test_list_wishlist_items_wishlist_not_found(self):
        """It should return 404 when listing items for a non-existent wishlist"""
        resp = self.client.get(f"{BASE_URL}/9999/items")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_wishlist_item(self):
        """It should Update a wishlist item on a wishlist"""
        # create a known wishlist item
        wishlist = self._create_wishlists(1)[0]
        wishlist_item = WishlistItemsFactory()
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items",
            json=wishlist_item.serialize(),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.get_json()
        logging.debug(data)
        product_id = data["product_id"]

        # send the update back
        resp = self.client.put(
            f"{BASE_URL}/{wishlist.id}/items/{product_id}",
            json=data,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # retrieve it back
        resp = self.client.get(
            f"{BASE_URL}/{wishlist.id}/items/{product_id}",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        logging.debug(data)
        self.assertEqual(data["product_id"], product_id)
        self.assertEqual(data["wishlist_id"], wishlist.id)

    def test_add_wishlist_item_wishlist_not_found(self):
        """It should return 404 when adding an item to a non-existent wishlist"""
        wishlist_item = WishlistItemsFactory()
        resp = self.client.post(
            f"{BASE_URL}/9999/items",
            json=wishlist_item.serialize(),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_wishlist_item_no_content_type(self):
        """It should return 415 when Content-Type header is missing"""
        wishlist = self._create_wishlists(1)[0]
        wishlist_item = WishlistItemsFactory()
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items",
            data=str(wishlist_item.serialize()),
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_add_wishlist_item_wrong_content_type(self):
        """It should return 415 when Content-Type is not application/json"""
        wishlist = self._create_wishlists(1)[0]
        wishlist_item = WishlistItemsFactory()
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items",
            json=wishlist_item.serialize(),
            content_type="text/html",
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_update_wishlist_item_wishlist_not_found(self):
        """It should return 404 when updating an item on a non-existent wishlist"""
        resp = self.client.put(
            f"{BASE_URL}/9999/items/1",
            json={"description": "updated"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_wishlist_item_not_found(self):
        """It should return 404 when updating a non-existent wishlist item"""
        wishlist = self._create_wishlists(1)[0]
        resp = self.client.put(
            f"{BASE_URL}/{wishlist.id}/items/9999",
            json={"description": "updated"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_wishlist_item_bad_request(self):
        """It should return 400 when updating a wishlist item with invalid data"""
        # create a known wishlist item
        wishlist = self._create_wishlists(1)[0]
        wishlist_item = WishlistItemsFactory()
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items",
            json=wishlist_item.serialize(),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.get_json()
        logging.debug(data)
        product_id = data["product_id"]

        # send the update back with invalid data
        resp = self.client.put(
            f"{BASE_URL}/{wishlist.id}/items/{product_id}",
            json={"position": "not-an-integer"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_move_wishlist_item(self):
        """It should Move a wishlist item to a new position"""
        # create a known wishlist item
        wishlist = WishlistsFactory()
        wishlist.create()

        # create 2 wishlist items
        wishlist_items = []
        for _ in range(2):
            wishlist_item = WishlistItemsFactory(wishlist_id=wishlist.id)
            wishlist_item.position = (
                WishlistItems.find_last_position(wishlist.id) + 1000
            )
            wishlist_item.create()
            wishlist_items.append(wishlist_item)

        # move the last item to the front
        data = {"before_position": 0}

        resp = self.client.patch(
            f"{BASE_URL}/{wishlist.id}/items/{wishlist_items[-1].product_id}",
            json=data,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(wishlist_items[-1].position, 500)

        data = {"position": 0}
        resp = self.client.patch(
            f"{BASE_URL}/{wishlist.id}/items/{wishlist_items[0].product_id}",
            json=data,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(wishlist_items[0].position, 250)

    def test_move_wishlist_item_not_found(self):
        """It should return 400 when moving an item on a non-existent wishlist"""
        data = {"before_position": 0}
        resp = self.client.patch(
            f"{BASE_URL}/9999/items/1",
            json=data,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_move_wishlist_item_invalid_data(self):
        """It should return 400 when moving an item with invalid data"""
        wishlist = WishlistsFactory()
        wishlist.create()
        wishlist_item = WishlistItemsFactory(wishlist_id=wishlist.id)
        wishlist_item.position = WishlistItems.find_last_position(wishlist.id) + 1000
        wishlist_item.create()

        data = {"before_position": "not-an-integer"}
        resp = self.client.patch(
            f"{BASE_URL}/{wishlist.id}/items/{wishlist_item.product_id}",
            json=data,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
