"""
Gera as imagens de um post (carrossel ou imagem única) a partir de um post.json.

Uso:
    python instagram/carrossel/gerar.py posts/2026-11-27-erros-imposto

Saída na mesma pasta:
    slide-01.png, slide-02.png ...  (1080 x 1350, prontos para o Instagram)
    previa.png                      (todos os slides lado a lado, para aprovação)
    legenda.txt                     (legenda + hashtags)

Formato do post.json: ver docs/POSTS.md.
Dependências: pip install playwright pillow  +  python -m playwright install chromium
"""

import html
import json
import os
import re
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[2]
PASTA_MODELO = Path(__file__).resolve().parent
CSS = PASTA_MODELO / "modelo.css"
MARCA = RAIZ / "assets" / "marca"
CONFIG = json.loads((RAIZ / "instagram" / "marca.json").read_text(encoding="utf-8"))

FUNDO_PADRAO = {"capa": "escuro", "cta": "escuro"}
MAX_SLIDES = 10  # limite de carrossel na API do Instagram


# --------------------------------------------------------------------------- texto

def fmt(texto: str) -> str:
    """Escapa HTML e aplica marcações: **negrito** e *destaque* (cor turquesa nos títulos)."""
    t = html.escape(texto or "")
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return t.replace("\n", "<br>")


def paragrafos(texto) -> str:
    partes = texto if isinstance(texto, list) else str(texto or "").split("\n\n")
    return "".join(f"<p>{fmt(p)}</p>" for p in partes if p.strip())


# --------------------------------------------------------------------------- slides

def corpo_slide(s: dict) -> str:
    tipo = s["tipo"]
    etiqueta = f'<div class="etiqueta">{fmt(s["etiqueta"])}</div>' if s.get("etiqueta") else ""

    if tipo == "capa":
        sub = f'<div class="sub">{fmt(s["subtitulo"])}</div>' if s.get("subtitulo") else ""
        return f'{etiqueta}<div class="barra"></div><h1>{fmt(s["titulo"])}</h1>{sub}'

    if tipo == "texto":
        titulo = f'<h2>{fmt(s["titulo"])}</h2>' if s.get("titulo") else ""
        return f'{etiqueta}{titulo}<div class="texto">{paragrafos(s["texto"])}</div>'

    if tipo == "lista":
        itens = "".join(
            f'<li><span class="n">{i}</span><span>{fmt(item)}</span></li>'
            for i, item in enumerate(s["itens"], start=s.get("inicio", 1))
        )
        return f'{etiqueta}<h2>{fmt(s["titulo"])}</h2><ol class="lista">{itens}</ol>'

    if tipo == "destaque":
        titulo = f'<h2>{fmt(s["titulo"])}</h2>' if s.get("titulo") else ""
        return (f'{etiqueta}{titulo}<div class="numero">{fmt(s["numero"])}</div>'
                f'<div class="texto">{paragrafos(s.get("texto", ""))}</div>')

    if tipo == "alerta":
        return (f'<div class="etiqueta">{fmt(s.get("etiqueta", "Atenção"))}</div>'
                f'<h2>{fmt(s["titulo"])}</h2><div class="caixa texto">{paragrafos(s["texto"])}</div>')

    if tipo == "comparacao":
        def col(classe, dados):
            itens = "".join(f"<li>{fmt(i)}</li>" for i in dados["itens"])
            return f'<div class="coluna {classe}"><h3>{fmt(dados["titulo"])}</h3><ul>{itens}</ul></div>'
        return (f'{etiqueta}<h2>{fmt(s["titulo"])}</h2>'
                f'<div class="duas-colunas">{col("errado", s["errado"])}{col("certo", s["certo"])}</div>')

    if tipo == "cta":
        escuro = s.get("fundo", FUNDO_PADRAO["cta"]) != "claro"
        logo = MARCA / ("logo-fedrizzi-fundo-escuro.svg" if escuro else "logo-fedrizzi.svg")
        if s.get("fundo") == "turquesa":
            logo = MARCA / "logo-fedrizzi-branco.svg"
        botao = f'<div class="botao">{fmt(s["botao"])}</div>' if s.get("botao") else ""
        return (f'<img class="logo" src="{logo.as_uri()}"><h2>{fmt(s["titulo"])}</h2>'
                f'<div class="texto">{paragrafos(s.get("texto", ""))}</div>{botao}')

    raise ValueError(f"Tipo de slide desconhecido: {tipo}")


