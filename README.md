# hydroshare-usagemetrics
ELK stack install and configuration files for HydroShare


## Configure Logrotate for Logstash

```
cp /etc/logrotate.d/nginx /etc/logrotate.d/logstash
```

```
$ vim /etc/logrotate.d/logstash  
/var/log/logstash/*log /var/log/logstash/*.err /var/log/logstash/*.stdout{  
  daily  
  rotate 10  
  copytruncate  
  compress  
  delaycompress  
  missingok  
  notifempty  
 }
```
