# ERP System - Backend Application

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials and settings
```

### 3. Initialize Database

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 4. Run Development Server

```bash
flask run
```

The API will be available at `http://localhost:5000/api/v1/`

## Project Structure

```
backend/
├── app/
│   ├── __init__.py           # Application factory
│   ├── modules/              # Business modules (Odoo-style)
│   │   ├── admin/            # User & role management
│   │   ├── inventory/        # Products, stock, warehouses
│   │   ├── purchase/         # Purchase orders, vendors
│   │   ├── cash/             # Cash transactions
│   │   ├── ap/               # Accounts Payable
│   │   ├── ar/               # Accounts Receivable
│   │   ├── production/       # Manufacturing, BoM
│   │   ├── costing/          # Cost calculations
│   │   ├── accounting/       # General ledger, reports
│   │   └── fixed_asset/      # Asset management
│   ├── models/               # SQLAlchemy models
│   ├── routes/               # API endpoints
│   ├── services/             # Business logic layer
│   └── utils/                # Helper functions
├── config/
│   └── settings.py           # Configuration classes
├── migrations/               # Database migrations
├── tests/                    # Test cases
├── requirements.txt          # Python dependencies
└── .env.example              # Environment template
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/change-password` - Change password

### Admin
- `GET /api/v1/admin/users` - List users
- `POST /api/v1/admin/users` - Create user
- `PUT /api/v1/admin/users/<id>` - Update user
- `DELETE /api/v1/admin/users/<id>` - Delete user
- `GET /api/v1/admin/roles` - List roles
- `POST /api/v1/admin/roles` - Create role
- `GET /api/v1/admin/audit-logs` - View audit logs

### Inventory
- `GET /api/v1/inventory/products` - List products
- `POST /api/v1/inventory/products` - Create product
- `GET /api/v1/inventory/stock` - View stock levels
- `POST /api/v1/inventory/stock-moves` - Record stock movement
- `GET /api/v1/inventory/warehouses` - List warehouses
- `GET /api/v1/inventory/low-stock-alerts` - Low stock warnings

## Default Roles

The system supports these default roles:
- **Super Admin** - Full system access
- **Admin** - Administrative access
- **Finance Officer** - Financial operations
- **Purchasing Officer** - Purchase management
- **Warehouse Staff** - Inventory operations
- **Production Manager** - Production planning
- **Accountant** - Accounting operations

## Database Schema

Core tables include:
- `users` - System users
- `roles` - User roles
- `products` - Product master data
- `warehouses` - Warehouse locations
- `stock_moves` - Stock transactions
- `vendors` - Supplier information
- `customers` - Customer information
- `journal_entries` - Accounting entries

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## Docker Deployment

```bash
# Build image
docker build -t erp-backend .

# Run container
docker run -p 5000:5000 --env-file .env erp-backend
```

## Next Steps

1. Set up database (MySQL 8.0+)
2. Configure `.env` file
3. Run migrations
4. Create initial admin user
5. Start developing additional modules

## License

Proprietary - All rights reserved
