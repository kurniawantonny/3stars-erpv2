"""
Purchase module models - Purchase Orders, Purchase Requests, Suppliers
"""

from app import db
from app.models.base import BaseModel


class Supplier(BaseModel):
    """Supplier/Vendor master data"""
    
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    tax_id = db.Column(db.String(50))
    payment_terms = db.Column(db.String(100))  # e.g., "Net 30", "COD"
    credit_limit = db.Column(db.Numeric(12, 2), default=0)
    currency = db.Column(db.String(10), default='IDR')
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy='dynamic')
    
    def __repr__(self):
        return f'<Supplier {self.code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'tax_id': self.tax_id,
            'payment_terms': self.payment_terms,
            'credit_limit': float(self.credit_limit) if self.credit_limit else 0,
            'currency': self.currency,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PurchaseRequest(BaseModel):
    """Internal purchase request"""
    
    __tablename__ = 'purchase_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    pr_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    request_date = db.Column(db.DateTime, nullable=False)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department = db.Column(db.String(100))
    status = db.Column(db.String(20), default='DRAFT')  # DRAFT, PENDING, APPROVED, REJECTED, PURCHASED
    notes = db.Column(db.Text)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    
    # Relationships
    items = db.relationship('PurchaseRequestItem', backref='request', lazy='dynamic')
    
    def __repr__(self):
        return f'<PurchaseRequest {self.pr_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'pr_number': self.pr_number,
            'request_date': self.request_date.isoformat() if self.request_date else None,
            'requested_by': self.requested_by,
            'department': self.department,
            'status': self.status,
            'notes': self.notes,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PurchaseRequestItem(BaseModel):
    """Individual items in purchase request"""
    
    __tablename__ = 'purchase_request_items'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('purchase_requests.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    unit_of_measure = db.Column(db.String(50))
    estimated_price = db.Column(db.Numeric(12, 2))
    notes = db.Column(db.Text)
    
    # Relationships
    product = db.relationship('Product', backref='purchase_request_items')
    
    def __repr__(self):
        return f'<PurchaseRequestItem Product:{self.product_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'product_id': self.product_id,
            'product': self.product.to_dict() if self.product else None,
            'quantity': float(self.quantity) if self.quantity else 0,
            'unit_of_measure': self.unit_of_measure,
            'estimated_price': float(self.estimated_price) if self.estimated_price else 0,
            'notes': self.notes
        }


class PurchaseOrder(BaseModel):
    """Purchase Order"""
    
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    order_date = db.Column(db.DateTime, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    status = db.Column(db.String(20), default='DRAFT')  # DRAFT, SENT, CONFIRMED, PARTIAL_RECEIVED, COMPLETED, CANCELLED
    expected_delivery_date = db.Column(db.DateTime)
    actual_delivery_date = db.Column(db.DateTime)
    payment_terms = db.Column(db.String(100))
    shipping_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    subtotal = db.Column(db.Numeric(14, 2), default=0)
    tax_amount = db.Column(db.Numeric(14, 2), default=0)
    discount_amount = db.Column(db.Numeric(14, 2), default=0)
    total_amount = db.Column(db.Numeric(14, 2), default=0)
    
    # Relationships
    items = db.relationship('PurchaseOrderItem', backref='order', lazy='dynamic')
    receipts = db.relationship('GoodsReceipt', backref='order', lazy='dynamic')
    
    def __repr__(self):
        return f'<PurchaseOrder {self.po_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'po_number': self.po_number,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'supplier_id': self.supplier_id,
            'supplier': self.supplier.to_dict() if self.supplier else None,
            'status': self.status,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'payment_terms': self.payment_terms,
            'shipping_address': self.shipping_address,
            'notes': self.notes,
            'subtotal': float(self.subtotal) if self.subtotal else 0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PurchaseOrderItem(BaseModel):
    """Individual items in purchase order"""
    
    __tablename__ = 'purchase_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_ordered = db.Column(db.Numeric(12, 2), nullable=False)
    quantity_received = db.Column(db.Numeric(12, 2), default=0)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(14, 2), default=0)
    tax_rate = db.Column(db.Numeric(5, 2), default=0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    discount_percent = db.Column(db.Numeric(5, 2), default=0)
    discount_amount = db.Column(db.Numeric(12, 2), default=0)
    total_amount = db.Column(db.Numeric(14, 2), default=0)
    notes = db.Column(db.Text)
    
    # Relationships
    product = db.relationship('Product', backref='purchase_order_items')
    
    def __repr__(self):
        return f'<PurchaseOrderItem Product:{self.product_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product': self.product.to_dict() if self.product else None,
            'quantity_ordered': float(self.quantity_ordered) if self.quantity_ordered else 0,
            'quantity_received': float(self.quantity_received) if self.quantity_received else 0,
            'unit_price': float(self.unit_price) if self.unit_price else 0,
            'subtotal': float(self.subtotal) if self.subtotal else 0,
            'tax_rate': float(self.tax_rate) if self.tax_rate else 0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0,
            'discount_percent': float(self.discount_percent) if self.discount_percent else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'notes': self.notes
        }


class GoodsReceipt(BaseModel):
    """Goods Receipt for tracking received items"""
    
    __tablename__ = 'goods_receipts'
    
    id = db.Column(db.Integer, primary_key=True)
    gr_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    receipt_date = db.Column(db.DateTime, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    status = db.Column(db.String(20), default='DRAFT')  # DRAFT, CONFIRMED, POSTED
    notes = db.Column(db.Text)
    
    # Relationships
    items = db.relationship('GoodsReceiptItem', backref='receipt', lazy='dynamic')
    
    def __repr__(self):
        return f'<GoodsReceipt {self.gr_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'gr_number': self.gr_number,
            'receipt_date': self.receipt_date.isoformat() if self.receipt_date else None,
            'order_id': self.order_id,
            'warehouse_id': self.warehouse_id,
            'status': self.status,
            'notes': self.notes,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class GoodsReceiptItem(BaseModel):
    """Individual items in goods receipt"""
    
    __tablename__ = 'goods_receipt_items'
    
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('goods_receipts.id'), nullable=False)
    order_item_id = db.Column(db.Integer, db.ForeignKey('purchase_order_items.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_received = db.Column(db.Numeric(12, 2), nullable=False)
    accepted_quantity = db.Column(db.Numeric(12, 2), default=0)
    rejected_quantity = db.Column(db.Numeric(12, 2), default=0)
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_locations.id'))
    notes = db.Column(db.Text)
    
    # Relationships
    product = db.relationship('Product', backref='goods_receipt_items')
    location = db.relationship('WarehouseLocation', backref='goods_receipt_items')
    order_item = db.relationship('PurchaseOrderItem', backref='goods_receipt_items')
    
    def __repr__(self):
        return f'<GoodsReceiptItem Product:{self.product_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'receipt_id': self.receipt_id,
            'order_item_id': self.order_item_id,
            'product_id': self.product_id,
            'product': self.product.to_dict() if self.product else None,
            'quantity_received': float(self.quantity_received) if self.quantity_received else 0,
            'accepted_quantity': float(self.accepted_quantity) if self.accepted_quantity else 0,
            'rejected_quantity': float(self.rejected_quantity) if self.rejected_quantity else 0,
            'location_id': self.location_id,
            'notes': self.notes
        }
