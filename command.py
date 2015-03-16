#!/usr/bin/env python

import serial
import argparse
import sys


def power(args):
    if args.state == 'on':
        send_command(args.port, args.baud, 'PWR01')
    elif args.state == 'off':
        send_command(args.port, args.baud, 'PWR00')
    elif args.state == 'toggle':
        send_command(args.port, args.baud, 'PWRQSTN')
    elif args.state == 'status':
        response = send_command(args.port, args.baud, 'PWRQSTN')
        if response == b'!1PWR00\x1a':
            print('Status: Off')
        elif response == b'!1PWR01\x1a':
            print('Status: On')
        else:
            print("Status: Unknown (%s)" % response)
    else:
        print("Error: Invalid state sent to command 'power'")


def get_volume(args):
    response = send_command(args.port, args.baud, 'MVLQSTN')
    hex_vol = response.decode('ascii').replace('!1MVL', '').replace('\x1a', '')
    dec_vol = int(hex_vol, 16)
    percent_vol = dec_vol * 100 / 92
    return int(percent_vol)


def set_volume(vol, args):
    vol = int(vol / 100 * 92)
    vol = format(vol, '02x').upper()
    send_command(args.port, args.baud, "MVL%s" % vol)


def volume(args):
    if args.state == 'status':
        print("Volume: %s" % get_volume(args))

    elif args.state[0] == '+':
        vol = get_volume(args)
        vol = vol + int(args.state.strip('+'))
        set_volume(vol, args)

    elif args.state[0] == '-':
        vol = get_volume(args)
        vol = vol - int(args.state.strip('-'))
        set_volume(vol, args)

    elif int(args.state[0]) in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
        vol = int(args.state)
        if vol < 0 or vol > 100:
            print("Invalid volume: %s" % args.state)
            sys.exit(1)
        set_volume(vol, args)
    else:
        print("Unknown argument: %s" % args.state)
        sys.exit(1)


def mute(args):
    if args.state == 'mute' or args.state == 'on':
        send_command(args.port, args.baud, 'AMT01')
        print('Mute: On (muted)')
    elif args.state == 'unmute' or args.state == 'off':
        send_command(args.port, args.baud, 'AMT00')
        print('Mute: Off (unmuted)')
    elif args.state == 'status':
        status = send_command(args.port, args.baud, 'AMTQSTN').decode('ascii')
        if status == '!1AMT00\x1a':
            print('Status: Off (unmuted)')
        if status == '!1AMT01\x1a':
            print('Status: On (muted)')
    else:
        print('Invalid command: %s' % args.state)
        sys.exit(1)


def r_input(args):
    if args.state == 'status':
        cur_input = send_command(args.port, args.baud, 'SLIQSTN')
        cur_input = cur_input.decode('ascii')
        cur_input = cur_input.replace('!1', '')
        cur_input = cur_input.replace('\x1a', '')
        if cur_input == 'SLI00':
            print('Current input: Wii (VCR/DVR)')
        if cur_input == 'SLI01':
            print('Current input: Cable/Satellite')
        if cur_input == 'SLI02':
            print('Current input: XBox 360 (Game/TV)')
        if cur_input == 'SLI03':
            print('Current input: PC (Aux1)')
        if cur_input == 'SLI04':
            print('Current input: Linux (Aux2)')

    if (args.state.lower() == 'wii' or
       args.state.lower() == 'vcr' or
       args.state.lower() == 'dvr' or
       args.state.lower() == 'vcr/dvr'):
        send_command(args.port, args.baud, 'SLI00')
    elif args.state.lower() == 'cable':
            send_command(args.port, args.baud, 'SLI01')
    elif (args.state.lower() == 'xbox' or
          args.state.lower() == 'xbox360' or
          args.state.lower() == '360'):
            send_command(args.port, args.baud, 'SLI02')
    elif args.state.lower() == 'pc':
            send_command(args.port, args.baud, 'SLI03')
    elif (args.state.lower() == 'linux' or
          args.state.lower() == 'aux2'):
            send_command(args.port, args.baud, 'SLI04')


def send_command(port, baud, command):
    compiled_command = "".join(['!1', command, '\r'])
    ser = serial.Serial(port, baud, timeout=1)
    ser.write(bytearray(compiled_command, 'ascii'))
    response = ser.read(size=10)
    ser.close()
    return response


def usage(args):
    print("Usage: command.py {power, volume, mute, input} --help")
    sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Control an Onkyo receiver')
    parser.set_defaults(func=usage)

    # Global optional arguments

    parser.add_argument('-p', '--port',
                        type=str,
                        help='Serial port to use (default: /dev/ttyUSB0)',
                        default='/dev/ttyUSB0')

    parser.add_argument('-b', '--baud',
                        type=int,
                        help='Baud rate to use (default: 9600)',
                        default=9600)
    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Show debug messages')

    subparsers = parser.add_subparsers()

    # Power subparser
    parser_power = subparsers.add_parser('power', help='Power command')
    parser_power.add_argument('state', default='on',
                              choices=['on', 'off', 'toggle', 'status'],
                              help='Change or query state of the receiver.')
    parser_power.set_defaults(func=power)

    # Volume subparser
    parser_volume = subparsers.add_parser(name='volume',
                                          help='Volume commands')
    parser_volume.add_argument('state', default='20',
                               help='Volume (as %) or +/-')
    parser_volume.set_defaults(func=volume)

    # Mute subparser
    parser_mute = subparsers.add_parser('mute', help='Mute commands')
    parser_mute.add_argument('state', default='off',
                             choices=['on', 'off', 'toggle', 'status'],
                             help='Change or query the state of mute')
    parser_mute.set_defaults(func=mute)

    # Input subparser
    parser_input = subparsers.add_parser('input', help='Input commands')
    parser_input.add_argument('state', default='pc',
                              help='change or query the input')
    parser_input.set_defaults(func=r_input)

    args = parser.parse_args()

    if args.debug:
        print(args)

    args.func(args)
