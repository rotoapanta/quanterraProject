# <p align="center">Quanterra Metrics

<p align="center">The "Quanterra Metrics" project focuses on collecting and monitoring data related to Quanterra seismic digitizers using the Zabbix monitoring platform. This project allows monitoring the status and performance of Quanterra digitizers, providing IT administrators with a detailed view of the equipment status.
The main objective of this project is to automate the collection of key information from Quanterra seismic digitizers, and then present this data in an organized and accessible manner through the Zabbix platform. This makes it easier to identify problems early, track performance, and make informed decisions for equipment maintenance.
Welcome to "Quanterra Metrics!" Read on for more details on how to start using this project to improve the management of your Quanterra seismic digitizers and other devices.</p>

##

![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)
[![GitHub issues](https://img.shields.io/github/issues/rotoapanta/botZabbixPackage)](https://github.com/rotoapanta/botZabbixPackage/issues)
![GitHub repo size](https://img.shields.io/github/repo-size/rotoapanta/botZabbixPackage)
![GitHub last commit](https://img.shields.io/github/last-commit/rotoapanta/botZabbixPackage)
![GitHub commit merge status](https://img.shields.io/github/commit-status/rotoapanta/botZabbixPackage/master/d8b7bfe)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/gpl-2.0)
![Discord](https://img.shields.io/discord/996422496842694726)
[![Discord Invite](https://img.shields.io/badge/discord-join%20now-green)](https://discord.gg/Gs9b3HFd)
![GitHub forks](https://img.shields.io/github/forks/rotoapanta/botZabbixPackage?style=social)

# Contents

* [Getting started](#getting-started)
    * [Getting started with Zabbix and Quanterra](#getting-started-with-zabbix-and-quanterra)
    * [Requirements](#requirements)
    * [Components Description](#components-description)
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

This project consists of the following components:

- json_files/
  - host_reachable.json 
  - host_rejected.json
  - utils/
    - __init__.py
    - extract_data.py
    - json_reader.py
    - zabbix_host_processing.py
  - zabbix/
    - __init__.py
    - zabbix.py
- config.ini
- main.py
- requirements.txt
- run_zabbix_quanterra.sh

- `utils/`: This directory contains utility modules for the project.
  - `init.py`: An empty file that marks the directory as a Python package.
  - `config_reader.py`: This module is responsible for reading the configuration file (config.ini). It uses the configparser library to parse the file and extract the required configuration parameters.
  - `logging_utils.py`: A module containing utility functions for logging.
 - `zbx_bot/`: This directory contains modules related to the Zabbix bot functionality.
   - `init.py`: An empty file that marks the directory as a Python package.
   - `telegram_bot.py`: A module that handles the Telegram bot functionality.
   - `zabbix.py`: A module that interacts with the Zabbix monitoring system.
- `app.py`: The main application file where the bot is initialized and run.
- `app.log`: A log file where application logs are stored.
- `config.ini`: A configuration file that contains settings for the application.
- `requirements.txt`: A file listing the required Python packages and their versions for the project.
- `run_bot_zabbix.sh`: A shell script used to execute the Zabbix bot, possibly with environment setup and specific commands.

# Installation

Follow the instructions to set up and run the project. The run_bot_zabbix.sh script takes care of setting up the environment, checking for the existence of directories and files, creating the conda environment if it doesn't already exist, activating the conda environment, installing the dependencies specified in the requirements.txt file, and running the Python script app. .py with the provided configuration file.

1. Clone the repository:

```shell
https://github.com/rotoapanta/botZabbixProject.git
```
   
2. Navigate to the project directory:

```shell
   cd repository
```

3. Ensure that Anaconda or Miniconda is installed on your system.

4. Run the script:

```shell
   ./run_bot_zabbix.sh
```

# Configuration

1. Open the config.ini file in the project directory.

2. Configure the Zabbix credentials:
   - Set the Zabbix URL in the url field.
   - Enter your Zabbix username in the user field.
   - Provide your Zabbix password in the password field.

3. Configure the Telegram access token:
   - Set your Telegram bot token in the token field under the [Telegram] section.

# Running the Application

1. Run the application using the following command:

    ```bash
      python app.py config.ini
    ```
2. The Telegram bot will start and listen for commands.

# Running the Project Automatically with Crontab

To run the Zabbix bot project automatically at specified intervals, you can use the `crontab` utility in Unix-like systems. Follow these steps to set up a cron job:

1. Open the terminal and execute the following command to edit the cron jobs for the current user:

    ```bash
      crontab -e
    ```

2. In the crontab file, add the following line to schedule the execution of the Zabbix bot script:

    ```bash
    * * * * * while true; do cd /path/to/project && python app.py config.ini; sleep 1; done
    ````
Replace /path/to/project with the actual path to the project directory.

3. Save and exit the crontab file. The cron job will be automatically scheduled and executed based on the specified interval.
Note: Ensure that the `run_bot_zabbix.sh` script has executable permissions. If not, you can set the permissions using the following command:

    ```bash
    chmod +x /path/to/project/run_bot_zabbix.sh
    ````
4. The output of the script will be redirected to the app.log file located in the project directory. You can check this file for any logs or error messages.

    ```bash
    tail -f /path/to/project/app.log
    ````

That's it! The Zabbix bot project will now be automatically executed at the scheduled intervals defined in the cron job.

## Environment Variables

Before running the project, make sure to set the following environment variables:

- `ZABBIX_URL`: The URL of the Zabbix instance.
- `ZABBIX_USER`: The username for accessing the Zabbix API.
- `ZABBIX_PASSWORD`: The password for accessing the Zabbix API.
- `TELEGRAM_TOKEN`: The token for accessing the Telegram Bot API.

You can either set these environment variables manually or create a `.env` file in the root directory of the project and populate it with the required values.

Example `.env` file:

## Change Log

* Revision: 1.4 - Add run_bot_zabbix.sh
* Revision: 1.3 - Add requirements.txt
* Revision: 1.2 - Add app.log
* Revision: 1.1 - Code cleaned.
* Revision: 1.0 - Initial commit

## Usage

- Send `/ping` command to the bot in a Telegram chat to initiate a host search and perform a ping test.
- Follow the prompts and instructions provided by the bot to interact and retrieve information from Zabbix.

## Logging

- The application logs are stored in the app.log file in the same directory as app.py.

- You can refer to this log file to track the application's execution and any errors or exceptions that may occur.

## Feedback

If you have any feedback, please reach out to us at robertocarlos.toapanta@gmail.com

## Support

For support, email robertocarlos.toapanta@gmail.com or join our Discord channel.

## License

[GPL v2](https://www.gnu.org/licenses/gpl-2.0)

## Autors
- [@rotoapanta](https://github.com/rotoapanta)

## More Info

* [Official documentation for py-zabbix](https://py-zabbix.readthedocs.io/en/latest/)
* [GitHub py-zabbix](https://github.com/adubkov/py-zabbix)
* [Install py-zabbix 1.1.7](https://pypi.org/project/pyzabbix/)
* [Install pyserial 3.5](https://pypi.org/project/pyserial/)

## Links
[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/roberto-carlos-toapanta-g/)
[![twitter](https://img.shields.io/badge/twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/rotoapanta)


