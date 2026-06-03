"""
Cash module models - Cash Transactions, Bank Accounts, Payment Vouchers
"""

from app import db
from app.models.base import BaseModel


class BankAccount(BaseModel):
    """Bank account master data"""
    
    __tablename__ = 'bank_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    bank_name = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    account_type = db.Column(db.String(50))  # CHECKING, SAVINGS, DEPOSIT
    currency = db.Column(db.String(10), default='IDR')
    balance = db.Column(db.Numeric(14, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    transactions = db.relationship('CashTransaction', backref='bank_account', lazy='dynamic')
    
    def __repr__(self):
        return f'<BankAccount {self.code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'account_type': self.account_type,
            'currency': self.currency,
            'balance': float(self.balance) if self.balance else 0,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CashTransaction(BaseModel):
    """Cash/Bank transaction record"""
    
    __tablename__ = 'cash_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    transaction_date = db.Column(db.DateTime, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # RECEIPT, PAYMENT, TRANSFER, JOURNAL_ENTRY
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    currency = db.Column(db.String(10), default='IDR')
    description = db.Column(db.Text)
    reference = db.Column(db.String(100))  # Check number, invoice number, etc.
    status = db.Column(db.String(20), default='DRAFT')  # DRAFT, POSTED, CANCELLED
    
    # Account references
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'))
    cash_account_id = db.Column(db.Integer, db.ForeignKey('cash_accounts.id'))
    
    # Related documents
    partner_type = db.Column(db.String(20))  # CUSTOMER, SUPPLIER, EMPLOYEE, OTHER
    partner_id = db.Column(db.Integer)  # ID of customer/supplier/employee
    
    # Relationships
    lines = db.relationship('CashTransactionLine', backref='transaction', lazy='dynamic')
    
    def __repr__(self):
        return f'<CashTransaction {self.transaction_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_number': self.transaction_number,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'transaction_type': self.transaction_type,
            'amount': float(self.amount) if self.amount else 0,
            'currency': self.currency,
            'description': self.description,
            'reference': self.reference,
            'status': self.status,
            'bank_account_id': self.bank_account_id,
            'bank_account': self.bank_account.to_dict() if self.bank_account else None,
            'cash_account_id': self.cash_account_id,
            'partner_type': self.partner_type,
            'partner_id': self.partner_id,
            'lines': [line.to_dict() for line in self.lines],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CashTransactionLine(BaseModel):
    """Individual lines in cash transaction"""
    
    __tablename__ = 'cash_transaction_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('cash_transactions.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'))
    description = db.Column(db.String(255))
    debit_amount = db.Column(db.Numeric(14, 2), default=0)
    credit_amount = db.Column(db.Numeric(14, 2), default=0)
    
    # Relationships
    account = db.relationship('ChartOfAccount', backref='transaction_lines')
    
    def __repr__(self):
        return f'<CashTransactionLine Transaction:{self.transaction_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'account_id': self.account_id,
            'account': self.account.to_dict() if self.account else None,
            'description': self.description,
            'debit_amount': float(self.debit_amount) if self.debit_amount else 0,
            'credit_amount': float(self.credit_amount) if self.credit_amount else 0
        }


class CashAccount(BaseModel):
    """Petty cash account"""
    
    __tablename__ = 'cash_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    currency = db.Column(db.String(10), default='IDR')
    balance = db.Column(db.Numeric(14, 2), default=0)
    max_balance = db.Column(db.Numeric(14, 2))  # Maximum petty cash limit
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    transactions = db.relationship('CashTransaction', backref='cash_account', lazy='dynamic')
    
    def __repr__(self):
        return f'<CashAccount {self.code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'currency': self.currency,
            'balance': float(self.balance) if self.balance else 0,
            'max_balance': float(self.max_balance) if self.max_balance else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PaymentVoucher(BaseModel):
    """Payment voucher for outgoing payments"""
    
    __tablename__ = 'payment_vouchers'
    
    id = db.Column(db.Integer, primary_key=True)
    voucher_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    voucher_date = db.Column(db.DateTime, nullable=False)
    payee = db.Column(db.String(200), nullable=False)  # Who receives the payment
    payment_method = db.Column(db.String(50))  # CASH, CHECK, BANK_TRANSFER
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    currency = db.Column(db.String(10), default='IDR')
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='DRAFT')  # DRAFT, APPROVED, PAID, CANCELLED
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    paid_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    paid_at = db.Column(db.DateTime)
    
    # References
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'))
    cash_account_id = db.Column(db.Integer, db.ForeignKey('cash_accounts.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'))
    
    # Relationships
    lines = db.relationship('PaymentVoucherLine', backref='voucher', lazy='dynamic')
    
    def __repr__(self):
        return f'<PaymentVoucher {self.voucher_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'voucher_number': self.voucher_number,
            'voucher_date': self.voucher_date.isoformat() if self.voucher_date else None,
            'payee': self.payee,
            'payment_method': self.payment_method,
            'amount': float(self.amount) if self.amount else 0,
            'currency': self.currency,
            'description': self.description,
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'paid_by': self.paid_by,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'bank_account_id': self.bank_account_id,
            'cash_account_id': self.cash_account_id,
            'supplier_id': self.supplier_id,
            'purchase_order_id': self.purchase_order_id,
            'lines': [line.to_dict() for line in self.lines],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PaymentVoucherLine(BaseModel):
    """Individual lines in payment voucher"""
    
    __tablename__ = 'payment_voucher_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('payment_vouchers.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'))
    description = db.Column(db.String(255))
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    
    # Relationships
    account = db.relationship('ChartOfAccount', backref='payment_voucher_lines')
    
    def __repr__(self):
        return f'<PaymentVoucherLine Voucher:{self.voucher_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'voucher_id': self.voucher_id,
            'account_id': self.account_id,
            'account': self.account.to_dict() if self.account else None,
            'description': self.description,
            'amount': float(self.amount) if self.amount else 0
        }


