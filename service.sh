#!/bin/bash

set -e

CUR_PATH=$(pwd)

cat > graphrag_webui.service <<EOF
[Unit]
Description=Graphrag WebUI
After=network.target
StartLimitIntervalSec=0

[Service]
WorkingDirectory=${CUR_PATH}
ExecStart=bash start.sh
Type=simple
Restart=always
RestartSec=5
User=root
StartLimitAction=reboot

[Install]
WantedBy=default.target
EOF

sudo cp -r graphrag_webui.service /etc/systemd/system
sudo chown root:root /etc/systemd/system/graphrag_webui.service
sudo systemctl stop graphrag_webui.service
sudo systemctl enable graphrag_webui.service
sudo systemctl start graphrag_webui.service
