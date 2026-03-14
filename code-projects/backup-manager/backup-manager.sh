#!/bin/bash
set -o pipefail
pass_file="$(dirname "$0")/password"

directories_to_backup=(
    '/etc'
#    '/var/log'
)

log_path='/var/log/backup-manager.log'
path='/var/backups/backup-manager'
date=$(date +%d-%m-%Y_%H-%M)

exec >> "$log_path" 2>&1
echo -e "=============================="
echo -e "$date program started"

if [ ! -d $path ]; then
    mkdir $path
fi

start_time=$(date +%s.%N)
tar -czf - "${directories_to_backup[@]}" | gpg --batch --yes --passphrase-file "$pass_file" --pinentry-mode loopback --symmetric --cipher-algo AES256 -o "$path/backup_from_$date.tar.gz.gpg"
exit_code1="$?"
tar_time=$(echo "$(date +%s.%N) - $start_time" |bc)

if [ $(ls $path/*.gpg | wc -l) -gt 3 ];then
    file_to_delete=$(ls -tr $path | head -n 1)
    rm -f "$path/$file_to_delete"
    echo -e " Old archive removed"
else
    echo -e " No older backups removed"
fi

if [ $exit_code1 -eq 0 ]; then
    echo -e " Archive status: success | time: $tar_time seconds"
else
    echo -e " Archive status: failed (code: $exit_code1) | time: $tar_time seconds"
fi

echo -e "#Program Finished \n"
