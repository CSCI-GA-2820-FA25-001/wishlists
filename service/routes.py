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
from flask import jsonify, request, url_for, abort, render_template
from flask import current_app as app  # Import Flask application
from service.models import Wishlists, WishlistItems
from service.common import status
from service.models.persistent_base import DataValidationError

# It should be based on the authenticated user
# For now, a hardcoded value is used
STATE_CUSTOMER_ID = 1


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    app.logger.info("Request for service metadata")
    return (
        jsonify(
            {
                "name": "wishlists-service",
                "version": "0.1.0",
                "endpoints": [
                    "/wishlists",
                    "/wishlists/{id}",
                    "/wishlists/{id}/items",
                    "/wishlists/{id}/items/{item_id}",
                    "/ui/update",
                ],
                "docs": "See README for examples",
            }
        ),
        status.HTTP_200_OK,
    )


######################################################################
# GET HEALTH CHECK
######################################################################
@app.route("/health")
def health():
    """Health Check"""
    app.logger.info("Request for health check")
    return jsonify({"status": "OK"}), status.HTTP_200_OK


######################################################################
# UI - UPDATE RESOURCE PAGE
######################################################################
@app.route("/ui/update", methods=["GET"])
def update_resource_ui():
    """Serve the Update Resource UI page"""
    app.logger.info("Request for Update Resource UI page")
    return render_template("update_resource.html")


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
# LIST ALL WISHLISTS
######################################################################
@app.route("/wishlists", methods=["GET"])
def list_wishlists():
    """
    List all Wishlists
    This endpoint will return all Wishlists
    """
    app.logger.info("Request to list all Wishlists")

    # Check for query parameter to filter by customer_id
    customer_id = request.args.get("customer_id")

    name_query = request.args.get("name")

    category_query = request.args.get("category")

    if name_query is not None and customer_id is not None:
        app.logger.info(
            "Filtering wishlists for customer_id: %s by name containing: %s",
            customer_id,
            name_query,
        )
        wishlists = Wishlists.find_all_by_customer_id_and_name_like(
            int(customer_id), name_query
        )
    elif customer_id is not None:
        app.logger.info("Returning all Wishlists for customer_id: %s", customer_id)
        wishlists = Wishlists.find_all_by_customer_id(int(customer_id))
    elif category_query is not None:
        app.logger.info(
            "Filtering wishlists for current user (customer_id: %s) by category: %s",
            STATE_CUSTOMER_ID,
            category_query,
        )
        wishlists = Wishlists.find_by_category(STATE_CUSTOMER_ID, category_query)
    else:
        app.logger.info("Returning all Wishlists")
        wishlists = Wishlists.all()

    results = [wishlist.serialize() for wishlist in wishlists]
    app.logger.info("Returning %d wishlists", len(results))

    return jsonify(results), status.HTTP_200_OK


######################################################################
# CREATE A NEW WISHLIST
######################################################################
@app.route("/wishlists", methods=["POST"])
def create_wishlist():
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
    # NOTE: Validate customer_id once authentication is implemented
    wishlist.create()

    # Create a message to return
    message = wishlist.serialize()

    location_url = url_for("get_wishlist", wishlist_id=wishlist.id, _external=True)

    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# UPDATE WISHLISTS
