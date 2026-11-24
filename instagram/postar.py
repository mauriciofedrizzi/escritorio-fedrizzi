"""
Posta vídeo no Instagram automaticamente.
Requer usuário e senha do Instagram no .env
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def postar_video(caminho_video: str, legenda: str, hashtags: list = None) -> bool:
    """
    Posta um vídeo no Instagram como Reel.

    Args:
        caminho_video: caminho local do arquivo .mp4 ou .mov
        legenda: texto do post
        hashtags: lista de hashtags (sem o #)

    Returns:
        True se postou com sucesso
    """
    usuario = os.getenv("INSTAGRAM_USUARIO")
    senha = os.getenv("INSTAGRAM_SENHA")

    if not usuario or not senha:
        print("[Instagram] Credenciais não configuradas no .env")
        print("  Adicione INSTAGRAM_USUARIO e INSTAGRAM_SENHA no arquivo .env")
        return False

    video = Path(caminho_video)
    if not video.exists():
        print(f"[Instagram] Arquivo não encontrado: {caminho_video}")
        return False

    tags = " ".join([f"#{h.strip('#')}" for h in (hashtags or [])])
    texto_completo = f"{legenda}\n\n{tags}"

    try:
        from instagrapi import Client
        cl = Client()
        cl.login(usuario, senha)
        cl.clip_upload(video, texto_completo)
        print(f"[Instagram] Reel postado com sucesso!")
        return True
    except ImportError:
        print("[Instagram] Instale: pip install instagrapi")
        return False
    except Exception as e:
        print(f"[Instagram] Erro ao postar: {e}")
        return False


if __name__ == "__main__":
    postar_video(
        caminho_video=r"C:\Users\mauri\escritorio-fedrizzi\videos\teste.mp4",
        legenda="Você sabe o que muda no MEI com a reforma tributária?",
        hashtags=["contabilidade", "MEI", "reformatributaria", "contadordigital", "escritoriofedrizzi"]
    )
