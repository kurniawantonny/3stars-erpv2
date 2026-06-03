"""
Purchase module routes - Suppliers, Purchase Orders, Goods Receipts
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.modules.purchase.models import (
    Supplier, PurchaseRequest, PurchaseRequestItem,
    PurchaseOrder, PurchaseOrderItem,
    GoodsReceipt, GoodsReceiptItem
)
from app.modules.inventory.models import Product, Warehouse, StockMove
from app import db
from datetime import datetime

purchase_bp = Blueprint('purchase', __name__)


# ==================== SUPPLIER MANAGEMENT ====================

@purchase_bp.route('/suppliers', methods=['GET'])
@jwt_required()
def get_suppliers():
    """Get all suppliers with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search')
    is_active = request.args.get('is_active', type=bool)
    
    query = Supplier.query
    
    if search:
        query = query.filter(
            (Supplier.name.ilike(f'%{search}%')) | 
            (Supplier.code.ilike(f'%{search}%')) |
            (Supplier.email.ilike(f'%{search}%'))
        )
    
    if is_active is not None:
        query = query.filter_by(is_active=is_active)
    
    suppliers = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'suppliers': [s.to_dict() for s in suppliers.items],
        'total': suppliers.total,
        'pages': suppliers.pages,
        'current_page': page
    }), 200


@purchase_bp.route('/suppliers/<int:supplier_id>', methods=['GET'])
@jwt_required()
def get_supplier(supplier_id):
    """Get single supplier by ID"""
    supplier = Supplier.query.get_or_404(supplier_id)
    return jsonify({'supplier': supplier.to_dict()}), 200


