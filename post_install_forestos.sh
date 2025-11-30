#!/bin/bash
# ForestOS Backend - Post-Installation Automation Script
# Run this script AFTER setup_forestos_server.sh completes successfully
# This script handles database migrations, data seeding, and service startup

set -e  # Exit on error

# Configuration
APP_DIR="/var/www/forestos"
VENV_PATH="$APP_DIR/Server/venv"
SERVER_DIR="$APP_DIR/Server"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=============================================="
echo "ForestOS Backend - Post-Installation Setup"
echo "Completing database and service configuration"
echo "=============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}ERROR: Please run as root (use sudo)${NC}"
    exit 1
fi

# Check if setup script was run
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}ERROR: ForestOS not found at $APP_DIR${NC}"
    echo "Please run setup_forestos_server.sh first"
    exit 1
fi

# Check if .env file exists
if [ ! -f "$SERVER_DIR/.env" ]; then
    echo -e "${RED}ERROR: .env file not found at $SERVER_DIR/.env${NC}"
    echo "Please ensure setup_forestos_server.sh completed successfully"
    exit 1
fi

# Step 1: Prompt for Perenual API key
echo -e "${BLUE}[1/7] Configuring Perenual API key...${NC}"
echo ""
echo "Get your free API key from: https://perenual.com/docs/api"
echo ""
read -p "Enter your Perenual API key (or press Enter to skip): " PERENUAL_KEY

if [ -n "$PERENUAL_KEY" ]; then
    sed -i "s/PERENUAL_API_KEY=.*/PERENUAL_API_KEY=$PERENUAL_KEY/" "$SERVER_DIR/.env"
    echo -e "  ${GREEN}✓ Perenual API key configured${NC}"
else
    echo -e "  ${YELLOW}⚠ Skipped - You can add it later by editing $SERVER_DIR/.env${NC}"
fi
echo ""

# Step 2: Check database connection
echo -e "${BLUE}[2/7] Verifying database connection...${NC}"
cd "$SERVER_DIR"
source "$VENV_PATH/bin/activate"

# Extract database connection details from .env
DB_URL=$(grep "^DATABASE_URL=" .env | cut -d '=' -f2)
if [ -z "$DB_URL" ]; then
    echo -e "  ${RED}✗ Could not find DATABASE_URL in .env${NC}"
    exit 1
fi

# Test connection using Python
python3 << EOF
import sys
from sqlalchemy import create_engine
try:
    engine = create_engine("$DB_URL")
    with engine.connect() as conn:
        print("  ✓ Database connection successful")
        sys.exit(0)
