#!/usr/bin/env python3
import argparse
import sys
import ipaddress

path='/etc/hosts'
separator="#====="

def main():
    parser=argparse.ArgumentParser(description=f"maintain {path}")  
    decision = parser.add_mutually_exclusive_group(required=False)
    decision.add_argument('-e', '--edit', action='store_true', help='Edit on existing entry')
    decision.add_argument('-n', '--new', action='store_true', help='adds new entry (default)')
    parser.add_argument('-i','--ip', help='IP address')
    parser.add_argument('-d', '--domain',help='Domain name')
    args = parser.parse_args()
    try:
        with open(path, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        lines = []

    editline = get_last_index(lines)

    if args.edit:
        if args.ip and args.domain:
            edit(args.ip, args.domain, parser, editline, lines)
        else:
            parser.print_help()
            print(f"Missing required arguments: --ip and --domain")
            sys.exit(1)
    else:
        if not args.new:
            args.new = True
        if args.ip and args.domain:
            new(args.ip, args.domain, parser, editline, lines)
        else:
            print(f"Invalid data: --ip and --dns cannot be empty")
            parser.print_help()
            sys.exit(1)

def check_ip(ip,parser):
    try:
        if len(ip.split(".")) == 2:
            ip = f"10.129.{ip}"
        ipaddress.ip_address(ip)
        return ip
    except ValueError:
        parser.print_help()
        sys.exit("Invalid IP address.")

def check_domain(dns,parser):
    return dns if '.' in dns else f"{dns}.htb"

def get_last_index(lines):
    if not lines:
        return 0
        
    system_end_point = 0 
    for i, el in enumerate(lines):
        if separator in el:
            system_end_point = i
    
    last_valid = system_end_point
    for i in range(system_end_point + 1, len(lines)):
        if lines[i].strip():
            last_valid = i
            
    return last_valid    

def new(ip, dns, parser, editline, lines):
    ip = check_ip(ip,parser)
    dns = check_domain(dns,parser)
    new_line = f"{ip}\t{dns}\n"
    
    if lines:
        oldline = f"#{lines[editline].lstrip('#')}"
        lines[editline] = oldline
        lines.insert(editline + 1, new_line)
    else:
        lines.append(new_line)
    save(lines)

def edit(ip, dns, parser, editline, lines):
    if not lines or editline >= len(lines):
        print('No records to edit.')
        sys.exit(1)

    if (ip and ip in lines[editline]) or (dns and dns in lines[editline]):
        ip = check_ip(ip,parser)
        dns = check_domain(dns,parser)
        
        parts = lines[editline].lstrip('#').split()
        get_old_ip = parts[0]
        get_old_dns = ' '.join(parts[1:])
        
        if ip in lines[editline]:
            lines[editline] = f"{get_old_ip}\t{dns}\n"
        else:
            lines[editline] = f"{ip}\t{get_old_dns}\n"
        save(lines)
    else:
        print('No matching record found.')
        sys.exit(1)

def save(a):
    try:
        with open(path, "w") as f:
            f.writelines(a)
        print(f"---{path} modified successfully---")
    except PermissionError:
        print("\n[!] ERROR: no rights to modify hosts. Use sudo.")

if __name__ == '__main__':
    main()
