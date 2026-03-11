# Infrastructure Notes

This directory contains deployment support files and environment-specific runtime helpers.

## Local dependencies

Local Postgres/Redis dependencies are defined in the repository root `docker-compose.yml`.

## Running without multiple terminals (systemd)

Sample service units are provided in `infra/systemd/`:

- `cyberincident-api.service`
- `cyberincident-worker.service`
- `cyberincident-beat.service`

Install on Ubuntu (adjust paths/user if needed):

1. Copy unit files:
   - `sudo cp infra/systemd/*.service /etc/systemd/system/`
2. Reload daemon:
   - `sudo systemctl daemon-reload`
3. Enable + start:
   - `sudo systemctl enable --now cyberincident-api cyberincident-worker cyberincident-beat`
4. Check status/logs:
   - `systemctl status cyberincident-api`
   - `journalctl -u cyberincident-api -f`
