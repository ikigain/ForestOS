# ForestOS Backend - Phase 1.3 Deployment Guide

**Date:** November 26, 2025  
**Status:** Production Deployment  
**Domain:** fos.total-smart.com  
**Repository:** https://github.com/ikigain/ForestOS.git

---

## Overview

This guide covers the complete deployment of ForestOS backend on an AliCloud Ubuntu 22.04 VPS. The automated setup script handles all infrastructure configuration, service setup, and application deployment.

---

## Prerequisites

### 1. AliCloud Resources

**VPS Instance:**
- **OS:** Ubuntu 22.04 LTS
- **Specs:** 2 vCPU, 4GB RAM minimum (recommended: 4 vCPU, 8GB RAM)
- **Storage:** 40GB SSD minimum
- **Network:** Public IP assigned
- **Security Group:** Ports 22 (SSH), 80 (HTTP), 443 (HTTPS) open

**AliCloud PostgreSQL (RDS):**
- **Version:** PostgreSQL 14+
- **Specs:** 2 vCPU, 4GB RAM minimum
- **Storage:** 20GB minimum
- **Network:** Same region as VPS
- **Database:** `forestos` (create before deployment)
- **User:** `forestos_user` with full privileges
- **Whitelist:** Add VPS public IP to whitelist

### 2. Domain Configuration

**Domain:** fos.total-smart.com

**DNS Records (Configure before deployment):**
```
Type: A
Name: fos.total-smart.com
Value: YOUR_VPS_PUBLIC_IP
TTL: 600
```

**Verification:**
```bash
# Wait for DNS propagation (5-30 minutes)
nslookup fos.total-smart.com
# Should return your VPS IP
```

### 3. API Keys

**Perenual Plant API:**
- Sign up at: https://perenual.com/docs/api
- Free tier: 100 requests/day
- Premium tier: 1,000 requests/day ($19/month)
- Save your API key for configuration

---

## Deployment Steps

### Step 1: Connect to VPS

```bash
# SSH into your AliCloud VPS
ssh root@YOUR_VPS_IP

# Or if using key authentication
ssh -i /path/to/key.pem root@YOUR_VPS_IP
```

### Step 2: Download Setup Script

```bash
# Download the setup script
curl -O https://raw.githubusercontent.com/ikigain/ForestOS/main/setup_forestos_server.sh

# Make it executable
chmod +x setup_forestos_server.sh
```

### Step 3: Run Deployment

```bash
# Set environment variables
export DOMAIN=fos.total-smart.com
export ADMIN_EMAIL=admin@total-smart.com

# Run the setup script
sudo bash setup_forestos_server.sh
```

**Expected Duration:** 10-15 minutes

The script will:
1. Update system packages
2. Install Python 3.11
3. Install PostgreSQL client
4. Install Redis
5. Install Nginx
6. Install Supervisor
7. Install Certbot
8. Clone ForestOS from GitHub
9. Set up Python virtual environment
10. Install Python dependencies
11. Create directory structure
12. Generate configuration files
13. Configure Supervisor
14. Configure Nginx
15. Start services

### Step 4: Configure Database Connection

```bash
# Edit the configuration file
nano /var/www/forestos/Server/.env
```

**Update the following lines:**
```env
# Replace with your AliCloud PostgreSQL credentials
DATABASE_URL=postgresql://forestos_user:YOUR_PASSWORD@rm-xxxxx.pg.rds.aliyuncs.com:5432/forestos
ASYNC_DATABASE_URL=postgresql+asyncpg://forestos_user:YOUR_PASSWORD@rm-xxxxx.pg.rds.aliyuncs.com:5432/forestos

# Update Perenual API key
PERENUAL_API_KEY=your-actual-api-key-here

# Update domain references
IMAGE_BASE_URL=https://fos.total-smart.com/images/plants

# Update CORS origins (add your frontend domains)
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:19006","https://fos.total-smart.com","https://total-smart.com"]
```

Save and exit (Ctrl+X, Y, Enter)

### Step 5: Run Database Migrations

```bash
# Navigate to server directory
cd /var/www/forestos/Server

# Activate virtual environment
source venv/bin/activate

# Run migrations
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema, Initial schema
```

### Step 6: Start Services

```bash
# Start the API service
supervisorctl start forestos-api

# Start the Celery worker
supervisorctl start forestos-celery

# Check status
supervisorctl status
```

**Expected Output:**
```
forestos-api                     RUNNING   pid 12345, uptime 0:00:05
forestos-celery                  RUNNING   pid 12346, uptime 0:00:05
```

### Step 7: Configure SSL Certificate

```bash
# Obtain Let's Encrypt SSL certificate
certbot --nginx -d fos.total-smart.com --email admin@total-smart.com --agree-tos --non-interactive
```

