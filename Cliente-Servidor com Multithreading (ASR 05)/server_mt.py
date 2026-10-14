"""Servidor multithread (ASR 05).

Arquitetura (como mostrado em aula):
  - a thread principal aceita a conexão e recebe a requisição;
  - ao receber a requisição, dispara uma NOVA thread que a processa, envia a
    resposta ao cliente e fecha a conexão.
Cada conexão carrega exatamente uma requisição.

Uso: python server_mt.py [--porta N] [--atraso SEGUNDOS] [--silencioso]
"""
import argparse
import threading
from socket import *
from constCS import *
from operacoes import processar, serializar

ap = argparse.ArgumentParser()
ap.add_argument("--porta", type=int, default=PORT)
ap.add_argument("--atraso", type=float, default=0.0,
                help="atraso artificial por requisição (s), usado nos experimentos")
ap.add_argument("--silencioso", action="store_true", help="não imprime as requisições")
args = ap.parse_args()


def atender(conn, addr, linha):
    """Executada em uma thread própria: processa e responde uma requisição."""
    try:
        with conn:
            resposta = processar(linha, args.atraso)
            conn.sendall(serializar(resposta))
    except OSError:
        pass  # cliente desconectou antes de receber a resposta
    if not args.silencioso:
        print(f"[{threading.current_thread().name}] requisição de {addr[0]}:{addr[1]} atendida", flush=True)


s = socket(AF_INET, SOCK_STREAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.bind((HOST, args.porta))
s.listen(128)
print(f"Servidor multithread ouvindo em {HOST}:{args.porta}", flush=True)

while True:
    (conn, addr) = s.accept()  # thread principal: aceita a conexão...
    conn.settimeout(5)  # evita que um cliente mudo bloqueie a thread principal
    try:
        with conn.makefile("rb") as entrada:
            linha = entrada.readline()  # ...e recebe a requisição
    except OSError:
        linha = b""
    if not linha:
        conn.close()
        continue
    threading.Thread(target=atender, args=(conn, addr, linha), daemon=True).start()  # nova thread por requisição
