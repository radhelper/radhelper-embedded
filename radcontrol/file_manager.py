import sys
import yaml
import subprocess


def open_tmux_window():
    subprocess.Popen(["gnome-terminal", "--", "bash", "-c", "./radcontrol/tmux.sh"])


def add_tmux_window(session_name, window_name, command):
    subprocess.run(
        ["tmux", "new-window", "-t", session_name, "-n", window_name, command]
    )


def remove_tmux_window(session_name, window_name):
    subprocess.run(["tmux", "kill-window", "-t", f"{session_name}:{window_name}"])


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
