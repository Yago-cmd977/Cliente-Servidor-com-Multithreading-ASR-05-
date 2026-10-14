# Relato do experimento — ASR 05

## O que foi implementado

Partindo do código da ASR 04, criei um servidor multithread (`server_mt.py`) e um cliente com geração automática de requisições (`client_auto.py`). No servidor, a thread principal aceita a conexão e recebe a requisição, e uma nova thread processa e responde. No cliente, cada requisição é enviada por uma nova thread. As requisições são geradas aleatoriamente (texto e operações sorteados, semente fixa), então todas as configurações recebem exatamente as mesmas. O servidor single-thread e o multithread usam o mesmo módulo de operações, e o cliente confere cada resposta com o resultado calculado localmente: em todas as execuções houve 0 respostas incorretas, ou seja, o comportamento funcional é idêntico.

## Metodologia

- Quantidade: 200 requisições por execução, 5 repetições por configuração (média ± desvio padrão do tempo total), com um aquecimento antes.
- Ambiente: [preencher: CPU, sistema operacional, versão do Python]. Cliente e servidor na mesma máquina, via `127.0.0.1`.
- Tempo medido: do envio da primeira requisição até o recebimento da última resposta.
- Configurações: **A** servidor single-thread + cliente sequencial (ASR 04); **B** servidor multithread + cliente sequencial (multithread só no servidor); **C** servidor multithread + cliente multithread (ASR 05); **D** (extra) servidor single-thread + cliente multithread.
- Dois cenários: sem atraso (só o processamento real, de microssegundos) e com atraso artificial de 20 ms por requisição no servidor (`time.sleep`), que simula uma requisição que espera por I/O, como acesso a disco ou banco de dados. O atraso é artificial e foi usado para tornar visível o efeito da concorrência.

## Resultados

**Sem atraso (processamento real):**

| Config | Tempo total (s) | Latência média (ms) | Vazão (req/s) | Speedup vs A |
|---|---|---|---|---|
| A single-thread | 0.041 ± 0.004 | 0.20 | 4927 | 1.00x |
| B multithread só no servidor | 0.076 ± 0.012 | 0.38 | 2626 | 0.53x |
| C multithread cliente + servidor | 0.099 ± 0.006 | 16.19 | 2015 | 0.41x |
| D cliente multithread, servidor single | 0.075 ± 0.002 | 14.51 | 2650 | 0.54x |

**Com atraso de 20 ms por requisição:**

| Config | Tempo total (s) | Latência média (ms) | Vazão (req/s) | Speedup vs A |
|---|---|---|---|---|
| A single-thread | 4.176 ± 0.008 | 20.87 | 48 | 1.00x |
| B multithread só no servidor | 4.220 ± 0.011 | 21.09 | 47 | 0.99x |
| C multithread cliente + servidor | 0.133 ± 0.005 | 25.81 | 1507 | 31.47x |
| D cliente multithread, servidor single | 4.135 ± 0.013 | 905.40 | 48 | 1.01x |

## Análise

1. **Sem custo de processamento, threads atrapalham.** Cada operação leva microssegundos, então criar uma thread (e manter várias conexões simultâneas) custa mais que o próprio trabalho. A versão single-thread foi a mais rápida (0.041 s) e as multithread ficaram entre 1,8x e 2,4x mais lentas.
2. **Com requisições que esperam (I/O), o multithread nos dois lados compensa muito.** Com 20 ms por requisição, a versão single-thread precisou de 4.18 s (≈ 200 × 20 ms, as requisições são atendidas uma a uma), enquanto a versão C terminou em 0.133 s, cerca de 31 vezes mais rápido, porque até 50 requisições esperam ao mesmo tempo.
3. **Multithread só no servidor não ajuda um cliente sequencial (B ≈ A).** O cliente só envia a próxima requisição depois de receber a resposta da anterior, então o servidor nunca tem duas requisições em andamento e as threads extras não têm o que paralelizar. O ganho do servidor multithread aparece quando chegam requisições concorrentes (vários clientes ou um cliente com threads).
4. **Multithread só no cliente também não ajuda (D ≈ A).** O tempo total ficou igual ao da versão single-thread, e a latência média por requisição explodiu (905 ms), porque as requisições ficam na fila de conexões esperando o servidor, que atende uma por vez. O gargalo é o servidor.
5. **Latência versus vazão.** Em C a latência de cada requisição é um pouco maior que a do atraso puro (25.8 ms contra 20 ms), pois as requisições disputam o servidor ao mesmo tempo, mas a vazão é muito maior (1507 contra 48 req/s).

## Limitações

- Cliente e servidor na mesma máquina: não há latência de rede real, que tenderia a aumentar o benefício do paralelismo.
- O atraso de 20 ms é artificial (`sleep`, que libera o processador como uma espera por I/O). Não testei processamento limitado por CPU; em CPython, o GIL impede que threads acelerem código que só usa CPU, então nesse caso o ganho seria pequeno ou nulo.
- O cliente limita o paralelismo a 50 threads simultâneas, o que também limita o ganho máximo da configuração C.
- Foram 200 requisições e 5 repetições em uma única máquina; os valores absolutos variam entre máquinas.

## Conclusão

O multithreading só traz ganho quando há trabalho que espera (I/O) e requisições concorrentes chegando ao servidor. Para ser eficaz, precisa estar nos dois lados: um cliente paralelo diante de um servidor serial só forma fila, e um servidor multithread diante de um cliente serial fica ocioso. Para requisições triviais e puramente de CPU, a versão single-thread é a mais rápida, por não pagar o custo de criar threads.
