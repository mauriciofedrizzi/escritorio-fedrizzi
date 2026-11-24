"""
Gera roteiro completo de vídeo para Instagram/Reels
a partir de um tópico de contabilidade.
Usa a API do Claude (Anthropic).
"""

import os
import re
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
import anthropic

load_dotenv(Path(__file__).parent.parent / ".env")

PASTA_ROTEIROS = Path(r"C:\Users\mauri\escritorio-fedrizzi\roteiros")

PROMPT_ROTEIRO = """
Você é um especialista em marketing de conteúdo para escritórios de contabilidade.

Crie um roteiro COMPLETO para um vídeo curto de Instagram Reels (60-90 segundos)
sobre o seguinte tema: "{tema}"

Contexto do tema: {contexto}

O vídeo é para o Escritório Fedrizzi, um escritório de contabilidade brasileiro.
O público são empresários, MEIs e pessoas físicas que precisam de orientação contábil/fiscal.

O roteiro deve ter:
1. GANCHO (0-5 seg): frase de impacto para parar o scroll
2. PROBLEMA (5-20 seg): apresenta a dor/dúvida do cliente
3. SOLUÇÃO (20-50 seg): explica de forma simples, 2-3 pontos práticos
4. CTA (50-60 seg): chamada para ação clara (ex: "manda mensagem", "segue o perfil")

Formato de saída:
- Texto exato que o Maurício vai falar em cada cena
- Duração sugerida de cada parte
- Dica de visual/enquadramento para cada cena
- Hashtags recomendadas (10-15)
- Legenda para o post (3-4 linhas)

Tom: direto, simples, sem juridiquês. Fala como se fosse um amigo contador.
"""


def gerar_roteiro(tema: str, contexto: str = "") -> dict:
    """Gera roteiro completo usando Claude API."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY não configurada no .env")

    client = anthropic.Anthropic(api_key=api_key)

    print(f"Gerando roteiro: {tema[:60]}...")

    resposta = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": PROMPT_ROTEIRO.format(tema=tema, contexto=contexto)
        }]
    )

    conteudo = resposta.content[0].text
    return {"tema": tema, "data": str(date.today()), "roteiro": conteudo}


def salvar_roteiro(roteiro: dict) -> Path:
    """Salva o roteiro em arquivo .txt na pasta roteiros."""
    PASTA_ROTEIROS.mkdir(parents=True, exist_ok=True)

    tema_slug = re.sub(r"[^a-zA-Z0-9\s]", "", roteiro["tema"])
    tema_slug = "_".join(tema_slug.lower().split()[:5])
    nome_arquivo = f"{roteiro['data']}_{tema_slug}.txt"
    caminho = PASTA_ROTEIROS / nome_arquivo

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(f"ROTEIRO — {roteiro['data']}\n")
        f.write(f"TEMA: {roteiro['tema']}\n")
        f.write("=" * 60 + "\n\n")
        f.write(roteiro["roteiro"])

    print(f"Roteiro salvo: {caminho}")
    return caminho


def gerar_e_salvar(tema: str, contexto: str = "") -> Path:
    roteiro = gerar_roteiro(tema, contexto)
    return salvar_roteiro(roteiro)


if __name__ == "__main__":
    tema_teste = "Reforma tributária: o que muda para o MEI em 2025"
    contexto_teste = "Em alta no Google Trends Brasil hoje"
    caminho = gerar_e_salvar(tema_teste, contexto_teste)
    print(f"\nRoteiro gerado em: {caminho}")
