"""
Coleta dados públicos de contas do Instagram (via Apify) para análise de referências.

Roda no PC (onde está a APIFY_API_KEY no .env). Lê a lista em pesquisa/referencias.txt,
baixa perfil + posts recentes + capas dos posts e, com --enviar, faz commit e push para o
GitHub, para a análise ser feita na sessão da nuvem.

Uso:
    python instagram/pesquisa/coletar.py                 # coleta e salva
    python instagram/pesquisa/coletar.py --enviar        # coleta, salva e manda para o GitHub
    python instagram/pesquisa/coletar.py --posts 50      # mais posts por conta (padrão 40)

Saída: pesquisa/coleta/AAAA-MM-DD/
    perfis.json   dados de cada perfil (bio, seguidores, nº de posts...)
    posts.json    posts com tipo, legenda, hashtags, curtidas, comentários, data
    resumo.md     tabela rápida por conta
    capas/<conta>/*.jpg   imagens dos posts de maior engajamento (capa + até 5 slides)

Custo: o actor apify/instagram-scraper cobra por resultado; 10 contas x 40 posts fica
dentro do crédito grátis mensal do Apify.
"""

import argparse
import io
import json
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")

API = "https://api.apify.com/v2"
ACTOR = "apify~instagram-scraper"
LISTA = RAIZ / "pesquisa" / "referencias.txt"
TOP_POR_CONTA = 12        # posts de maior engajamento com imagens baixadas
SLIDES_POR_POST = 5       # máximo de slides baixados por carrossel
LARGURA_IMG = 540         # reduz as imagens para o repositório não pesar


def ler_lista() -> list[str]:
    contas = []
    for linha in LISTA.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        conta = linha.split()[0].lstrip("@").strip("/")
        if conta and conta not in contas:
            contas.append(conta)
    return contas


def rodar_actor(token: str, entrada: dict, rotulo: str) -> list[dict]:
    cab = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{API}/acts/{ACTOR}/runs", headers=cab, json=entrada, timeout=60)
    r.raise_for_status()
    run = r.json()["data"]
    print(f"[Apify] {rotulo}: execução {run['id']} iniciada", end="", flush=True)
    while run["status"] in ("READY", "RUNNING"):
        time.sleep(10)
        print(".", end="", flush=True)
        run = requests.get(f"{API}/actor-runs/{run['id']}", headers=cab, timeout=60).json()["data"]
    print(f" {run['status']}")
    if run["status"] != "SUCCEEDED":
        raise RuntimeError(f"Execução do Apify terminou com status {run['status']}")
    itens = requests.get(f"{API}/datasets/{run['defaultDatasetId']}/items",
                         headers=cab, params={"clean": "true", "format": "json"}, timeout=120)
    itens.raise_for_status()
    return itens.json()


def tipo_post(p: dict) -> str:
    if p.get("productType") == "clips" or p.get("type") == "Video":
        return "reels/video"
    if p.get("type") == "Sidecar":
        return "carrossel"
    return "imagem"


