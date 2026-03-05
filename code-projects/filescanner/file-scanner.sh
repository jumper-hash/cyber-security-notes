#!/bin/bash
read -p "Put path to the directory to find files in directory (empty for current): " path;
echo "[type * or leave empty for everyone]";
read -p "Owner to find: " owner;
read -p "Group to find: " group;
echo -e "\n\n--------------------------------------------------------------------------\n\n"
starting_directory=$(pwd)

if [[ "$path" == '' ]]; then
path=$starting_directory;
fi

cd "$path"
find "$path" -type f -exec ls -la {} + | grep -v "^total" | while read -r privileges links owner_file group_file rest ; do
    if [[ "$owner" == '*' || "$owner" == '' ]] && [[ "$group" == '*' || "$group" == '' ]]; then
        echo "$privileges $links $owner_file $group_file $rest";
    else
        if [[ "$owner_file" == "$owner" ]] && [[ "$group_file" == "$group" ]]; then
            echo -e "$privileges $links $owner_file $group_file $rest \n";
        fi
    fi
done
cd "$starting_directory"
echo -e "\n      -#- jumper -#-";
