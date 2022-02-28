#!/bin/bash

# Install docker
apt update
apt install docker.io

# Setup containers
docker run --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=1337 -d mysql
docker run --name phpmyadmin -d --link mysql:db -p 8081:80 phpmyadmin

# Help to user)
echo SETUP DATABASE FROM IP:8081
echo DATABASE NAME - sgo_bot
echo FILE WITH TABLES - sgo_bot/sgo_bot.sql
