"""
Cash module routes - Bank Accounts, Cash Transactions, Payment/Receipt Vouchers
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.modules.cash.models import (
    BankAccount, CashAccount, CashTransaction, CashTransactionLine,
    PaymentVoucher, PaymentVoucherLine,
    ReceiptVoucher, ReceiptVoucherLine
)
from app import db
from datetime import datetime

cash_bp = Blueprint('cash', __name__)


# ==================== BANK ACCOUNT MANAGEMENT ====================

@cash_bp.route('/bank-accounts', methods=['GET'])
@jwt_required()
def get_bank_accounts():
    """Get all bank accounts"""
    is_active = request.args.get('is_active', type=bool)
    
    query = BankAccount.query
    
    if is_active is not None:
        query = query.filter_by(is_active=is_active)
    
    accounts = query.all()
    
    return jsonify({
        'bank_accounts': [a.to_dict() for a in accounts]
    }), 200


@cash_bp.route('/bank-accounts/<int:account_id>', methods=['GET'])
@jwt_required()
def get_bank_account(account_id):
    """Get single bank account by ID"""
    account = BankAccount.query.get_or_404(account_id)
    return jsonify({'bank_account': account.to_dict()}), 200


@cash_bp.route('/bank-accounts', methods=['POST'])
@jwt_required()
def create_bank_account():
    """Create new bank account"""
    data = request.get_json()
    
    required_fields = ['code', 'name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if BankAccount.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Bank account code already exists'}), 400
    
    account = BankAccount(
        code=data['code'],
        name=data['name'],
        bank_name=data.get('bank_name'),
        account_number=data.get('account_number'),
        account_type=data.get('account_type', 'CHECKING'),
        currency=data.get('currency', 'IDR'),
        balance=data.get('balance', 0),
        created_by=get_jwt_identity()
    )
    account.save()
    
    return jsonify({'message': 'Bank account created successfully', 'bank_account': account.to_dict()}), 201


@cash_bp.route('/bank-accounts/<int:account_id>', methods=['PUT'])
@jwt_required()
def update_bank_account(account_id):
    """Update existing bank account"""
    account = BankAccount.query.get_or_404(account_id)
    data = request.get_json()
    
    if 'code' in data:
        if BankAccount.query.filter_by(code=data['code']).first():
            return jsonify({'error': 'Bank account code already exists'}), 400
        account.code = data['code']
    
    if 'name' in data:
        account.name = data['name']
    if 'bank_name' in data:
        account.bank_name = data['bank_name']
    if 'account_number' in data:
        account.account_number = data['account_number']
    if 'account_type' in data:
        account.account_type = data['account_type']
    if 'currency' in data:
        account.currency = data['currency']
    if 'is_active' in data:
        account.is_active = data['is_active']
    
    account.updated_by = get_jwt_identity()
    account.save()
    
    return jsonify({'message': 'Bank account updated successfully', 'bank_account': account.to_dict()}), 200


# ==================== CASH ACCOUNT MANAGEMENT ====================

@cash_bp.route('/cash-accounts', methods=['GET'])
@jwt_required()
def get_cash_accounts():
    """Get all cash accounts"""
    accounts = CashAccount.query.filter_by(is_active=True).all()
    
    return jsonify({
        'cash_accounts': [a.to_dict() for a in accounts]
    }), 200


@cash_bp.route('/cash-accounts', methods=['POST'])
@jwt_required()
def create_cash_account():
    """Create new cash account"""
    data = request.get_json()
    
    required_fields = ['code', 'name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if CashAccount.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Cash account code already exists'}), 400
    
    account = CashAccount(
        code=data['code'],
        name=data['name'],
        description=data.get('description'),
        currency=data.get('currency', 'IDR'),
        max_balance=data.get('max_balance'),
        created_by=get_jwt_identity()
    )
    account.save()
    
    return jsonify({'message': 'Cash account created successfully', 'cash_account': account.to_dict()}), 201


# ==================== CASH TRANSACTION ====================

@cash_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_cash_transactions():
    """Get all cash transactions"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    transaction_type = request.args.get('transaction_type')
    status = request.args.get('status')
    bank_account_id = request.args.get('bank_account_id', type=int)
    
    query = CashTransaction.query
    
    if transaction_type:
        query = query.filter_by(transaction_type=transaction_type)
    if status:
        query = query.filter_by(status=status)
    if bank_account_id:
        query = query.filter_by(bank_account_id=bank_account_id)
    
    transactions = query.order_by(CashTransaction.transaction_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'transactions': [t.to_dict() for t in transactions.items],
        'total': transactions.total,
        'pages': transactions.pages,
        'current_page': page
    }), 200


