"""
Inventory module models - Products, Warehouses, Stock Moves
"""

from app import db
from app.models.base import BaseModel


class Product(BaseModel):
    """Product master data"""
    
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    unit_of_measure = db.Column(db.String(50), default='PCS')
    cost_price = db.Column(db.Numeric(12, 2), default=0)
    sale_price = db.Column(db.Numeric(12, 2), default=0)
    min_stock_level = db.Column(db.Integer, default=0)
    max_stock_level = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    category = db.relationship('ProductCategory', backref='products')
    stock_moves = db.relationship('StockMove', backref='product', lazy='dynamic')
    
    def __repr__(self):
        return f'<Product {self.sku}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'category': self.category.to_dict() if self.category else None,
            'unit_of_measure': self.unit_of_measure,
            'cost_price': float(self.cost_price) if self.cost_price else 0,
            'sale_price': float(self.sale_price) if self.sale_price else 0,
            'min_stock_level': self.min_stock_level,
            'max_stock_level': self.max_stock_level,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ProductCategory(BaseModel):
    """Product categories for hierarchical organization"""
    
    __tablename__ = 'product_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    
    # Self-referential relationship for hierarchy
    parent = db.relationship('ProductCategory', remote_side=[id], backref='children')
    
    def __repr__(self):
        return f'<ProductCategory {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'parent': self.parent.to_dict() if self.parent else None
        }


class Warehouse(BaseModel):
    """Warehouse locations"""
    
    __tablename__ = 'warehouses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    locations = db.relationship('WarehouseLocation', backref='warehouse', lazy='dynamic')
    stock_moves = db.relationship('StockMove', backref='warehouse', lazy='dynamic')
    
    def __repr__(self):
        return f'<Warehouse {self.code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'address': self.address,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WarehouseLocation(BaseModel):
    """Specific locations within a warehouse"""
    
    __tablename__ = 'warehouse_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100))
    zone = db.Column(db.String(50))
    aisle = db.Column(db.String(50))
    rack = db.Column(db.String(50))
    shelf = db.Column(db.String(50))
    
    # Relationships
    stock_quants = db.relationship('StockQuant', backref='location', lazy='dynamic')
    
    def __repr__(self):
        return f'<WarehouseLocation {self.code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'code': self.code,
            'name': self.name,
            'zone': self.zone,
            'aisle': self.aisle,
            'rack': self.rack,
            'shelf': self.shelf
        }


class StockQuant(BaseModel):
    """Current stock quantities per product and location"""
    
    __tablename__ = 'stock_quants'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_locations.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    reserved_quantity = db.Column(db.Numeric(12, 2), default=0)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('product_id', 'location_id', name='unique_product_location'),)
    
    def __repr__(self):
        return f'<StockQuant Product:{self.product_id} Location:{self.location_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'location_id': self.location_id,
            'quantity': float(self.quantity) if self.quantity else 0,
            'reserved_quantity': float(self.reserved_quantity) if self.reserved_quantity else 0
        }


class StockMove(BaseModel):
    """Stock movement tracking (in/out/transfer)"""
    
    __tablename__ = 'stock_moves'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    move_type = db.Column(db.String(20), nullable=False)  # IN, OUT, TRANSFER, ADJUSTMENT
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    source_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_locations.id'))
    dest_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_locations.id'))
    reference = db.Column(db.String(100))  # PO number, SO number, etc.
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='DRAFT')  # DRAFT, CONFIRMED, DONE, CANCELLED
    
    # Relationships
    source_location = db.relationship('WarehouseLocation', foreign_keys=[source_location_id])
    dest_location = db.relationship('WarehouseLocation', foreign_keys=[dest_location_id])
    
    def __repr__(self):
        return f'<StockMove {self.move_type} Product:{self.product_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product': self.product.to_dict() if self.product else None,
            'warehouse_id': self.warehouse_id,
            'move_type': self.move_type,
            'quantity': float(self.quantity) if self.quantity else 0,
            'source_location': self.source_location.to_dict() if self.source_location else None,
            'dest_location': self.dest_location.to_dict() if self.dest_location else None,
            'reference': self.reference,
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }


class StockOpname(BaseModel):
    """Stock opname / physical inventory count"""
    
    __tablename__ = 'stock_opnames'
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    opname_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='DRAFT')  # DRAFT, IN_PROGRESS, COMPLETED, POSTED
    notes = db.Column(db.Text)
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    items = db.relationship('StockOpnameItem', backref='opname', lazy='dynamic')
    
    def __repr__(self):
        return f'<StockOpname {self.opname_date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'opname_date': self.opname_date.isoformat() if self.opname_date else None,
            'status': self.status,
            'notes': self.notes,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StockOpnameItem(BaseModel):
    """Individual items in stock opname"""
    
    __tablename__ = 'stock_opname_items'
    
    id = db.Column(db.Integer, primary_key=True)
    opname_id = db.Column(db.Integer, db.ForeignKey('stock_opnames.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_locations.id'))
    system_quantity = db.Column(db.Numeric(12, 2), default=0)
    counted_quantity = db.Column(db.Numeric(12, 2), default=0)
    difference = db.Column(db.Numeric(12, 2))
    notes = db.Column(db.Text)
    
    # Relationships
    product = db.relationship('Product', backref='opname_items')
    location = db.relationship('WarehouseLocation', backref='opname_items')
    
    def __repr__(self):
        return f'<StockOpnameItem Product:{self.product_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'opname_id': self.opname_id,
            'product_id': self.product_id,
            'product': self.product.to_dict() if self.product else None,
            'location_id': self.location_id,
            'system_quantity': float(self.system_quantity) if self.system_quantity else 0,
            'counted_quantity': float(self.counted_quantity) if self.counted_quantity else 0,
            'difference': float(self.difference) if self.difference else 0,
            'notes': self.notes
        }
