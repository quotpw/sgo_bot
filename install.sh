#!/bin/bash

# Install required packages
apt update
apt install supervisor python3 python3-dev python3-pip libmagickwand-dev wget unzip -y

# Download fonts from jetbrains suite
wget https://download.jetbrains.com/fonts/JetBrainsMono-2.242.zip -O fonts.zip

# Unzip ttf fonts
unzip -j fonts.zip "fonts/ttf/*" -d "/usr/share/fonts/ttf"

# Delete archive
rm fonts.zip

# Install python dependencies
pip3 install -r /root/sgo_bot/requirements.txt

# Create task in cron
crontab -l | {
  cat
  echo "*/25 * * * * bash /root/sgo_bot/homeworks_listener.sh"
} | crontab -

# Configure supervisor and delete conf
cp /root/sgo_bot/supervisord.conf /etc/supervisor/supervisord.conf
rm /root/sgo_bot/supervisord.conf
service supervisor restart
