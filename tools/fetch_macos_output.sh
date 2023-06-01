#!/bin/bash

# SyncedFolders don't work with macOS guest, so using this peace of 
# buiishit to fetch output files

mkfifo fifo
vagrant ssh-config make_macos> fifo &
SSH_ASKPASS= SSH_ASKPASS_REQUIRE= sshpass -p 'vagrant' scp -r -F fifo make_macos:output .
rm fifo

