# prepare for secured SSL run

### 1. **Environment Setup**

Update your `.env` file with the template above, using your specific values:

- `HOSTNAME=inquilinato.duckdns.org`
- `DUCKDNS_TOKEN=566ab832-c328-4750-865e-6cd9d979f68d`
- `EMAIL=maiktreya@example.com` (replace with your actual email)

### 2. **Security Improvements**

Your Docker Compose now exposes only nginx externally (ports 80/443), while keeping database and API services internal-only using `expose` instead of `ports`.

### 3. **SSL Certificate Process**

**Initial Setup:**

```bash
# Make scripts executable
chmod +x utils/init-letsencrypt-duckdns.sh
chmod +x utils/renew-certificates.sh

# Run initial SSL setup
bash utils/init-letsencrypt-duckdns.sh
```

**What the script does:**

1. Downloads SSL security parameters
2. Creates dummy certificates for nginx startup
3. Starts nginx with dummy certs
4. Requests real certificates via DNS-01 challenge
5. Reloads nginx with real certificates

### 4. **Automatic  cert Renewal**

Add to your system crontab for automatic renewal & backupp:

```bash
# Edit crontab
crontab -e

# Add this line to check for renewal twice daily at 12:00 and 00:00
0 2 * * * /path/to/your/project/renew-certificates.sh >> /path/to/your/project/renewal.log 2>&1
0 3 * * * /path/to/tenantsUnion/backup_storage.sh >> /home/$USER/back/backup.log 2>&1

```

### 4. **Automatic DB backup**

Add to your system  backup of the DB storage folder ever 24 h at 3am. The script automatizes holding just a max of the 3 latest scripts:

```bash
# Edit crontab
crontab -e

# Add this line to check for renewal twice daily at 12:00 and 00:00
0 3 * * * /path/to/tenantsUnion/backup_storage.sh >> /home/$USER/back/backup.log 2>&1

```

### 6. **Deployment Commands**

**First-time deployment:**

```bash
# Start services without SSL first
docker compose --profile Frontend up -d

# Then set up SSL
bash utils/init-letsencrypt-duckdns.sh

# Finally start with SSL
docker compose --profile Secured up -d
```

**Regular deployment:**

```bash
docker compose --profile Secured up -d
```

### 7. **Troubleshooting**

**Test with staging first:**
Edit the script and set `staging=1` to test with Let's Encrypt's staging environment to avoid rate limits.

**Check certificate status:**

```bash
docker compose run --rm --entrypoint "certbot certificates" certbot
```

**Manual renewal:**

```bash
bash utils/renew-certificates.sh
```

### 8. **Directory Structure**

Your project should have:

```
project/
├── docker-compose.yaml
├── .env
├── utils/
    ├── init-letsencrypt-duckdns.sh
    └── renew-certificates.sh
└── build/
    └── nginx/
        ├── nginx.conf.template
        └── certbot/
            ├── conf/
            └── www/
```

### Key Differences from HTTP-01 Challenge

- Uses DNS-01 challenge (required for DuckDNS)
- No need for `.well-known/acme-challenge` directory
- Requires DuckDNS token for DNS record manipulation
- Works even if your server is behind NAT/firewall
- Allows wildcard certificates (if needed later)

The automation handles all the complexity of DNS challenges and integrates seamlessly with your existing nginx reverse proxy setup.