def baixar_img(url: str, destino: Path) -> bool:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        if im.width > LARGURA_IMG:
            im = im.resize((LARGURA_IMG, round(im.height * LARGURA_IMG / im.width)), Image.LANCZOS)
        destino.parent.mkdir(parents=True, exist_ok=True)
        im.save(destino, quality=82)
        return True
    except Exception as e:  # imagem expirada ou bloqueada não deve parar a coleta
        print(f"  (imagem não baixada: {e})")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts", type=int, default=40, help="posts por conta")
    ap.add_argument("--enviar", action="store_true", help="commit + push do resultado")
    args = ap.parse_args()

    token = os.getenv("APIFY_API_KEY")
    if not token:
        sys.exit("APIFY_API_KEY não encontrada no .env")
    contas = ler_lista()
    if not contas:
        sys.exit(f"Nenhuma conta em {LISTA}")
    print(f"Contas: {', '.join('@' + c for c in contas)}")

    urls = [f"https://www.instagram.com/{c}/" for c in contas]
    perfis = rodar_actor(token, {"directUrls": urls, "resultsType": "details", "resultsLimit": 1}, "perfis")
    posts = rodar_actor(token, {"directUrls": urls, "resultsType": "posts", "resultsLimit": args.posts}, "posts")

    pasta = RAIZ / "pesquisa" / "coleta" / date.today().isoformat()
    pasta.mkdir(parents=True, exist_ok=True)

    # perfis: guarda só o que interessa para a análise
    campos_perfil = ["username", "fullName", "biography", "externalUrl", "followersCount", "followsCount",
                     "postsCount", "businessCategoryName", "verified", "isBusinessAccount"]
    perfis_limpos = [{k: p.get(k) for k in campos_perfil} for p in perfis if p.get("username")]
    encontrados = {p["username"].lower() for p in perfis_limpos}
    faltando = [c for c in contas if c.lower() not in encontrados]

    posts_limpos = []
    for p in posts:
        if not p.get("ownerUsername"):
            continue
        posts_limpos.append({
            "conta": p.get("ownerUsername"),
            "url": p.get("url"),
            "codigo": p.get("shortCode"),
            "data": p.get("timestamp"),
            "tipo": tipo_post(p),
            "slides": len(p.get("childPosts") or p.get("images") or []) or 1,
            "curtidas": p.get("likesCount"),
            "comentarios": p.get("commentsCount"),
            "visualizacoes": p.get("videoPlayCount") or p.get("videoViewCount"),
            "legenda": p.get("caption"),
            "hashtags": p.get("hashtags"),
            "fixado": p.get("isPinned"),
            "_imagens": [p.get("displayUrl")] + [c.get("displayUrl") for c in (p.get("childPosts") or [])],
        })

    # imagens dos posts de maior engajamento de cada conta
    for conta in {p["conta"] for p in posts_limpos}:
        da_conta = sorted((p for p in posts_limpos if p["conta"] == conta), key=engajamento_limpo, reverse=True)
        print(f"[Imagens] @{conta}")
        for p in da_conta[:TOP_POR_CONTA]:
            urls_img = [u for u in dict.fromkeys(p["_imagens"]) if u][:SLIDES_POR_POST]
            p["imagens_locais"] = []
            for i, u in enumerate(urls_img, start=1):
                dest = pasta / "capas" / conta / f"{p['codigo']}-{i}.jpg"
                if baixar_img(u, dest):
                    p["imagens_locais"].append(dest.relative_to(pasta).as_posix())
    for p in posts_limpos:
        p.pop("_imagens", None)

    (pasta / "perfis.json").write_text(json.dumps(perfis_limpos, ensure_ascii=False, indent=2), encoding="utf-8")
    (pasta / "posts.json").write_text(json.dumps(posts_limpos, ensure_ascii=False, indent=2), encoding="utf-8")
    escrever_resumo(pasta, perfis_limpos, posts_limpos, faltando)
    print(f"\nOK: {len(perfis_limpos)} perfis, {len(posts_limpos)} posts em {pasta}")
    if faltando:
        print("ATENÇÃO, contas não encontradas (conferir o @):", ", ".join("@" + c for c in faltando))

    if args.enviar:
        enviar(pasta)


def engajamento_limpo(p: dict) -> int:
    return max(p.get("curtidas") or 0, 0) + max(p.get("comentarios") or 0, 0)


def escrever_resumo(pasta: Path, perfis: list, posts: list, faltando: list):
    linhas = [f"# Coleta de referências do Instagram — {pasta.name}", "",
              "| Conta | Seguidores | Posts coletados | Carrossel | Imagem | Reels | Engaj. médio | Posts/semana |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for pf in perfis:
        ps = [p for p in posts if p["conta"].lower() == pf["username"].lower()]
        if not ps:
            continue
        cont = {t: sum(1 for p in ps if p["tipo"] == t) for t in ("carrossel", "imagem", "reels/video")}
        media = sum(engajamento_limpo(p) for p in ps) / len(ps)
        datas = sorted(p["data"] for p in ps if p.get("data"))
        por_semana = "-"
        if len(datas) > 1:
            from datetime import datetime
            d0 = datetime.fromisoformat(datas[0].replace("Z", "+00:00"))
            d1 = datetime.fromisoformat(datas[-1].replace("Z", "+00:00"))
            semanas = max((d1 - d0).days / 7, 1)
            por_semana = f"{len(ps) / semanas:.1f}"
        linhas.append(f"| @{pf['username']} | {pf.get('followersCount') or '-'} | {len(ps)} | {cont['carrossel']} | "
                      f"{cont['imagem']} | {cont['reels/video']} | {media:.0f} | {por_semana} |")
    if faltando:
        linhas += ["", "Contas não encontradas: " + ", ".join("@" + c for c in faltando)]
    (pasta / "resumo.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def enviar(pasta: Path):
    rel = pasta.relative_to(RAIZ).as_posix()
    cmds = [["git", "add", rel, "pesquisa/referencias.txt"],
            ["git", "commit", "-m", f"Coleta de referências do Instagram ({pasta.name})"],
            ["git", "push"]]
    for c in cmds:
        print("$", " ".join(c))
        r = subprocess.run(c, cwd=RAIZ)
        if r.returncode != 0:
            sys.exit("Falhou ao enviar para o GitHub. Rode os comandos acima manualmente.")
    print("Enviado para o GitHub. Avise o Claude na nuvem que a coleta chegou.")


if __name__ == "__main__":
    main()
