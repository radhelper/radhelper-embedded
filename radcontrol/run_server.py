import argparse
import sys
import yaml
from .host.server import Server


def in_venv():
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def load_config(config_file):
    try:
        with open(config_file, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        sys.exit(f"Error: The configuration file '{config_file}' was not found.")
    except yaml.YAMLError:
        sys.exit(f"Error: The configuration file '{config_file}' is not valid YAML.")


def add_arguments_from_config(parser, config):
    existing_args = set()
    for section, params in config.items():
        for param, details in params.items():
            arg_name = f"--{param.replace('_', '-')}"
            if arg_name in existing_args:
                continue
            existing_args.add(arg_name)
            parser.add_argument(
                arg_name,
                dest=param,
                type=type(details["value"]),
                default=details["value"],
                help=details["help"],
            )


def get_dut_info(config_file):
    config = load_config(config_file)

    uart_info = {
        "number_connected_uarts": len(config),
        "duts": config,
    }

    return uart_info


def start_server(args):
    server = Server(args=args)
    # Assuming some signal to stop the server, for example, a keyboard interrupt
    try:
        while True:
            pass
    except KeyboardInterrupt:
        server.stop()


def run():
    if not in_venv():
        sys.exit(
            "Please run this script from within the virtual environment.\n"
            "To activate the virtual environment, run:\nsource .venv/bin/activate"
        )

    _epilog = (
        "This software acts as the radiation testing utility from University of Twente"
    )
    _description = (
        "Radiation tester utility to control devices during radiation testing"
    )

    # Load configuration
    config = load_config("server_config.yaml")

    # Setup parser
    parser = argparse.ArgumentParser(description=_description, epilog=_epilog)

    # Common parser for server
    parser.set_defaults(func=start_server)

    # Dynamically add arguments from config
    add_arguments_from_config(parser, config)

    # Parse arguments and start server
    args = parser.parse_args()

    # Get UART info
    dut_config = get_dut_info("dut_config.yaml")
    # print(dut_config)
    args.uart_info = dut_config

    # Start process (Server)
    if args.func:
        args.func(args)


if __name__ == "__main__":
    run()