def html_slide(s: dict, n: int, total: int) -> str:
    fundo = s.get("fundo", FUNDO_PADRAO.get(s["tipo"], "claro"))
    simbolo = MARCA / ("simbolo-fedrizzi.svg" if fundo == "claro" else "simbolo-fedrizzi-branco.svg")
    marca_dagua = MARCA / ("simbolo-fedrizzi-branco.svg" if fundo != "claro" else "simbolo-fedrizzi.svg")
    if total > 1 and n == 1:
        direita = '<span class="arrasta">Arrasta &rarr;</span>'
    elif total > 1:
        direita = f'<span class="pagina">{n}/{total}</span>'
    else:
        direita = ""
    mostrar_dagua = s["tipo"] in ("capa", "destaque", "cta") and not s.get("sem_marca_dagua")
    dagua = f'<img class="marca-dagua" src="{marca_dagua.as_uri()}">' if mostrar_dagua else ""
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<link rel="stylesheet" href="{CSS.as_uri()}"></head><body>
<div class="slide {fundo} {s['tipo']}">
  {dagua}
  <div class="conteudo"><div class="ajuste">{corpo_slide(s)}</div></div>
  <div class="rodape"><img src="{simbolo.as_uri()}"><span>{html.escape(CONFIG['arroba'])}</span>{direita}</div>
</div>
<script>
// encolhe o conteúdo se o texto passar da área útil (evita texto cortado)
document.fonts.ready.then(() => {{
  const caixa = document.querySelector('.conteudo'), aj = document.querySelector('.ajuste');
  let z = 1;
  while (aj.scrollHeight * z > caixa.clientHeight && z > 0.6) {{ z -= 0.02; aj.style.zoom = z; }}
  document.body.dataset.zoom = z.toFixed(2);
  document.body.dataset.pronto = '1';
}});
</script></body></html>"""


# --------------------------------------------------------------------------- render

def abrir_navegador(p):
    caminho = os.getenv("CHROMIUM_PATH")
    return p.chromium.launch(executable_path=caminho) if caminho else p.chromium.launch()


def gerar(pasta: Path) -> list[Path]:
    post = json.loads((pasta / "post.json").read_text(encoding="utf-8"))
    slides = post["slides"]
    if not 1 <= len(slides) <= MAX_SLIDES:
        raise ValueError(f"O post precisa ter de 1 a {MAX_SLIDES} slides (tem {len(slides)}).")

    for velho in pasta.glob("slide-*.png"):
        velho.unlink()

    saidas, avisos = [], []
    with sync_playwright() as p:
        nav = abrir_navegador(p)
        pagina = nav.new_page(viewport={"width": 1080, "height": 1350})
        for i, s in enumerate(slides, start=1):
            tmp = pasta / f".slide-{i:02d}.html"
            tmp.write_text(html_slide(s, i, len(slides)), encoding="utf-8")
            pagina.goto(tmp.as_uri())
            pagina.wait_for_selector("body[data-pronto='1']")
            zoom = float(pagina.evaluate("document.body.dataset.zoom"))
            if zoom < 0.85:
                avisos.append(f"slide {i}: texto longo, fonte reduzida para {zoom:.0%}. Considere encurtar.")
            saida = pasta / f"slide-{i:02d}.png"
            pagina.screenshot(path=str(saida))
            tmp.unlink()
            saidas.append(saida)
        nav.close()

    montar_previa(saidas, pasta / "previa.png")
    legenda = post.get("legenda", "").strip()
    tags = " ".join("#" + h.lstrip("#") for h in post.get("hashtags", []))
    (pasta / "legenda.txt").write_text(f"{legenda}\n\n{tags}".strip() + "\n", encoding="utf-8")

    for a in avisos:
        print("AVISO", a)
    print(f"OK: {len(saidas)} slide(s) em {pasta}")
    return saidas


def montar_previa(imagens: list[Path], destino: Path, largura=360):
    """Folha com os slides lado a lado (até 5 por linha)."""
    altura = int(largura * 1350 / 1080)
    por_linha = min(5, len(imagens))
    linhas = (len(imagens) + por_linha - 1) // por_linha
    gap = 16
    folha = Image.new("RGB", (por_linha * (largura + gap) + gap, linhas * (altura + gap) + gap), "#DDE5E5")
    for i, img in enumerate(imagens):
        mini = Image.open(img).convert("RGB").resize((largura, altura), Image.LANCZOS)
        folha.paste(mini, (gap + (i % por_linha) * (largura + gap), gap + (i // por_linha) * (altura + gap)))
    folha.save(destino)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    gerar(Path(sys.argv[1]).resolve())
