# Python Server Project

## Overview
This project consists of a server that manages multiple DUT (Device Under Test) instances. The server is responsible for initializing DUTs, monitoring their status, and handling their lifecycle, including power cycling and restarting monitoring threads if necessary.

## Files
- `log_id.py`: Contains constants used throughout the project for logging and error identification.
- `server.py`: Implements the main server logic, including initializing DUTs, starting and monitoring their threads, and handling power cycling.

## Features
- Initialization of DUTs: Automatically initialize and manage multiple DUT instances.
- Power Cycling: Power cycle DUTs to ensure they are properly reset and operational.
- Monitoring: Continuously monitor the status of DUTs and restart their monitoring threads if they become unresponsive.