@purchase_bp.route('/suppliers', methods=['POST'])
@jwt_required()
def create_supplier():
    """Create new supplier"""
    data = request.get_json()
    
    required_fields = ['code', 'name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if code already exists
    if Supplier.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Supplier code already exists'}), 400
    
    supplier = Supplier(
        code=data['code'],
        name=data['name'],
        contact_person=data.get('contact_person'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        tax_id=data.get('tax_id'),
        payment_terms=data.get('payment_terms'),
        credit_limit=data.get('credit_limit', 0),
        currency=data.get('currency', 'IDR'),
        created_by=get_jwt_identity()
    )
    supplier.save()
    
    return jsonify({'message': 'Supplier created successfully', 'supplier': supplier.to_dict()}), 201


@purchase_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
@jwt_required()
def update_supplier(supplier_id):
    """Update existing supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.get_json()
    
    if 'code' in data:
        if Supplier.query.filter_by(code=data['code']).first():
            return jsonify({'error': 'Supplier code already exists'}), 400
        supplier.code = data['code']
    
    if 'name' in data:
        supplier.name = data['name']
    if 'contact_person' in data:
        supplier.contact_person = data['contact_person']
    if 'email' in data:
        supplier.email = data['email']
    if 'phone' in data:
        supplier.phone = data['phone']
    if 'address' in data:
        supplier.address = data['address']
    if 'tax_id' in data:
        supplier.tax_id = data['tax_id']
    if 'payment_terms' in data:
        supplier.payment_terms = data['payment_terms']
    if 'credit_limit' in data:
        supplier.credit_limit = data['credit_limit']
    if 'currency' in data:
        supplier.currency = data['currency']
    if 'is_active' in data:
        supplier.is_active = data['is_active']
    
    supplier.updated_by = get_jwt_identity()
    supplier.save()
    
    return jsonify({'message': 'Supplier updated successfully', 'supplier': supplier.to_dict()}), 200


@purchase_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
@jwt_required()
def delete_supplier(supplier_id):
    """Delete supplier (soft delete)"""
    supplier = Supplier.query.get_or_404(supplier_id)
    supplier.is_active = False
    supplier.updated_by = get_jwt_identity()
    supplier.save()
    
    return jsonify({'message': 'Supplier deleted successfully'}), 200


# ==================== PURCHASE REQUEST ====================

@purchase_bp.route('/purchase-requests', methods=['GET'])
@jwt_required()
def get_purchase_requests():
    """Get all purchase requests"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = PurchaseRequest.query
    
    if status:
        query = query.filter_by(status=status)
    
    requests = query.order_by(PurchaseRequest.request_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'purchase_requests': [pr.to_dict() for pr in requests.items],
        'total': requests.total,
        'pages': requests.pages,
        'current_page': page
    }), 200


@purchase_bp.route('/purchase-requests', methods=['POST'])
@jwt_required()
def create_purchase_request():
    """Create new purchase request"""
    data = request.get_json()
    
    if not data.get('items'):
        return jsonify({'error': 'At least one item is required'}), 400
    
    # Generate PR number
    pr_number = f"PR-{datetime.utcnow().strftime('%Y%m%d')}-{PurchaseRequest.query.count() + 1:04d}"
    
    purchase_request = PurchaseRequest(
        pr_number=pr_number,
        request_date=datetime.utcnow(),
        requested_by=get_jwt_identity(),
        department=data.get('department'),
        notes=data.get('notes'),
        status='DRAFT'
    )
    purchase_request.save()
    
    # Add items
    for item_data in data['items']:
        if not item_data.get('product_id') or not item_data.get('quantity'):
            continue
        
        pr_item = PurchaseRequestItem(
            request_id=purchase_request.id,
            product_id=item_data['product_id'],
            quantity=item_data['quantity'],
            unit_of_measure=item_data.get('unit_of_measure'),
            estimated_price=item_data.get('estimated_price'),
            notes=item_data.get('notes')
        )
        pr_item.save()
    
    return jsonify({
        'message': 'Purchase request created successfully',
        'purchase_request': purchase_request.to_dict()
    }), 201


@purchase_bp.route('/purchase-requests/<int:request_id>/approve', methods=['POST'])
@jwt_required()
def approve_purchase_request(request_id):
    """Approve purchase request"""
    purchase_request = PurchaseRequest.query.get_or_404(request_id)
    
    if purchase_request.status != 'PENDING':
        return jsonify({'error': 'Only pending requests can be approved'}), 400
    
    purchase_request.status = 'APPROVED'
    purchase_request.approved_by = get_jwt_identity()
    purchase_request.approved_at = datetime.utcnow()
    purchase_request.save()
    
    return jsonify({'message': 'Purchase request approved'}), 200


# ==================== PURCHASE ORDER ====================

@purchase_bp.route('/purchase-orders', methods=['GET'])
@jwt_required()
def get_purchase_orders():
    """Get all purchase orders"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    supplier_id = request.args.get('supplier_id', type=int)
    status = request.args.get('status')
    
    query = PurchaseOrder.query
    
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(PurchaseOrder.order_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'purchase_orders': [po.to_dict() for po in orders.items],
        'total': orders.total,
        'pages': orders.pages,
        'current_page': page
    }), 200


@purchase_bp.route('/purchase-orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_purchase_order(order_id):
    """Get single purchase order by ID"""
    order = PurchaseOrder.query.get_or_404(order_id)
    return jsonify({'purchase_order': order.to_dict()}), 200


@purchase_bp.route('/purchase-orders', methods=['POST'])
@jwt_required()
def create_purchase_order():
    """Create new purchase order"""
    data = request.get_json()
    
    required_fields = ['supplier_id', 'items']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if not data['items']:
        return jsonify({'error': 'At least one item is required'}), 400
    
    # Generate PO number
    po_number = f"PO-{datetime.utcnow().strftime('%Y%m%d')}-{PurchaseOrder.query.count() + 1:04d}"
    
    purchase_order = PurchaseOrder(
        po_number=po_number,
        order_date=datetime.utcnow(),
        supplier_id=data['supplier_id'],
        expected_delivery_date=data.get('expected_delivery_date'),
        payment_terms=data.get('payment_terms'),
        shipping_address=data.get('shipping_address'),
        notes=data.get('notes'),
        status='DRAFT'
    )
    purchase_order.save()
    
    # Calculate totals
    subtotal = 0
    tax_amount = 0
    discount_amount = 0
    total_amount = 0
    
    # Add items
    for item_data in data['items']:
        if not item_data.get('product_id') or not item_data.get('quantity_ordered') or not item_data.get('unit_price'):
            continue
        
        item_subtotal = item_data['quantity_ordered'] * item_data['unit_price']
        item_tax = item_subtotal * (item_data.get('tax_rate', 0) / 100)
        item_discount = item_subtotal * (item_data.get('discount_percent', 0) / 100)
        item_total = item_subtotal + item_tax - item_discount
        
        po_item = PurchaseOrderItem(
            order_id=purchase_order.id,
            product_id=item_data['product_id'],
            quantity_ordered=item_data['quantity_ordered'],
            unit_price=item_data['unit_price'],
            subtotal=item_subtotal,
            tax_rate=item_data.get('tax_rate', 0),
            tax_amount=item_tax,
            discount_percent=item_data.get('discount_percent', 0),
            discount_amount=item_discount,
            total_amount=item_total,
            notes=item_data.get('notes')
        )
        po_item.save()
        
        subtotal += item_subtotal
        tax_amount += item_tax
        discount_amount += item_discount
        total_amount += item_total
    
    # Update order totals
    purchase_order.subtotal = subtotal
    purchase_order.tax_amount = tax_amount
    purchase_order.discount_amount = discount_amount
    purchase_order.total_amount = total_amount
    purchase_order.save()
    
    return jsonify({
        'message': 'Purchase order created successfully',
        'purchase_order': purchase_order.to_dict()
    }), 201


@purchase_bp.route('/purchase-orders/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_purchase_order(order_id):
    """Update purchase order (only in DRAFT status)"""
    order = PurchaseOrder.query.get_or_404(order_id)
    
    if order.status != 'DRAFT':
        return jsonify({'error': 'Only draft orders can be modified'}), 400
    
    data = request.get_json()
    
    if 'supplier_id' in data:
        order.supplier_id = data['supplier_id']
    if 'expected_delivery_date' in data:
        order.expected_delivery_date = data['expected_delivery_date']
    if 'payment_terms' in data:
        order.payment_terms = data['payment_terms']
    if 'shipping_address' in data:
        order.shipping_address = data['shipping_address']
    if 'notes' in data:
        order.notes = data['notes']
    
    order.save()
    
    return jsonify({'message': 'Purchase order updated successfully', 'purchase_order': order.to_dict()}), 200


@purchase_bp.route('/purchase-orders/<int:order_id>/send', methods=['POST'])
@jwt_required()
def send_purchase_order(order_id):
    """Send purchase order to supplier"""
    order = PurchaseOrder.query.get_or_404(order_id)
    
    if order.status != 'DRAFT':
        return jsonify({'error': 'Only draft orders can be sent'}), 400
    
    order.status = 'SENT'
    order.save()
    
    return jsonify({'message': 'Purchase order sent to supplier'}), 200


@purchase_bp.route('/purchase-orders/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_purchase_order(order_id):
    """Cancel purchase order"""
    order = PurchaseOrder.query.get_or_404(order_id)
    
    if order.status in ['COMPLETED', 'CANCELLED']:
        return jsonify({'error': 'Cannot cancel completed or cancelled orders'}), 400
    
    order.status = 'CANCELLED'
    order.save()
    
    return jsonify({'message': 'Purchase order cancelled'}), 200


# ==================== GOODS RECEIPT ====================

@purchase_bp.route('/goods-receipts', methods=['GET'])
@jwt_required()
def get_goods_receipts():
    """Get all goods receipts"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    order_id = request.args.get('order_id', type=int)
    status = request.args.get('status')
    
    query = GoodsReceipt.query
    
    if order_id:
        query = query.filter_by(order_id=order_id)
    if status:
        query = query.filter_by(status=status)
    
    receipts = query.order_by(GoodsReceipt.receipt_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'goods_receipts': [gr.to_dict() for gr in receipts.items],
        'total': receipts.total,
        'pages': receipts.pages,
        'current_page': page
    }), 200


