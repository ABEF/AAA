#!/usr/bin/env bash
# Explicit operator installation on an authorized host. No production chain.
set -euo pipefail
test "$(id -u)" = 0
test "$(uname -m)" = x86_64
base=/opt/zzz-keeper-staging
state=/var/lib/zzz-keeper-staging
test -f "$base/keeper/monitor.py"
test ! -e "$state"
if getent passwd zzz-stage >/dev/null; then echo 'Staging account already exists; stop for review.' >&2; exit 1; fi
if ss -lntH '( sport = :18545 )' | grep -q .; then echo 'Staging port already occupied.' >&2; exit 1; fi
useradd --system --user-group --home-dir "$state" --shell /usr/sbin/nologin zzz-stage
install -d -m 0700 -o zzz-stage -g zzz-stage "$state" "$state/chain" "$state/keeper" "$state/keys" "$state/backups" "$state/build" "$state/build/src"
install -d -m 0755 "$base/bin"
curl --fail --location --silent --show-error --max-time 120 \
  https://github.com/foundry-rs/foundry/releases/download/v1.4.4/foundry_v1.4.4_linux_amd64.tar.gz \
  --output "$base/foundry.tar.gz"
printf '%s  %s\n' 22ba110a40e4de7791b007b08284e7b038c6bd4ce141b7ac34b5accec04f71a4 "$base/foundry.tar.gz" | sha256sum --check --status
tar -xzf "$base/foundry.tar.gz" -C "$base/bin" cast anvil forge
chmod 0755 "$base/bin/"{cast,anvil,forge}
install -m 0600 -o zzz-stage -g zzz-stage "$base/keeper/rehearsal/KeeperVenue.sol" "$state/build/src/KeeperVenue.sol"
printf '[profile.default]\nsolc_version="0.8.26"\nevm_version="cancun"\n' > "$state/build/foundry.toml"
chown zzz-stage:zzz-stage "$state/build/foundry.toml"
runuser -u zzz-stage -- env HOME="$state" "$base/bin/forge" build --root "$state/build"

cat > /etc/systemd/system/zzz-stage-anvil.service <<'UNIT'
[Unit]
Description=PoPL isolated staging chain (test ETH only)
After=network.target
StartLimitIntervalSec=600
StartLimitBurst=5
[Service]
User=zzz-stage
Group=zzz-stage
WorkingDirectory=/opt/zzz-keeper-staging
ExecStart=/opt/zzz-keeper-staging/bin/anvil --host 127.0.0.1 --port 18545 --chain-id 31337 --block-time 5 --state /var/lib/zzz-keeper-staging/chain/state.json --preserve-historical-states --state-interval 30 --silent
Restart=on-failure
RestartSec=15
TimeoutStopSec=60
KillMode=control-group
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
CapabilityBoundingSet=
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
IPAddressDeny=any
IPAddressAllow=localhost
ReadWritePaths=/var/lib/zzz-keeper-staging/chain
CPUQuota=20%
MemoryMax=512M
TasksMax=64
UMask=0077
[Install]
WantedBy=multi-user.target
UNIT
cat > /etc/systemd/system/zzz-stage-keeper.service <<'UNIT'
[Unit]
Description=PoPL keeper staging (isolated test chain only)
Requires=zzz-stage-anvil.service
After=zzz-stage-anvil.service
StartLimitIntervalSec=600
StartLimitBurst=5
[Service]
User=zzz-stage
Group=zzz-stage
WorkingDirectory=/opt/zzz-keeper-staging
ExecStart=/usr/bin/python3 -m keeper.monitor --config /var/lib/zzz-keeper-staging/keeper/config.json --live
Environment=PYTHONDONTWRITEBYTECODE=1
Restart=on-failure
RestartSec=30
KillMode=control-group
TimeoutStopSec=120
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
CapabilityBoundingSet=
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
IPAddressDeny=any
IPAddressAllow=localhost
ReadWritePaths=/var/lib/zzz-keeper-staging/keeper
ReadOnlyPaths=/var/lib/zzz-keeper-staging/keys
InaccessiblePaths=/var/lib/zzz-keeper-staging/chain /var/lib/zzz-keeper-staging/backups
CPUQuota=20%
MemoryMax=256M
TasksMax=64
UMask=0077
[Install]
WantedBy=multi-user.target
UNIT
systemd-analyze verify /etc/systemd/system/zzz-stage-anvil.service /etc/systemd/system/zzz-stage-keeper.service
systemctl daemon-reload
systemctl start zzz-stage-anvil.service
for attempt in {1..20}; do
  if curl --fail --silent --max-time 2 -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}' http://127.0.0.1:18545/ | grep -q '0x7a69'; then break; fi
  sleep 1
done
cd "$base"
runuser -u zzz-stage -- env HOME="$state" PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m keeper.staging
systemctl enable --now zzz-stage-anvil.service zzz-stage-keeper.service
systemctl is-active zzz-stage-anvil.service zzz-stage-keeper.service
