# Docker Infrastructure and PrivateBin Implementation

## Secure Nginx Reverse Proxy and PrivateBin Service

	Service Architecture: PrivateBin (PHP-FPM) behind an Nginx SSL Termination Proxy
	External Access: Host Port 8443 mapped to Container Port 443 (HTTPS)
	Security: 
		-SSL encryption enabled via self-signed certificates
		-PrivateBin container running in `read_only` mode with UID 1000
		-TLS protocols restricted to v1.2 and v1.3
	Storage: Bind mount volume from `./data` to `/srv/data` for persistent pastes
	Images: `privatebin/nginx-fpm-alpine` and `nginx:alpine` managed via Docker Compose


## Operational Diagnostics and Permissions

	Permission Management: Applied `chown` to `./data` directory to match container UID (1000) for write access
	User Privileges: Administrative user added to the `docker` group; container processes isolated from root
	Syntax Validation: Corrected `.yaml` indentation and Nginx `.conf` block structures
	Certificate Path: Verified mount points for `/etc/nginx/certs` within the proxy container

## .yaml File

	`
	version: '3'
	services:
	  privatebin:
	    image: privatebin/nginx-fpm-alpine
	    container_name: privatebin
	    restart: always
	    read_only: true
	    user: '1000:1000'
	    volumes:
	      - ./data:/srv/data
	
	  nginx-proxy:
	    image: nginx:alpine
	    container_name: nginx-proxy
	    restart: always
	    ports:
	      - "8443:443"
	    volumes:
	      - ./nginx.conf:/etc/nginx/nginx.conf:ro
	      - ./https_keys:/etc/nginx/certs:ro
	    depends_on:
	      - privatebin
	`

## Network and Proxy Configuration

	Upstream Communication: Nginx proxying traffic to PrivateBin container on internal port 8080
	Header Forwarding: Configured X-Real-IP and X-Forwarded-For to preserve client origin data
	Encryption Layer: SSL certificates (`selfsigned.crt` / `key`) generated and stored in `./https_keys`

## Troubleshooting and Forensics

	Write Errors: Diagnosed as permission denied in `./data`. Fixed by aligning host directory ownership with container UID
	Connectivity: Resolved upstream communication by using Docker service discovery (`http://privatebin:8080`)
	Configuration Fix: Adjusted Nginx worker connections and SSL cipher suites for enhance
