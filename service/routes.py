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
            "Content-Type must be application/json",
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


######################################################################
# UPDATE WISHLISTS
######################################################################
@app.route("/wishlists/<int:wishlist_id>", methods=["PUT"])
def update_wishlist(wishlist_id):
    app.logger.info("Request to update wishlist with id: %s", wishlist_id)

    wishlist = Wishlists.find_by_id(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    if wishlist.customer_id != STATE_CUSTOMER_ID:
        abort(
            status.HTTP_403_FORBIDDEN,
            f"You do not have permission to update this wishlist.",
        )

    data = request.get_json()
    try:
        wishlist.deserialize(data)
        wishlist.update()
    except DataValidationError as error:
        abort(status.HTTP_400_BAD_REQUEST, str(error))

    return jsonify(wishlist.serialize()), status.HTTP_200_OK


######################################################################
# RETRIEVE A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>", methods=["GET"])
def get_wishlist(wishlist_id):
    """
    Retrieve a single Wishlist

    This endpoint will return an Wishlist based on it's id
    """
    app.logger.info("Request for Wishlist with id: %s", wishlist_id)

    # See if the wishlist exists and abort if it doesn't
    wishlist = Wishlists.find(wishlist_id)
    if not wishlist:
        app.logger.warning("Wishlist with id [%s] was not found.", wishlist_id)
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    return jsonify(wishlist.serialize()), status.HTTP_200_OK


######################################################################
# DELETE A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>", methods=["DELETE"])
def delete_wishlist(wishlist_id):
    """
    Delete a Wishlist

    This endpoint will delete a Wishlist based the id specified in the path
    """
    app.logger.info("Request to delete wishlist with id: %s", wishlist_id)

    # Retrieve the wishlist to delete and delete it if it exists
    wishlist = Wishlists.find(wishlist_id)
    if wishlist:
        app.logger.info("Deleting wishlist with id: %s", wishlist_id)
        wishlist.delete()
        app.logger.info("Wishlist with id: %s deleted", wishlist_id)

    return "", status.HTTP_204_NO_CONTENT


# ---------------------------------------------------------------------
#                I T E M S   M E T H O D S
# ---------------------------------------------------------------------


######################################################################
# READ A WISHLIST ITEM
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items/<int:product_id>", methods=["GET"])
def get_wishlist_item(wishlist_id, product_id):
    """
    Get a Wishlist Item
    This endpoint returns just a wishlist item
    """
    app.logger.info(
        "Request to retrieve a Wishlist Item with id: %s from Wishlist with id: %s",
        product_id,
        wishlist_id,
    )

    # First check if the wishlist exists and abort if it doesn't
    wishlist = Wishlists.find(wishlist_id)
    if not wishlist:
        app.logger.warning("Wishlist with id [%s] was not found", wishlist_id)
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' not found",
        )

    # See if the wishlist item exists and abort if it doesn't
    wishlist_item = WishlistItems.find_by_wishlist_and_product(wishlist_id, product_id)
    if not wishlist_item:
        app.logger.warning(
            "Wishlist Item with id [%s] was not found in Wishlist with id [%s]",
            product_id,
            wishlist_id,
        )
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist Item with id '{product_id}' not found in Wishlist with id '{wishlist_id}'",
        )
    return jsonify(wishlist_item.serialize()), status.HTTP_200_OK


######################################################################
# ADD AN ITEM TO A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items", methods=["POST"])
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
        "get_wishlist_item",
        wishlist_id=wishlist.id,
        product_id=wishlist_item.product_id,
        _external=True,
    )
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# DELETE A WISHLIST ITEM
######################################################################
@app.route(
    "/wishlists/<int:wishlist_id>/items/<int:product_id>",
    methods=["DELETE"],
)
def delete_wishlist_items(wishlist_id, product_id):
    """
    Delete a wishlist item

    This endpoint will delete a wishlist item based the id specified in the path
    """
    app.logger.info(
        "Request to delete wishlist item %s for wishlist id: %s",
        (product_id, wishlist_id),
    )

    # See if the wishlist item exists and delete it if it does
    wishlist_item = WishlistItems.find_by_wishlist_and_product(wishlist_id, product_id)

    if wishlist_item:
        wishlist_item.delete()

    return "", status.HTTP_204_NO_CONTENT


######################################################################
# UPDATE A WISHLIST ITEM
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items/<int:product_id>", methods=["PUT"])
def update_wishlist_items(wishlist_id, product_id):
    """
    Update a wishlist item

    This endpoint will update a wishlist item based the body that is posted
    """
    app.logger.info(
        "Request to update wishlist item %s for wishlist id: %s",
        (product_id, wishlist_id),
    )
    check_content_type("application/json")

    # See if the wishlist exists and abort if it doesn't
    wishlist = Wishlists.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    # See if the wishlist_item exists and abort if it doesn't
    wishlist_item = WishlistItems.find_by_wishlist_and_product(wishlist_id, product_id)
    if not wishlist_item:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist item with id '{product_id}' could not be found.",
        )

    # Update from the json in the body of the request
    try:
        wishlist_item.deserialize(request.get_json())
        wishlist_item.wishlist_id = wishlist_id
        wishlist_item.product_id = product_id
    except DataValidationError as error:
        abort(status.HTTP_400_BAD_REQUEST, str(error))

    wishlist.update()

    return jsonify(wishlist_item.serialize()), status.HTTP_200_OK


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