**Expected Output:**
```
Congratulations! You have successfully enabled HTTPS on https://fos.total-smart.com
```

### Step 8: Verify Deployment

```bash
# Test API endpoint
curl https://fos.total-smart.com/docs

# Should return HTML for Swagger UI
```

**In Browser:**
- Visit: https://fos.total-smart.com/docs
- You should see the FastAPI Swagger documentation
- Test the `/` endpoint to confirm API is responding

---

## Post-Deployment Configuration

### 1. Create Admin User

```bash
# Connect to database
psql postgresql://forestos_user:PASSWORD@rm-xxxxx.pg.rds.aliyuncs.com:5432/forestos

# Create admin user manually or via API
```

**Via API:**
```bash
curl -X POST https://fos.total-smart.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@total-smart.com",
    "password": "SecurePassword123!",
    "full_name": "Admin User"
  }'
```

### 2. Test Authentication

```bash
# Login to get JWT token
curl -X POST https://fos.total-smart.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@total-smart.com",
    "password": "SecurePassword123!"
  }'

# Save the access_token from response
```

### 3. Populate Plant Database

```bash
# Create initial plant data (via admin script or API calls)
# This can be done via the mobile app or admin panel later
```

---

## Service Management

### Supervisor Commands

```bash
# Check all services
supervisorctl status

# Restart API
supervisorctl restart forestos-api

# Restart Celery
supervisorctl restart forestos-celery

# Restart all services
supervisorctl restart all

# Stop a service
supervisorctl stop forestos-api

# Start a service
supervisorctl start forestos-api

# View logs in real-time
tail -f /var/log/forestos/api.out.log
tail -f /var/log/forestos/api.err.log
```

### Nginx Commands

```bash
# Test configuration
nginx -t

# Reload configuration
systemctl reload nginx

# Restart Nginx
systemctl restart nginx

# Check status
systemctl status nginx
```

### Database Commands

```bash
# Connect to database
psql postgresql://forestos_user:PASSWORD@rm-xxxxx.pg.rds.aliyuncs.com:5432/forestos

# Run migrations
cd /var/www/forestos/Server
source venv/bin/activate
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check current version
alembic current
```

---

## Monitoring & Logs

### Log Locations

```bash
# API logs
/var/log/forestos/api.out.log     # Standard output
/var/log/forestos/api.err.log     # Errors

# Celery logs
/var/log/forestos/celery.out.log  # Standard output
/var/log/forestos/celery.err.log  # Errors

# Nginx logs
/var/log/nginx/access.log         # HTTP requests
/var/log/nginx/error.log          # Nginx errors

# System logs
journalctl -u supervisor -f        # Supervisor logs
```

### Monitoring Commands

```bash
# Watch API logs
tail -f /var/log/forestos/api.out.log

# Check for errors
grep -i error /var/log/forestos/api.err.log

# Monitor system resources
htop

# Check disk space
df -h

# Check memory usage
free -h

# Check database connections
psql postgresql://forestos_user:PASSWORD@rm-xxxxx.pg.rds.aliyuncs.com:5432/forestos \
  -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## Maintenance

### Update Code from GitHub

```bash
# Pull latest code
cd /var/www/forestos
git pull origin main

# Install new dependencies (if any)
cd Server
source venv/bin/activate
pip install -r requirements.txt

# Run new migrations (if any)
alembic upgrade head

# Restart services
supervisorctl restart all
```

### Database Backup

```bash
# Create backup directory
mkdir -p /var/backups/forestos

# Backup database
pg_dump postgresql://forestos_user:PASSWORD@rm-xxxxx.pg.rds.aliyuncs.com:5432/forestos \
  > /var/backups/forestos/forestos_$(date +%Y%m%d_%H%M%S).sql

# Automated daily backup (add to crontab)
0 2 * * * pg_dump postgresql://forestos_user:PASSWORD@rm-xxxxx.pg.rds.aliyuncs.com:5432/forestos > /var/backups/forestos/forestos_$(date +\%Y\%m\%d).sql
```

### SSL Certificate Renewal

```bash
# Certbot auto-renewal is configured
# Test renewal
certbot renew --dry-run

# Manual renewal (if needed)
certbot renew

# Check certificate expiry
certbot certificates
```

---

## Troubleshooting

### API Not Starting

```bash
# Check logs
tail -100 /var/log/forestos/api.err.log

# Common issues:
# 1. Database connection failed
#    - Check DATABASE_URL in .env
#    - Verify VPS IP is whitelisted in AliCloud PostgreSQL
#    - Test connection: psql postgresql://...

# 2. Port 8000 already in use
ps aux | grep uvicorn
kill -9 <PID>
supervisorctl restart forestos-api

# 3. Permission issues
chown -R www-data:www-data /var/www/forestos
supervisorctl restart forestos-api
```

### SSL Certificate Issues

```bash
# Check certificate status
certbot certificates

