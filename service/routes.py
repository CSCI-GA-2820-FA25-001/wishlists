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
# CREATE A NEW WISHLIST
######################################################################
@app.route("/wishlists", methods=["POST"])
def create_wishlists():
    """
    Creates a Wishlist
    This endpoint will create a Wishlist based the data in the body that is posted
    """
    app.logger.info("Request to create a Wishlist")
    if not request.is_json:
        app.logger.error(
            "Invalid Content-Type: %s", request.headers.get("Content-Type")
        )
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be application/json",
        )

    # Create the wishlist
    wishlist = Wishlists()
    wishlist.deserialize(request.get_json())
    # TODO: Validate customer_id once authentication is implemented
    wishlist.create()

    # Create a message to return
    message = wishlist.serialize()

    # **TODO** Uncomment once get_wishlists is implemented
    # location_url = url_for("get_wishlists", wishlist_id=wishlist.id, _external=True)
    location_url = None

    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


# ---------------------------------------------------------------------
#                I T E M S   M E T H O D S
# ---------------------------------------------------------------------


######################################################################
# ADD AN ITEM TO A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>/wishlist_items", methods=["POST"])
def create_wishlist_items(wishlist_id):
    """
    Create a wishlist item on a wishlist

    This endpoint will add a wishlist item to a wishlist
    """
    app.logger.info(
        "Request to create a wishlist item for wishlist with id: %s", wishlist_id
    )
    check_content_type("application/json")

    # See if the wishlist exists and abort if it doesn't
    wishlist = Wishlists.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' could not be found.",
        )

    # Create an wishlist_item from the json data
    wishlist_item = WishlistItems()
    wishlist_item.deserialize(request.get_json())

    # Append the wishlist_item to the wishlist
    wishlist.wishlist_items.append(wishlist_item)
    wishlist.update()

    # Prepare a message to return
    message = wishlist_item.serialize()

    # Send the location to GET the new item
    location_url = url_for(
        # TODO delete this code and uncomment "get_wishlist_items"
        "index",
        # "get_wishlist_items",
        wishlist_id=wishlist.id,
        wishlist_item_id=wishlist_item.product_id,
        _external=True,
    )
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(content_type):
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
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Content-Type must be {content_type}"
    )
