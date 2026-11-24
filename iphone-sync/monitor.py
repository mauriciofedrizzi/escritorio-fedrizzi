"""
Monitor a pasta iCloudPhotos e detecta vídeos novos no álbum "Trabalho".
Quando um vídeo novo aparece, copia para a pasta de trabalho e notifica.
"""

import os
import time
import shutil
from pathlib import Path
from datetime import datetime

ICLOUD_TRABALHO = Path(r"C:\Users\mauri\iCloudDrive\Trabalho")
PASTA_TRABALHO  = Path(r"C:\Users\mauri\escritorio-fedrizzi\videos")
EXTENSOES_VIDEO = {".mov", ".mp4", ".m4v", ".avi"}
EXTENSOES_FOTO  = {".jpg", ".jpeg", ".heic", ".png"}

def log(msg):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"[{agora}] {msg}")

def arquivos_novos(pasta, vistos):
    """Retorna arquivos que ainda não foram processados."""
    novos = []
    if not pasta.exists():
        return novos
    for arquivo in pasta.iterdir():
        if arquivo.is_file() and arquivo.suffix.lower() in EXTENSOES_VIDEO | EXTENSOES_FOTO:
            if str(arquivo) not in vistos:
                novos.append(arquivo)
    return novos

def copiar_para_trabalho(arquivo):
    """Copia o arquivo para a pasta de trabalho com timestamp."""
    PASTA_TRABALHO.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = PASTA_TRABALHO / f"{timestamp}_{arquivo.name}"
    shutil.copy2(arquivo, destino)
    log(f"✅ Copiado: {arquivo.name} → {destino}")
    return destino

def notificar(arquivo, destino):
    """Mostra notificação no Windows."""
    try:
        import subprocess
        msg = f"Novo arquivo do iPhone: {arquivo.name}"
        subprocess.run([
            "powershell", "-Command",
            f'New-BurntToastNotification -Text "iPhone Sync", "{msg}"'
        ], capture_output=True)
    except Exception:
        pass  # notificação é opcional
    log(f"📱 NOVO ARQUIVO DETECTADO: {arquivo.name}")
    log(f"   Salvo em: {destino}")

def monitorar():
    log("Iniciando monitor da pasta Trabalho no iCloud Drive...")
    log(f"   Monitorando: {ICLOUD_TRABALHO}")
    log(f"   Destino:     {PASTA_TRABALHO}")

    vistos = set()

    while True:
        if not ICLOUD_TRABALHO.exists():
            log("Pasta Trabalho ainda não sincronizou. Aguardando...")
            time.sleep(30)
            continue

        novos = arquivos_novos(ICLOUD_TRABALHO, vistos)

        for arquivo in novos:
            destino = copiar_para_trabalho(arquivo)
            notificar(arquivo, destino)
            vistos.add(str(arquivo))

        time.sleep(15)  # verifica a cada 15 segundos

if __name__ == "__main__":
    monitorar()
