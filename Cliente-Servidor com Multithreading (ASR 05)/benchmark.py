"""Experimento de desempenho (ASR 05).

Para cada configuração, sobe o servidor, envia as MESMAS N requisições geradas
automaticamente (mesma semente) e mede o tempo total até receber todas as
respostas. Repete REPS vezes e reporta média e desvio padrão.

Configurações:
  A  servidor single-thread  + cliente sequencial   (ASR 04)
  B  servidor multithread    + cliente sequencial   (multithread só no servidor)
  C  servidor multithread    + cliente multithread  (ASR 05)
  D  servidor single-thread  + cliente multithread  (extra: só o cliente em threads)

Uso: python benchmark.py [-n 200] [--reps 5] [--atrasos 0 0.02]
"""
import argparse
import csv
import os
import socket
import statistics
import subprocess
import sys
import time

import client_auto as ca
from constCS import HOST, PORT

PASTA = os.path.dirname(os.path.abspath(__file__))

CONFIGS = [
    ("A", "single-thread (ASR 04)", "server.py", "sequencial"),
    ("B", "multithread só no servidor", "server_mt.py", "sequencial"),
    ("C", "multithread cliente + servidor", "server_mt.py", "threads"),
    ("D", "(extra) cliente multithread, servidor single", "server.py", "threads"),
]


def iniciar_servidor(script, porta, atraso):
    proc = subprocess.Popen(
        [sys.executable, os.path.join(PASTA, script), "--porta", str(porta),
         "--atraso", str(atraso), "--silencioso"],
        cwd=PASTA, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):  # espera o servidor aceitar conexões
        try:
            socket.create_connection((HOST, porta), timeout=0.2).close()
            return proc
        except OSError:
            time.sleep(0.05)
    proc.kill()
    raise RuntimeError(f"servidor {script} não subiu na porta {porta}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--requisicoes", type=int, default=200)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--atrasos", type=float, nargs="+", default=[0.0, 0.02],
                    help="atraso artificial por requisição no servidor (s)")
    ap.add_argument("--semente", type=int, default=42)
    ap.add_argument("--porta", type=int, default=PORT)
    ap.add_argument("--max-simultaneas", type=int, default=50)
    args = ap.parse_args()

    reqs = ca.gerar_requisicoes(args.requisicoes, args.semente)
    linhas_csv = []

    for atraso in args.atrasos:
        print(f"\n### Atraso artificial no servidor: {atraso * 1000:.0f} ms | "
              f"{args.requisicoes} requisições | {args.reps} repetições\n", flush=True)
        medias_total = {}
        tabela = []
        for chave, nome, script, modo in CONFIGS:
            proc = iniciar_servidor(script, args.porta, atraso)
            try:
                ca.executar(modo, reqs[:10], args.porta, args.max_simultaneas)  # aquecimento
                totais, lat_med, lat_p95, incorretas = [], [], [], 0
                for rep in range(args.reps):
                    total, resp, lat = ca.executar(modo, reqs, args.porta, args.max_simultaneas)
                    r = ca.resumir(total, lat)
                    erradas = ca.contar_incorretas(reqs, resp)
                    totais.append(total)
                    lat_med.append(r["lat_media_ms"])
                    lat_p95.append(r["lat_p95_ms"])
                    incorretas += erradas
                    linhas_csv.append([atraso, chave, nome, rep + 1, round(total, 4),
                                       round(r["lat_media_ms"], 3), round(r["lat_p95_ms"], 3), erradas])
            finally:
                proc.terminate()
                proc.wait()
            media = statistics.mean(totais)
            dp = statistics.stdev(totais) if len(totais) > 1 else 0.0
            medias_total[chave] = media
            tabela.append((chave, nome, media, dp, statistics.mean(lat_med),
                           statistics.mean(lat_p95), args.requisicoes / media, incorretas))

        print("| Config | Descrição | Tempo total (s) | Latência média (ms) | p95 (ms) | Vazão (req/s) | Speedup vs A | Incorretas |")
        print("|---|---|---|---|---|---|---|---|")
        for chave, nome, media, dp, lm, p95, vazao, inc in tabela:
            print(f"| {chave} | {nome} | {media:.3f} ± {dp:.3f} | {lm:.2f} | {p95:.2f} | "
                  f"{vazao:.0f} | {medias_total['A'] / media:.2f}x | {inc} |")
        sys.stdout.flush()

    with open(os.path.join(PASTA, "resultados.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["atraso_s", "config", "descricao", "repeticao", "total_s",
                    "lat_media_ms", "lat_p95_ms", "incorretas"])
        w.writerows(linhas_csv)
    print("\nDados brutos salvos em resultados.csv")


if __name__ == "__main__":
    main()
