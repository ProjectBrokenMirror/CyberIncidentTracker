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
