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


######################################################################
# CREATE A NEW WISHLIST ITEM
######################################################################
@app.route("/wishlist_items", methods=["POST"])
def create_wishlist_items():
    """
    Create a Wishlist item
    This endpoint will create a Wishlist item based the data in the body that is posted
    """
    app.logger.info("Request to Create a Wishlist item...")
    check_content_type("application/json")

    wishlist_item = WishlistItems()
    # Get the data from the request and deserialize it
    data = request.get_json()
    app.logger.info("Processing: %s", data)
    wishlist_item.deserialize(data)

    # Save the new WishlistItems to the database
    wishlist_item.create()
    app.logger.info("Wishlist item with new id [%s] saved!", wishlist_item.product_id)

    # Todo: uncomment this code when get_wishlist_items is implemented
    # Return the location of the new WishlistItems
    # location_url = url_for(
    #     "get_wishlist_items", wishlist_item_id=wishlist_item.product_id, _external=True
    # )
    location_url = "unknown"

    return (
        jsonify(wishlist_item.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


######################################################################
# Checks the ContentType of a request
######################################################################
def check_content_type(content_type) -> None:
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )
