#!/bin/bash

# Check if OpenSSL is installed
if ! command -v openssl &> /dev/null; then
    echo "OpenSSL is not installed. Please install it first."
    exit 1
fi

# Create directories
mkdir -p ssl data

# Generate random tokens for security
CONFIG_TOKEN=$(openssl rand -hex 32)
COOKIE_SECRET=$(openssl rand -hex 32)

# Create .env file with these tokens
echo "CONFIGPROXY_AUTH_TOKEN=$CONFIG_TOKEN" > .env
echo "JUPYTERHUB_COOKIE_SECRET=$COOKIE_SECRET" >> .env

# Generate SSL certificates if they don't exist
if [ ! -f ssl/jupyterhub.key ] || [ ! -f ssl/jupyterhub.crt ]; then
    echo "Generating SSL certificates..."
    
    # Create OpenSSL config if it doesn't exist
    if [ ! -f ssl/openssl.cnf ]; then
        cat > ssl/openssl.cnf <<EOL
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = YourState
L = YourCity
O = YourOrganization
OU = YourOrganizationalUnit
CN = 34.173.62.66

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = jupyterhub
DNS.3 = 34.173.62.66
IP.1 = 127.0.0.1
IP.2 = 10.128.15.218
IP.3 = 34.173.62.66
EOL
    fi
    
    # Generate certificate and key
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -config ssl/openssl.cnf \
      -keyout ssl/jupyterhub.key -out ssl/jupyterhub.crt
    
    # Set permissions
    chmod 600 ssl/jupyterhub.key
    chmod 644 ssl/jupyterhub.crt
fi

# Create users list if it doesn't exist
if [ ! -f userlist ]; then
    echo "Creating default userlist with admin user..."
    echo "admin admin" > userlist
fi

# Build and start the services
echo "Building images and starting services..."
docker compose up -d

echo "JupyterHub is now running!"
echo "Access via HTTPS at: https://localhost/"
echo "First time setup: Go to https://localhost/hub/signup to create the admin account"
echo ""
echo "IMPORTANT: Since we're using self-signed certificates, you'll need to accept"
echo "the security warning in your browser when you first connect."