class ReceiptVoucher(BaseModel):
    """Receipt voucher for incoming payments"""
    
    __tablename__ = 'receipt_vouchers'
    
    id = db.Column(db.Integer, primary_key=True)
    voucher_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    voucher_date = db.Column(db.DateTime, nullable=False)
    payer = db.Column(db.String(200), nullable=False)  # Who makes the payment
    payment_method = db.Column(db.String(50))  # CASH, CHECK, BANK_TRANSFER
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    currency = db.Column(db.String(10), default='IDR')
    description = db.Column(db.Text)
    reference = db.Column(db.String(100))  # Check number, etc.
    status = db.Column(db.String(20), default='DRAFT')  # DRAFT, POSTED, CANCELLED
    
    # References
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'))
    cash_account_id = db.Column(db.Integer, db.ForeignKey('cash_accounts.id'))
    customer_id = db.Column(db.Integer)  # Could link to AR module
    sales_order_id = db.Column(db.Integer)  # Could link to SO
    
    # Relationships
    lines = db.relationship('ReceiptVoucherLine', backref='voucher', lazy='dynamic')
    
    def __repr__(self):
        return f'<ReceiptVoucher {self.voucher_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'voucher_number': self.voucher_number,
            'voucher_date': self.voucher_date.isoformat() if self.voucher_date else None,
            'payer': self.payer,
            'payment_method': self.payment_method,
            'amount': float(self.amount) if self.amount else 0,
            'currency': self.currency,
            'description': self.description,
            'reference': self.reference,
            'status': self.status,
            'bank_account_id': self.bank_account_id,
            'cash_account_id': self.cash_account_id,
            'customer_id': self.customer_id,
            'sales_order_id': self.sales_order_id,
            'lines': [line.to_dict() for line in self.lines],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ReceiptVoucherLine(BaseModel):
    """Individual lines in receipt voucher"""
    
    __tablename__ = 'receipt_voucher_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('receipt_vouchers.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'))
    description = db.Column(db.String(255))
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    
    # Relationships
    account = db.relationship('ChartOfAccount', backref='receipt_voucher_lines')
    
    def __repr__(self):
        return f'<ReceiptVoucherLine Voucher:{self.voucher_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'voucher_id': self.voucher_id,
            'account_id': self.account_id,
            'account': self.account.to_dict() if self.account else None,
            'description': self.description,
            'amount': float(self.amount) if self.amount else 0
        }
