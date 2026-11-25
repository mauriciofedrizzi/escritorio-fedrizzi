# Posts de imagem e carrossel (Instagram)

Fluxo planejado: **tema -> post.json -> gerar imagens -> aprovação no Telegram -> publicar (Graph API)**, a cada 2 dias.
Hoje está pronto: identidade visual, modelo e gerador de imagens. Falta: envio para aprovação no Telegram,
hospedagem pública das imagens e publicação de carrossel (a API exige URL HTTPS de cada imagem).

## Gerar um post

```bash
pip install playwright pillow
python -m playwright install chromium
python instagram/carrossel/gerar.py posts/exemplo-erros-imposto
```

Gera na pasta do post: `slide-01.png` ... (1080 x 1350, formato 4:5 do feed), `previa.png` (todos os slides lado a lado)
e `legenda.txt`. Se o texto não couber, a fonte é reduzida automaticamente e o script avisa para encurtar.

## Formato do `post.json`

```json
{
  "titulo_interno": "nome para controle",
  "formato": "carrossel",            // ou "imagem" (1 slide só)
  "status": "rascunho",              // rascunho -> aguardando_aprovacao -> aprovado -> publicado
  "slides": [ ... até 10 ... ],
  "legenda": "texto do post",
  "hashtags": ["contabilidade", "impostos"]
}
```

Marcações no texto: `*palavra*` = destaque em turquesa (nos títulos); `**palavra**` = negrito; linha em branco (`\n\n`) = novo parágrafo.
Todo slide aceita `"fundo": "claro" | "escuro" | "turquesa"` e `"etiqueta"` (selo no topo).

| tipo | campos | uso |
|---|---|---|
| `capa` | `titulo`, `subtitulo` | primeiro slide (fundo escuro por padrão) |
| `texto` | `titulo`, `texto` | explicação |
| `lista` | `titulo`, `itens` (lista), `inicio` | passos, checklist |
| `destaque` | `numero`, `titulo`, `texto` | um valor grande (ex.: "R$ 81 mil") |
| `alerta` | `titulo`, `texto`, `etiqueta` | atenção / erro comum (selo laranja) |
| `comparacao` | `titulo`, `errado {titulo, itens}`, `certo {titulo, itens}` | evite x faça assim |
| `cta` | `titulo`, `texto`, `botao` | último slide, com logo |

## Identidade visual

- Cores e logos: [assets/marca/README.md](../assets/marca/README.md).
- Fontes (licença livre OFL, em `assets/fontes/`): **Barlow Condensed** nos títulos (parecida com o "FEDRIZZI") e **Jost** no texto (parecida com "contabilidade").
- O @ da conta fica em `instagram/marca.json`.

## Regras de conteúdo

- Conferir todo número, prazo e alíquota antes de mandar para aprovação (valores mudam todo ano).
- Nada é publicado sem aprovação do Maurício.
