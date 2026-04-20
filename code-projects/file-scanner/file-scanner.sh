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
find . -type f 2>/dev/null -exec ls -la {} + | grep -v "^total" | while read -r privileges links owner_file group_file size month day time rest ; do
    match_owner=false
    match_group=false

    if [[ "$owner" == '*' || "$owner" == '' || "$owner_file" == "$owner" ]]; then
        match_owner=true
    fi
    if [[ "$group" == '*' || "$group" == '' || "$group_file" == "$group" ]]; then
        match_group=true
    fi
    if [[ "$match_owner" == true && "$match_group" == true ]]; then
        echo -e "$privileges $links $owner_file $group_file $size $month $day $time $rest"
    fi
done
cd "$starting_directory"
echo -e "\n      -#- jumper -#-";
