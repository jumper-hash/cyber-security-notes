import time
import os
import sys
import ipaddress
import subprocess
import argparse

sd="sudo -l" #if not possible, pass
paswd="cat /etc/passwd"
separator=" ========================================================================\n"
mid="|------------------------------------------------------------------------|\n"
underscore='_______________________________________________________________________'
def main():
    result=[]
    target="./dump"

    commands=[
        'ps -aux',
        'env',
        'uname -a',
        'cat /etc/passwd',
    ]
    finds=[
        'find / -perm -4000 2>/dev/null',
    ]
    sudos=[
        'ss -tulpn',
        'sudo -l',
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

    with open(target,"w") as tmp:
        tmp.write("\n\t\t###---Jumper dumper---###")
        print("\n\t\t###---Jumper dumper---###")

    if args.password is not None: s = f"sudo -S "
    if args.ip is not None:#ip check
        try:
            ipaddress.ip_address(args.ip) 
        except ValueError:
            print("incorrect ip")
            sys.exit(1)

    finish1=str(default(commands,separator,mid,result))+'\n' #[commands] operation
    finish2=str(looper(finds,separator,mid))+'\n'                          #[finds] operation
    final=finish1+finish2                                    #fetch
    # print(final)





def default(tab,s,m,result):
    for command in tab:
        try:    #executing commands one by one
            effect = [command, subprocess.check_output(command, text=True, shell=True).strip()]
        except subprocess.CalledProcessError as e:
            effect = [command, e.output.strip()]
            pass

        #joining results into one, then return
        result.append(f"{s}{2*m}{s}\n\nScript:{subprocess.check_output("pwd", text=True ).strip()}# {command}\n\n")
        result.append(str(effect[1])+f"\n\n")
    return (''.join(result))

def looper(find,s,m):
    result=[]
    effect='' #loop for another set of commands based on $find
    for command in find:
        pass #work in progress
    result.append(f"{s}{2*m}{s}\n\nScript:{subprocess.check_output("pwd", text=True ).strip()}# {command}\n\n")
    result.append(str(effect)+f"\n\n")

    print(*result)





if __name__ == "__main__":
    main()
