#!/bin/bash

/usr/sbin/sshd &

if [[ $# -eq 1 && $1 =~ ^-?[0-9]+$  ]]; then
  echo "CPU_SPEED=$1" >> /etc/environment
else
  echo "CPU_SPEED=1" >> /etc/environment
fi

tail -f /dev/null

