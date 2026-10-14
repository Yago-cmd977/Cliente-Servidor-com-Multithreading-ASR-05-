"""Funcionalidades do servidor (ASR 04) e processamento de requisições.

Este módulo é compartilhado pelo servidor single-thread (server.py) e pelo
servidor multithread (server_mt.py), o que garante que o comportamento
funcional seja idêntico nas duas versões.

Protocolo: uma requisição por linha, em JSON.
  Requisição: {"text": "Hello World", "ops": ["upper", "reverse", "words"]}
  Resposta:   {"results": {...}, "errors": {...}}
"""
import hashlib
import json
import time

VOGAIS = set("aeiouAEIOUáéíóúâêôãõàÁÉÍÓÚÂÊÔÃÕÀ")


def palindromo(t):
    limpo = [c.lower() for c in t if c.isalnum()]
    return limpo == limpo[::-1]


# Funcionalidades oferecidas aos clientes
OPERACOES = {
    "upper": lambda t: t.upper(),
    "lower": lambda t: t.lower(),
    "reverse": lambda t: t[::-1],
    "length": lambda t: len(t),
    "words": lambda t: len(t.split()),
    "vowels": lambda t: sum(1 for c in t if c in VOGAIS),
    "palindrome": palindromo,
    "sha256": lambda t: hashlib.sha256(t.encode()).hexdigest(),
}


def processar(linha, atraso=0.0):
    """Interpreta a requisição (bytes com JSON) e executa cada operação pedida.

    atraso: segundos de espera ao final do processamento. Serve apenas para
    simular uma requisição "cara" (ex.: acesso a disco ou banco de dados) nos
    experimentos. O padrão (0) não altera o comportamento.
    """
    try:
        req = json.loads(linha.decode())
        texto, ops = req["text"], req["ops"]
        if not isinstance(texto, str) or not isinstance(ops, list):
            raise ValueError
    except (ValueError, KeyError, TypeError):
        return {"results": {}, "errors": {"requisicao": 'formato esperado: {"text": str, "ops": [str, ...]}'}}

    resultados, erros = {}, {}
    for op in ops:
        if op in OPERACOES:
            resultados[op] = OPERACOES[op](texto)
        else:
            erros[op] = "operação desconhecida (disponíveis: " + ", ".join(OPERACOES) + ")"

    if atraso > 0:
        time.sleep(atraso)
    return {"results": resultados, "errors": erros}


def serializar(resposta):
    """Resposta -> uma linha JSON em bytes."""
    return (json.dumps(resposta, ensure_ascii=False) + "\n").encode()
