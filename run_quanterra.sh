#!/bin/bash

# Define variables
ENV_NAME="quanterra_env"
CONDA_PATH="/home/rotoapanta/anaconda3/bin/conda"
SCRIPT_PATH="/home/rotoapanta/Documentos/Proyects/quanterraProject/"
PYTHON_SCRIPT="main.py"

# Añadir la línea para configurar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_PATH}"

# Validar la existencia de rutas y archivos
if [ ! -d "${SCRIPT_PATH}" ]; then
    echo "El directorio del script no existe: ${SCRIPT_PATH}"
    exit 1
fi

if [ ! -f "${SCRIPT_PATH}/${PYTHON_SCRIPT}" ]; then
    echo "El script Python no existe: ${SCRIPT_PATH}/${PYTHON_SCRIPT}"
    exit 1
fi

# Ejecutar el script Python dentro del entorno Conda
"${CONDA_PATH}" run -n "${ENV_NAME}" python "${SCRIPT_PATH}/${PYTHON_SCRIPT}" 2>&1


