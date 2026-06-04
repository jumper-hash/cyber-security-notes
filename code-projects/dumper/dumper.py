import os
import sys
import ipaddress
import subprocess
import argparse

separator=" ========================================================================\n"
mid="|------------------------------------------------------------------------|\n"
underscore='_______________________________________________________________________'

def main():
    result=[]
    target="./dump"

    commands=[
        'ps -aux',
        'env',
        'cat /proc/version',
        'cat /etc/passwd',
    ]
    finds=[
        'find / -perm -4000 2>/dev/null',
        # 'find / -writable -type d 2>/dev/null'
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

    if args.password is not None:
        if subprocess.run("sudo -k -S -v", input=args.password, capture_output=True, text=True, shell=True).returncode==0:
            finish3=sudofunc(sudos,args.password,separator,mid)
        else:
            print("Incorrect Password")
            sys.exit(1)

    if args.ip is not None:#ip check
        try:
            ipaddress.ip_address(args.ip)
            sender() 
        except ValueError:
            print("incorrect ip")
            sys.exit(1)
    to_send=postman(commands,separator,mid,result,finds,finish3,target)

    sender(to_send)


def postman(commands,separator,mid,result,finds,finish3,target):
    finish1=str(default(commands,separator,mid,result))+'\n' #[commands] operation
    finish2=str(looper(finds,separator,mid))+'\n'         #[finds] operation
    final=finish1+finish2+str(finish3)                                    #fetch

    print("\n\t\t###---Jumper dumper---###\n"+final)



def default(tab,s,m,result):
    for command in tab:
        try:    #executing commands one by one
            effect = [command, subprocess.check_output(command, text=True, shell=True).strip()]
        except subprocess.CalledProcessError as e:
            effect = [command, e.output.strip()]

        #joining results into one, then return
        result.append(f"{s}{2*m}{s}\n\nScript:{subprocess.check_output("pwd", text=True ).strip()}# {command}\n\n")
        result.append(str(effect[1])+f"\n\n")
    return (''.join(result))

def looper(find,s,m):
    result=[]
    tmp=[]
     #loop for another set of commands based on $find
    for command in find:
        effect=subprocess.run(command, capture_output=True, shell=True, text=True)


        result.append(f"{s}{2*m}{s}\n\nScript:{subprocess.check_output("pwd", text=True ).strip()}# {command}\n\n")

        tmp=effect.stdout.split()
        for e in tmp:
            t=subprocess.run(f"ls -l {e}", capture_output=True, shell=True, text=True)
            result.append(str(t.stdout).strip()+'\n')
        result.append("\n\n")
        return "".join(result)

def sudofunc(tab,p,s,m):
    result=[]
    admin_prefix="sudo -S -k "

    for command in tab:
        try:    #executing commands one by one
            effect = [admin_prefix+command, subprocess.check_output(command, text=True, shell=True, input=p).strip()]
        except subprocess.CalledProcessError as e:
            effect = [admin_prefix+command, e.output.strip()]
            pass

        #joining results into one, then return
        result.append(f"{s}{2*m}{s}\n\nScript:{subprocess.check_output("pwd", text=True ).strip()}# {admin_prefix+command}\n\n")
        result.append(str(effect[1])+f"\n\n")
    return "".join(result)

def sender(content):
    pass


if __name__ == "__main__":
    main()
