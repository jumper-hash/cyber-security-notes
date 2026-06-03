import time
import sys
import ipaddress
import subprocess
import argparse

sd="sudo -l" #if not possible, pass
paswd="cat /etc/passwd"
separator="\n ===================================================\n"

def main():
    target="./dump"

    commands=[
        'ps -aux',
        'ss -tulpn',
        'cat /etc/passwd',
        'ls /etc',
        'sudo -l',
        'uname -a',
        'env',
        'find / -perm -4000 2>/dev/null'
    ]


    s=""
    parser= argparse.ArgumentParser(
        description="Quick system scan"
    )
    parser.add_argument("-i","--ip",help="put destination ip address with port")
    parser.add_argument("-p","--password",help="password for the account")
    parser.add_argument("-d","--destination",help="no file ale by default")
    parser.add_argument("-a","--additional",help="additional commands") 
    args = parser.parse_args()

    if args.password is not None: s = f"sudo -S "
                                        # f"sudo -S {parser.password} "
    if args.ip is not None:
        try:
            ipaddress.ip_address(args.ip)
            default(s, commands, args.password, target)
        except ValueError:
            print("Ip error")
            return
    else:
        default(s, commands, args.password, target)

def default(sudo, tab, pwd, target):
    with open(target,"w") as tmp:
        tmp.write('Jumper dumping script')
    for el in tab:
        new=sudo.split()
        for i in el.split():
            new.append(i)
        try:
            effect = [new, subprocess.check_output(new, input=pwd, text=True, shell=True).strip()]
        except:
            effect = [new, "Incorrect password for sudo"]
            pass
        command=''
        for s in effect[0]:
            command=command+s+" "

        #can replace {el} with {command}, similar output

        peroid=[f"Script:{subprocess.check_output("pwd", text=True ).strip()}# {el}\n",str(effect[1])+"\n\n\n"]
     
        with open(target,"a") as f:
            for a in peroid:
                print(a)
                f.write(a)


if __name__ == "__main__":
    main()
