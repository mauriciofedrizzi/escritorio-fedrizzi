"""
Pipeline principal do Escritório Fedrizzi.

Fluxo diário:
  17h00 → busca top 5 tópicos → notifica Maurício
  Maurício escolhe → gera roteiro → salva na pasta roteiros/
  Maurício grava no iPhone → iCloud sincroniza → monitor.py detecta
  Vídeo editado → postado no Instagram

Rodando manualmente:
  python pipeline.py buscar          → busca e notifica top 5
  python pipeline.py roteiro <1-5>   → gera roteiro do tópico escolhido
  python pipeline.py status          → mostra o que está pendente hoje
"""

import sys
import json
from datetime import date
from pathlib import Path

from tendencias import buscar_tendencias
from notificacao import notificar
from roteiro import gerar_e_salvar

PASTA_BASE    = Path(r"C:\Users\mauri\escritorio-fedrizzi")
PASTA_ESTADO  = PASTA_BASE / "roteiros"
ARQUIVO_HOJE  = PASTA_ESTADO / f"{date.today()}_estado.json"


def salvar_estado(topicos):
    PASTA_ESTADO.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_HOJE, "w", encoding="utf-8") as f:
        json.dump({"data": str(date.today()), "topicos": topicos, "escolha": None}, f, ensure_ascii=False, indent=2)


def carregar_estado():
    if not ARQUIVO_HOJE.exists():
        return None
    with open(ARQUIVO_HOJE, encoding="utf-8") as f:
        return json.load(f)


def cmd_buscar():
    print("Buscando tendências de contabilidade hoje...")
    topicos = buscar_tendencias()
    salvar_estado(topicos)
    notificar(topicos)
    print("\nAguardando Maurício escolher o tema.")
    print(f"Para gerar o roteiro: python pipeline.py roteiro <número 1-5>")


def cmd_roteiro(numero: int):
    estado = carregar_estado()
    if not estado:
        print("Nenhum tópico encontrado para hoje. Rode: python pipeline.py buscar")
        return

    topicos = estado["topicos"]
    if numero < 1 or numero > len(topicos):
        print(f"Número inválido. Escolha entre 1 e {len(topicos)}.")
        return

    topico = topicos[numero - 1]
    print(f"\nTema escolhido: {topico['tema']}")
    print("Gerando roteiro com IA...\n")

    caminho = gerar_e_salvar(topico["tema"], topico.get("contexto", ""))

    # atualiza estado
    estado["escolha"] = numero
    with open(ARQUIVO_HOJE, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)

    print(f"\nRoteiro salvo em:\n  {caminho}")
    print("\nAgora é com você:")
    print("  1. Leia o roteiro")
    print("  2. Grave o vídeo no iPhone")
    print("  3. Salve na pasta iCloud Drive > Trabalho")
    print("  4. O monitor vai detectar e processar automaticamente!")


def cmd_status():
    estado = carregar_estado()
    print(f"\n=== STATUS DO DIA {date.today().strftime('%d/%m/%Y')} ===")
    if not estado:
        print("Nenhuma busca feita hoje. Rode: python pipeline.py buscar")
        return

    print(f"Tópicos encontrados: {len(estado['topicos'])}")
    if estado.get("escolha"):
        topico = estado["topicos"][estado["escolha"] - 1]
        print(f"Tema escolhido: {topico['tema']}")
        roteiro = PASTA_ESTADO / f"{date.today()}_roteiro.txt"
        print(f"Roteiro: {'✓ gerado' if roteiro.exists() else '✗ pendente'}")
    else:
        print("Escolha: pendente")

    videos = list((PASTA_BASE / "videos").glob("*.mp4")) + list((PASTA_BASE / "videos").glob("*.mov"))
    print(f"Vídeos na fila: {len(videos)}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "buscar":
        cmd_buscar()
    elif cmd == "roteiro":
        if len(sys.argv) < 3:
            print("Uso: python pipeline.py roteiro <número 1-5>")
            return
        cmd_roteiro(int(sys.argv[2]))
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Comando desconhecido: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
