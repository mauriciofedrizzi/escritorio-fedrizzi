"""
Posta vídeo no Instagram como Reel via Meta Graph API oficial.
Requer META_ACCESS_TOKEN e META_IG_ID no .env
"""

import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

GRAPH_URL = "https://graph.facebook.com/v27.0"


def _upload_video(ig_id: str, token: str, caminho_video: Path, legenda: str) -> str | None:
    """Faz upload do vídeo e retorna o container ID."""
    tamanho = caminho_video.stat().st_size
    print(f"[Instagram] Iniciando upload ({tamanho // 1024 // 1024} MB)...")

    # Inicia sessão de upload resumível
    r = requests.post(
        f"{GRAPH_URL}/{ig_id}/media",
        params={
            "media_type": "REELS",
            "caption": legenda,
            "access_token": token,
        }
    )
    data = r.json()

    if "error" in data:
        print(f"[Instagram] Erro ao criar container: {data['error']['message']}")
        return None

    return data.get("id")


def _upload_via_url(ig_id: str, token: str, video_url: str, legenda: str) -> str | None:
    """Cria container de mídia com URL pública do vídeo."""
    r = requests.post(
        f"{GRAPH_URL}/{ig_id}/media",
        params={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": legenda,
            "access_token": token,
        }
    )
    data = r.json()
    if "error" in data:
        print(f"[Instagram] Erro: {data['error']['message']}")
        return None
    return data.get("id")


def _aguardar_processamento(container_id: str, token: str, tentativas: int = 15) -> bool:
    """Aguarda o Instagram processar o vídeo."""
    print("[Instagram] Aguardando processamento do vídeo...", end="", flush=True)
    for _ in range(tentativas):
        r = requests.get(
            f"{GRAPH_URL}/{container_id}",
            params={"fields": "status_code,status", "access_token": token}
        )
        status = r.json().get("status_code", "")
        if status == "FINISHED":
            print(" pronto!")
            return True
        if status == "ERROR":
            print(f" erro! {r.json()}")
            return False
        print(".", end="", flush=True)
        time.sleep(10)
    print(" timeout!")
    return False


def _publicar(ig_id: str, container_id: str, token: str) -> bool:
    """Publica o container como Reel."""
    r = requests.post(
        f"{GRAPH_URL}/{ig_id}/media_publish",
        params={"creation_id": container_id, "access_token": token}
    )
    data = r.json()
    if "id" in data:
        print(f"[Instagram] Reel publicado! ID: {data['id']}")
        return True
    print(f"[Instagram] Erro ao publicar: {data}")
    return False


def postar_video(caminho_video: str, legenda: str, hashtags: list = None, video_url: str = None) -> bool:
    """
    Posta um vídeo no Instagram como Reel via API oficial do Meta.

    Args:
        caminho_video: caminho local do arquivo (usado para verificar existência)
        legenda: texto do post
        hashtags: lista de hashtags (sem o #)
        video_url: URL pública do vídeo (necessária para a API do Meta)

    Returns:
        True se postou com sucesso
    """
    token = os.getenv("META_ACCESS_TOKEN")
    ig_id = os.getenv("META_IG_ID")

    if not token or not ig_id:
        print("[Instagram] META_ACCESS_TOKEN ou META_IG_ID não configurados no .env")
        return False

    video = Path(caminho_video)
    if not video.exists():
        print(f"[Instagram] Arquivo não encontrado: {caminho_video}")
        return False

    tags = " ".join([f"#{h.strip('#')}" for h in (hashtags or [])])
    texto_completo = f"{legenda}\n\n{tags}".strip()

    if not video_url:
        print("[Instagram] AVISO: A API do Meta requer uma URL pública para o vídeo.")
        print("  O vídeo precisa estar acessível via HTTPS para ser postado.")
        print("  Configure um servidor de upload ou use um serviço de hospedagem.")
        return False

    container_id = _upload_via_url(ig_id, token, video_url, texto_completo)
    if not container_id:
        return False

    if not _aguardar_processamento(container_id, token):
        return False

    return _publicar(ig_id, container_id, token)


if __name__ == "__main__":
    # Teste de conexão
    token = os.getenv("META_ACCESS_TOKEN")
    ig_id = os.getenv("META_IG_ID")
    if token and ig_id:
        r = requests.get(
            f"{GRAPH_URL}/{ig_id}",
            params={"fields": "username,followers_count", "access_token": token}
        )
        data = r.json()
        print(f"Conectado como @{data.get('username')} ({data.get('followers_count')} seguidores)")
    else:
        print("Configure META_ACCESS_TOKEN e META_IG_ID no .env")