######################################################################
@app.route("/wishlists/<int:wishlist_id>", methods=["PUT"])
def update_wishlist(wishlist_id):
    """
    Updates a Wishlist
    This endpoint will update a Wishlist based the data in the body that is posted
    """
    app.logger.info("Request to update wishlist with id: %s", wishlist_id)

    wishlist = Wishlists.find_by_id(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Wishlist with id '{wishlist_id}' was not found.",
        )

    if wishlist.customer_id != STATE_CUSTOMER_ID:
        abort(
            status.HTTP_403_FORBIDDEN,
            description="You do not have permission to update this wishlist.",
        )

    data = request.get_json()
    if "id" in data and data["id"] != wishlist_id:
        abort(
            status.HTTP_400_BAD_REQUEST,
            description=f"ID in the body {data['id']} does not match the path ID {wishlist_id}.",
        )
    data["customer_id"] = wishlist.customer_id

    try:
        wishlist.deserialize(data)
        wishlist.update()
    except DataValidationError as error:
        abort(status.HTTP_400_BAD_REQUEST, description=str(error))

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
# LIST ALL ITEMS IN A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items", methods=["GET"])
def list_wishlist_items(wishlist_id):
    """
    List all Wishlist Items for a Wishlist
    This endpoint will return all Wishlist Items for a Wishlist
    """
    app.logger.info("Request to list all Wishlist Items for Wishlist %s", wishlist_id)

    # See if the wishlist exists and abort if it doesn't
    wishlist = Wishlists.find(wishlist_id)
    if not wishlist:
        app.logger.warning("Wishlist with id [%s] was not found", wishlist_id)
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' could not be found.",
        )

    # Get all items from the wishlist
    results = [item.serialize() for item in wishlist.wishlist_items]
    app.logger.info("Returning %d items", len(results))

    return jsonify(results), status.HTTP_200_OK


######################################################################
# ADD AN ITEM TO A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items", methods=["POST"])
def create_wishlist_item(wishlist_id):
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
    try:
        wishlist_item.deserialize(request.get_json())

        # Check if the product is already in the wishlist
        existing_items = WishlistItems.find_by_wishlist_and_product(
            wishlist_id, wishlist_item.product_id
        )
        if existing_items:
            abort(
                status.HTTP_409_CONFLICT,
                f"Product with id '{wishlist_item.product_id}' is already in the wishlist.",
            )
        last_position = WishlistItems.find_last_position(wishlist_id)

        wishlist_item.wishlist_id = wishlist_id
        wishlist_item.position = last_position + 1000

    except DataValidationError as error:
        abort(status.HTTP_400_BAD_REQUEST, str(error))

    wishlist_item.create()

    # Update the wishlist's updated_date
    wishlist.updated_date = date.fromisoformat(date.today().isoformat())
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
        data = request.get_json()
        data.pop("position", None)  # Position should not be updated via this method
        wishlist_item.deserialize(data)
        wishlist_item.wishlist_id = wishlist_id
        wishlist_item.product_id = product_id
    except DataValidationError as error:
        abort(status.HTTP_400_BAD_REQUEST, str(error))

    wishlist.update()

    return jsonify(wishlist_item.serialize()), status.HTTP_200_OK


######################################################################
# DELETE A WISHLIST ITEM
######################################################################
@app.route(
    "/wishlists/<int:wishlist_id>/items/<int:product_id>",
    methods=["DELETE"],
)
def delete_wishlist_item(wishlist_id, product_id):
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
# Move a wishlist item
######################################################################
@app.route(
    "/wishlists/<int:wishlist_id>/items/<int:product_id>",
    methods=["PATCH"],
)
def move_wishlist_item(wishlist_id, product_id):
    """
    Move a wishlist item to a new position

    This endpoint will move a wishlist item to a new position in the wishlist
    """
    app.logger.info(
        "Request to move wishlist item %s for wishlist id: %s",
        (product_id, wishlist_id),
    )
    check_content_type("application/json")

    data = request.get_json()
    before_position = data.get("before_position")
    if before_position is None:
        before_position = data.get("position")
    if before_position is None or not isinstance(before_position, int):
        abort(
            status.HTTP_400_BAD_REQUEST,
            "before_position must be provided and must be an integer",
        )

    try:
        item = Wishlists.move_item(wishlist_id, product_id, before_position)
    except DataValidationError as error:
        abort(status.HTTP_400_BAD_REQUEST, str(error))

    return jsonify(item.serialize()), status.HTTP_204_NO_CONTENT


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
