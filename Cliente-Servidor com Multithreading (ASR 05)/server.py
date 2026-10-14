"""Servidor single-thread (ASR 04).

Atende uma conexão por vez e uma requisição por vez: enquanto uma requisição
está sendo processada, as demais esperam na fila de conexões.

Uso: python server.py [--porta N] [--atraso SEGUNDOS] [--silencioso]
"""
import argparse
from socket import *
from constCS import *
from operacoes import processar, serializar

ap = argparse.ArgumentParser()
ap.add_argument("--porta", type=int, default=PORT)
ap.add_argument("--atraso", type=float, default=0.0,
                help="atraso artificial por requisição (s), usado nos experimentos")
ap.add_argument("--silencioso", action="store_true", help="não imprime as requisições")
args = ap.parse_args()

s = socket(AF_INET, SOCK_STREAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.bind((HOST, args.porta))
s.listen(128)  # fila de conexões pendentes (na ASR 04 era 1)
print(f"Servidor single-thread ouvindo em {HOST}:{args.porta}", flush=True)

while True:  # atende um cliente por vez
    (conn, addr) = s.accept()  # retorna novo socket e endereço do cliente
    with conn, conn.makefile("rb") as entrada:
        for linha in entrada:  # uma requisição por linha
            if not args.silencioso:
                print("Requisição de", addr, ":", linha.decode().strip(), flush=True)
            resposta = processar(linha, args.atraso)  # processa na própria thread
            conn.sendall(serializar(resposta))
