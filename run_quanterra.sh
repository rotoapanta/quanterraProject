#!/bin/bash

# Define variables
ENV_NAME="quanterra_env"
CONDA_PREFIX="/home/rotoapanta/anaconda3/"
SCRIPT_PATH="/home/rotoapanta/Documentos/Proyects/quanterraProject/"
PYTHON_SCRIPT="main.py"
CONFIG_FILE="config.ini"

# Welcome message
echo "Welcome ${USER}."

# Redirect standard output and error to the log
exec 1> >(logger -s -t $(basename $0)) 2>&1

# Configure Conda environment
eval "$(${CONDA_PREFIX}/bin/conda shell.bash hook)"

if [ $? != 0 ]; then
    echo "Error al ejecutar quanterraProject: error en la carga de Conda: CRONTAB_SCRIPT_ERROR" >&2
    exit 1
fi

# Create Conda environment if it doesn't exist
if ! conda env list | grep -q "${ENV_NAME}"; then
    conda create --name ${ENV_NAME} python=3.10
fi

# Activate Conda environment
conda activate ${ENV_NAME}

if [ $? != 0 ]; then
    echo "Error al ejecutar quanterraProject: error al activar el entorno: CRONTAB_SCRIPT_ERROR" >&2
    exit 1
fi

# Install all dependencies from 'requirements.txt'
pip install -r ${SCRIPT_PATH}/requirements.txt

# Validate the existence of paths and files
if [ ! -d "${SCRIPT_PATH}" ]; then
    echo "El directorio del script no existe: ${SCRIPT_PATH}"
    exit 1
fi

if [ ! -f "${SCRIPT_PATH}/${PYTHON_SCRIPT}" ]; then
    echo "El script Python no existe: ${SCRIPT_PATH}/${PYTHON_SCRIPT}"
    exit 1
fi

if [ ! -f "${SCRIPT_PATH}/${CONFIG_FILE}" ]; then
    echo "El archivo de configuración no existe: ${SCRIPT_PATH}/${CONFIG_FILE}"
    exit 1
fi

# Navigate to the Python script directory
cd ${SCRIPT_PATH}

# Run the Python script with the configuration file and redirect standard output to standard error
python ./${PYTHON_SCRIPT}

if [ $? != 0 ]; then
    echo "Error al ejecutar quanterraProject: error al ejecutar main.py: CRONTAB_SCRIPT_ERROR" >&2
    exit 1
fi