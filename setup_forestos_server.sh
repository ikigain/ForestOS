#!/bin/bash
# ForestOS Backend - Production VPS Setup Script
# This script automates complete deployment on a fresh AliCloud Ubuntu 22.04 VPS
# Version: Phase 1.3 - Production Deployment
# Repository: https://github.com/ikigain/ForestOS.git

set -e  # Exit on error

# Configuration variables
GITHUB_REPO="https://github.com/ikigain/ForestOS.git"
APP_DIR="/var/www/forestos"
DB_NAME="forestos"
DB_USER="forestos"
DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -base64 32)}"  # Generate random password if not provided
DOMAIN="${DOMAIN:-}"  # Set via environment variable: DOMAIN=api.forestos.com
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@forestos.com}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "ForestOS Backend - Production VPS Setup"
echo "Phase 1.3 - Complete Deployment Automation"
echo "=============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}ERROR: Please run as root (use sudo)${NC}"
    exit 1
fi

# Check Ubuntu version
echo -e "${GREEN}[1/15] Checking system requirements...${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        echo -e "${YELLOW}Warning: This script is designed for Ubuntu. Detected: $ID${NC}"
    fi
    echo "  ✓ Operating System: $PRETTY_NAME"
fi

# Check if Python 3.11 is already installed FIRST (before any apt operations)
echo -e "${GREEN}[2/15] Checking Python 3.11 installation...${NC}"
PYTHON_311_EXISTS=false
if command -v python3.11 &> /dev/null; then
    echo "  ✓ Python 3.11 already installed"
    PYTHON_311_EXISTS=true
else
    echo "  ℹ Python 3.11 not found, will install from PPA"
fi

# Update system packages
echo -e "${GREEN}[3/15] Updating system packages...${NC}"
apt update
apt upgrade -y

# Install system dependencies
echo -e "${GREEN}[4/15] Installing system dependencies...${NC}"
apt install -y \
    git \
    curl \
    wget \
    build-essential \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release

# Install Python 3.11 based on earlier check
echo -e "${GREEN}[5/15] Installing Python 3.11...${NC}"
if [ "$PYTHON_311_EXISTS" = true ]; then
    echo "  ✓ Skipping PPA setup (Python 3.11 already installed)"
    # Only install supporting packages, not python3.11 itself
    apt install -y \
        python3.11-venv \
        python3.11-dev \
        python3-pip 2>/dev/null || echo "  ℹ Some packages may already be installed"
else
    # Add PPA and install Python 3.11
    echo "  Installing Python 3.11 from deadsnakes PPA..."
    add-apt-repository -y ppa:deadsnakes/ppa
    apt update
    apt install -y \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3-pip
fi

# Set Python 3.11 as default (only if not already set)
if ! python3 --version | grep -q "3.11"; then
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
fi
echo "  ✓ Python version: $(python3 --version)"

# Install PostgreSQL server
echo -e "${GREEN}[6/15] Installing PostgreSQL server...${NC}"
apt install -y postgresql postgresql-contrib
systemctl start postgresql
systemctl enable postgresql
echo "  ✓ PostgreSQL server installed and running"

# Create database and user
echo "  Creating ForestOS database..."
sudo -u postgres psql -c "CREATE USER forestos_user WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "  ℹ User already exists"
sudo -u postgres psql -c "CREATE DATABASE forestos OWNER forestos_user;" 2>/dev/null || echo "  ℹ Database already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE forestos TO forestos_user;" 2>/dev/null
echo "  ✓ Database and user created"

# Install Redis
echo -e "${GREEN}[7/15] Installing Redis...${NC}"
apt install -y redis-server
systemctl start redis-server
systemctl enable redis-server
echo "  ✓ Redis server installed and running"

# Install Nginx
echo -e "${GREEN}[8/15] Installing Nginx...${NC}"
apt install -y nginx
systemctl start nginx
systemctl enable nginx
echo "  ✓ Nginx installed and running"

