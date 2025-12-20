#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI, Query, HTTPException
from typing import Optional

app = FastAPI(title="API IMC", description="API para classificação de IMC", version="1.0.0")


def classificar_imc(imc: float) -> dict:
    """
    Classifica o IMC conforme a tabela fornecida.
    
    Args:
        imc: Valor do índice de massa corporal
        
    Returns:
        dict: Dicionário com classificação, grau de obesidade e mensagem
    """
    if imc < 18.5:
        return {
            "classificacao": "Magreza",
            "obesidade_grau": 0,
            "mensagem": "A pessoa está abaixo do peso (Magreza)"
        }
    elif 18.5 <= imc <= 24.9:
        return {
            "classificacao": "Normal",
            "obesidade_grau": 0,
            "mensagem": "A pessoa está com peso normal"
        }
    elif 25.0 <= imc <= 29.9:
        return {
            "classificacao": "Sobrepeso",
            "obesidade_grau": 1,
            "mensagem": "A pessoa está com sobrepeso"
        }
    elif 30.0 <= imc <= 39.9:
        return {
            "classificacao": "Obesidade",
            "obesidade_grau": 2,
            "mensagem": "A pessoa está com obesidade"
        }
    else:  # imc >= 40.0
        return {
            "classificacao": "Obesidade Grave",
            "obesidade_grau": 3,
            "mensagem": "A pessoa está com obesidade grave"
        }


@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "mensagem": "API de Classificação de IMC",
        "endpoint": "/imc?valor=<numero>",
        "exemplo": "/imc?valor=25.5"
    }


@app.get("/imc")
async def calcular_imc(valor: float = Query(..., description="Valor do IMC", gt=0)):
    """
    Recebe o valor do IMC e retorna a classificação.
    
    Args:
        valor: Valor do índice de massa corporal (deve ser maior que 0)
        
    Returns:
        dict: Resultado com classificação, grau de obesidade e mensagem
    """
    try:
        resultado = classificar_imc(valor)
        return {
            "imc": valor,
            **resultado
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar IMC: {str(e)}")


@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5600)

