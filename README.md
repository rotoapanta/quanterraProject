# <p align="center">Quanterra with Zabbix

<p align="center">This project aims to monitor the health status of Quanterra using Zabbix.</p>

##

[![Python](https://img.shields.io/badge/Python-3.11-brightgreen)](https://www.python.org/)
[![Zabbix](https://img.shields.io/badge/Zabbix-4.6-orange)](https://www.zabbix.com/)
![GitHub issues](https://img.shields.io/github/issues/rotoapanta/quanterraProject)
![GitHub repo size](https://img.shields.io/github/repo-size/rotoapanta/quanterraProject)
![GitHub last commit](https://img.shields.io/github/last-commit/rotoapanta/quanterraProject)
![GitHub commit merge status](https://img.shields.io/github/commit-status/rotoapanta/quanterraProject/master/9b53f1d)
![Discord](https://img.shields.io/discord/1104588661321908335)
[![Discord Invite](https://img.shields.io/badge/discord-join%20now-green)](https://discord.gg/bf6rWDbJ)
[![Docker](https://img.shields.io/badge/Docker-No-brightgreen)](https://www.docker.com/)
[![GitHub](https://img.shields.io/badge/GitHub-Project-brightgreen)](https://github.com/rotoapanta/gpsNetRsProject.git)
[![Linux](https://img.shields.io/badge/Linux-Supported-brightgreen)](https://www.linux.org/)
[![Windows](https://img.shields.io/badge/Windows-Supported-brightgreen)](https://www.microsoft.com/)
[![Crontab](https://img.shields.io/badge/Crontab-Supported-brightgreen)](#installation)
[![Author 1](https://img.shields.io/badge/Roberto%20-Toapanta-brightgreen)](https://www.linkedin.com/in/roberto-carlos-toapanta-g/)
[![Version](https://img.shields.io/badge/Version-1.4-brightgreen)](#change-log)
![GitHub forks](https://img.shields.io/github/forks/rotoapanta/gpsNetRsProject?style=social)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/gpl-2.0)

# Contents

- [Getting started](#getting-started)
  - [Getting started with Zabbix and Quanterra](#getting-started-with-zabbix-and-quanterra)
  - [Features](#features)
  - [Requirements](#requirements)
  - [Components Description](#components-description)
* [Installation](#installation)
* [Configuration](#configuration)
* [Running the Application](#running-the-application)
* [Running the Project Automatically with Crontab](#running-the-project-automatically-with-crontab)
* [Environment Variables](#environment-variables)
* [Change Log](#change-log)
* [Running Tests](#running-tests)
* [Usage/Examples](#usage-examples)
* [Feedback](#feedback)
  * [Support](#support)
  * [License](#license)
  * [Autors](#autors)
  * [More Info](#more-info)
  * [Links](#links)

# Getting started

## Getting started with Zabbix and Quanterra

Welcome to the project! This guide will help you get started with setting up and running the application.

The project is a Python-based application designed to obtain the metrics (voltage, current, number of satellites, disk capacity) of Quanterra seismic digitizers. 

Let’s get started!

### Features

- Retrieve various metrics from Quanterra devices.
- Send collected data to Zabbix for analysis.
- Easily schedule monitoring tasks using `crontab`.
 
## Requirements

Before you get started, make sure you have the following:

- Python 3.11 or higher installed on your system.
- [Anaconda](https://www.anaconda.com/) for creating and managing Conda environments.
- A Zabbix server for storing and analyzing the collected data.
- Basic knowledge of using `crontab` for scheduling tasks.
- Quanterra devices
- Computer running Anaconda on Windows, Linux or macOS (in this case macOS is used).

## Components Description

The project consists of the following components:

- quanterraProject/
  - api/
    - __init__.py
    - api_zbx_processing.py
  - logs/
    - __init__.py
    - aaaa-mm-dd_quanterra.log
  - templates/
    - zbx_export_templates.xml
  - test/
    - __init__.py
    - test_quanterra_project.py
  - utils/
    - __init__.py
    - utilities.py
  - zabbix/
    - __init__.py
    - zabbix_sender.py
  - config.ini
  - main.py
  - requirements.txt
  - run_quanterra.sh
  - setup.py

- `api/`: This package contains modules related to the project's API functionality.
  - `init.py`: An empty file that marks the directory as a Python package. 
  - `api_zbx_processing.py`: Module for processing Zabbix data through the API.
- `logs/`: Directory for storing log files.
  - `init.py`: An empty file that marks the directory as a Python package.
  - `aaaa-mm-dd_gps_netrs.log`: File is a project log that records events and errors.
  - `gps_netrs_crontab.log`: Log file that captures the execution details of the project's scheduled tasks.
- `templates/`: Directory for Zabbix templates.
- `test/`: Package for unit tests.
  - `init.py`: An empty file that marks the directory as a Python package.
  - `test_gps_netrs_project.py`: File contains unit tests for the GPS NetRS Project.
- `utils/`: Package for utility functions.
  - `init.py`: An empty file that marks the directory as a Python package.
  - `utilities.py`: Script containing reusable functions that provide common functionality for the project.
- `zabbix/`: Package for Zabbix Integration.
  - `zabbix_sender.py`: A script for sending data to Zabbix
- `config.ini`: Project configuration file with project-specific details.
- `main.py`: The main script of the project, which likely contains the core logic.
- `requirements.txt`: A list of project dependencies, typically used for package management.
- `run_gps_netrs.sh`: A shell script for executing the project.
- `setup.py`: A script used for packaging and distribution of the project.
- `zabbix_sender.py`: A script responsible for sending data to Zabbix.

## Installation


1. Clone the repository to your local machine:
  
  ```bash
   git clone https://github.com/rotoapanta/quanterraProject.git
  ```
2.Create the `config.ini` in the same directory as the project and configure according to your credentials.

## Configuration

1. Open the config.ini file in the project directory.

2. Configure the Zabbix credentials:

```ini
[zabbix]
zabbix_server = ZABBIX_SERVER_IP_OR_HOSTNAME
zabbix_port = ZABBIX_SERVER_PORT
zabbix_url = ZABBIX_SERVER_URL
zabbix_user = ZABBIX_USERNAME
zabbix_password = ZABBIX_PASSWORD
```

## Running the Application

The run_quanterra.sh shell script is used to set up the environment, activate the Conda environment, install dependencies, and execute the main project script. The script is responsible for the following tasks:

- Setting environment variables.
- Activating the Conda environment.
- Installing project dependencies.
- Validating the existence of directories and files.
- Navigating to the project directory.
- Running the main project script (main.py).

Please review the script's comments for details about its operation and make sure it points to the correct paths for your specific environment.

  ```plaintext
  Note: Ensure that the script has the necessary permissions to execute.
  ```

## Running the Project Automatically with Crontab

To automate the monitoring process, you can use crontab to schedule the execution of the script at specific intervals. The provided run_gps_netrs.sh shell script helps you set up the environment and run the project under cron. 

Here's how to configure and use crontab with the project:

1. Open the crontab configuration for your user by running the following command

  ```bash
   crontab -e
  ```
2. Add an entry to schedule the script to run at regular intervals. For example, to run the script every 10 minutes, add the following line:
  
  ```bash
   */10 * * * * bash /path/to/run_quanterra.sh >> /path/to/logs/quanterra_crontab.log 2>&1
  ```
Be sure to replace /path/to with the actual paths to the run_quanterra.sh script and the desired log file.

Save and exit the crontab editor.

The script will now run automatically at the specified intervals and log its output to the specified log file.

## Environment Variables

Before running the project, make sure to set the following environment variables:

- `zabbix_url` = ZABBIX_SERVER_URL
- `zabbix_user` = ZABBIX_USERNAME
- `zabbix_password` = ZABBIX_PASSWORD
- `digitizer_username` = DIGITIZER_USERNAME
- `digitizer_password` = DIGITIZER_PASSWORD

## Change Log

* Revision: 1.4 - Refactor code
* Revision: 1.3 - Add test unit
* Revision: 1.2 - Add run_gps_netrs.sh
* Revision: 1.1 - Code cleaned.
* Revision: 1.0 - Initial commit

## Running Tests

To run the tests for this project, you have two options:

### Option 1: Using Test Discovery

You can use Python's built-in test discovery to automatically discover and run all tests that follow the naming convention `test_*.py`. Navigate to your project directory and execute the following command:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```
This command will search for and execute all tests within the tests directory and its subdirectories.

### Option 2: Running Specific Test Modules

If you want to run specific test modules or individual tests, you can use the following command. Replace tests.test_module with the appropriate test module you want to run:

```bash
python -m unittest tests.test_quanterra_project
```
This command allows you to execute tests from a particular test module. Adjust test_module to the desired module name.

![Testing](images/img_1.png)
<p align="center">Figure 1. Testing the code</p>

![Data collected](images/img_2.png)
<p align="center">Figure 2. Data collected on the Zabbix Server</p>

![Digitizer input voltage](images/img_3.png)
<p align="center">Figure 3. Digitizer input voltage</p>

![Digitizer temperature](images/img_4.png)
<p align="center">Figure 4. Digitizer temperature</p>

## Usage

To run the project manually, execute the following command:

  ```bash
   python main.py
  ```
For scheduling and automation, refer to the Scheduling with crontab section.

## Feedback

If you have any feedback, please reach out to us at robertocarlos.toapanta@gmail.com

## Support

For support, email robertocarlos.toapanta@gmail.com or join our Discord channel.

## License

[GPL v2](https://www.gnu.org/licenses/gpl-2.0)

## Authors

- [@rotoapanta](https://github.com/rotoapanta)

## More Info

* [Official documentation for py-zabbix](https://py-zabbix.readthedocs.io/en/latest/)
* [Install py-zabbix 1.1.7](https://pypi.org/project/pyzabbix/)

## Links

[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/roberto-carlos-toapanta-g/)
[![twitter](https://img.shields.io/badge/twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/rotoapanta)
