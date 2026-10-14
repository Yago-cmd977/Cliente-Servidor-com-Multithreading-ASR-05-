# Cliente-Servidor com Multithreading (ASR 05)

Extensão do sistema cliente-servidor da ASR 04 (servidor que processa texto, cliente que chama várias operações em uma requisição) com multithreading, geração automática de requisições e um experimento de desempenho.

## O que foi implementado

1. **Servidor multithread (`server_mt.py`):** a thread principal aceita a conexão e recebe a requisição; em seguida dispara uma **nova thread** que processa a requisição, envia a resposta e fecha a conexão.
2. **Cliente multithread (`client_auto.py --modo threads`):** cada requisição é enviada por uma **nova thread**, que conecta, envia e aguarda a resposta. Várias requisições ficam em andamento em paralelo.
3. **Geração automática de requisições:** o cliente sorteia o texto (5 a 40 palavras aleatórias) e de 2 a 5 operações por requisição. A semente é fixa (`--semente`, padrão 42), então todas as configurações recebem exatamente as mesmas requisições.
4. **Experimento (`benchmark.py`):** compara o tempo para processar a mesma quantidade de requisições em quatro configurações.

## Arquivos

| Arquivo | Função |
|---|---|
| `constCS.py` | `HOST` e `PORT` |
| `operacoes.py` | funcionalidades da ASR 04 (`upper`, `lower`, `reverse`, `length`, `words`, `vowels`, `palindrome`, `sha256`) e `processar()`, compartilhados pelos dois servidores |
| `server.py` | servidor **single-thread** (ASR 04) |
| `server_mt.py` | servidor **multithread** (thread por requisição) |
| `client.py` | cliente manual da ASR 04 (uma requisição) |
| `client_auto.py` | cliente com geração automática, modos `threads` e `sequencial` |
| `benchmark.py` | experimento de desempenho |
| `RELATORIO.md` | relato do experimento |

O protocolo não mudou: uma linha JSON por requisição, por exemplo `{"text": "Hello World", "ops": ["upper", "reverse"]}`, e uma linha JSON de resposta. O comportamento funcional dos dois servidores é idêntico, porque ambos usam `operacoes.processar()`.

## Como executar

Requer Python 3 (somente biblioteca padrão).

```bash
# servidor (escolha um)
python server_mt.py            # multithread
python server.py               # single-thread

# cliente, em outro terminal
python client_auto.py -n 100 --modo threads        # uma thread por requisição
python client_auto.py -n 100 --modo sequencial     # uma requisição por vez
python client.py "Hello World" upper reverse       # cliente manual da ASR 04
```

Opções úteis: `--porta`, `--atraso` (servidor, ver abaixo), `--semente` e `--max-simultaneas` (cliente).

O `client_auto.py` confere cada resposta recebida com o resultado calculado localmente e imprime `respostas incorretas: 0` quando tudo bate. Isso é o teste de que o comportamento funcional é o mesmo nas duas versões.

## Experimento

```bash
python benchmark.py -n 200 --reps 5 --atrasos 0 0.02
```

O script sobe cada servidor, faz um aquecimento, mede `reps` execuções e imprime uma tabela em Markdown; os dados brutos vão para `resultados.csv`.

| Config | Servidor | Cliente |
|---|---|---|
| A | single-thread (ASR 04) | sequencial |
| B | multithread | sequencial (multithread só no servidor) |
| C | multithread | uma thread por requisição (ASR 05) |
| D (extra) | single-thread | uma thread por requisição |

Métricas: tempo total até receber todas as respostas, latência média e p95 por requisição, vazão (req/s) e speedup em relação à configuração A. O resultado e a análise estão em `RELATORIO.md`.

## Observações e limitações

- **`--atraso`:** o servidor aceita um atraso artificial por requisição (`time.sleep`), usado só no experimento para simular uma requisição que espera por I/O (disco, banco de dados). As operações reais levam microssegundos, então sem esse atraso o experimento mede basicamente o custo de criar threads e conexões. O padrão é 0 e não altera o comportamento.
- **Uma requisição por conexão:** o `server_mt.py` recebe uma requisição por conexão, como na arquitetura mostrada em aula.
- **Fila de conexões:** o `listen()` passou de 1 para 128 para que muitas conexões simultâneas esperem na fila sem serem recusadas.
- **Limite de threads no cliente:** `--max-simultaneas` (padrão 50) limita quantas threads do cliente ficam vivas ao mesmo tempo, para não estourar o limite de arquivos abertos do sistema. Mesmo assim, cada requisição usa uma thread nova.
- Cliente e servidor rodam na mesma máquina (`127.0.0.1`), então o experimento não inclui latência de rede real.
