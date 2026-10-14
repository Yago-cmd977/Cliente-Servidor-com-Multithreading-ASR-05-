"""Cliente manual (ASR 04): envia UMA requisição com várias operações.

Uso:
  python client.py "Hello World" upper reverse words
  python client.py                      # usa um exemplo padrão
"""
import json
import sys
from socket import *
from constCS import *

texto = sys.argv[1] if len(sys.argv) > 1 else "Hello World"
ops = sys.argv[2:] or ["upper", "reverse", "words", "vowels", "palindrome"]

s = socket(AF_INET, SOCK_STREAM)
s.connect((HOST, PORT))  # conecta ao servidor (bloqueia até ser aceito)

requisicao = {"text": texto, "ops": ops}  # compõe a requisição
s.sendall((json.dumps(requisicao) + "\n").encode())  # envia

resposta = json.loads(s.makefile("rb").readline().decode())  # recebe a resposta
s.close()  # fecha a conexão

print(f'Texto enviado: "{texto}"')
for op, valor in resposta["results"].items():
    print(f"  {op:<11} -> {valor}")
for op, msg in resposta["errors"].items():
    print(f"  [erro] {op}: {msg}")