except Exception as e:
    print(f"  ✗ Database connection failed: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}Database connection failed. Please check your DATABASE_URL in .env${NC}"
    exit 1
fi
echo ""

# Step 3: Run database migrations
echo -e "${BLUE}[3/7] Running database migrations...${NC}"
cd "$SERVER_DIR"
source "$VENV_PATH/bin/activate"

# Check if alembic is configured
if [ ! -f "../alembic.ini" ]; then
    echo -e "  ${RED}✗ alembic.ini not found${NC}"
    exit 1
fi

# Run migrations
cd ..
alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✓ Database migrations completed successfully${NC}"
else
    echo -e "  ${RED}✗ Database migrations failed${NC}"
    exit 1
fi
echo ""

# Step 4: Seed initial plant data (optional)
echo -e "${BLUE}[4/7] Seeding initial plant data...${NC}"
read -p "Do you want to seed the plant database with sample data? (y/n): " SEED_DATA

if [[ "$SEED_DATA" =~ ^[Yy]$ ]]; then
    cd "$SERVER_DIR"
    source "$VENV_PATH/bin/activate"
    
    # Check if seed script exists
    if [ -f "scripts/seed_plants.py" ]; then
        python scripts/seed_plants.py
        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✓ Plant data seeded successfully${NC}"
        else
            echo -e "  ${YELLOW}⚠ Seeding had some issues, but continuing...${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠ Seed script not found, skipping...${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Skipped - You can seed data later${NC}"
fi
echo ""

# Step 5: Start Supervisor services
echo -e "${BLUE}[5/7] Starting ForestOS services...${NC}"

# Stop services if running
supervisorctl stop forestos-api forestos-celery 2>/dev/null || true

# Start services
supervisorctl start forestos-api
if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✓ API service started${NC}"
else
    echo -e "  ${RED}✗ Failed to start API service${NC}"
fi

supervisorctl start forestos-celery
if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✓ Celery worker started${NC}"
else
    echo -e "  ${RED}✗ Failed to start Celery worker${NC}"
fi
echo ""

# Step 6: Wait and verify services
echo -e "${BLUE}[6/7] Verifying services are running...${NC}"
sleep 5

# Check service status
API_STATUS=$(supervisorctl status forestos-api | grep -o "RUNNING" || echo "STOPPED")
CELERY_STATUS=$(supervisorctl status forestos-celery | grep -o "RUNNING" || echo "STOPPED")

if [ "$API_STATUS" = "RUNNING" ]; then
    echo -e "  ${GREEN}✓ API service is running${NC}"
else
    echo -e "  ${RED}✗ API service is not running${NC}"
    echo "  Check logs: tail -f /var/log/forestos/api.err.log"
fi

if [ "$CELERY_STATUS" = "RUNNING" ]; then
    echo -e "  ${GREEN}✓ Celery worker is running${NC}"
else
    echo -e "  ${RED}✗ Celery worker is not running${NC}"
    echo "  Check logs: tail -f /var/log/forestos/celery.err.log"
fi
echo ""

# Step 7: Test API endpoint
echo -e "${BLUE}[7/7] Testing API endpoint...${NC}"
sleep 2

# Try to access the health endpoint
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")

if [ "$RESPONSE" = "200" ]; then
    echo -e "  ${GREEN}✓ API is responding (HTTP 200)${NC}"
    echo -e "  ${GREEN}✓ Swagger docs available at: http://localhost:8000/docs${NC}"
elif [ "$RESPONSE" = "307" ] || [ "$RESPONSE" = "301" ]; then
    echo -e "  ${GREEN}✓ API is responding (HTTP $RESPONSE - redirect)${NC}"
else
    echo -e "  ${YELLOW}⚠ API returned HTTP $RESPONSE${NC}"
    echo "  This might be normal. Check logs if you encounter issues."
fi
echo ""

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

# Print completion summary
echo "=============================================="
echo -e "${GREEN}Post-Installation Complete!${NC}"
echo "=============================================="
echo ""
echo "Service Status:"
supervisorctl status forestos-api forestos-celery
echo ""
echo "=============================================="
echo "Access Your API:"
echo "=============================================="
echo ""
echo "Local access:"
echo "  http://localhost:8000/docs"
echo ""
if [ -n "$SERVER_IP" ]; then
echo "Remote access (if firewall allows):"
echo "  http://$SERVER_IP/docs"
echo ""
fi
echo "=============================================="
echo "Useful Commands:"
echo "=============================================="
echo ""
echo "View API logs:"
echo "  tail -f /var/log/forestos/api.out.log"
echo "  tail -f /var/log/forestos/api.err.log"
echo ""
echo "View Celery logs:"
echo "  tail -f /var/log/forestos/celery.out.log"
echo "  tail -f /var/log/forestos/celery.err.log"
echo ""
echo "Restart services:"
echo "  supervisorctl restart forestos-api"
echo "  supervisorctl restart forestos-celery"
echo ""
echo "Check service status:"
echo "  supervisorctl status"
echo ""
echo "Stop services:"
echo "  supervisorctl stop forestos-api forestos-celery"
echo ""
echo "=============================================="
echo "Next Steps:"
echo "=============================================="
echo ""
echo "1. Test the API:"
echo "   curl http://localhost:8000/docs"
echo ""
echo "2. Create your first user (via API):"
echo "   See API documentation at /docs endpoint"
echo ""
echo "3. Configure SSL (if you have a domain):"
echo "   export DOMAIN=your-domain.com"
echo "   certbot --nginx -d \$DOMAIN --email admin@\$DOMAIN --agree-tos"
echo ""
echo "4. Configure firewall (if needed):"
echo "   ufw allow 80/tcp"
echo "   ufw allow 443/tcp"
echo ""
echo "=============================================="
echo ""
echo -e "${GREEN}Your ForestOS backend is now running!${NC}"
echo ""
