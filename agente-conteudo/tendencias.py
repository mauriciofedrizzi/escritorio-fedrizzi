"""
Busca os tópicos mais quentes de contabilidade no Brasil hoje.
Fontes: Google Trends + portais de notícias contábeis.
"""

import requests
from bs4 import BeautifulSoup
from datetime import date
from pytrends.request import TrendReq


TERMOS_BASE = [
    "contabilidade", "imposto de renda", "MEI", "simples nacional",
    "IRPF", "IRPJ", "nota fiscal", "FGTS", "INSS", "folha de pagamento",
    "reforma tributária", "split payment", "NF-e", "eSocial"
]

PORTAIS = [
    {"nome": "Contábeis", "url": "https://www.contabeis.com.br/noticias/"},
    {"nome": "Jornal Contábil", "url": "https://www.jornalcontabil.com.br/"},
]


def buscar_google_trends():
    """Retorna top termos de contabilidade em alta no Google Trends Brasil."""
    try:
        pt = TrendReq(hl="pt-BR", tz=-180, timeout=(10, 25))
        pt.build_payload(TERMOS_BASE[:5], cat=0, timeframe="now 1-d", geo="BR")
        interesse = pt.interest_over_time()

        if interesse.empty:
            return []

        media = interesse.drop(columns=["isPartial"], errors="ignore").mean()
        top = media.sort_values(ascending=False).head(5)
        return [{"termo": t, "pontuacao": round(float(v), 1), "fonte": "Google Trends"} for t, v in top.items()]
    except Exception as e:
        print(f"[Trends] Erro: {e}")
        return []


def buscar_noticias_contabeis():
    """Raspa manchetes dos portais de contabilidade."""
    noticias = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for portal in PORTAIS:
        try:
            resp = requests.get(portal["url"], headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")

            titulos = []
            for tag in ["h2", "h3", "h4"]:
                titulos += [t.get_text(strip=True) for t in soup.find_all(tag) if len(t.get_text(strip=True)) > 20]

            for titulo in titulos[:5]:
                noticias.append({"titulo": titulo, "fonte": portal["nome"]})
        except Exception as e:
            print(f"[Notícias] Erro em {portal['nome']}: {e}")

    return noticias


def montar_top5(trends, noticias):
    """Combina trends e notícias e monta uma lista de 5 tópicos."""
    topicos = []

    for t in trends[:3]:
        topicos.append({
            "posicao": len(topicos) + 1,
            "tema": t["termo"],
            "contexto": f"Em alta no Google Trends Brasil hoje (pontuação {t['pontuacao']})",
            "fonte": t["fonte"]
        })

    for n in noticias[:5]:
        if len(topicos) >= 5:
            break
        topicos.append({
            "posicao": len(topicos) + 1,
            "tema": n["titulo"][:80],
            "contexto": "Destaque nos portais de contabilidade hoje",
            "fonte": n["fonte"]
        })

    return topicos[:5]


def buscar_tendencias():
    """Função principal — retorna top 5 tópicos do dia."""
    print(f"[{date.today()}] Buscando tendências de contabilidade...")

    trends = buscar_google_trends()
    noticias = buscar_noticias_contabeis()
    top5 = montar_top5(trends, noticias)

    print(f"  {len(trends)} termos do Google Trends")
    print(f"  {len(noticias)} notícias dos portais")
    print(f"  Top 5 montado com {len(top5)} tópicos")

    return top5


if __name__ == "__main__":
    topicos = buscar_tendencias()
    print("\n=== TOP 5 TÓPICOS DO DIA ===")
    for t in topicos:
        print(f"{t['posicao']}. {t['tema']}")
        print(f"   → {t['contexto']} ({t['fonte']})")
