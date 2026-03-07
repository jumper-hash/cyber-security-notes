#!/bin/bash
services=( "NetworkManager.service" "apache2.service" )
bold='\033[1m'
none='\033[0m'
red='\033[1;31m'
green='\033[1;32m'
yellow='\033[1;33m'
blue='\033[1;34m'
logDir='/var/log/service-monitor/'

read -p "    How often repeat the script (in seconds, 0 for norepeat): " repeat
echo -e "    script started with PID: ${red}$$ ${none}"

function default(){
    timeStamp=$(date '+%d-%m-%Y %H:%M:%S')
    logFile="/var/log/service-monitor/$(date '+%d-%m-%Y').log"
    echo "---------------------------------------- "
    echo "---------------------------------------- " >> "$logFile"
    echo "Status \"$timeStamp\" started: " >> "$logFile"

    for item in "${services[@]}"; do
        if [ $(sudo systemctl is-active "$item") == 'inactive' ]; then
            failure1 $item
        else
            success $item
        fi
    done
    echo -e "Status finished." >> "$logFile"
}

function failure1(){
    if [ $(systemctl is-active "$1") != 'active' ]; then
        echo -e " # ${blue}$1${none} not working, ${yellow}retry in 5s...${none}"
        echo " # $1 not working, retrying" >> "$logFile"
        sudo systemctl restart $1
        sleep 5
        failure2 $1
    else
        success $1
    fi
}

function failure2(){
    if [ $(sudo systemctl is-active "$1") != 'active' ]; then
        echo -e " # ${blue}$1${none} not working after retry, ${red}skipping${none}"
        echo " # $1 not working after retry, skipping." >> "$logFile"
    else
        success $1
    fi
}

function success(){
    echo -e "    ${blue}$1${none} is currently  ${green}running${none}."
    echo "    $1 is currently  running." >> "$logFile"
}

if [ ! -d "$logDir" ]; then
sudo mkdir "$logDir"
fi

if [ "$repeat" == "0" ]; then
    default
else
    if [ "$repeat" == '' ]; then
        while true; do
        default
        echo -e "    ${yellow}Sleeping for 60 seconds...${none}"
        sleep 60
        done
    else
        while true; do
        default
        echo -e "    ${yellow}Sleeping for $repeat seconds...${none}"
        sleep "$repeat"
        done
    fi
fi
