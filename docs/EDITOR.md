# Editor de vídeo Fedrizzi (`editor/`)

Transforma o vídeo gravado em um Reel pronto: corta silêncios, legenda por frase, cards animados, câmera com vários ângulos, efeitos sonoros discretos e tela final com o logo.

## Uso

```powershell
# 1) Prepara: corta silêncios e transcreve, listando cada palavra com o tempo (para escrever o plano)
python -m editor.pipeline videos\MEU_VIDEO.MOV --preparar

# 2) Escreve planos\meu_video.json (ver formato abaixo) e renderiza
python -m editor.pipeline videos\MEU_VIDEO.MOV --plano planos\meu_video.json --saida videos\editados\MEU_VIDEO.mp4
```

Opções: `--titulo`, `--subtitulo` (sem plano, usa plano automático), `--preview N` (renderiza só N segundos), `--modelo` (padrão `medium`).
Renderizar 40 s leva ~2,5 min. Caches em `videos/cortes/` (proxy, corte e transcrição `*_words.json`): apague para refazer do zero.

## Etapas

1. **Proxy** 1296x2304 vertical (aplica a rotação do iPhone).
2. **auto-editor** remove silêncios (margens 0,25 s / 0,35 s).
3. **whisperX** (`medium`, `initial_prompt` contábil) transcreve com tempo por palavra; `reparar_tempos` corrige números.
4. **Plano** (JSON) é resolvido nas palavras faladas: cada gráfico nasce numa frase-âncora, não num tempo fixo.
5. **Render quadro a quadro** (Pillow): câmera, cards, legenda, barra de progresso, tela final. Saída H.264 1080x1920, 30 fps.
6. **Áudio**: voz tratada (passa-alta 80 Hz, redução de ruído, compressor, loudnorm -16 LUFS) + efeitos sintetizados.

## Formato do plano (`planos/*.json`)

Chaves do topo:

| Chave | Descrição |
|---|---|
| `titulo`, `subtitulo` | Abertura (título grande no centro que vira card no topo) |
| `foco_y` | Altura do rosto no quadro (0 a 1) para o zoom (padrão 0,46; vídeo de corpo inteiro: ~0,30) |
| `hero` | `false` desliga a abertura grande |
| `nome` | `false` desliga a etiqueta "MAURICIO FEDRIZZI / CEO" |
| `destaques` | Trechos que ficam em ciano nas legendas (números e termos como MEI/imposto já são automáticos) |
| `cta` | `{ "pergunta": "...", "botao": "Fale com a Fedrizzi" }` da tela final |
| `eventos` | Lista de gráficos, em ordem cronológica |

Tipos de `eventos` (todos usam `ancora`: palavras faladas que disparam o gráfico; `duracao` em segundos, opcional):

| `tipo` | Campos | Resultado |
|---|---|---|
| `valor` | `rotulo`, `valor` (ex.: "R$ 81 MIL"), `icone`, `contar` | Card com número que conta até o valor |
| `palavra` | `texto`, `icone` | Palavra grande no topo que "acende" de ciano para branco |
| `chip` | `texto`, `icone` | Pílula de vidro no topo à esquerda |
| `lista` | `titulo`, `itens[{texto, icone, ancora}]` | Lista que acende item a item |
| `medidor` | `titulo`, `maximo`, `fim_ancora`, `segmentos[{de, ate, cor, marca, ancora}]` | Barra de limite com zonas (`ciano`, `ambar`, `vermelho`, `verde`) que enchem na fala |
| `cta` | `texto`, `icone` (`salvar`, `compartilhar`, `seguir`) | Botão de ação embaixo, acima da legenda |
| `nome` | `nome`, `cargo` | Etiqueta de nome |
| `soco` | `quanto` | Zoom rápido de ênfase |
| `tremida` | — | Tremida de tela com som de impacto |

Ícones disponíveis: ver `ICONES` em `editor/motion.py` (Font Awesome Free). Elementos do topo nunca se sobrepõem: o anterior sai quando o próximo entra. Âncora não encontrada gera aviso `[aviso]` e o item é pulado.

Exemplo completo: `planos/limite_mei.json`.

## Design (identidade visual)

- Tela 1080x1920. Cards do topo em `y=192` (abaixo da interface do Instagram), legenda centrada em `y=1445`, barra de progresso ciano em `y=163`, botões de ação em `y~1275`.
- Cor da marca: ciano `#18C8CC`. Fontes: **Poppins** (legenda e textos), **Bebas Neue** (títulos e números), **Font Awesome Free** (ícones).
- Cards: vidro fosco (vídeo desfocado e escurecido atrás), cantos arredondados, borda branca fina.
- Legenda: frases de até ~5 palavras, só as palavras-chave em ciano (máx. 2 por frase), contorno e degradê escuro no rodapé para contraste.
- Câmera: novo ângulo a cada ~3 s em pausas da fala, ciclo de zoom 1,0 a 1,26 com deslocamento lateral alternado e empurrada lenta; micro-zoom nas palavras destacadas.
- Tela final: fundo escuro, logo branco/ciano, pergunta e botão "Fale com a Fedrizzi" (3,4 s extras).

## Áudio e efeitos sonoros

Efeitos (`whoosh`, `pop`, `ding`, `tick`, `impacto`) são **sintetizados** em `editor/sfx.py` e ficam bem abaixo da voz (a referência quase não tem efeito). Para usar sons melhores, coloque `sfx/<nome>.wav` com o mesmo nome e eles substituem os sintéticos. Volumes em `GANHO_DB`. Não há música de fundo (as referências analisadas não usam).

## Assets (fora do git — recriar em outra máquina)

- Fontes em `assets/fonts/`: `Poppins-SemiBold.ttf`, `Poppins-Bold.ttf`, `BebasNeue-Regular.ttf` (repositório `google/fonts`, pasta `ofl/`) e `fa-solid-900.ttf` (Font Awesome Free 6.5.1, cdnjs).
- Logo: rasterizar o PDF do logo (`Downloads\logo.pdf`, 4x) para `assets/raw_logo.png` e rodar `python editor/gerar_assets.py`, que gera `assets/logo_branco.png` e `assets/icone.png`.

## Referências estudadas

- Vídeo do amigo (Fedrizzi, 82 s): card de vidro no topo, valores grandes ("R$ 5 MIL"), listas que acendem, legenda por frase com palavra em ciano, etiqueta de nome, tela final com logo e botão; só efeitos sonoros curtos, sem música.
- Raul Sena / Investidor Sardinha (YouTube): troca de ângulo a cada ~6 s com 3 enquadramentos, painéis de dados com números entrando um a um, botões de ação (curtir/inscrever) no meio do vídeo, áudio limpo sem efeitos.

## Arquitetura (para manutenção)

- `editor/motion.py`: elementos gráficos (`Hero`, `CartaoTitulo`, `CartaoValor`, `Palavra`, `Chip`, `Lista`, `Medidor`, `PilulaCTA`, `EtiquetaNome`, `Legenda`, `Final`, `Progresso`) e a `Camera`. Cada elemento tem `draw(frame, t)` e `sfx`.
- `editor/pipeline.py`: etapas de mídia, transcrição, resolução do plano nas palavras, render e mistura.
- `editor/sfx.py`: síntese dos sons e mixagem. `editor/gerar_assets.py`: logo para fundo escuro.
