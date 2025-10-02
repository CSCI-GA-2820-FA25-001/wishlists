import logging
from datetime import date
from .persistent_base import db, PersistentBase, DataValidationError
from .wishlist_items import WishlistItems

logger = logging.getLogger('flask.app')

class Wishlists(db.Model, PersistentBase):
    """ Class that represents a Wishlist """

    __tablename__ = 'wishlists'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(63), nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(63))
    created_date = db.Column(db.Date, nullable=False, default=date.today())
    updated_date = db.Column(db.Date, onupdate=date.today())    

    wishlist_items = db.relationship('WishlistItems', backref='wishlists', lazy=True)

    def __repr__(self):
        return f'<Wishlists {self.name} id=[{self.id}]>'
    
    def serialize(self) -> dict:
        """ Convert a Wishlist into a dictionary """
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'created_date': self.created_date.isoformat(),
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'wishlist_items': sorted([item.serialize() for item in self.wishlist_items], key=lambda x: x['position'])
        }
    
    def deserialize(self, data: dict) -> None:
        """ Convert a dictionary into a Wishlist """
        try:
            if type(data['customer_id']) is not int:
                raise DataValidationError('customer_id must be an integer')
            if type(data['name']) is not str:
                raise DataValidationError('name must be a string')
            self.customer_id = data['customer_id']
            self.name = data['name']
            self.description = data.get('description')
            self.category = data.get('category')
            self.created_date = date.fromisoformat(data['created_date']) if 'created_date' in data else date.today()
            self.updated_date = date.fromisoformat(data['updated_date']) if 'updated_date' in data else None
        except AttributeError as e:
            raise DataValidationError(f'Invalid attribute: {e.args[0]}') from e
        except KeyError as e:
            raise DataValidationError(f'Missing key: {e.args[0]}') from e
        except TypeError as e:
            raise DataValidationError(f'Invalid type: {e}') from e
        return self
        

    @classmethod
    def find_by_id(cls, wishlist_id: int):
        """ Find a Wishlist by its ID """
        return cls.query.get(wishlist_id)
    
    @classmethod
    def find_all_by_customer_id(cls, customer_id: int):
        """ Find all Wishlists for a given customer ID """
        return cls.query.filter(cls.customer_id == customer_id).all()
    
    @classmethod
    def reposition(cls, wishlist_id: int):
        """ Reposition items in a Wishlist to ensure positions are sequential starting from 1000, with increments of 1000 """
        wishlist = cls.find_by_id(wishlist_id)
        if not wishlist:
            raise DataValidationError(f'Wishlist with id {wishlist_id} not found')
        items = sorted(wishlist.wishlist_items, key=lambda item: item.position)
        for index, item in enumerate(items):
            item.position = (index + 1) * 1000
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        return items
