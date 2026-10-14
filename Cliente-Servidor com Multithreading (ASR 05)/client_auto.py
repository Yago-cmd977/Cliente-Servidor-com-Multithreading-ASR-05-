"""Cliente com geração automática de requisições (ASR 05).

Gera N requisições aleatórias (texto e operações sorteados, com semente fixa
para que todas as configurações do experimento recebam exatamente as mesmas
requisições) e as envia ao servidor em um de dois modos:

  threads     cada requisição é enviada por uma NOVA thread (versão multithread)
  sequencial  as requisições são enviadas uma após a outra, na thread principal
              (usado como linha de base nos experimentos)

Cada requisição usa uma conexão própria: conecta, envia, aguarda a resposta, fecha.

Uso: python client_auto.py [-n 100] [--modo threads|sequencial] [--semente 42]
"""
import argparse
import json
import random
import statistics
import string
import threading
import time
from socket import *
from constCS import *
from operacoes import OPERACOES, processar


def gerar_requisicoes(n, semente=42):
    """Gera n requisições aleatórias (reprodutíveis a partir da semente)."""
    rng = random.Random(semente)
    nomes_ops = list(OPERACOES)
    reqs = []
    for _ in range(n):
        palavras = ["".join(rng.choices(string.ascii_lowercase, k=rng.randint(3, 10)))
                    for _ in range(rng.randint(5, 40))]
        ops = rng.sample(nomes_ops, rng.randint(2, 5))
        reqs.append({"text": " ".join(palavras), "ops": ops})
    return reqs


def enviar(req, porta=PORT):
    """Envia uma requisição e aguarda a resposta. Retorna (resposta, latência em s)."""
    t0 = time.perf_counter()
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.settimeout(30)
            s.connect((HOST, porta))
            s.sendall((json.dumps(req) + "\n").encode())
            with s.makefile("rb") as f:
                linha = f.readline()
        resposta = json.loads(linha.decode())
    except (OSError, ValueError):
        resposta = None
    return resposta, time.perf_counter() - t0


def executar(modo, reqs, porta=PORT, max_simultaneas=50):
    """Envia todas as requisições. Retorna (tempo total em s, respostas, latências)."""
    n = len(reqs)
    respostas, latencias = [None] * n, [0.0] * n
    t0 = time.perf_counter()

    if modo == "sequencial":
        for i, req in enumerate(reqs):
            respostas[i], latencias[i] = enviar(req, porta)
    else:
        # Uma thread nova por requisição. O semáforo limita quantas ficam vivas ao
        # mesmo tempo (evita estourar o limite de arquivos abertos do sistema).
        vagas = threading.BoundedSemaphore(max_simultaneas)

        def trabalho(i, req):
            try:
                respostas[i], latencias[i] = enviar(req, porta)
            finally:
                vagas.release()

        threads = []
        for i, req in enumerate(reqs):
            vagas.acquire()
            t = threading.Thread(target=trabalho, args=(i, req))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    return time.perf_counter() - t0, respostas, latencias


def contar_incorretas(reqs, respostas):
    """Teste funcional: compara cada resposta com o resultado calculado localmente."""
    return sum(1 for req, resp in zip(reqs, respostas)
               if resp != processar(json.dumps(req).encode()))


def resumir(total, latencias):
    lat = sorted(latencias)
    return {
        "total_s": total,
        "vazao": len(lat) / total,
        "lat_media_ms": statistics.mean(lat) * 1000,
        "lat_p95_ms": lat[int(0.95 * (len(lat) - 1))] * 1000,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--requisicoes", type=int, default=100)
    ap.add_argument("--modo", choices=["threads", "sequencial"], default="threads")
    ap.add_argument("--semente", type=int, default=42)
    ap.add_argument("--porta", type=int, default=PORT)
    ap.add_argument("--max-simultaneas", type=int, default=50,
                    help="máximo de threads ativas ao mesmo tempo (modo threads)")
    ap.add_argument("--mostrar", type=int, default=3, help="quantas respostas imprimir")
    args = ap.parse_args()

    reqs = gerar_requisicoes(args.requisicoes, args.semente)
    total, respostas, lat = executar(args.modo, reqs, args.porta, args.max_simultaneas)

    for req, resp in list(zip(reqs, respostas))[:args.mostrar]:
        print("req :", json.dumps(req)[:90], "...")
        print("resp:", json.dumps(resp, ensure_ascii=False)[:90], "...")
    r = resumir(total, lat)
    print(f"\nmodo={args.modo}  requisições={args.requisicoes}")
    print(f"tempo total: {r['total_s']:.3f} s  |  vazão: {r['vazao']:.0f} req/s")
    print(f"latência média: {r['lat_media_ms']:.2f} ms  |  p95: {r['lat_p95_ms']:.2f} ms")
    print(f"respostas incorretas: {contar_incorretas(reqs, respostas)}")
