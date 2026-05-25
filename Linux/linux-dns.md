# Linux Domain Name Service configuration
## server configuration
- OS `Ubuntu 6.17.0-20-generic`
- WAN Interface `enp0s3` -> External / Internet Access
- LAN Interface `enp0s8`, working as default gateway for other devices

# `named.conf.options` configuration:
  
    options {
      directory "/var/cache/bind";
      recursion yes;
      forwarders {
          8.8.8.8;
          8.8.4.4;
      };
      dnssec-validation auto;
      allow-query { any; };
      listen-on { any; };
      listen-on-v6 { any; };
      };
Google servers set as forwarders to resolve unknown domains
- `8.8.8.8`
- `8.8.4.4`
- Remote host test for Ubuntu client connected to the server: `nslookup google.com` resulted in return of `142.250.109.113` proving server working properly

# `db.test` configuration

    $TTL 604800
    @ IN SOA server.test. root.test. (
                4          ; Serial
                604800     ; Refresh
                86400      ; Retry
                2419200    ; Expire
                604800 )   ; Negative Cache TTL
    
      @ IN NS server.test.
      wazuh IN A 192.168.10.1
      website IN A 192.168.10.1
      server IN A 192.168.10.1
      router IN A 192.168.10.1

# Setup for multi-container Docker reverse-proxy powered by Nginx
- `website.test` declared for web-service hosting html docs from Docker container using proxy
- `wazuh.test` declared for easier access to the wazuh instance running inside a container


