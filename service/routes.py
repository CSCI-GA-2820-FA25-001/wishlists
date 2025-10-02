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
Wishlists Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Wishlists
"""

from datetime import date
from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from service.models import Wishlists, WishlistItems
from service.common import status
from service.models.persistent_base import DataValidationError  # HTTP Status Codes

# It should be based on the authenticated user
# For now, a hardcoded value is used
STATE_CUSTOMER_ID = 1


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        "Reminder: return some useful information in json format about the service here",
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


@app.route("/wishlists", methods=["GET"])
def get_wishlists():
    """Returns all of the Wishlists"""
    app.logger.info("Request for wishlists for customer %s", STATE_CUSTOMER_ID)
    wishlists = Wishlists.find_all_by_customer_id(STATE_CUSTOMER_ID)
    results = [wishlist.serialize() for wishlist in wishlists]
    return jsonify(results), status.HTTP_200_OK


@app.route("/wishlists", methods=["POST"])
def create_wishlist():
    """Creates a Wishlist"""
    app.logger.info("Request to create a wishlist for customer %s", STATE_CUSTOMER_ID)
    if not request.is_json:
        abort(status.HTTP_400_BAD_REQUEST, "Request body must be JSON")
    data = request.get_json()
    wishlist = Wishlists()
    try:
        wishlist.deserialize(data)
    except DataValidationError as e:
        abort(status.HTTP_400_BAD_REQUEST, str(e))
    wishlist.customer_id = STATE_CUSTOMER_ID
    wishlist.create()
    message = wishlist.serialize()
    location_url = url_for("get_wishlist", wishlist_id=wishlist.id, _external=True)
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


@app.route("/wishlists/<int:wishlist_id>", methods=["GET"])
def get_wishlist(wishlist_id):
    """Returns a Wishlist"""
    app.logger.info(
        "Request for wishlist %s for customer %s", wishlist_id, STATE_CUSTOMER_ID
    )
    wishlist = Wishlists.find_by_id(wishlist_id)
    if not wishlist:
        abort(status.HTTP_404_NOT_FOUND, f"Wishlist with id {wishlist_id} not found")
    if wishlist.customer_id != STATE_CUSTOMER_ID:
        abort(
            status.HTTP_403_FORBIDDEN,
            f"Access to wishlist id {wishlist_id} is forbidden",
        )
    return jsonify(wishlist.serialize()), status.HTTP_200_OK


@app.route("/wishlists/<int:wishlist_id>", methods=["PUT"])
def update_wishlist(wishlist_id):
    """Updates a Wishlist"""
    app.logger.info(
        "Request to update wishlist %s for customer %s", wishlist_id, STATE_CUSTOMER_ID
    )
    if not request.is_json:
        abort(status.HTTP_400_BAD_REQUEST, "Request body must be JSON")
    wishlist = Wishlists.find_by_id(wishlist_id)
    if not wishlist:
        abort(status.HTTP_404_NOT_FOUND, f"Wishlist with id {wishlist_id} not found")
    if wishlist.customer_id != STATE_CUSTOMER_ID:
        abort(
            status.HTTP_403_FORBIDDEN,
            f"Access to wishlist id {wishlist_id} is forbidden",
        )
    data = request.get_json()
    try:
        wishlist.deserialize(data)
        wishlist.id = wishlist_id
        wishlist.customer_id = STATE_CUSTOMER_ID
        wishlist.updated_date = date.fromisoformat(date.today().isoformat())
    except DataValidationError as e:
        abort(status.HTTP_400_BAD_REQUEST, str(e))
    wishlist.update()
    return jsonify(wishlist.serialize()), status.HTTP_200_OK


@app.route("/wishlists/<int:wishlist_id>/items", methods=["POST"])
def add_wishlist_item(wishlist_id):
    """Adds an item to a Wishlist"""
    app.logger.info(
        "Request to add item to wishlist %s for customer %s",
        wishlist_id,
        STATE_CUSTOMER_ID,
    )
    if not request.is_json:
        abort(status.HTTP_400_BAD_REQUEST, "Request body must be JSON")
    wishlist = Wishlists.find_by_id(wishlist_id)
    if not wishlist:
        abort(status.HTTP_404_NOT_FOUND, f"Wishlist with id {wishlist_id} not found")
    if wishlist.customer_id != STATE_CUSTOMER_ID:
        abort(
            status.HTTP_403_FORBIDDEN,
            f"Access to wishlist id {wishlist_id} is forbidden",
        )
    data = request.get_json()
    product_id = data.get("product_id")
    if not product_id:
        abort(status.HTTP_400_BAD_REQUEST, "Product ID is required")
    # Determine the next position
    last_position = WishlistItems.find_last_position(wishlist_id)
    item = WishlistItems()
    try:
        item.deserialize(data)
        item.wishlist_id = wishlist_id
        item.position = last_position + 1000

        # Check if the product is already in the wishlist
        existing_items = WishlistItems.find_by_wishlist_and_product(
            wishlist_id, item.product_id
        )
        if existing_items:
            abort(
                status.HTTP_409_CONFLICT,
                f"Product ID {product_id} is already in wishlist id {wishlist_id}",
            )
    except DataValidationError as e:
        abort(status.HTTP_400_BAD_REQUEST, str(e))
    item.create()

    # Update the wishlist's updated_date
    wishlist.updated_date = date.fromisoformat(date.today().isoformat())
    wishlist.update()

    # location is /wishlists/{wishlist_id}/items/{product_id}
    location_url = url_for(
        "get_wishlist_item",
        wishlist_id=wishlist_id,
        product_id=product_id,
        _external=True,
    )
    return (
        jsonify(item.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


@app.route("/wishlists/<int:wishlist_id>/items/<int:product_id>", methods=["GET"])
def get_wishlist_item(wishlist_id, product_id):
    """Returns a Wishlist Item"""
    app.logger.info(
        "Request for item %s in wishlist %s for customer %s",
        product_id,
        wishlist_id,
        STATE_CUSTOMER_ID,
    )
    wishlist = Wishlists.find_by_id(wishlist_id)
    if not wishlist:
        abort(status.HTTP_404_NOT_FOUND, f"Wishlist with id {wishlist_id} not found")
    if wishlist.customer_id != STATE_CUSTOMER_ID:
        abort(
            status.HTTP_403_FORBIDDEN,
            f"Access to wishlist id {wishlist_id} is forbidden",
        )
    item = WishlistItems.find_by_wishlist_and_product(wishlist_id, product_id)
    if not item:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Product ID {product_id} not found in wishlist id {wishlist_id}",
        )
    return jsonify(item.serialize()), status.HTTP_200_OK
