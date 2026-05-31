# Docker Infrastructure and Wazuh, Nginx, Apache2 Implementation

## Environment
- OS `Ubutnu server 24.04 LTS`
- Containers:
  - Wazuh v4.14.5 
  - Apache2 v2.4 //latest
 
# Wazuh setup
- Official github repository pull: `git clone https://github.com/wazuh/wazuh-docker.git -b v4.14.5`
- `generate-indexer-certs.yaml` configuration:
      
      services:
        generator:
          image: wazuh/wazuh-certs-generator:0.0.4
          hostname: wazuh-certs-generator
          volumes:
            - ./config/wazuh_indexer_ssl_certs/:/certificates/
            - ./config/certs.yml:/config/certs.yml
## Excessive option removed from the default configuration file:

    environment:
      - HTTP_PROXY=<YOUR_PROXY_ADDRESS_OR_DNS>

## Generating certificates for wazuh
`docker compose -f generate-indexer-certs.yml run --rm generator`
## Starting Wazuh container
- `docker compose up -d`: current configuraion resulted in creation of Docker internal network `wazuh-network`, which will be later used between other services to communicate with Nginx
- `docker ps -a`: confirmed Wazuh container working properly

# Apache2 setup
- `docker-compose.yaml` configuration:

        services:
          apache-server:
            image: httpd:latest
            container_name: apache
            restart: always
            volumes:
              - ./html:/usr/local/apache2/htdocs/
            networks:
              - wazuh-network
        
        networks:
          wazuh-network:
            external: true
            name: single-node_default
- `wazuh-network` selected as network used for communication

- `docker compose up -d && docker ps -a` started and confirmed apache2 service working properly
  
# Encountered problems
Starting the Wazuh container caused the host machine to run out of disk space, which led to:
- Docker container crash
- Filesystem corruption
  - Containers
  - Images
    
## Troubleshooting: Extending Docker storage
- Added new disk intended for Docker storage
- Mounting disk `sudo mount /dev/sdb /mnt/data`

## Creating Docker config file `/etc/docker/daemon.json`, resulted in limiting used space and changed pyhsical destination

      {
      "data-root": "/mnt/data/docker",
      "log-driver": "json-file",
      "log-opts": {
        "max-size": "80m",
        "max-file": "4"
      }
## Modifying /mnt/data/wazuh-docker/single-node/docker-compose.yaml
- Replacing path for Wazuh filesystem: `sed -i 's|\./config|/mnt/data/wazuh/config|g' docker-compose.yml`
- Starting Wazuh again: `docker compose up -d`  

  
