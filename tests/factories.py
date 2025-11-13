"""
Test Factory to make fake objects for testing
"""

from datetime import date
import factory
from service.models import Wishlists, WishlistItems

CUSTOMER_ID = 1001


class WishlistsFactory(factory.Factory):
    """Creates fake wishlists for testing"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Wishlists

    id = factory.Sequence(lambda n: n)
    customer_id = CUSTOMER_ID
    name = factory.Faker("word")
    description = factory.Faker("sentence")
    category = factory.Faker("word")
    created_date = date.today()
    updated_date = None


class WishlistItemsFactory(factory.Factory):
    """Creates fake wishlist items for testing"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = WishlistItems

    def __init__(self, wishlist_id: int = 1):
        super().__init__()
        self.wishlist_id = wishlist_id

    wishlist_id = 1
    product_id = factory.Sequence(lambda n: n)
    description = factory.Faker("sentence")
    position = factory.Sequence(lambda n: n * 1000)