@purchase_bp.route('/goods-receipts', methods=['POST'])
@jwt_required()
def create_goods_receipt():
    """Create new goods receipt"""
    data = request.get_json()
    
    required_fields = ['order_id', 'warehouse_id', 'items']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Generate GR number
    gr_number = f"GR-{datetime.utcnow().strftime('%Y%m%d')}-{GoodsReceipt.query.count() + 1:04d}"
    
    goods_receipt = GoodsReceipt(
        gr_number=gr_number,
        receipt_date=datetime.utcnow(),
        order_id=data['order_id'],
        warehouse_id=data['warehouse_id'],
        notes=data.get('notes'),
        status='DRAFT'
    )
    goods_receipt.save()
    
    # Add items
    for item_data in data['items']:
        if not item_data.get('product_id') or not item_data.get('quantity_received'):
            continue
        
        gr_item = GoodsReceiptItem(
            receipt_id=goods_receipt.id,
            order_item_id=item_data.get('order_item_id'),
            product_id=item_data['product_id'],
            quantity_received=item_data['quantity_received'],
            accepted_quantity=item_data.get('accepted_quantity', item_data['quantity_received']),
            rejected_quantity=item_data.get('rejected_quantity', 0),
            location_id=item_data.get('location_id'),
            notes=item_data.get('notes')
        )
        gr_item.save()
    
    return jsonify({
        'message': 'Goods receipt created successfully',
        'goods_receipt': goods_receipt.to_dict()
    }), 201


