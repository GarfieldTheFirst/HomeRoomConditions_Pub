#!/usr/bin/bash
chmod +x setup_linux.sh

####### script to deploy homeroomconditions #######

# STEP 1: adding app user optional
# update apt (needed later as well)
sudo apt-get update
sudo apt-get install adduser
sudo apt-get install usermod
sudo adduser --gecos "" homeroomconditions
sudo usermod -aG sudo homeroomconditions
sudo su homeroomconditions

# SETP 1.1: (optional)
# generate keypair with ssh-keygen and register the key with github
sudo ssh-keygen

# STEP 2: add public key if not already present
# echo <paste-your-key-here> >> ~/.ssh/authorized_keys
# chmod 600 ~/.ssh/authorized_keys

# STEP 3 (working): Set permissions for root login, password authentication to no, set pubkey authentication to yes, set authorized keys directory and 
file="/etc/ssh/sshd_config"
# give user rw access to this file
sudo chmod -R u+rw ${file}
sudo chown -R admin ${file}

param[1]="PermitRootLogin"
param[2]="PubkeyAuthentication"
param[3]="AuthorizedKeysFile"
param[4]="PasswordAuthentication"

# edit
for PARAM in ${param[@]}
do
  sudo sed -i '/^'"${PARAM}"'/d' ${file}
  sudo echo "All lines beginning with '${PARAM}' were deleted from ${file}."
done
sudo echo "${param[1]} no" >> ${file}
sudo echo "'${param[1]} no' was added to ${file}."
sudo echo "${param[2]} yes" >> ${file}
sudo echo "'${param[2]} yes' was added to ${file}."
sudo echo "${param[3]} .ssh/authorized_keys" >> ${file}
sudo echo "'${param[3]} .ssh/authorized_keys' was added to ${file}."
sudo echo "${param[4]} no" >> ${file}
sudo echo "'${param[4]} no' was added to ${file}"

# reload
sudo service ssh restart

# STEP 4 (working): install and setup firewall
sudo apt-get install -y ufw
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status

# STEP 5 (working): install base dependencies
sudo apt-get -y update
sudo apt-get -y install python3 python3-venv python3-dev
# install gnupg dependency of mysql
# sudo apt-get install gnupg
# # make swap file
# sudo dd if=/dev/zero of=/swapfile bs=1024 count=1048576
# sudo mkswap /swapfile
# sudo chmod 600 /swapfile
# # download mysql package with wget
# sudo apt-get install wget
# sudo wget https://dev.mysql.com/get/mysql-apt-config_0.8.23-1_all.deb
# sudo dpkg -i mysql-apt-config_0.8.23-1_all.deb
# sudo apt-get update
# sudo apt-get install mysql-community-server
# sudo apt-get install mysql-cluster-community-server
# sudo apt-get install mysql-server
# sudo systemctl status mysql
sudo apt-get -y install postfix supervisor nginx git 
sudo apt install docker.io

# STEP 6: installation of the application
# register keys with ssh agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
git clone git@github.com:GarfieldTheFirst/HomeRoomConditions.git
cd ~/HomeRoomConditions
git checkout master
# setup virtual environment
python3 -m venv venv
source ~/HomeRoomConditions/venv/bin/activate
pip install -r requirements.txt
# pip install waitress pymysql cryptography
# sets the flask application environment variable
echo "export FLASK_APP=homeroomconditions.py" >> ~/.profile

# # STEP 7: setup mysql
# sudo mysql -u root
# mysql> create database roomdata character set utf8 collate utf8_bin;
# mysql> create database users character set utf8 collate utf8_bin;
# mysql> create user 'roomdata'@'localhost' identified by 'r00md8t8!&';
# mysql> grant all privileges on roomdata.* to 'roomdata'@'localhost';
# mysql> grant all privileges on users.* to 'roomdata'@'localhost';
# mysql> flush privileges;
# mysql> quit;
# flask db init --multidb
# flask db migrate
# flask db upgrade

# Step 7: run the application with supervisor
echo -e 
'[program:homeroomconditions] \n
command=/home/homeroomconditions/HomeRoomConditions/venv/bin/waitress-serve --listen=*:8000 --expose-tracebacks homeroomconditions:app \n
directory=/home/homeroomconditions/HomeRoomConditions \n
user=homeroomconditions \n
autostart=true \n
autorestart=true \n
stopasgroup=true \n
killasgroup=true'
>> /etc/supervisor/conf.d/homeroomconditions.conf

sudo supervisorctl reload

#Step 8: insert ssl certificate
sudo apt install certbot
sudo certbot certonly --standalone --preferred-challenges http -d my-domain.com

# ls -l /etc/letsencrypt/live/my-domain.com/

# So first open the crontab file:

# sudo crontab -e
# after that, add the certbot command to run weekly:

# @weekly certbot renew --pre-hook "systemctl stop nginx" --post-hook "systemctl start nginx" --renew-hook "systemctl reload nginx" --quiet 

#Step 10: setup nginx
$ sudo rm /etc/nginx/sites-enabled/default

echo -e ' server {
    # listen on port 80 (http)
    listen 80;
    server_name _;
    location / {
        # redirect any requests to the same URL but on https
        return 301 https://$host$request_uri;
    }}
    server {
    # listen on port 443 (https)
    listen 443 ssl;
    server_name _;

    # location of the self-signed SSL certificate
    ssl_certificate /etc/letsencrypt/live/my-domain.com/fullchain.pem;;
    ssl_certificate_key /etc/letsencrypt/live/my-domain.com/privkey.pem;;

    # write access and error logs to /var/log
    access_log /var/log/homeroomconditions_access.log;
    error_log /var/log/homeroomconditions_error.log;

    location / {
        # forward application requests to the waitress
        proxy_pass http://localhost:8000;
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        # handle static files directly, without forwarding to the application
        alias /home/homeroomconditions/HomeRoomConditions/app/static;
        expires 30d;
    }}' >> /etc/nginx/sites-enabled/homeroomconditions

sudo service nginx reload

