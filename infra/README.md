# Infrastructure Notes

This directory contains deployment support files and environment-specific runtime helpers.

## Local dependencies

Local Postgres/Redis dependencies are defined in the repository root `docker-compose.yml`.

## Running without multiple terminals (systemd)

Sample service units are provided in `infra/systemd/`:

- `cyberincident-api.service`
- `cyberincident-worker.service`
- `cyberincident-beat.service`
- `cyberincident-frontend.service`

Install on Ubuntu (adjust paths/user if needed):

1. Copy unit files:
   - `sudo cp infra/systemd/*.service /etc/systemd/system/`
2. Reload daemon:
   - `sudo systemctl daemon-reload`
3. Enable + start:
   - `sudo systemctl enable --now cyberincident-api cyberincident-worker cyberincident-beat`
4. Build frontend once, then enable frontend service:
   - `cd /root/apps/CyberIncidentTracker/frontend && npm install && npm run build`
   - `sudo systemctl enable --now cyberincident-frontend`
5. Check status/logs:
   - `systemctl status cyberincident-api`
   - `journalctl -u cyberincident-api -f`

Security hardening recommendation:

- Create a dedicated service user instead of running units as root:
  - `sudo useradd --system --create-home --shell /usr/sbin/nologin cyberincident`
  - Update `User=` and ownership of `/root/apps/CyberIncidentTracker` (or deploy under `/srv/cyberincident`).

## Optional reverse proxy (Nginx)

Sample config is provided at `infra/nginx/cyberincident.conf`.

1. Install Nginx:
   - `sudo apt install -y nginx`
2. Copy and enable site:
   - `sudo cp infra/nginx/cyberincident.conf /etc/nginx/sites-available/cyberincident.conf`
   - `sudo ln -s /etc/nginx/sites-available/cyberincident.conf /etc/nginx/sites-enabled/cyberincident.conf`
   - `sudo rm -f /etc/nginx/sites-enabled/default`
3. Validate and reload:
   - `sudo nginx -t`
   - `sudo systemctl restart nginx`

## Optional TLS (Let's Encrypt)

After your domain points to the server and Nginx is running:

- `sudo apt install -y certbot python3-certbot-nginx`
- `sudo certbot --nginx -d your-domain.example`

## Backups and restore

Scripts are provided in `infra/scripts/`:

- `backup_postgres.sh` (creates timestamped custom-format dump with `pg_dump`)
- `restore_postgres.sh` (restores dump with `pg_restore --clean`)

Usage:

1. Export DB URL:
   - `export DATABASE_URL='postgresql://incident_user:incident_pass@localhost:5432/incident_tracker'`
2. Create backup:
   - `bash infra/scripts/backup_postgres.sh /var/backups/cyberincident`
3. Restore backup:
   - `bash infra/scripts/restore_postgres.sh /var/backups/cyberincident/incident-tracker-YYYYMMDD-HHMMSS.dump`

Suggested automation:

- Add daily cron/systemd timer for backups.
- Keep at least 7 daily + 4 weekly snapshots.
- Run a monthly restore drill in a staging database.
