#!/bin/bash

while true; do
    rsync -avz -e "ssh -i ~/.ssh/pi_chipir" pihub@192.168.1.81:/home/pihub/radhelper-embedded/dut_tester/logs_client ./logs/dut0
    rsync -avz -e "ssh -i ~/.ssh/pi_chipir" pihub@192.168.1.81:/home/pihub/radhelper-embedded/dut_tester1/logs_client ./logs/dut1
    rsync -avz -e "ssh -i ~/.ssh/pi_chipir" pihub@192.168.1.82:/home/pihub/radhelper-embedded/dut_tester2/logs_client ./logs/dut2
    rsync -avz -e "ssh -i ~/.ssh/pi_chipir" pihub@192.168.1.82:/home/pihub/radhelper-embedded/dut_tester3/logs_client ./logs/dut3
    sleep 60
done
