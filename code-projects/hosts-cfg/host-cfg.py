#!/usr/bin/env python3

import argparse
import sys
import re 

path='./hosts'
ip_full = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
ip_short = r"^\d{1,3}\.\d{1,3}$"

with open(path,"r") as file:
    list = file.readlines()

def main():
    parser=argparse.ArgumentParser(
        description=f"maintain {path}"
    )
    
    decision = parser.add_mutually_exclusive_group(required=False)
    decision.add_argument('-e', '--edit', action='store_true', help='Edit on existing entry')
    decision.add_argument('-n', '--new', action='store_true', help='adds new entry (default)')

    parser.add_argument('-i','--ip', help='IP address (full or last 2 octets, e.g., 10.15)')
    parser.add_argument('-d', '--domain',help='Domain name (automatically appends .htb if missing)')
    #parser.add_argument('-c', '--comment', default=True, help='Comment out the previous line (applies only to new entries)')

    args= parser.parse_args()
    # print("  ip, dns, edit-bool, new-bool")
    # print(f"  {args.ip}, {args.domain}, {args.edit}, {args.new},")

    if args.edit:
        if args.ip and args.domain:
            edit(args.ip, args.domain, parser)
        else:
            print(f"Invalid data: ip and dns cannot be empty")
            if not args.ip:
                print('ERROR: no ip')
            if not args.domain:
                print('ERROR: no dns')
            parser.print_help()
            sys.exit(1)
    else:
        if not args.new:
            args.new=True
        if args.ip and args.domain:
            new(args.ip, args.domain, parser)
        else:
            print(f"Invalid data: ip and dns cannot be empty")
            if not args.ip:
                print('ERROR: no ip')
            if not args.domain:
                print('ERROR: no dns')
            parser.print_help()
            sys.exit(1)

def check_ip(ip):
    if re.search(ip_full, ip):
        new_ip=ip
    elif re.search(ip_short, ip): 
        new_ip=f"10.129.{ip}"
    else:
        sys.exit("Invalid IP address. Provide a full IP or the last 2 octets. Exiting.")
    return new_ip

def check_domain(dns):
    if not '.' in dns:
        new_dns=f"{dns}.htb"
    else:
        new_dns=dns
    return new_dns

def last_list_element(path, lines):
        for system_end_point, el in enumerate(lines):
            if "#=====" in el:
                return system_end_point        
index_end_of_system_part=last_list_element(path, list) 



def get_last_index(system_end_point, lines):
    last_valid = system_end_point
    for i in range(system_end_point + 1, len(lines)):
        if lines[i].strip():
            last_valid = i
    return last_valid    
###get index of last not empty line inside file 
editline=get_last_index(index_end_of_system_part, list)


def new(ip,dns,parser):
    if not ip:
            parser.print_help()
            sys.exit(1)
    elif not dns:
            parser.print_help()
            sys.exit(1)
    else:
        ip=check_ip(ip)
        dns=check_domain(dns)
        new_line=f"{ip}\t{dns} \n"
        #now hash the last element in list, then increase index by 1
        oldline=f"#{list[editline]}"
        list[editline]=oldline
        list.insert(editline+1,new_line)
        save(list)

def edit(ip,dns,parser):
    if (ip and ip in list[editline]) or (dns and dns in list[editline]):
        try:
            ip=check_ip(ip)
            dns=check_domain(dns)
        except:
            pass
        parts=list[editline].split()
        get_old_ip=parts[0]
        get_old_dns_list=parts[1:]
        get_old_dns=' '.join(get_old_dns_list)
        if ip in list[editline]:
            new_line=f"{get_old_ip}\t{dns} \n"
            list[editline]=new_line
            save(list)
        elif dns in list[editline]:
            new_line=f"{ip}\t{get_old_dns} \n"
            list[editline]=new_line
            save(list)
        else:
            parser.print_help()
            sys.exit(1)


    else:
        print('No matching record found. Try adding a new one')
        parser.print_help()
        sys.exit(1)
def save(a):
    try:
        with open(path, "w") as f:
            f.writelines(a)
        print(f"---{path} modified successfully---")
    except PermissionError:
        print("\n[!] ERROR: no rights to modify /etc/hosts.")
        print("[!] Use: sudo etc ...")
  
if __name__ == '__main__':
    main()
