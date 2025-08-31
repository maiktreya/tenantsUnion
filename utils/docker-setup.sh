#!/bin/bash
# Add Docker's official GPG key:
 apt-get update
 apt-get install ca-certificates curl
 install -m 0755 -d /etc/apt/keyrings
 curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
 chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
   ee /etc/apt/sources.list.d/docker.list > /dev/null
 apt-get update &&

# install docker and set permissions for running without sudo
apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin &&
groupadd docker &&
sudo usermod -aG docker $USER &&
echo "logout and login to check docker is working without sudo rights"