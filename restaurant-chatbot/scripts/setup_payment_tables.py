"""
Setup Payment Tables - Aligned with A24 Schema
===============================================
Create payment-related tables matching the A24 dump schema.
These tables support mock payment flows for the chat agent.

Tables created:
- order_payment_method: Payment method types (card, upi, cash, wallet)
- payment_status_type: Payment statuses (pending, authorized, captured, failed, refunded)
- payment_gateway: Mock gateway configuration
- payment_order: Payment order records
- payment_transaction: Individual payment transactions
- order_payment: Links orders to payments

Run:
    python scripts/setup_payment_tables.py
"""

import sys
sys.path.insert(0, '.')


def create_tables():
    """Create payment tables matching A24 schema."""
    from app.core.db_pool import SyncDBConnection

    sql_statements = [
        # Enable uuid-ossp extension for uuid_generate_v4()
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"',

        # Create order_payment_method (payment method types)
        """
        CREATE TABLE IF NOT EXISTS order_payment_method (
            order_payment_method_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            order_payment_method_code VARCHAR(20),
            order_payment_method_name VARCHAR(255),
            order_payment_method_is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,

        # Create payment_status_type (payment status codes)
        """
        CREATE TABLE IF NOT EXISTS payment_status_type (
            payment_status_type_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            payment_status_code VARCHAR(20),
            payment_status_name VARCHAR(255),
            payment_status_description TEXT,
            payment_status_is_terminal BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,

        # Create payment_gateway (mock gateway config)
        """
        CREATE TABLE IF NOT EXISTS payment_gateway (
            payment_gateway_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            gateway_code VARCHAR(50),
            gateway_name VARCHAR(255),
            gateway_type VARCHAR(50),
            is_active BOOLEAN DEFAULT TRUE,
            is_sandbox BOOLEAN DEFAULT TRUE,
            sandbox_api_key TEXT,
            sandbox_api_secret TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,

        # Create payment_order (payment order records)
        """
        CREATE TABLE IF NOT EXISTS payment_order (
            payment_order_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            order_id UUID,
            restaurant_id VARCHAR(50),
            customer_id UUID,
            payment_gateway_id UUID REFERENCES payment_gateway(payment_gateway_id),
            gateway_order_id TEXT,
            amount NUMERIC(12,2),
            currency VARCHAR(3) DEFAULT 'INR',
            payment_status_type_id UUID REFERENCES payment_status_type(payment_status_type_id),
            attempts INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 3,
            expires_at TIMESTAMP WITH TIME ZONE,
            notes TEXT,
            receipt_number VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_payment_order_order ON payment_order(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_payment_order_gateway_order ON payment_order(gateway_order_id)",

        # Create payment_transaction (individual transactions)
        """
        CREATE TABLE IF NOT EXISTS payment_transaction (
            payment_transaction_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            payment_order_id UUID REFERENCES payment_order(payment_order_id),
            order_id UUID,
            restaurant_id VARCHAR(50),
            customer_id UUID,
            payment_gateway_id UUID REFERENCES payment_gateway(payment_gateway_id),
            gateway_payment_id TEXT,
            gateway_transaction_id TEXT,
            gateway_signature TEXT,
            order_payment_method_id UUID REFERENCES order_payment_method(order_payment_method_id),
            payment_method_details JSONB,
            transaction_amount NUMERIC(12,2),
            amount_paid NUMERIC(12,2),
            amount_due NUMERIC(12,2),
            transaction_currency VARCHAR(3) DEFAULT 'INR',
            gateway_fee NUMERIC(10,2),
            gateway_tax NUMERIC(10,2),
            net_amount NUMERIC(12,2),
            payment_status_type_id UUID REFERENCES payment_status_type(payment_status_type_id),
            failure_reason TEXT,
            failure_code VARCHAR(20),
            error_description TEXT,
            bank_name TEXT,
            card_network TEXT,
            card_type TEXT,
            card_last4 VARCHAR(4),
            wallet_provider TEXT,
            upi_vpa TEXT,
            customer_email TEXT,
            customer_contact TEXT,
            gateway_response JSONB,
            otp_verified BOOLEAN DEFAULT FALSE,
            otp_sent_at TIMESTAMP WITH TIME ZONE,
            otp_verified_at TIMESTAMP WITH TIME ZONE,
            attempted_at TIMESTAMP WITH TIME ZONE,
            authorized_at TIMESTAMP WITH TIME ZONE,
            captured_at TIMESTAMP WITH TIME ZONE,
            settled_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_payment_transaction_order ON payment_transaction(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_payment_transaction_payment_order ON payment_transaction(payment_order_id)",
        "CREATE INDEX IF NOT EXISTS idx_payment_transaction_gateway ON payment_transaction(gateway_payment_id)",

        # Create order_payment (links orders to payments)
        """
        CREATE TABLE IF NOT EXISTS order_payment (
            order_payment_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            payment_order_id UUID REFERENCES payment_order(payment_order_id),
            primary_transaction_id UUID REFERENCES payment_transaction(payment_transaction_id),
            order_id UUID,
            order_payment_method_id UUID REFERENCES order_payment_method(order_payment_method_id),
            paid_amount NUMERIC(12,2),
            refund_amount NUMERIC(12,2),
            wallet_amount_used NUMERIC(10,2) DEFAULT 0,
            loyalty_points_used INTEGER DEFAULT 0,
            loyalty_points_earned INTEGER DEFAULT 0,
            collect_cash BOOLEAN DEFAULT FALSE,
            order_payment_status VARCHAR(20),
            order_payment_transaction_reference VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_order_payment_order ON order_payment(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_order_payment_payment_order ON order_payment(payment_order_id)",

        # Add payment_status column to orders table if not exists
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'orders' AND column_name = 'payment_status'
            ) THEN
                ALTER TABLE orders ADD COLUMN payment_status VARCHAR(20) DEFAULT 'pending';
            END IF;
        END $$;
        """,

        # Add payment_order_id to orders if not exists
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'orders' AND column_name = 'payment_order_id'
            ) THEN
                ALTER TABLE orders ADD COLUMN payment_order_id UUID;
            END IF;
        END $$;
        """,
    ]

    print("Creating payment tables (A24 schema)...")

    with SyncDBConnection() as conn:
        with conn.cursor() as cursor:
            for sql in sql_statements:
                try:
                    cursor.execute(sql)
                    conn.commit()
                except Exception as e:
                    print(f"Warning: {e}")
                    conn.rollback()

    print("[DONE] Payment tables created successfully")


def seed_lookup_tables():
    """Seed payment lookup tables with default values."""
    from app.core.db_pool import SyncDBConnection
    from psycopg2.extras import RealDictCursor

    print("\nSeeding payment lookup tables...")

    with SyncDBConnection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Seed order_payment_method
            payment_methods = [
                ('card', 'Credit/Debit Card'),
                ('upi', 'UPI'),
                ('cash', 'Cash'),
                ('wallet', 'Digital Wallet'),
                ('netbanking', 'Net Banking'),
            ]
            for code, name in payment_methods:
                cursor.execute("""
                    INSERT INTO order_payment_method (order_payment_method_code, order_payment_method_name)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (code, name))

            # Seed payment_status_type
            payment_statuses = [
                ('pending', 'Pending', 'Payment initiated, awaiting user action', False),
                ('awaiting_otp', 'Awaiting OTP', 'OTP sent, waiting for verification', False),
                ('otp_verified', 'OTP Verified', 'OTP verified, processing payment', False),
                ('authorized', 'Authorized', 'Payment authorized by bank', False),
                ('captured', 'Captured', 'Payment successfully captured', True),
                ('failed', 'Failed', 'Payment failed', True),
                ('cancelled', 'Cancelled', 'Payment cancelled by user', True),
                ('refunded', 'Refunded', 'Payment refunded', True),
                ('partially_refunded', 'Partially Refunded', 'Payment partially refunded', False),
            ]
            for code, name, desc, is_terminal in payment_statuses:
                cursor.execute("""
                    INSERT INTO payment_status_type (
                        payment_status_code, payment_status_name,
                        payment_status_description, payment_status_is_terminal
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (code, name, desc, is_terminal))

            # Seed payment_gateway (mock gateway)
            cursor.execute("""
                INSERT INTO payment_gateway (
                    gateway_code, gateway_name, gateway_type, is_active, is_sandbox
                )
                VALUES ('mock_gateway', 'Mock Payment Gateway', 'mock', TRUE, TRUE)
                ON CONFLICT DO NOTHING
            """)

            conn.commit()

    print("  [DONE] Payment lookup tables seeded")


def verify():
    """Verify the payment tables were created."""
    from app.core.db_pool import SyncDBConnection
    from psycopg2.extras import RealDictCursor

    print("\nVerifying payment tables...")

    with SyncDBConnection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check each table
            tables = [
                'order_payment_method',
                'payment_status_type',
                'payment_gateway',
                'payment_order',
                'payment_transaction',
                'order_payment',
            ]

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"  {table}: {count} rows")

            # Show payment methods
            print("\n  Payment methods:")
            cursor.execute("SELECT order_payment_method_code, order_payment_method_name FROM order_payment_method")
            for row in cursor.fetchall():
                print(f"    - {row['order_payment_method_code']}: {row['order_payment_method_name']}")

            # Show payment statuses
            print("\n  Payment statuses:")
            cursor.execute("SELECT payment_status_code, payment_status_name FROM payment_status_type")
            for row in cursor.fetchall():
                print(f"    - {row['payment_status_code']}: {row['payment_status_name']}")

            # Show gateways
            print("\n  Payment gateways:")
            cursor.execute("SELECT gateway_code, gateway_name, is_sandbox FROM payment_gateway")
            for row in cursor.fetchall():
                sandbox = "(sandbox)" if row['is_sandbox'] else "(live)"
                print(f"    - {row['gateway_code']}: {row['gateway_name']} {sandbox}")


if __name__ == "__main__":
    create_tables()
    seed_lookup_tables()
    verify()
    print("\n[SUCCESS] Payment tables ready (A24 schema)!")
    print("\nMock payment flow:")
    print("  1. Checkout creates order with payment_status='pending'")
    print("  2. initiate_payment creates payment_order and returns payment form")
    print("  3. User enters card details (via AG-UI form in chat)")
    print("  4. verify_otp validates mock OTP (always '123456' in sandbox)")
    print("  5. process_payment captures payment and updates order status")