# Install Supervisor (process manager)
echo -e "${GREEN}[9/15] Installing Supervisor...${NC}"
apt install -y supervisor
systemctl start supervisor
systemctl enable supervisor
echo "  ✓ Supervisor installed and running"

# Install Certbot (Let's Encrypt SSL)
echo -e "${GREEN}[10/15] Installing Certbot for SSL...${NC}"
apt install -y certbot python3-certbot-nginx
echo "  ✓ Certbot installed"

# Clone ForestOS repository
echo -e "${GREEN}[11/15] Cloning ForestOS from GitHub...${NC}"
if [ -d "$APP_DIR" ]; then
    echo "  ⚠ Directory $APP_DIR exists. Backing up..."
    mv "$APP_DIR" "${APP_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
fi
git clone "$GITHUB_REPO" "$APP_DIR"
cd "$APP_DIR"
echo "  ✓ Repository cloned to $APP_DIR"

# Create Python virtual environment
echo -e "${GREEN}[12/15] Setting up Python virtual environment...${NC}"
cd "$APP_DIR/Server"
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
echo "  ✓ Virtual environment created"

# Install Python dependencies
echo "  Installing Python packages..."
pip install -r requirements.txt
echo "  ✓ All Python dependencies installed"

# Create directories
echo -e "${GREEN}[13/15] Creating application directories...${NC}"
mkdir -p "$APP_DIR/images/plants"
mkdir -p "$APP_DIR/logs"
mkdir -p /var/log/forestos
echo "  ✓ Directories created"

# Generate .env file
echo -e "${GREEN}[14/15] Generating configuration files...${NC}"
cat > "$APP_DIR/Server/.env" << EOF
# ForestOS Backend Configuration
# Generated: $(date)

# Database Configuration (Local PostgreSQL)
DATABASE_URL=postgresql://forestos_user:$DB_PASSWORD@localhost:5432/forestos
ASYNC_DATABASE_URL=postgresql+asyncpg://forestos_user:$DB_PASSWORD@localhost:5432/forestos

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Perenual API (Get from https://perenual.com/docs/api)
PERENUAL_API_KEY=your-api-key-here

# Image Storage
IMAGE_BASE_PATH=$APP_DIR/images/plants
IMAGE_BASE_URL=https://${DOMAIN:-api.forestos.com}/images/plants

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:19006","https://forestos.com"]

# Environment
ENVIRONMENT=production
DEBUG=False

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EOF

echo "  ✓ Configuration file created at $APP_DIR/Server/.env"
echo "  ⚠ IMPORTANT: Edit .env file with your actual credentials!"

# Set permissions
echo "  Setting permissions..."
chown -R www-data:www-data "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod 600 "$APP_DIR/Server/.env"
echo "  ✓ Permissions configured"

# Configure Supervisor
echo -e "${GREEN}[15/15] Configuring Supervisor for process management...${NC}"
cat > /etc/supervisor/conf.d/forestos.conf << EOF
[program:forestos-api]
command=$APP_DIR/Server/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
directory=$APP_DIR/Server
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/forestos/api.err.log
stdout_logfile=/var/log/forestos/api.out.log
environment=PATH="$APP_DIR/Server/venv/bin"

[program:forestos-celery]
command=$APP_DIR/Server/venv/bin/celery -A app.core.celery_app worker -l info
directory=$APP_DIR/Server
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/forestos/celery.err.log
stdout_logfile=/var/log/forestos/celery.out.log
environment=PATH="$APP_DIR/Server/venv/bin"
EOF

supervisorctl reread
supervisorctl update
echo "  ✓ Supervisor configured"

# Configure Nginx
echo -e "${GREEN}[16/16] Configuring Nginx reverse proxy...${NC}"
cat > /etc/nginx/sites-available/forestos << 'EOF'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;

    # Serve static images
    location /images/ {
        alias /var/www/forestos/images/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin *;
    }

    # API endpoints
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Increase upload size
    client_max_body_size 10M;
}
EOF

