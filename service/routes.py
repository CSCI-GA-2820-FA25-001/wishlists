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
Wishlists Service with Swagger

Paths:
------
GET / - Displays the UI
GET /api/wishlists - Returns a list all of the Wishlists
GET /api/wishlists/{id} - Returns the Wishlist with a given id number
POST /api/wishlists - Creates a new Wishlist
PUT /api/wishlists/{id} - Updates a Wishlist
DELETE /api/wishlists/{id} - Deletes a Wishlist

GET /api/wishlists/{id}/items - Returns all items in a Wishlist
GET /api/wishlists/{id}/items/{product_id} - Returns a specific item
POST /api/wishlists/{id}/items - Adds a new item to a Wishlist
PUT /api/wishlists/{id}/items/{product_id} - Updates an item
DELETE /api/wishlists/{id}/items/{product_id} - Deletes an item
PATCH /api/wishlists/{id}/items/{product_id} - Moves an item
"""

# from datetime import date
from flask import jsonify, request
from flask import current_app as app  # Import Flask application
from flask_restx import Api, Resource, fields, reqparse
from service.models import Wishlists, WishlistItems
from service.common import status
from service.common.error_handlers import bad_request
from service.models.persistent_base import DataValidationError

# It should be based on the authenticated user
# For now, a hardcoded value is used
STATE_CUSTOMER_ID = 1001


######################################################################
# Configure Swagger before initializing it
######################################################################
api = Api(
    app,
    version="1.0.0",
    title="Wishlists REST API Service",
    description="This is a REST API service for managing wishlists",
    default="wishlists",
    default_label="Wishlists operations",
    doc="/apidocs",  # default also could use doc='/apidocs/'
    prefix="/api",
)


######################################################################
# CONFIGURE ERROR HANDLING
######################################################################
@api.errorhandler(DataValidationError)
def request_validation_error(error):
    """Handles Value Errors from bad data"""
    return bad_request(error)


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
# GET HEALTH CHECK
######################################################################
@app.route("/health")
def health():
    """Health Check"""
    app.logger.info("Request for health check")
    return jsonify({"status": "OK"}), status.HTTP_200_OK


# Define the model so that the docs reflect what can be sent
wishlist_create_model = api.model(
    "Wishlist",
    {
        "name": fields.String(required=True, description="The name of the Wishlist"),
        "customer_id": fields.Integer(required=True, description="Customer identifier"),
        "category": fields.String(required=False, description="Wishlist category"),
        "description": fields.String(
            required=False, description="Description of the Wishlist"
        ),
        "created_date": fields.Date(required=False, description="Creation date"),
    },
)

wishlist_model = api.inherit(
    "WishlistModel",
    wishlist_create_model,
    {
        "id": fields.Integer(
            readOnly=True,
            description="The unique id assigned internally by the service",
        ),
        "updated_date": fields.String(
            readOnly=True, description="Last updated date (ISO format)"
        ),
    },
)

wishlist_item_create_model = api.model(
    "WishlistItem",
    {
        "product_id": fields.Integer(required=True, description="Product ID"),
        "description": fields.String(required=False, description="Item description"),
    },
)

wishlist_item_model = api.inherit(
    "WishlistItemModel",
    wishlist_item_create_model,
    {
        "wishlist_id": fields.Integer(
            readOnly=True, description="The ID of the wishlist this item belongs to"
        ),
        "position": fields.Integer(
            readOnly=True, description="Position of the item within the wishlist"
        ),
    },
)

# query string arguments
wishlist_args = reqparse.RequestParser()

wishlist_args.add_argument(
    "customer_id",
    type=int,
    location="args",
    required=False,
    help="List Wishlists by customer_id",
)

wishlist_args.add_argument(
    "name",
    type=str,
    location="args",
    required=False,
    help="List Wishlists by name",
)

wishlist_args.add_argument(
    "category",
    type=str,
    location="args",
    required=False,
    help="List Wishlists by category",
)


######################################################################
#  PATH: /wishlists/{id}
######################################################################
@api.route("/wishlists/<int:wishlist_id>")
@api.param("wishlist_id", "The Wishlist identifier")
class WishlistResource(Resource):
    """
    WishlistResource class

    Allows the manipulation of a single Wishlist
    GET /wishlists/{id} - Returns a Wishlist with the id
    PUT /wishlists/{id} - Update a Wishlist with the id
    DELETE /wishlists/{id} -  Deletes a Wishlist with the id
    """

    # ------------------------------------------------------------------
    # RETRIEVE A WISHLIST
    # ------------------------------------------------------------------
    @api.doc("get_wishlist")
    @api.response(404, "Wishlist not found")
    @api.marshal_with(wishlist_model)
    def get(self, wishlist_id):
        """
        Retrieve a single Wishlist

        This endpoint will return a Wishlist based on its id.
        """
        app.logger.info("Request for Wishlist with id: %s", wishlist_id)
        wishlist = Wishlists.find(wishlist_id)
        if not wishlist:
            app.logger.warning("Wishlist with id [%s] was not found.", wishlist_id)
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Wishlist with id '{wishlist_id}' was not found.",
            )

        return wishlist.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # Update AN EXISTING WISHLIST
    # ------------------------------------------------------------------
    @api.doc("update_wishlist")
    @api.response(404, "Wishlist not found")
    @api.response(400, "The posted Wishlist data was not valid")
    @api.expect(wishlist_create_model)
    @api.marshal_with(wishlist_model)
    def put(self, wishlist_id):
        """
        Update a Wishlist

        This endpoint will update a Wishlist based on the body that is posted.
        """
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
                "You do not have permission to update this wishlist.",
            )

        data = api.payload
        if "id" in data and data["id"] != wishlist_id:
            abort(
                status.HTTP_400_BAD_REQUEST,
                f"ID in the body {data['id']} does not match the path ID {wishlist_id}.",
            )
        data["customer_id"] = wishlist.customer_id

        try:
            wishlist.deserialize(data)
            wishlist.update()
        except DataValidationError as error:
            abort(status.HTTP_400_BAD_REQUEST, str(error))

        return wishlist.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # Delete A WISHLIST
    # ------------------------------------------------------------------
    @api.doc("delete_wishlist")
    @api.response(204, "Wishlist deleted")
    def delete(self, wishlist_id):
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


######################################################################
#  PATH: /wishlists
######################################################################
@api.route("/wishlists", strict_slashes=False)
class WishlistCollection(Resource):
    """Handles all interactions with collections of Wishlists"""

    # ------------------------------------------------------------------
    # LIST ALL WISHLISTS
    # ------------------------------------------------------------------
    @api.doc("list_wishlists")
    @api.expect(wishlist_args, validate=True)
    @api.marshal_list_with(wishlist_model)
    def get(self):
        """Returns all of the Wishlists"""
        app.logger.info("Request to list all Wishlists")

        # Parse query parameters
        args = wishlist_args.parse_args()
        customer_id = args.get("customer_id")
        name_query = args.get("name")
        category_query = args.get("category")

        if (
            customer_id is not None
            and category_query is not None
            and name_query is not None
        ):
            app.logger.info(
                "Filter by customer_id=%s, category=%s, name like=%s",
                customer_id,
                category_query,
                name_query,
            )
            wishlists = Wishlists.find_by_customer_category_name_like(
                customer_id, category_query, name_query
            )

        elif customer_id is not None and category_query is not None:
            app.logger.info(
                "Filter by customer_id=%s AND category=%s", customer_id, category_query
            )
            wishlists = Wishlists.find_by_customer_and_category(
                customer_id, category_query
            )

        elif customer_id is not None and name_query is not None:
            app.logger.info(
                "Filter by customer_id=%s AND name like=%s", customer_id, name_query
            )
            wishlists = Wishlists.find_all_by_customer_id_and_name_like(
                customer_id, name_query
            )

        elif customer_id is not None:
            app.logger.info("Filter by customer_id=%s", customer_id)
            wishlists = Wishlists.find_all_by_customer_id(customer_id)
        elif name_query is not None:
            wishlists = Wishlists.find_by_name_like(name_query)
        elif category_query is not None:
            app.logger.info(
                "Filter by category=%s (global, no customer_id)", category_query
            )
            wishlists = Wishlists.find_by_category(category_query)
        else:
            app.logger.info("Returning all Wishlists")
            wishlists = Wishlists.all()

        results = [wishlist.serialize() for wishlist in wishlists]
        app.logger.info("Returning %d wishlists", len(results))

        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # ADD A NEW WISHLIST
    # ------------------------------------------------------------------
    @api.doc("create_wishlist")
    @api.response(400, "The posted data was not valid")
    @api.expect(wishlist_create_model)
    @api.marshal_with(wishlist_model, code=201)
    def post(self):
        """
        Creates a Wishlist
        This endpoint will create a Wishlist based the data in the body that is posted
        """
        app.logger.info("Request to create a Wishlist")
        # Create the wishlist
        wishlist = Wishlists()
        wishlist.deserialize(api.payload)
        # NOTE: Validate customer_id once authentication is implemented
        wishlist.create()

        # Create a message to return
        message = wishlist.serialize()

        location_url = api.url_for(
            WishlistResource, wishlist_id=wishlist.id, _external=True
        )

        return message, status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
#  PATH: /wishlists/{wishlist_id}/items/{product_id}
######################################################################
@api.route("/wishlists/<int:wishlist_id>/items/<int:product_id>")
@api.param("wishlist_id", "The Wishlist identifier")
@api.param("product_id", "The Product identifier")
class WishlistItemResource(Resource):
    """
    WishlistItemResource class

    Allows the manipulation of a single Wishlist Item
    GET /wishlists/{wishlist_id}/items/{product_id} - Returns a Wishlist Item
    PUT /wishlists/{wishlist_id}/items/{product_id} - Updates a Wishlist Item
    DELETE /wishlists/{wishlist_id}/items/{product_id} - Deletes a Wishlist Item
    PATCH /wishlists/{wishlist_id}/items/{product_id} - Moves a Wishlist Item to a new position
    """

    # ------------------------------------------------------------------
    # RETRIEVE A WISHLIST ITEM
    # ------------------------------------------------------------------
    @api.doc("get_wishlist_item")
    @api.response(404, "Wishlist or Wishlist Item not found")
    @api.marshal_with(wishlist_item_model)
    def get(self, wishlist_id, product_id):
        """
        Retrieve a single Wishlist Item

        This endpoint will return a Wishlist Item based on its id
        """
        app.logger.info(
            "Request to retrieve a Wishlist Item with id: %s from Wishlist with id: %s",
            product_id,
            wishlist_id,
        )

        wishlist = Wishlists.find(wishlist_id)
        if not wishlist:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Wishlist with id '{wishlist_id}' not found",
            )

        wishlist_item = WishlistItems.find_by_wishlist_and_product(
            wishlist_id, product_id
        )
        if not wishlist_item:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Wishlist Item with id '{product_id}' not found in Wishlist with id '{wishlist_id}'",
            )

        return wishlist_item.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # Update A WISHLIST ITEM
    # ------------------------------------------------------------------
    @api.doc("update_wishlist_item")
    @api.response(404, "Wishlist or Wishlist Item not found")
    @api.response(400, "Invalid request body")
    @api.expect(wishlist_item_create_model)
    @api.marshal_with(wishlist_item_model)
    def put(self, wishlist_id, product_id):
        """
        Update a Wishlist Item

        This endpoint will update a Wishlist Item based the body that is posted
        """
        app.logger.info(
            "Request to update Wishlist Item with id: %s for Wishlist with id: %s",
            product_id,
            wishlist_id,
        )

        wishlist = Wishlists.find(wishlist_id)
        if not wishlist:
            abort(
                status.HTTP_404_NOT_FOUND, f"Wishlist with id '{wishlist_id}' not found"
            )

        wishlist_item = WishlistItems.find_by_wishlist_and_product(
            wishlist_id, product_id
        )
        if not wishlist_item:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Wishlist Item with id '{product_id}' not found in Wishlist with id '{wishlist_id}'",
            )

        data = api.payload
        data.pop("position", None)  # position cannot be updated via PUT
        wishlist_item.deserialize(data)
        wishlist_item.wishlist_id = wishlist_id
        wishlist_item.product_id = product_id
        wishlist_item.update()

        return wishlist_item.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # Delete A WISHLIST ITEM
    # ------------------------------------------------------------------
    @api.doc("delete_wishlist_item")
    @api.response(204, "Wishlist Item deleted")
    def delete(self, wishlist_id, product_id):
        """
        Delete a Wishlist Item

        This endpoint will delete a Wishlist Item based the id specified in the path
        """
        app.logger.info(
            "Request to delete Wishlist Item with id: %s for Wishlist with id: %s",
            product_id,
            wishlist_id,
        )

        wishlist = Wishlists.find(wishlist_id)
        if not wishlist:
            abort(
                status.HTTP_404_NOT_FOUND, f"Wishlist with id '{wishlist_id}' not found"
            )

        wishlist_item = WishlistItems.find_by_wishlist_and_product(
            wishlist_id, product_id
        )
        if not wishlist_item:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Wishlist Item with id '{product_id}' not found in Wishlist with id '{wishlist_id}'",
            )

        wishlist_item.delete()

        return "", status.HTTP_204_NO_CONTENT

    # ------------------------------------------------------------------
    # MOVE A WISHLIST ITEM
    # ------------------------------------------------------------------
    @api.doc("move_wishlist_item")
    @api.response(400, "Invalid request body")
    @api.response(404, "Wishlist or Wishlist Item not found")
    def patch(self, wishlist_id, product_id):
        """
        Move a Wishlist Item

        This endpoint will Move a Wishlist Item based the id specified in the path
        """
        app.logger.info(
            "Request to move Wishlist Item with id: %s for Wishlist with id: %s",
            product_id,
            wishlist_id,
        )

        wishlist = Wishlists.find(wishlist_id)
        if not wishlist:
            abort(
                status.HTTP_400_BAD_REQUEST,
                f"Wishlist with id '{wishlist_id}' not found",
            )

        wishlist_item = WishlistItems.find_by_wishlist_and_product(
            wishlist_id, product_id
        )
        if not wishlist_item:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Wishlist Item with id '{product_id}' not found in Wishlist with id '{wishlist_id}'",
            )

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
            moved_item = Wishlists.move_item(wishlist_id, product_id, before_position)
        except DataValidationError as error:
            abort(status.HTTP_400_BAD_REQUEST, str(error))

        return moved_item.serialize(), status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /wishlists/{wishlist_id}/items
######################################################################
@api.route("/wishlists/<int:wishlist_id>/items", strict_slashes=False)
@api.param("wishlist_id", "The Wishlist identifier")
class WishlistItemCollection(Resource):
    """Handles all interactions with collections of Wishlist Items"""

    # ------------------------------------------------------------------
    # LIST ALL ITEMS IN A WISHLIST
    # ------------------------------------------------------------------
    @api.doc("list_wishlist_items")
    @api.response(404, "Wishlist or Wishlist Item not found")
    @api.marshal_list_with(wishlist_item_model)
    def get(self, wishlist_id):
        """Returns all of the Wishlist Items"""
        app.logger.info(
            "Request to list all Wishlist Items for Wishlist with id: %s", wishlist_id
        )

        wishlist = Wishlists.find(wishlist_id)
        if not wishlist:
            abort(
                status.HTTP_404_NOT_FOUND, f"Wishlist with id '{wishlist_id}' not found"
            )

        items = wishlist.wishlist_items
        results = [item.serialize() for item in items]

        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # ADD A NEW WISHLIST ITEM
    # ------------------------------------------------------------------
    @api.doc("create_wishlist_item")
    @api.response(400, "Invalid request body")
    @api.response(404, "Wishlist or Wishlist Item not found")
    @api.response(409, "Product already exists in wishlist")
    @api.expect(wishlist_item_create_model)
    @api.marshal_with(wishlist_item_model, code=201)
    def post(self, wishlist_id):
        """
        Create a Wishlist Item

        This endpoint will create a Wishlist item based the data in the body that is posted
        """
        app.logger.info(
            "Request to create Wishlist Item for Wishlist with id: %s",
            wishlist_id,
        )

        wishlist = Wishlists.find(wishlist_id)
        if not wishlist:
            abort(
                status.HTTP_404_NOT_FOUND, f"Wishlist with id '{wishlist_id}' not found"
            )

        data = request.get_json()
        wishlist_item = WishlistItems()
        try:
            wishlist_item.deserialize(data)
        except DataValidationError as error:
            abort(status.HTTP_400_BAD_REQUEST, str(error))

        existing_items = WishlistItems.find_by_wishlist_and_product(
            wishlist_id, wishlist_item.product_id
        )
        if existing_items:
            abort(
                status.HTTP_409_CONFLICT,
                f"Product with id '{wishlist_item.product_id}' already exists in wishlist",
            )

        last_position = WishlistItems.find_last_position(wishlist_id)
        wishlist_item.wishlist_id = wishlist_id
        wishlist_item.position = last_position + 1000
        wishlist_item.create()

        message = wishlist_item.serialize()
        location_url = f"/api/wishlists/{wishlist_id}/items/{wishlist_item.product_id}"

        return message, status.HTTP_201_CREATED, {"location": location_url}


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def abort(error_code: int, message: str):
    """Logs errors before aborting"""
    app.logger.error(message)
    api.abort(error_code, message)