@cash_bp.route('/transactions', methods=['POST'])
@jwt_required()
def create_cash_transaction():
    """Create new cash transaction"""
    data = request.get_json()
    
    required_fields = ['transaction_type', 'amount']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Generate transaction number
    trans_number = f"TRX-{datetime.utcnow().strftime('%Y%m%d')}-{CashTransaction.query.count() + 1:04d}"
    
    transaction = CashTransaction(
        transaction_number=trans_number,
        transaction_date=datetime.utcnow(),
        transaction_type=data['transaction_type'],
        amount=data['amount'],
        currency=data.get('currency', 'IDR'),
        description=data.get('description'),
        reference=data.get('reference'),
        bank_account_id=data.get('bank_account_id'),
        cash_account_id=data.get('cash_account_id'),
        partner_type=data.get('partner_type'),
        partner_id=data.get('partner_id'),
        status='DRAFT'
    )
    transaction.save()
    
    # Add transaction lines
    if data.get('lines'):
        for line_data in data['lines']:
            line = CashTransactionLine(
                transaction_id=transaction.id,
                account_id=line_data.get('account_id'),
                description=line_data.get('description'),
                debit_amount=line_data.get('debit_amount', 0),
                credit_amount=line_data.get('credit_amount', 0)
            )
            line.save()
    
    return jsonify({
        'message': 'Cash transaction created successfully',
        'transaction': transaction.to_dict()
    }), 201


# ==================== PAYMENT VOUCHER ====================

@cash_bp.route('/payment-vouchers', methods=['GET'])
@jwt_required()
def get_payment_vouchers():
    """Get all payment vouchers"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    supplier_id = request.args.get('supplier_id', type=int)
    
    query = PaymentVoucher.query
    
    if status:
        query = query.filter_by(status=status)
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    
    vouchers = query.order_by(PaymentVoucher.voucher_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'payment_vouchers': [v.to_dict() for v in vouchers.items],
        'total': vouchers.total,
        'pages': vouchers.pages,
        'current_page': page
    }), 200


@cash_bp.route('/payment-vouchers', methods=['POST'])
@jwt_required()
def create_payment_voucher():
    """Create new payment voucher"""
    data = request.get_json()
    
    required_fields = ['payee', 'amount']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Generate voucher number
    voucher_number = f"PV-{datetime.utcnow().strftime('%Y%m%d')}-{PaymentVoucher.query.count() + 1:04d}"
    
    voucher = PaymentVoucher(
        voucher_number=voucher_number,
        voucher_date=datetime.utcnow(),
        payee=data['payee'],
        payment_method=data.get('payment_method', 'CASH'),
        amount=data['amount'],
        currency=data.get('currency', 'IDR'),
        description=data.get('description'),
        bank_account_id=data.get('bank_account_id'),
        cash_account_id=data.get('cash_account_id'),
        supplier_id=data.get('supplier_id'),
        purchase_order_id=data.get('purchase_order_id'),
        status='DRAFT'
    )
    voucher.save()
    
    # Add voucher lines
    if data.get('lines'):
        for line_data in data['lines']:
            line = PaymentVoucherLine(
                voucher_id=voucher.id,
                account_id=line_data.get('account_id'),
                description=line_data.get('description'),
                amount=line_data.get('amount', 0)
            )
            line.save()
    
    return jsonify({
        'message': 'Payment voucher created successfully',
        'payment_voucher': voucher.to_dict()
    }), 201


@cash_bp.route('/payment-vouchers/<int:voucher_id>/approve', methods=['POST'])
@jwt_required()
def approve_payment_voucher(voucher_id):
    """Approve payment voucher"""
    voucher = PaymentVoucher.query.get_or_404(voucher_id)
    
    if voucher.status != 'DRAFT':
        return jsonify({'error': 'Only draft vouchers can be approved'}), 400
    
    voucher.status = 'APPROVED'
    voucher.approved_by = get_jwt_identity()
    voucher.approved_at = datetime.utcnow()
    voucher.save()
    
    return jsonify({'message': 'Payment voucher approved'}), 200


@cash_bp.route('/payment-vouchers/<int:voucher_id>/pay', methods=['POST'])
@jwt_required()
def pay_payment_voucher(voucher_id):
    """Mark payment voucher as paid"""
    voucher = PaymentVoucher.query.get_or_404(voucher_id)
    
    if voucher.status != 'APPROVED':
        return jsonify({'error': 'Only approved vouchers can be paid'}), 400
    
    voucher.status = 'PAID'
    voucher.paid_by = get_jwt_identity()
    voucher.paid_at = datetime.utcnow()
    voucher.save()
    
    # Update bank/cash account balance
    if voucher.bank_account_id:
        account = BankAccount.query.get(voucher.bank_account_id)
        if account:
            account.balance -= voucher.amount
            account.save()
    elif voucher.cash_account_id:
        account = CashAccount.query.get(voucher.cash_account_id)
        if account:
            account.balance -= voucher.amount
            account.save()
    
    return jsonify({'message': 'Payment voucher marked as paid'}), 200


# ==================== RECEIPT VOUCHER ====================

@cash_bp.route('/receipt-vouchers', methods=['GET'])
@jwt_required()
def get_receipt_vouchers():
    """Get all receipt vouchers"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = ReceiptVoucher.query
    
    if status:
        query = query.filter_by(status=status)
    
    vouchers = query.order_by(ReceiptVoucher.voucher_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'receipt_vouchers': [v.to_dict() for v in vouchers.items],
        'total': vouchers.total,
        'pages': vouchers.pages,
        'current_page': page
    }), 200


