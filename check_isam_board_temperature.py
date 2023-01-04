#!/usr/bin/env python
###
# Version 1.0 - ali/01.05.2019
# Monitoring Nokia ISAM temperature sensors
###
# Version 1.1 - ali/02.05.2019
# added performance data
###
# Version 1.2 - ali/14.04.2020
# modified performance data and return codes
###
# Version 1.3 - ali/13.12.2022
# added low warning thresholds
###
# Version 1.4 - ali/04.01.2023
# cleanup
###
# Nagios Exit-Codes:
# 0 = OK
# 1 = WARNING
# 2 = CRITICAL
# 3 = UNKNOWN
###
# Name:     eqptBoardThermalSensorActualTemperature
# OID:      1.3.6.1.4.1.637.61.1.23.10.1.2
# MID:      ASAM-EQUIP-MIB
# Type:     Integer
# Descr:    A table representing the actual value and thresholds of Thermal Sensor(s) on boards.
# Descr:    One entry corresponds to each sensor on board.
# Descr:    The entries are presented only when the board is plugged in, operationally up, has thermal sensors on it, and when operator put a read request for it.
###


import sys
import re
import subprocess


def main(switchhostname, snmpcommunity, temp_hi_warning, temp_hi_critical, temp_lo_warning, temp_lo_critical):

    regex_integer = re.compile(r'=\sINTEGER:\s(.+)')
    boardthermalsensors_int = []
    code_warning = 0
    code_critical = 0

#   check input thresholds
    try:
#       cast input thresholds to int
        t_hi_warning = int(temp_hi_warning)
        t_hi_critical = int(temp_hi_critical)
        t_lo_warning = int(temp_lo_warning)
        t_lo_critical = int(temp_lo_critical)

        if t_hi_critical <= t_hi_warning or t_lo_critical >= t_lo_warning:
            print("Error: Please check your thresholds!")
            sys.exit(3)

    except Exception as e:
        print("Error casting arguments! Please check your input!")
        print("%s" % e)
        sys.exit(3)

#   gather ISAM board thermal sensors
    p = subprocess.Popen("snmpwalk " + switchhostname + " -v 2c -c " + snmpcommunity + " 1.3.6.1.4.1.637.61.1.23.10.1.2", shell=True, stdout=subprocess.PIPE)
#   read output from subprocess and decode bytes to string as utf-8
    boardthermalsensors_proc = p.stdout.read().decode('utf-8')

    try:

#       split new-lines to extract board status and type
        boardthermalsensors_list = boardthermalsensors_proc.splitlines()

#       extract board-sensors using regex, cast output to int and append to new list
        for line in boardthermalsensors_list:
            boardthermalsensors_int.append(int(regex_integer.search(line).group(1)))

    except Exception as e:
        print("UNKNOWN - An error occured")
        print("%s" % e)
        sys.exit(3)


#   walk through elements and search for warning and critical conditions
    i = 0
    while(i < len(boardthermalsensors_int)):
        if boardthermalsensors_int[i] >= t_hi_critical or boardthermalsensors_int[i] <= t_lo_critical:
            code_critical += 1

        elif boardthermalsensors_int[i] >= t_hi_warning or boardthermalsensors_int[i] <= t_lo_warning:
            code_warning += 1

        i += 1

#   nagios return-codes and performance-data
#   loop through boards backwards -> output from plugin should be equal to board-position in chassis, generate performance-data
    if code_critical:
        print("ISAM Board Thermal Status: CRITICAL  -  %i/%i sensors reporting CRITICAL\n" % (code_critical,len(boardthermalsensors_int)))
    elif code_warning:
        print("ISAM Board Thermal Status: WARNING  -  %i/%i sensors reporting WARNING\n" % (code_warning,len(boardthermalsensors_int)))
    else:
        print("ISAM Board Thermal Status: OK  -  %i/%i sensors reporting OK\n" % (len(boardthermalsensors_int),len(boardthermalsensors_int)))

#   print seperator between status and performance-data
    print("|")

#   generate performance-data
    i = len(boardthermalsensors_int)-1
    while(i >= 0):
        print("board_sensor_%i=%icelsius;%i;%i;;" % (i,boardthermalsensors_int[i],t_hi_warning,t_hi_critical))
        i -= 1

#   exit script with nagios return-code
    if code_critical:
        sys.exit(2)
    elif code_warning:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':

    if len(sys.argv) != 7:
        print("\n\t[*] check_isam_board_temperature 1.4 [*]")
        print("\n\tUsage: check_isam_board_temperature.py HOSTNAME SNMPCOMMUNITY TEMP_HIGH_WARNING TEMP_HIGH_CRITICAL TEMP_LOW_WARNING TEMP_LOW_CRITICAL")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
