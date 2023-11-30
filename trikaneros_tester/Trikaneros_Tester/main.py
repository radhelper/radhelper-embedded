import argparse
import os
import sys
import traceback


def in_venv():
    return sys.prefix != sys.base_prefix


def main():

    if not in_venv():
        print("Please run this script from within the virtual environment")
        print("To activate the virtual environment, run:")
        print("source .venv/bin/activate")
        exit(1)

    _epilog = "This software is part of the PULP Project, ETH Zurich: https://pulp-platform.org/"
    _description = "Trikaneros Tester - Automated testing utility for fault tolerance monitoring in radiation environments"
    # Setup parser
    parser = argparse.ArgumentParser(description = _description, epilog = _epilog)

    subparsers = parser.add_subparsers(help = 'Specify the operation mode.', required = True)

    parser_client = subparsers.add_parser('client',
                                          help = 'Monitor and test DUT and stream data to server.',
                                          formatter_class = argparse.ArgumentDefaultsHelpFormatter,
                                          description = _description,
                                          epilog = _epilog)
    parser_client.set_defaults(func = start_client)
    parser_client.add_argument(
        dest = 'ip_address',
        type = str,
        help = 'IP address of the server.',
    )
    parser_client.add_argument('-v',
                               action = 'count',
                               dest = 'verbose',
                               default = 0,
                               help = 'Set whether to verbose or not n')

    parser_client.add_argument('-p', dest = 'port', type = int, help = 'Server port to connect to.', default = 2154)



    parser_client.add_argument('-fms',
                               '--freq-monitor-data',
                               metavar = 'FREQ',
                               dest = 'freq_monitor_data',
                               type = int,
                               help = 'Frequency of the Data monitor thread.',
                               default = 5)



    parser_client.add_argument('--log_rotate_interval',
                               metavar = 'MINUTES',
                               dest = 'log_rotate_interval',
                               type = int,
                               help = 'Interval in minutes to rotate the log file.',
                               default = 10)


    parser_client.add_argument('--log_folder',
                               metavar = 'PATH',
                               dest = 'log_folder',
                               type = str,
                               help = 'Folder to store the log files.',
                               default = 'logs_client/')

    parser_server = subparsers.add_parser('server',
                                          help = 'Receive and log data from client.',
                                          formatter_class = argparse.ArgumentDefaultsHelpFormatter,
                                          description = _description,
                                          epilog = _epilog)
    parser_server.set_defaults(func = start_server)

    parser_server.add_argument('-v',
                               action = 'count',
                               dest = 'verbose',
                               default = 0,
                               help = 'Set whether to verbose or not n')

    parser_server.add_argument(dest = 'client_ip', type = str, help = 'IP Address to ping regularly')

    parser_server.add_argument('-p',
                               dest = 'port',
                               type = int,
                               help = 'Port to listen for incom<ing connections.',
                               default = 2154)

    parser_server.add_argument('-t',
                               dest = 'timeout',
                               type = int,
                               help = 'Timeout in seconds before restarting the Raspberry Pi',
                               default = 120)

    parser_server.add_argument("--no-power-cycle",
                               dest = "no_power_cycle",
                               action = "store_true",
                               help = "Do not power cycle the DUT",
                               default = False)

    parser_server.add_argument("--fallback-power-switch",
                               dest = "fallback_power_switch",
                               action = "store_true",
                               help = "Use the fallback API for the power switch",
                               default = False)

    parser_server.add_argument('--switch_id',
                               dest = 'switch_id',
                               type = int,
                               help = 'ID of the power switch',
                               default = 6)

    parser_server.add_argument('--switch_ip',
                               dest = 'switch_ip',
                               type = str,
                               help = 'ID of the power switch',
                               default = '192.168.0.100')

    parser_server.add_argument('--switch_password',
                               dest = 'switch_password',
                               type = str,
                               help = 'Password of the power switch',
                               default = '1234')

    parser_server.add_argument('--switch_username',
                               dest = 'switch_username',
                               type = str,
                               help = 'Username of the power switch',
                               default = 'snmp')

    parser_server.add_argument('-l',
                               dest = 'ip_address',
                               type = str,
                               help = 'IP address to listen for incoming connections.',
                               default = '0.0.0.0')

    parser_server.add_argument('-u',
                               '--user',
                               metavar = 'USER',
                               dest = 'user',
                               type = str,
                               help = 'User to connect to via SSH to download log files.',
                               default = 'trikarenos')

    parser_server.add_argument('-d',
                               '--directory',
                               metavar = 'DIR',
                               dest = 'directory',
                               type = str,
                               help = 'Folder on client to download log files from.',
                               default = '/opt/trikaneros_tester/logs_client/')

    parser_server.add_argument('--log_fetch_interval',
                               metavar = 'MINUTES',
                               dest = 'log_fetch_interval',
                               type = float,
                               help = 'Interval in minutes to fetch the log file.',
                               default = 10)

    parser_server.add_argument('--log_folder',
                               metavar = 'PATH',
                               dest = 'log_folder',
                               type = str,
                               help = 'Folder to store the log files.',
                               default = 'logs_server/')

    # Parse arguments and start client or server
    args = parser.parse_args()
    args.func(args)


def start_server(args):
    from Trikaneros_Tester.Server import Server
    server = Server(args = args)
    server.start()


def start_client(args):
    from Trikaneros_Tester.Client import Client
    try:
        client = Client(args = args)
        client.start()
    except SystemExit as e:
        os._exit(e.code)
    except:
        print("Uncatched Error! This will not be logged :( ")
        traceback.print_exc()
        os.system('sudo kill -9 %d' % os.getpid())


if __name__ == '__main__':
    main()
