# Docker Infrastructure and Nginx Implementation
 ## Nginx Containerized Web Service
		Standard Web: Nginx listening on Port 80 (Internal Container Port)
		External Access: Host Port 3000 mapped to Container Port 80
		Storage: Bind mount volume from `/docker/website` to `/usr/share/nginx/html`
		Image: Official nginx:latest managed via Docker Compose
		Verification: 
			Confirmed HTTP via curl `http://localhost:3000`
			Confirmed HTTP from remote host via curl `http://192.168.10.1:3000`

## Operational Diagnostics and Traffic Analysis
	Socket Monitoring (`ss -tulnp`)
	Port 3000: Docker-proxy active on host to relay traffic to Nginx container
	Port 80: Internal container socket verified via docker exec
	
## docker-compose.yaml
`
	version: '3'
	services:
      website:          
	  image: nginx:latest
	    container_name: www
	    volumes:
	      - /docker/website:/usr/share/nginx/html
	    ports:
	      - "3000:80"
	    restart: always
`

## Network Isolation
	Virtual Bridge: docker0 interface acting as the gateway for container traffic
	IP Addressing: Internal container IP assigned within the `172.18.x.x/16` range

## Troubleshooting and Forensics
	Error 403 Forbidden: Diagnosed as missing index.html and directory permission mismatch
	Permission Fix: Applied `chmod 755` to host directory for container read access