@cash_bp.route('/receipt-vouchers', methods=['POST'])
@jwt_required()
def create_receipt_voucher():
    """Create new receipt voucher"""
    data = request.get_json()
    
    required_fields = ['payer', 'amount']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Generate voucher number
    voucher_number = f"RV-{datetime.utcnow().strftime('%Y%m%d')}-{ReceiptVoucher.query.count() + 1:04d}"
    
    voucher = ReceiptVoucher(
        voucher_number=voucher_number,
        voucher_date=datetime.utcnow(),
        payer=data['payer'],
        payment_method=data.get('payment_method', 'CASH'),
        amount=data['amount'],
        currency=data.get('currency', 'IDR'),
        description=data.get('description'),
        reference=data.get('reference'),
        bank_account_id=data.get('bank_account_id'),
        cash_account_id=data.get('cash_account_id'),
        customer_id=data.get('customer_id'),
        status='DRAFT'
    )
    voucher.save()
    
    # Add voucher lines
    if data.get('lines'):
        for line_data in data['lines']:
            line = ReceiptVoucherLine(
                voucher_id=voucher.id,
                account_id=line_data.get('account_id'),
                description=line_data.get('description'),
                amount=line_data.get('amount', 0)
            )
            line.save()
    
    return jsonify({
        'message': 'Receipt voucher created successfully',
        'receipt_voucher': voucher.to_dict()
    }), 201


@cash_bp.route('/receipt-vouchers/<int:voucher_id>/post', methods=['POST'])
@jwt_required()
def post_receipt_voucher(voucher_id):
    """Post receipt voucher"""
    voucher = ReceiptVoucher.query.get_or_404(voucher_id)
    
    if voucher.status == 'POSTED':
        return jsonify({'error': 'Voucher already posted'}), 400
    
    voucher.status = 'POSTED'
    voucher.save()
    
    # Update bank/cash account balance
    if voucher.bank_account_id:
        account = BankAccount.query.get(voucher.bank_account_id)
        if account:
            account.balance += voucher.amount
            account.save()
    elif voucher.cash_account_id:
        account = CashAccount.query.get(voucher.cash_account_id)
        if account:
            account.balance += voucher.amount
            account.save()
    
    return jsonify({'message': 'Receipt voucher posted successfully'}), 200
