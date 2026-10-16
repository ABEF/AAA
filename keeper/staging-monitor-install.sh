#!/usr/bin/env bash
# Installs only the explicitly authorized staging observer, not production access.
set -euo pipefail
test "$(id -u)" = 0
test -f /opt/zzz-keeper-staging/keeper/staging_observer.py
keyfile=${1:?Path to the read-only monitor public key required}
test "$(wc -l < "$keyfile")" = 1
grep -Eq '^ssh-ed25519 [A-Za-z0-9+/=]+( [A-Za-z0-9_-]+)?$' "$keyfile"
ssh-keygen -lf "$keyfile" >/dev/null
if getent passwd zzz-stage-monitor >/dev/null; then echo 'Monitor account already exists; stop for review.' >&2; exit 1; fi
useradd --system --user-group --home-dir /var/lib/zzz-stage-monitor --shell /bin/sh zzz-stage-monitor
install -d -m 0755 /var/lib/zzz-stage-monitor
install -d -m 0700 /var/lib/zzz-stage-monitor/.ssh
install -d -m 2750 -o zzz-stage -g zzz-stage-monitor /var/lib/zzz-stage-monitor/export
install -d -m 0755 /usr/local/libexec
cat > /usr/local/libexec/zzz-stage-monitor-read <<'READ'
#!/bin/sh
exec /usr/bin/head -c 1048576 /var/lib/zzz-stage-monitor/export/status.json
READ
chmod 0755 /usr/local/libexec/zzz-stage-monitor-read
printf 'restrict,command="/usr/local/libexec/zzz-stage-monitor-read" %s\n' "$(cat "$keyfile")" > /var/lib/zzz-stage-monitor/.ssh/authorized_keys
chmod 0600 /var/lib/zzz-stage-monitor/.ssh/authorized_keys
cat > /etc/systemd/system/zzz-stage-observer.service <<'UNIT'
[Unit]
Description=PoPL staging health and recovery snapshot export
[Service]
Type=oneshot
User=zzz-stage
Group=zzz-stage-monitor
WorkingDirectory=/opt/zzz-keeper-staging
ExecStart=/usr/bin/python3 -m keeper.staging_observer
Environment=PYTHONDONTWRITEBYTECODE=1
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
CapabilityBoundingSet=
RestrictAddressFamilies=AF_UNIX
InaccessiblePaths=/var/lib/zzz-keeper-staging/keys /var/lib/zzz-keeper-staging/chain
ReadWritePaths=/var/lib/zzz-keeper-staging/backups /var/lib/zzz-stage-monitor/export
CPUQuota=10%
MemoryMax=64M
TasksMax=16
TimeoutStartSec=30
UMask=0077
UNIT
cat > /etc/systemd/system/zzz-stage-observer.timer <<'UNIT'
[Unit]
Description=Refresh isolated staging health and backup every five minutes
[Timer]
OnBootSec=30
OnUnitActiveSec=5min
AccuracySec=5s
[Install]
WantedBy=timers.target
UNIT
systemd-analyze verify /etc/systemd/system/zzz-stage-observer.service /etc/systemd/system/zzz-stage-observer.timer
systemctl daemon-reload
systemctl start zzz-stage-observer.service
systemctl enable --now zzz-stage-observer.timer