# Re-obtain certificate
certbot --nginx -d fos.total-smart.com --force-renewal

# Check Nginx configuration
nginx -t
```

### Database Connection Issues

```bash
# Test connection from VPS
psql postgresql://forestos_user:PASSWORD@rm-xxxxx.pg.rds.aliyuncs.com:5432/forestos

# If fails:
# 1. Check VPS IP is whitelisted in AliCloud console
# 2. Check firewall rules
# 3. Verify credentials in .env
# 4. Check PostgreSQL is running in AliCloud console
```

### High Memory Usage

```bash
# Check memory
free -h

# Reduce API workers (in /etc/supervisor/conf.d/forestos.conf)
command=/var/www/forestos/Server/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

# Restart
supervisorctl restart forestos-api
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
# Install UFW
apt install ufw

# Allow SSH
ufw allow 22

# Allow HTTP/HTTPS
ufw allow 80
ufw allow 443

# Enable firewall
ufw enable

# Check status
ufw status
```

### 2. Fail2Ban (Brute Force Protection)

```bash
# Install Fail2Ban
apt install fail2ban

# Configure
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit /etc/fail2ban/jail.local
[sshd]
enabled = true
maxretry = 3
bantime = 3600

# Restart
systemctl restart fail2ban
```

### 3. Regular Updates

```bash
# Set up automatic security updates
apt install unattended-upgrades
dpkg-reconfigure --priority=low unattended-upgrades
```

### 4. Database Security

- Use strong passwords
- Limit database user permissions
- Enable SSL for PostgreSQL connections
- Regular backups
- Monitor access logs

---

## Performance Optimization

### 1. Nginx Caching

```nginx
# Add to /etc/nginx/sites-available/forestos
location /images/ {
    alias /var/www/forestos/images/;
    expires 30d;
    add_header Cache-Control "public, immutable";
    add_header Access-Control-Allow-Origin *;
}

# Static API responses (if applicable)
location ~ ^/api/plants {
    proxy_pass http://127.0.0.1:8000;
    proxy_cache_valid 200 10m;
}
```

### 2. Database Connection Pooling

Already configured in SQLAlchemy (see `Server/app/db/session.py`)

### 3. Redis Caching

Configure in application for:
- Latest sensor readings (1 min TTL)
- Plant catalog (1 hour TTL)
- User plant lists (5 min TTL)

---

## Scaling Considerations

### Horizontal Scaling

**Load Balancer Setup:**
1. Deploy multiple VPS instances with same script
2. Configure AliCloud SLB (Server Load Balancer)
3. Point fos.total-smart.com to SLB
4. Share image storage via AliCloud OSS

**Database:**
- Use AliCloud PostgreSQL read replicas
- Route read queries to replicas
- Keep writes on primary

### Vertical Scaling

**Upgrade VPS:**
- Increase to 8 vCPU, 16GB RAM
- Increase API workers to 8
- Increase database connections

---

## Deployment Checklist

### Pre-Deployment
- [ ] AliCloud VPS provisioned
- [ ] AliCloud PostgreSQL created
- [ ] Domain DNS configured (fos.total-smart.com)
- [ ] Perenual API key obtained
- [ ] Email configured for SSL certificates

### Deployment
- [ ] Setup script executed successfully
- [ ] `.env` file configured with actual credentials
- [ ] Database migrations run
- [ ] Services started (API + Celery)
- [ ] SSL certificate obtained
- [ ] API accessible at https://fos.total-smart.com/docs

### Post-Deployment
- [ ] Admin user created
- [ ] Authentication tested
- [ ] Endpoints tested via Swagger
- [ ] Logs monitored for errors
- [ ] Backup strategy implemented
- [ ] Monitoring alerts configured
- [ ] Documentation updated with actual IPs/credentials

---

## Support & Resources

**Documentation:**
- API Docs: https://fos.total-smart.com/docs
- GitHub: https://github.com/ikigain/ForestOS

**Contact:**
- Technical Lead: admin@total-smart.com
- DevOps: devops@total-smart.com

**External Services:**
- Perenual API: https://perenual.com/docs/api
- AliCloud Console: https://www.alibabacloud.com/
- Let's Encrypt: https://letsencrypt.org/

---

## Rollback Procedure

If deployment fails or issues arise:

```bash
# Stop services
supervisorctl stop all

# Restore from backup (if available)
cd /var/www
mv forestos forestos_failed
mv forestos_backup_TIMESTAMP forestos

# Rollback database (if needed)
psql postgresql://... < /var/backups/forestos/forestos_TIMESTAMP.sql

# Restart services
supervisorctl start all
```

---

**Deployment Guide Version:** 1.0  
**Last Updated:** November 26, 2025  
**Maintainer:** ForestOS Development Team

---

**Status:** ✅ Ready for Production Deployment
