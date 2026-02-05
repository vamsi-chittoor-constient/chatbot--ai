#!/bin/sh
# =============================================================================
# Auto-generate self-signed SSL certificate for nginx
# =============================================================================

SSL_DIR="/etc/nginx/ssl"
CERT_FILE="$SSL_DIR/nginx-selfsigned.crt"
KEY_FILE="$SSL_DIR/nginx-selfsigned.key"

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

# Generate certificate only if it doesn't exist
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "Generating self-signed SSL certificate..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "/C=US/ST=State/L=City/O=Restaurant/CN=restaurant-ai" \
        2>/dev/null

    # Set proper permissions
    chmod 600 "$KEY_FILE"
    chmod 644 "$CERT_FILE"

    echo "SSL certificate generated successfully"
else
    echo "SSL certificate already exists, skipping generation"
fi
