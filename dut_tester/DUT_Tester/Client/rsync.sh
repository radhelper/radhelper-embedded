#!/bin/bash

while true; do
    rsync -avz -e "ssh -i ~/.ssh/pi_chipir" pihub@192.168.1.81:/home/pihub/radhelper-embedded/dut_tester/logs_client ./logs/dut0
    rsync -avz -e "ssh -i ~/.ssh/pi_chipir" pihub@192.168.1.81:/home/pihub/radhelper-embedded/dut_tester1/logs_client ./logs/dut1
    sleep 30
done
