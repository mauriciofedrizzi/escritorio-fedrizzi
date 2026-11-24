"""
Envia notificação diária com os top 5 tópicos para o Maurício escolher.
Salva em arquivo local e envia por email (quando configurado).
"""

import os
import smtplib
import subprocess
from datetime import date
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

PASTA_NOTIFICACOES = Path(r"C:\Users\mauri\escritorio-fedrizzi\roteiros")


def formatar_topicos(topicos: list) -> str:
    linhas = [f"TOP 5 TÓPICOS DE CONTABILIDADE — {date.today().strftime('%d/%m/%Y')}\n"]
    linhas.append("Escolha um tema para o vídeo de hoje:\n")
    for t in topicos:
        linhas.append(f"  {t['posicao']}. {t['tema']}")
        linhas.append(f"     Fonte: {t['fonte']}")
        linhas.append("")
    linhas.append("Responda com o número do tema escolhido.")
    return "\n".join(linhas)


def notificar_windows(topicos: list):
    """Exibe notificação toast no Windows."""
    temas = " | ".join([f"{t['posicao']}. {t['tema'][:30]}" for t in topicos[:3]])
    try:
        subprocess.run([
            "powershell", "-Command",
            f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms");'
            f'$n = New-Object System.Windows.Forms.NotifyIcon;'
            f'$n.Icon = [System.Drawing.SystemIcons]::Information;'
            f'$n.Visible = $true;'
            f'$n.ShowBalloonTip(10000, "Escritorio Fedrizzi", "Top 5 topicos prontos! {temas}", [System.Windows.Forms.ToolTipIcon]::Info)'
        ], capture_output=True, timeout=5)
    except Exception:
        pass


def salvar_resumo(topicos: list) -> Path:
    """Salva o resumo dos tópicos em arquivo para o Maurício consultar."""
    PASTA_NOTIFICACOES.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_NOTIFICACOES / f"{date.today()}_topicos_do_dia.txt"
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(formatar_topicos(topicos))
    print(f"Resumo salvo em: {caminho}")
    return caminho


def enviar_email(topicos: list):
    """Envia email com os top 5 tópicos (requer configuração no .env)."""
    remetente = os.getenv("EMAIL_REMETENTE")
    senha = os.getenv("EMAIL_SENHA_APP")
    if not remetente or not senha:
        print("[Email] Não configurado — pulando envio por email.")
        return

    corpo = formatar_topicos(topicos)
    msg = MIMEMultipart()
    msg["From"] = remetente
    msg["To"] = remetente
    msg["Subject"] = f"[Fedrizzi] Top 5 tópicos para vídeo — {date.today().strftime('%d/%m/%Y')}"
    msg.attach(MIMEText(corpo, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remetente, senha)
            smtp.send_message(msg)
        print(f"[Email] Enviado para {remetente}")
    except Exception as e:
        print(f"[Email] Erro ao enviar: {e}")


def notificar(topicos: list):
    """Notifica o Maurício por todos os canais disponíveis."""
    print("\n" + formatar_topicos(topicos))
    salvar_resumo(topicos)
    notificar_windows(topicos)
    enviar_email(topicos)


if __name__ == "__main__":
    topicos_teste = [
        {"posicao": 1, "tema": "Reforma tributária e o MEI em 2025", "fonte": "Google Trends", "contexto": ""},
        {"posicao": 2, "tema": "Como declarar imposto de renda corretamente", "fonte": "Jornal Contábil", "contexto": ""},
        {"posicao": 3, "tema": "Split payment: o que é e como afeta seu negócio", "fonte": "Contábeis", "contexto": ""},
        {"posicao": 4, "tema": "FGTS Digital: novidades para 2025", "fonte": "Google Trends", "contexto": ""},
        {"posicao": 5, "tema": "Simples Nacional: tabela atualizada", "fonte": "Jornal Contábil", "contexto": ""},
    ]
    notificar(topicos_teste)
