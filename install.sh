#!/usr/bin/env bash

set -eu
set -o pipefail
sudo ls > /dev/null # get sudo rights before user walks away

CONFIGS_DIR="configs" # relative path in this repo to our configuration directory
USAGE="Usage: $0 [elasticsearch, kibana, nginx, logstash]\nNo arguments defaults to installing everything."


prepare() {

  wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
  sudo apt-get install apt-transport-https
  if ! fgrep artifacts /etc/apt/sources.list.d/elastic-5.x.list; then
    echo "deb https://artifacts.elastic.co/packages/5.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-5.x.list
  fi
  sudo apt-get update
}

java8() {
  
    printf "\nInstalling Java Development Kit 8\n"
    
    wget --no-cookies --no-check-certificate --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" "http://download.oracle.com/otn-pub/java/jdk/8u73-b02/jdk-8u73-linux-x64.rpm"
    
    sudo yum -y localinstall jdk-8u73-linux-x64.rpm
    
    rm ~/jdk-8u*-linux-x64.rpm
}

elasticsearch() {
  printf "\nInstalling Elasticsearch \n"
  
  rpm --import http://packages.elastic.co/GPG-KEY-elasticsearch

  ELASTIC="./elasticsearch.repo"
  if [ ! -f /etc/yum.repos.d/elasticsearch.repo ]; then
     echo "[elasticsearch-5x]" >> $ELASTIC 
     echo "name=Elasticsearch repository for 5.x packages" >> $ELASTIC
     echo "baseurl=https://artifacts.elastic.co/packages/5.x/yum" >> $ELASTIC
     echo "gpgcheck=1" >> $ELASTIC
     echo "gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch" >> $ELASTIC
     echo "enabled=1" >> $ELASTIC
     echo "autorefresh=1" >> $ELASTIC
     echo "type=rpm-md" >> $ELASTIC
  fi

  sudo yum install elasticsearch
  chkconfig --add elasticsearch
  sudo service elasticsearch start

}

kibana() {
  printf "\nInstalling Kibana\n"
  prepare
  sudo apt-get install kibana
  sudo update-rc.d kibana defaults 96 9

  printf -- "--> Copying configuration files\n" 
  KIBANA_CONFIG="kibana.yml"
  KIBANA_CONFIG_PATH="/opt/kibana/config/$KIBANA_CONFIG"
  sudo cp "$CONFIGS_DIR/kibana/$KIBANA_CONFIG" $KIBANA_CONFIG_PATH

  sudo service kibana restart
}

kibana5() {
  printf "\nInstalling Kibana v5\n"
  prepare
  sudo apt-get install kibana
  sudo update-rc.d kibana defaults 96 9

  printf -- "--> Copying configuration files\n" 
  KIBANA_CONFIG="kibana.yml"
  KIBANA_CONFIG_PATH="/etc/kibana/$KIBANA_CONFIG"
  sudo cp "$CONFIGS_DIR/kibana/$KIBANA_CONFIG" $KIBANA_CONFIG_PATH

  sudo service kibana restart
}
nginx() {
  printf "\nInstalling Nginx\n" 
  sudo apt-get install -y nginx apache2-utils

  printf -- "--> Copying configuration files\n" 
  NGINX_DEFAULT_SITE_CONFIG="nginx_default"
  NGINX_DEFAULT_SITE_DEST="/etc/nginx/sites-available/default"
  sudo cp "$CONFIGS_DIR/nginx/$NGINX_DEFAULT_SITE_CONFIG" $NGINX_DEFAULT_SITE_DEST 
  
  printf -- "--> Creating administrator account for user: cuahsi\n"
  sudo htpasswd -c /etc/nginx/htpasswd.users cuahsi 
  sudo nginx -s reload
}

logstash() {
  printf "\nInstalling Logstash\n"
  
 wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
  if ! fgrep logstash /etc/apt/sources.list; then
    echo "deb http://packages.elastic.co/logstash/2.2/debian stable main" | sudo tee -a /etc/apt/sources.list
  fi
  sudo apt-get update && sudo apt-get install logstash=1:2.2.4-1
  
  printf -- "--> Copying configuration files\n" 
  LOGSTASH_CONFD_PATH="/etc/logstash/conf.d"
  sudo cp $CONFIGS_DIR/conf.d/*.conf $LOGSTASH_CONFD_PATH
  
  
  printf -- "--> Copying jdbc driver library\n"
  if [ ! -d /etc/logstash/java ]; then    
    sudo mkdir /etc/logstash/java;
  fi
  sudo cp -r sqljdbc_4.0 /etc/logstash/java/
 
  printf -- "--> Installing Logstash plugins\n"
  LOGSTASH_PLUGIN=/opt/logstash/bin/plugin
  PRUNE_FILTER=logstash-filter-prune
  if ! $LOGSTASH_PLUGIN list $PRUNE_FILTER; then
    sudo -u logstash $LOGSTASH_PLUGIN install $PRUNE_FILTER
  fi
  if ! $LOGSTASH_PLUGIN list "logstash-filter-cuahsi-service-name"; then
    sudo -u logstash $LOGSTASH_PLUGIN install "logstash-plugins/logstash-filter-cuahsi-service-name-2.1.0.gem"
  fi
}

filebeat() {
  printf "\nInstalling Filebeat\n"  
  prepare
  
  sudo apt-get install filebeat 

  printf -- "--> Making folder for archived his-webclient logs\n"
  if [ ! -d /var/log/his-webclient ]; then 
    sudo mkdir /var/log/his-webclient
  fi

  printf -- "--> Extracting his-webclient archive\n"
  sudo tar -xvf ./archive/his-webclient/logs.tar -C /var/log/his-webclient
 
  printf -- "--> Moving filebeat configutation into /etc/filebeat\n" 
  FILEBEAT_CONF_PATH="/etc/filebeat/filebeat.yml"  
  sudo cp $CONFIGS_DIR/filebeat/*.yml $FILEBEAT_CONF_PATH  

}

wait_for_spinup() {
  secs=${2}
  name=${1}
  while [ $secs -gt 0 ]; do
     echo -ne "$secs\033[0K... spinning up $name\r"
     sleep 1
     : $((secs--))
  done
  printf "0\n"
}

start_server() {
 
  sudo service nginx start
  wait_for_spinup nginx 10 
  
  sudo service elasticsearch start
  wait_for_spinup elasticsearch 10 

  sudo service logstash start
  wait_for_spinup logstash 10 

  sudo service kibana start  
  wait_for_spinup kibana 10
  
  sudo service filebeat start
  wait_for_spinup filebeat 10  
}

# Main
if [ ! -z ${1:-} ]; then
  # Run function provided as first argument
  $1 || { echo -e $USAGE; exit 1; }
else 
  # Install everything
  elasticsearch
  kibana5
  nginx
  logstash
  filebeat
  start_server

  printf -- "--> ELK installation complete\n"
  printf -- "--> To watch ES indices build, issue the following command: \n"
  printf -- "--> watch curl -XGET http://localhost:9200/_cat/indices?v" 

fi