# Replace domain placeholder
if [ -n "$DOMAIN" ]; then
    sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /etc/nginx/sites-available/forestos
else
    sed -i "s/DOMAIN_PLACEHOLDER/_/g" /etc/nginx/sites-available/forestos
fi

# Enable Nginx site
ln -sf /etc/nginx/sites-available/forestos /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
echo "  ✓ Nginx configured"

# Print completion message
echo ""
echo "=============================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=============================================="
echo ""
echo "Summary:"
echo "  ✓ Python 3.11 installed"
echo "  ✓ PostgreSQL client installed"
echo "  ✓ Redis server running"
echo "  ✓ Nginx configured as reverse proxy"
echo "  ✓ Supervisor managing processes"
echo "  ✓ ForestOS cloned from GitHub"
echo "  ✓ Python dependencies installed"
echo "  ✓ Configuration files generated"
echo ""
echo "=============================================="
echo "IMPORTANT: Next Steps"
echo "=============================================="
echo ""
echo "1. Database Configuration:"
echo "   ✓ PostgreSQL installed locally"
echo "   ✓ Database 'forestos' created"
echo "   ✓ User 'forestos_user' created"
echo "   ✓ Password: $DB_PASSWORD"
echo "   (Password saved in .env file)"
echo ""
echo "2. Get Perenual API Key:"
echo "   - Visit: https://perenual.com/docs/api"
echo "   - Update PERENUAL_API_KEY in .env"
echo ""
echo "3. Run Database Migrations:"
echo "   cd $APP_DIR/Server"
echo "   source venv/bin/activate"
echo "   alembic upgrade head"
echo ""
echo "4. Populate Initial Plant Data (optional):"
echo "   cd $APP_DIR/Server"
echo "   source venv/bin/activate"
echo "   python scripts/seed_plants.py"
echo ""
echo "5. Start Services:"
echo "   supervisorctl start forestos-api"
echo "   supervisorctl start forestos-celery"
echo ""
if [ -n "$DOMAIN" ]; then
echo "6. Configure SSL Certificate:"
echo "   certbot --nginx -d $DOMAIN --email $ADMIN_EMAIL --agree-tos --non-interactive"
echo ""
echo "7. Test API:"
echo "   curl https://$DOMAIN/docs"
else
echo "6. Configure SSL Certificate (when domain is ready):"
echo "   export DOMAIN=api.forestos.com"
echo "   certbot --nginx -d \$DOMAIN --email $ADMIN_EMAIL --agree-tos"
echo ""
echo "7. Test API:"
echo "   curl http://YOUR_SERVER_IP/docs"
fi
echo ""
echo "=============================================="
echo "Database Information"
echo "=============================================="
echo ""
echo "Database: forestos"
echo "User: forestos_user"
echo "Password: $DB_PASSWORD"
echo "Host: localhost"
echo "Port: 5432"
echo "Connection String: postgresql://forestos_user:$DB_PASSWORD@localhost:5432/forestos"
echo ""
echo "⚠️  IMPORTANT: Save the database password!"
echo ""
echo "=============================================="
echo "Useful Commands"
echo "=============================================="
echo ""
echo "View API logs:"
echo "  tail -f /var/log/forestos/api.out.log"
echo "  tail -f /var/log/forestos/api.err.log"
echo ""
echo "Restart services:"
echo "  supervisorctl restart forestos-api"
echo "  supervisorctl restart forestos-celery"
echo ""
echo "Check service status:"
echo "  supervisorctl status"
echo ""
echo "Update code from GitHub:"
echo "  cd $APP_DIR && git pull"
echo "  supervisorctl restart all"
echo ""
echo "=============================================="
echo ""
echo -e "${GREEN}Setup script completed successfully!${NC}"
echo ""
