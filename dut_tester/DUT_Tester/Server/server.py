import subprocess
import paramiko
import socket
import time

import DUT_Tester.power_switch.powerswitch as ps


class StateMachine:
    def __init__(self):
        self.states = {
            "Initial_state",
            "physically_connected",
            "physically_connected_and_responsive",
            "physically_connected_but_unresponsive",
            "lost_physical_connection",
        }
        self.current_state = "Initial_state"
        self.output = 0
        self.do_time_sync = False

    def transition(self, x, y):
        if self.current_state == "Initial_state":
            self.do_time_sync = True
            if x == True:
                self.current_state = "physically_connected"
        elif self.current_state == "physically_connected":
            if x == False:
                self.current_state = "lost_physical_connection"
            elif x == True and y == False:
                self.current_state = "physically_connected"
            elif x == True and y == True:
                self.current_state = "physically_connected_and_responsive"
        elif self.current_state == "physically_connected_and_responsive":
            if x == False:
                self.current_state = "lost_physical_connection"
            elif x == True and y == False:
                self.current_state = "physically_connected_but_unresponsive"
            elif x == True and y == True:
                self.current_state = "physically_connected_and_responsive"
        elif self.current_state == "physically_connected_but_unresponsive":
            if x == False:
                self.current_state = "lost_physical_connection"
            elif x == True and y == False:
                self.current_state = "physically_connected_but_unresponsive"
            elif x == True and y == True:
                self.current_state = "physically_connected_and_responsive"
        elif self.current_state == "lost_physical_connection":
            if x == False:
                self.current_state = "lost_physical_connection"
            elif x == True:
                self.current_state = "physically_connected_but_unresponsive"

    def process_input(self, x, y):
        self.output = 0  # Reset output to 0
        self.transition(x, y)
        return self.output

    def toString(self):
        return "current state: " + self.current_state + ", output: " + str(self.output)


def ping_pi(ip_address):
    try:
        response = subprocess.run(
            ["ping", "-c", "1", ip_address],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if response.returncode == 0:
            # print(f"{ip_address} is alive")
            return True
        else:
            # print(f"{ip_address} is down or not responding.")
            return False
    except Exception as e:
        print(f"Error pinging {ip_address}: {e}")
        return False


def ssh_connect(ip_address, username, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip_address, username=username, password=password)
        return ssh
    except Exception as e:
        print(f"Error connecting to {ip_address} via SSH: {e}")
        return None


def is_ssh_connection_active(client, host, port, username, password, ssh_timeout):
    try:
        # Connect to the SSH server using a password
        client.connect(
            host, port=port, username=username, password=password, timeout=ssh_timeout
        )

        # If the connection is successful, return True
        return True

    except (paramiko.AuthenticationException, paramiko.SSHException, socket.error) as e:
        # print(f"Error connecting to {ip_address} via SSH: {e}")
        # If there is an exception, return False
        return False


def run_command_over_ssh(ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    # while not stdout.channel.exit_status_ready():
    #     # Print stdout
    #     if stdout.channel.recv_ready():
    #         alldata = stdout.channel.recv(1024)
    #         while stdout.channel.recv_ready():
    #             alldata += stdout.channel.recv(1024)

    #         print(str(alldata, "utf8"))

    #     # Print stderr
    #     if stderr.channel.recv_stderr_ready():
    #         errdata = stderr.channel.recv_stderr(1024)
    #         while stderr.channel.recv_stderr_ready():
    #             errdata += stderr.channel.recv_stderr(1024)

    #         print(str(errdata, "utf8"))

    print("Command execution completed.")


if __name__ == "__main__":
    ip_address = "192.168.0.32"
    username = "pihub"
    password = "123456789"
    port = 22  # Default SSH port

    fsm = StateMachine()
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_timeout = 5  # 5 seconds

    while True:
        # print(fsm.toString())
        ping_pi_ = ping_pi(ip_address)
        ssh_is_active = is_ssh_connection_active(
            ssh_client, ip_address, port, username, password, ssh_timeout
        )
        fsm.process_input(ping_pi_, ssh_is_active)

        if (
            fsm.current_state == "physically_connected_and_responsive"
            and fsm.do_time_sync
        ):
            # print("Time sync")
            if ssh_is_active:
                time_sync_command = "sudo ~/radhelper-embedded/dut_tester/util/time_sync/time_sync_script.sh"
                print("sync")
                run_command_over_ssh(ssh_client, time_sync_command)
                # wait for 7 seconds for the time sync to complete
                time.sleep(7)

                # code to start the DUT script
                print("DUT")
                run_command_over_ssh(
                    ssh_client,
                    "cd ~/radhelper-embedded/dut_tester/; pwd; source .venv/bin/activate; python -m DUT_Tester client 192.168.0.32",
                )

            fsm.do_time_sync = False

        elif fsm.current_state == "lost_physical_connection":
            print("lost connection")
            # Do a power cycle: call the pwer cycle script
            ps.power_cycle(8, "192.168.0.100")

            # wait for 5 seconds
            time.sleep(5)
            # Reset the state machine
            fsm.current_state = "Initial_state"
            fsm.output = 0
            fsm.do_time_sync = False

        # print(fsm.toString())
        time.sleep(2)  # Check every 2 seconds
