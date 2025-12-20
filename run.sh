#!/bin/bash
# Script para executar a API IMC usando o ambiente virtual

cd "$(dirname "$0")"
source .venv/bin/activate
python main.py