@purchase_bp.route('/goods-receipts/<int:receipt_id>/post', methods=['POST'])
@jwt_required()
def post_goods_receipt(receipt_id):
    """Post goods receipt and update inventory"""
    goods_receipt = GoodsReceipt.query.get_or_404(receipt_id)
    
    if goods_receipt.status == 'POSTED':
        return jsonify({'error': 'Receipt already posted'}), 400
    
    # Update PO item quantities
    for gr_item in goods_receipt.items:
        if gr_item.order_item_id:
            order_item = PurchaseOrderItem.query.get(gr_item.order_item_id)
            if order_item:
                order_item.quantity_received += gr_item.accepted_quantity
                order_item.save()
        
        # Create stock move for accepted items
        if gr_item.accepted_quantity > 0:
            stock_move = StockMove(
                product_id=gr_item.product_id,
                warehouse_id=goods_receipt.warehouse_id,
                move_type='IN',
                quantity=gr_item.accepted_quantity,
                dest_location_id=gr_item.location_id,
                reference=goods_receipt.gr_number,
                notes=f"Goods receipt for {goods_receipt.gr_number}",
                status='DONE',
                created_by=get_jwt_identity()
            )
            stock_move.save()
            
            # Update stock quant
            from app.modules.inventory.routes import _adjust_stock_quant
            _adjust_stock_quant(gr_item.product_id, gr_item.location_id, gr_item.accepted_quantity)
    
    # Update PO status if fully received
    order = PurchaseOrder.query.get(goods_receipt.order_id)
    if order:
        all_received = all(
            item.quantity_received >= item.quantity_ordered 
            for item in order.items
        )
        if all_received:
            order.status = 'COMPLETED'
        else:
            order.status = 'PARTIAL_RECEIVED'
        order.actual_delivery_date = datetime.utcnow()
        order.save()
    
    goods_receipt.status = 'POSTED'
    goods_receipt.save()
    
    return jsonify({'message': 'Goods receipt posted successfully'}), 200
