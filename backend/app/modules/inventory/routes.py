"""
Inventory module routes - Products, Stock, Warehouses
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.modules.inventory.models import (
    Product, ProductCategory, Warehouse, 
    WarehouseLocation, StockQuant, StockMove, 
    StockOpname, StockOpnameItem
)
from app import db
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)


# ==================== PRODUCT MANAGEMENT ====================

@inventory_bp.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    """Get all products with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search')
    
    query = Product.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) | 
            (Product.sku.ilike(f'%{search}%'))
        )
    
    products = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'products': [p.to_dict() for p in products.items],
        'total': products.total,
        'pages': products.pages,
        'current_page': page
    }), 200


@inventory_bp.route('/products/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """Get single product by ID"""
    product = Product.query.get_or_404(product_id)
    return jsonify({'product': product.to_dict()}), 200


@inventory_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    """Create new product"""
    data = request.get_json()
    
    required_fields = ['sku', 'name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if SKU already exists
    if Product.query.filter_by(sku=data['sku']).first():
        return jsonify({'error': 'SKU already exists'}), 400
    
    product = Product(
        sku=data['sku'],
        name=data['name'],
        description=data.get('description'),
        category_id=data.get('category_id'),
        unit_of_measure=data.get('unit_of_measure', 'PCS'),
        cost_price=data.get('cost_price', 0),
        sale_price=data.get('sale_price', 0),
        min_stock_level=data.get('min_stock_level', 0),
        max_stock_level=data.get('max_stock_level'),
        created_by=get_jwt_identity()
    )
    product.save()
    
    return jsonify({'message': 'Product created successfully', 'product': product.to_dict()}), 201


@inventory_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """Update existing product"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if 'sku' in data:
        if Product.query.filter_by(sku=data['sku']).first():
            return jsonify({'error': 'SKU already exists'}), 400
        product.sku = data['sku']
    
    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'category_id' in data:
        product.category_id = data['category_id']
    if 'unit_of_measure' in data:
        product.unit_of_measure = data['unit_of_measure']
    if 'cost_price' in data:
        product.cost_price = data['cost_price']
    if 'sale_price' in data:
        product.sale_price = data['sale_price']
    if 'min_stock_level' in data:
        product.min_stock_level = data['min_stock_level']
    if 'max_stock_level' in data:
        product.max_stock_level = data['max_stock_level']
    if 'is_active' in data:
        product.is_active = data['is_active']
    
    product.updated_by = get_jwt_identity()
    product.save()
    
    return jsonify({'message': 'Product updated successfully', 'product': product.to_dict()}), 200


@inventory_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """Delete product (soft delete)"""
    product = Product.query.get_or_404(product_id)
    product.is_active = False
    product.updated_by = get_jwt_identity()
    product.save()
    
    return jsonify({'message': 'Product deleted successfully'}), 200


# ==================== PRODUCT CATEGORIES ====================

@inventory_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get all product categories"""
    categories = ProductCategory.query.all()
    return jsonify({'categories': [c.to_dict() for c in categories]}), 200


@inventory_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    """Create new product category"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Category name is required'}), 400
    
    category = ProductCategory(
        name=data['name'],
        parent_id=data.get('parent_id')
    )
    category.save()
    
    return jsonify({'message': 'Category created successfully', 'category': category.to_dict()}), 201


# ==================== WAREHOUSE MANAGEMENT ====================

@inventory_bp.route('/warehouses', methods=['GET'])
@jwt_required()
def get_warehouses():
    """Get all warehouses"""
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    return jsonify({'warehouses': [w.to_dict() for w in warehouses]}), 200


@inventory_bp.route('/warehouses', methods=['POST'])
@jwt_required()
def create_warehouse():
    """Create new warehouse"""
    data = request.get_json()
    
    required_fields = ['code', 'name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if Warehouse.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Warehouse code already exists'}), 400
    
    warehouse = Warehouse(
        code=data['code'],
        name=data['name'],
        address=data.get('address'),
        created_by=get_jwt_identity()
    )
    warehouse.save()
    
    return jsonify({'message': 'Warehouse created successfully', 'warehouse': warehouse.to_dict()}), 201


# ==================== STOCK MANAGEMENT ====================

@inventory_bp.route('/stock', methods=['GET'])
@jwt_required()
def get_stock():
    """Get current stock levels"""
    product_id = request.args.get('product_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    query = StockQuant.query
    
    if product_id:
        query = query.filter_by(product_id=product_id)
    if warehouse_id:
        # Join with locations to filter by warehouse
        query = query.join(WarehouseLocation).filter(
            WarehouseLocation.warehouse_id == warehouse_id
        )
    
    stock_quants = query.all()
    
    return jsonify({
        'stock': [s.to_dict() for s in stock_quants]
    }), 200


@inventory_bp.route('/stock-moves', methods=['GET'])
@jwt_required()
def get_stock_moves():
    """Get stock movement history"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    product_id = request.args.get('product_id', type=int)
    move_type = request.args.get('move_type')
    status = request.args.get('status')
    
    query = StockMove.query
    
    if product_id:
        query = query.filter_by(product_id=product_id)
    if move_type:
        query = query.filter_by(move_type=move_type)
    if status:
        query = query.filter_by(status=status)
    
    moves = query.order_by(StockMove.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'stock_moves': [m.to_dict() for m in moves.items],
        'total': moves.total,
        'pages': moves.pages,
        'current_page': page
    }), 200


@inventory_bp.route('/stock-moves', methods=['POST'])
@jwt_required()
def create_stock_move():
    """Create new stock movement"""
    data = request.get_json()
    
    required_fields = ['product_id', 'warehouse_id', 'move_type', 'quantity']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    valid_move_types = ['IN', 'OUT', 'TRANSFER', 'ADJUSTMENT']
    if data['move_type'] not in valid_move_types:
        return jsonify({'error': f'Invalid move type. Must be one of: {valid_move_types}'}), 400
    
    stock_move = StockMove(
        product_id=data['product_id'],
        warehouse_id=data['warehouse_id'],
        move_type=data['move_type'],
        quantity=data['quantity'],
        source_location_id=data.get('source_location_id'),
        dest_location_id=data.get('dest_location_id'),
        reference=data.get('reference'),
        notes=data.get('notes'),
        created_by=get_jwt_identity()
    )
    stock_move.save()
    
    # Update stock quant
    _update_stock_quant(stock_move)
    
    return jsonify({
        'message': 'Stock move created successfully', 
        'stock_move': stock_move.to_dict()
    }), 201


def _update_stock_quant(stock_move):
    """Helper function to update stock quantities based on move"""
    if stock_move.move_type == 'IN':
        # Add stock to destination location
        location_id = stock_move.dest_location_id
        change = stock_move.quantity
    elif stock_move.move_type == 'OUT':
        # Remove stock from source location
        location_id = stock_move.source_location_id
        change = -stock_move.quantity
    elif stock_move.move_type == 'TRANSFER':
        # Remove from source, add to destination
        if stock_move.source_location_id:
            _adjust_stock_quant(
                stock_move.product_id, 
                stock_move.source_location_id, 
                -stock_move.quantity
            )
        if stock_move.dest_location_id:
            _adjust_stock_quant(
                stock_move.product_id, 
                stock_move.dest_location_id, 
                stock_move.quantity
            )
        return
    else:  # ADJUSTMENT
        location_id = stock_move.dest_location_id or stock_move.source_location_id
        change = stock_move.quantity
    
    if location_id:
        _adjust_stock_quant(stock_move.product_id, location_id, change)


def _adjust_stock_quant(product_id, location_id, change):
    """Adjust stock quant by a given amount"""
    stock_quant = StockQuant.query.filter_by(
        product_id=product_id, 
        location_id=location_id
    ).first()
    
    if not stock_quant:
        stock_quant = StockQuant(
            product_id=product_id,
            location_id=location_id,
            quantity=0
        )
    
    stock_quant.quantity += change
    stock_quant.save()


# ==================== STOCK OPNAME ====================

@inventory_bp.route('/stock-opnames', methods=['GET'])
@jwt_required()
def get_stock_opnames():
    """Get all stock opnames"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    status = request.args.get('status')
    
    query = StockOpname.query
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if status:
        query = query.filter_by(status=status)
    
    opnames = query.order_by(StockOpname.opname_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'stock_opnames': [o.to_dict() for o in opnames.items],
        'total': opnames.total,
        'pages': opnames.pages,
        'current_page': page
    }), 200


@inventory_bp.route('/stock-opnames', methods=['POST'])
@jwt_required()
def create_stock_opname():
    """Create new stock opname"""
    data = request.get_json()
    
    if not data.get('warehouse_id'):
        return jsonify({'error': 'warehouse_id is required'}), 400
    
    opname = StockOpname(
        warehouse_id=data['warehouse_id'],
        opname_date=data.get('opname_date', datetime.utcnow()),
        notes=data.get('notes'),
        status='DRAFT'
    )
    opname.save()
    
    return jsonify({
        'message': 'Stock opname created successfully', 
        'stock_opname': opname.to_dict()
    }), 201


# ==================== LOW STOCK ALERTS ====================

@inventory_bp.route('/low-stock-alerts', methods=['GET'])
@jwt_required()
def get_low_stock_alerts():
    """Get products below minimum stock level"""
    alerts = []
    
    products = Product.query.filter_by(is_active=True).all()
    
    for product in products:
        total_stock = db.session.query(
            db.func.sum(StockQuant.quantity)
        ).filter_by(product_id=product.id).scalar() or 0
        
        if total_stock < product.min_stock_level:
            alerts.append({
                'product': product.to_dict(),
                'current_stock': float(total_stock),
                'min_stock_level': product.min_stock_level,
                'shortage': product.min_stock_level - float(total_stock)
            })
    
    return jsonify({'alerts': alerts}), 200
