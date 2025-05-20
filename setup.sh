#!/bin/bash

# Check OpenSSL installation
if ! command -v openssl &> /dev/null; then
    echo "OpenSSL is not installed. Please install it first."
    exit 1
fi

# Get host IP address (excluding loopback)
HOST_IP=$(ip route get 1 | awk '{print $7; exit}')
if [ -z "$HOST_IP" ]; then
    echo "Failed to detect host IP address."
    exit 1
fi
echo "Detected host IP: $HOST_IP"

# Create directories
mkdir -p ssl data

# Generate security tokens
CONFIG_TOKEN=$(openssl rand -hex 32)
COOKIE_SECRET=$(openssl rand -hex 32)

# Create environment file
echo "CONFIGPROXY_AUTH_TOKEN=$CONFIG_TOKEN" > .env
echo "JUPYTERHUB_COOKIE_SECRET=$COOKIE_SECRET" >> .env

# Generate SSL certificates
if [ ! -f ssl/jupyterhub.key ] || [ ! -f ssl/jupyterhub.crt ]; then
    echo "Generating SSL certificates..."
    
    # Create OpenSSL configuration with detected IP
    cat > ssl/openssl.cnf <<EOL
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = VN
ST = HCM
L = HCM
O = OCB
OU = RRKTS
CN = $HOST_IP

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = jupyterhub
DNS.3 = $HOST_IP
IP.1 = 127.0.0.1
IP.2 = $HOST_IP
EOL
    
    # Generate certificate and key
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -config ssl/openssl.cnf \
      -keyout ssl/jupyterhub.key -out ssl/jupyterhub.crt
    
    # Set permissions
    chmod 600 ssl/jupyterhub.key
    chmod 644 ssl/jupyterhub.crt
fi

# Build and start services
echo "Building images and starting services..."
docker compose up -d

echo "JupyterHub is now running!"
echo "Access via HTTPS at: https://$HOST_IP:7443/"
