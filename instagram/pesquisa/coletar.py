"""
Coleta dados públicos de contas do Instagram (via Apify) para análise de referências.

Roda no PC (onde está a APIFY_API_KEY no .env). Lê a lista em pesquisa/referencias.txt,
baixa perfil + posts recentes + TODAS as imagens de cada post (todos os slides dos
carrosséis, capa das imagens e dos reels) e, com --enviar, faz commit e push para o GitHub,
para a análise ser feita na sessão da nuvem.

Uso:
    python instagram/pesquisa/coletar.py                 # coleta e salva
    python instagram/pesquisa/coletar.py --enviar        # coleta, salva e manda para o GitHub
    python instagram/pesquisa/coletar.py --posts 80      # mais posts por conta (padrão 60)

Saída: pesquisa/coleta/AAAA-MM-DD/
    perfis.json   dados de cada perfil (bio, seguidores, nº de posts...)
    posts.json    posts com tipo, legenda, hashtags, curtidas, comentários, data
    resumo.md     tabela rápida por conta
    folhas/<conta>/<data>_<codigo>.jpg   uma folha por post com todos os slides lado a lado

Recomendado rodar numa cópia separada (git worktree) numa branch só de dados, para as imagens
não pesarem na branch principal. O .env é procurado na pasta atual e, se não existir, na pasta
principal do repositório.

Custo: o actor apify/instagram-scraper cobra por resultado (cerca de US$ 2-3 por 1.000);
10 contas x 60 posts fica perto de US$ 1-2.
"""

import argparse
import io
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]

API = "https://api.apify.com/v2"
ACTOR = "apify~instagram-scraper"
LISTA = RAIZ / "pesquisa" / "referencias.txt"
MAX_SLIDES = 20           # o Instagram permite até 20 slides por carrossel
LARGURA_SLIDE = 360       # largura de cada slide na folha
POR_LINHA = 5             # slides por linha na folha


def carregar_env():
    """Lê o .env da pasta atual; numa worktree, cai para o .env da pasta principal do repositório."""
    if (RAIZ / ".env").exists():
        load_dotenv(RAIZ / ".env")
        return
    try:
        comum = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=RAIZ,
                               capture_output=True, text=True, check=True).stdout.strip()
        principal = (RAIZ / comum).resolve().parent
        load_dotenv(principal / ".env")
    except Exception:
        pass


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
                         headers=cab, params={"clean": "true", "format": "json"}, timeout=300)
    itens.raise_for_status()
    return itens.json()


def tipo_post(p: dict) -> str:
    if p.get("productType") == "clips" or p.get("type") == "Video":
        return "reels/video"
    if p.get("type") == "Sidecar":
        return "carrossel"
    return "imagem"


def engajamento(p: dict) -> int:
    return max(p.get("curtidas") or 0, 0) + max(p.get("comentarios") or 0, 0)


def baixar(url: str):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        return None


def montar_folha(urls: list[str], destino: Path) -> int:
    """Baixa os slides e salva uma folha com todos lado a lado. Retorna quantos baixou."""
    with ThreadPoolExecutor(max_workers=6) as ex:
        imgs = [im for im in ex.map(baixar, urls) if im is not None]
    if not imgs:
        return 0
    imgs = [im.resize((LARGURA_SLIDE, round(im.height * LARGURA_SLIDE / im.width)), Image.LANCZOS) for im in imgs]
    alt = max(im.height for im in imgs)
    cols = min(POR_LINHA, len(imgs))
    linhas = (len(imgs) + cols - 1) // cols
    g = 8
    folha = Image.new("RGB", (cols * (LARGURA_SLIDE + g) + g, linhas * (alt + g) + g), "#E6E6E6")
    for i, im in enumerate(imgs):
        folha.paste(im, (g + (i % cols) * (LARGURA_SLIDE + g), g + (i // cols) * (alt + g)))
    destino.parent.mkdir(parents=True, exist_ok=True)
    folha.save(destino, quality=78)
    return len(imgs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts", type=int, default=60, help="posts por conta")
    ap.add_argument("--enviar", action="store_true", help="commit + push do resultado")
    args = ap.parse_args()

    carregar_env()
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
    (pasta / "bruto_posts.json").write_text(json.dumps(posts, ensure_ascii=False), encoding="utf-8")

    campos_perfil = ["username", "fullName", "biography", "externalUrl", "followersCount", "followsCount",
                     "postsCount", "businessCategoryName", "verified", "isBusinessAccount", "highlightReelCount"]
    perfis_limpos = [{k: p.get(k) for k in campos_perfil} for p in perfis if p.get("username")]
    encontrados = {p["username"].lower() for p in perfis_limpos}
    faltando = [c for c in contas if c.lower() not in encontrados]

    posts_limpos = []
    for p in posts:
        if not p.get("ownerUsername"):
            continue
        filhos = p.get("childPosts") or []
        imagens = [c.get("displayUrl") for c in filhos if c.get("displayUrl")] or p.get("images") or []
        if not imagens and p.get("displayUrl"):
            imagens = [p["displayUrl"]]
        posts_limpos.append({
            "conta": p.get("ownerUsername"),
            "url": p.get("url"),
            "codigo": p.get("shortCode"),
            "data": p.get("timestamp"),
            "tipo": tipo_post(p),
            "slides": len(filhos) or len(p.get("images") or []) or 1,
            "curtidas": p.get("likesCount"),
            "comentarios": p.get("commentsCount"),
            "visualizacoes": p.get("videoPlayCount") or p.get("videoViewCount"),
            "duracao_video_s": p.get("videoDuration"),
            "legenda": p.get("caption"),
            "hashtags": p.get("hashtags"),
            "mencoes": p.get("mentions"),
            "fixado": p.get("isPinned"),
            "colaboradores": [c.get("username") for c in (p.get("coauthorProducers") or []) if isinstance(c, dict)],
            "_imagens": list(dict.fromkeys(imagens))[:MAX_SLIDES],
        })

    total = len(posts_limpos)
    for n, p in enumerate(posts_limpos, start=1):
        dia = (p["data"] or "")[:10]
        dest = pasta / "folhas" / p["conta"] / f"{dia}_{p['codigo']}.jpg"
        print(f"[Imagens] {n}/{total} @{p['conta']} {p['tipo']} ({len(p['_imagens'])} img)")
        qtd = montar_folha(p["_imagens"], dest)
        p["folha"] = dest.relative_to(pasta).as_posix() if qtd else None
        p["imagens_baixadas"] = qtd
        p.pop("_imagens")

    (pasta / "perfis.json").write_text(json.dumps(perfis_limpos, ensure_ascii=False, indent=2), encoding="utf-8")
    (pasta / "posts.json").write_text(json.dumps(posts_limpos, ensure_ascii=False, indent=2), encoding="utf-8")
    escrever_resumo(pasta, perfis_limpos, posts_limpos, faltando)
    print(f"\nOK: {len(perfis_limpos)} perfis, {total} posts em {pasta}")
    if faltando:
        print("ATENÇÃO, contas não encontradas (conferir o @):", ", ".join("@" + c for c in faltando))

    if args.enviar:
        enviar(pasta)


def escrever_resumo(pasta: Path, perfis: list, posts: list, faltando: list):
    linhas = [f"# Coleta de referências do Instagram — {pasta.name}", "",
              "| Conta | Seguidores | Posts coletados | Carrossel | Imagem | Reels | Engaj. médio | Posts/semana |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for pf in perfis:
        ps = [p for p in posts if p["conta"].lower() == pf["username"].lower()]
        if not ps:
            continue
        cont = {t: sum(1 for p in ps if p["tipo"] == t) for t in ("carrossel", "imagem", "reels/video")}
        media = sum(engajamento(p) for p in ps) / len(ps)
        datas = sorted(p["data"] for p in ps if p.get("data"))
        por_semana = "-"
        if len(datas) > 1:
            d0 = datetime.fromisoformat(datas[0].replace("Z", "+00:00"))
            d1 = datetime.fromisoformat(datas[-1].replace("Z", "+00:00"))
            por_semana = f"{len(ps) / max((d1 - d0).days / 7, 1):.1f}"
        linhas.append(f"| @{pf['username']} | {pf.get('followersCount') or '-'} | {len(ps)} | {cont['carrossel']} | "
                      f"{cont['imagem']} | {cont['reels/video']} | {media:.0f} | {por_semana} |")
    if faltando:
        linhas += ["", "Contas não encontradas: " + ", ".join("@" + c for c in faltando)]
    (pasta / "resumo.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def enviar(pasta: Path):
    rel = pasta.relative_to(RAIZ).as_posix()
    cmds = [["git", "add", rel, "pesquisa/referencias.txt"],
            ["git", "commit", "-m", f"Coleta de referências do Instagram ({pasta.name})"],
            ["git", "push", "-u", "origin", "HEAD"]]
    for c in cmds:
        print("$", " ".join(c))
        r = subprocess.run(c, cwd=RAIZ)
        if r.returncode != 0:
            sys.exit("Falhou ao enviar para o GitHub. Rode os comandos acima manualmente.")
    print("Enviado para o GitHub. Avise o Claude na nuvem que a coleta chegou.")


if __name__ == "__main__":
    main()
