# Pipeline de Reels — visão geral

Última atualização: 24/11/2026.

## Fluxo completo

1. **Tema do dia** — `agente-conteudo/pipeline.py buscar`: Google Trends (geo BR) + portais contábeis + vídeos virais do Virlo.ai.
2. **Roteiro** — preferência do Maurício: o **Claude escreve o roteiro no chat** (com cues de animação e PDF se pedir). Alternativa automática gratuita: `agente-conteudo/roteiro.py` usa o Hermes3 local (Ollama), com qualidade inferior.
3. **Gravação** — iPhone, vertical 9:16, câmera na altura dos olhos, luz de frente, **sem fone com microfone**, rosto na altura de ~35-45% do quadro (cards ocupam o topo).
4. **Entrada do vídeo no PC** — ver "Como o vídeo chega ao PC".
5. **Edição** — `python -m editor.pipeline <video> --plano planos/<nome>.json` (ver [EDITOR.md](EDITOR.md)). Saída em `videos/editados/`.
6. **Postagem** — `instagram/postar.py` (Meta Graph API). **Pendente:** a API exige uma URL pública HTTPS do vídeo (ideia: Cloudinary, plano grátis).

## Como o vídeo chega ao PC

| Caminho | Situação |
|---|---|
| iCloud Drive/Trabalho | Funciona, mas sincroniza com muito atraso. Abandonado como principal. |
| Bot do Telegram (`@Fedrizzi_video_bot`) | **Limite de 20 MB por arquivo** (API de bots). Só serve para vídeos pequenos. |
| **Telegram Desktop + Mensagens Salvas** | **Caminho recomendado.** No iPhone: Mensagens Salvas -> clipe -> *Arquivo* (não Galeria) -> o Telegram Desktop baixa em `Downloads\Telegram Desktop` sem limite. `iphone-sync/monitor.py` vigia essa pasta. |

Observação: hoje `monitor.py` ainda chama o editor antigo (`editar_video.py`). Falta ligá-lo ao `editor/pipeline.py`.

## Credenciais (`.env`, nunca no git)

Nomes das variáveis (os valores ficam só na máquina):
`META_ACCESS_TOKEN` (System User, não expira), `META_IG_ID`, `META_PAGE_ID`, `APIFY_API_KEY`, `VIRLO_API_KEY`, `TELEGRAM_BOT_TOKEN`, `EMAIL_REMETENTE`, `EMAIL_SENHA_APP`, `ANTHROPIC_API_KEY` (não usada hoje).

Outros arquivos locais que não devem ir ao git: `telegram_chat_id.txt` (gerado pelo bot) e `*.env.txt`.

## Dependências (Windows, Python 3.12)

- FFmpeg e ffprobe no PATH.
- `pip install auto-editor whisperx pillow numpy scipy pymupdf python-telegram-bot requests python-dotenv ollama yt-dlp`
- Ollama + modelo `hermes3` (só para roteiro automático).
- Whisper/whisperX roda em CPU (torch sem CUDA neste PC); o modelo `medium` leva ~2-4 min para 40 s de áudio.

## Problemas conhecidos e como foram resolvidos

| Problema | Causa | Solução adotada |
|---|---|---|
| Vídeo do iPhone saía deitado | A rotação fica só em metadado; o auto-editor descartava | O editor gera primeiro um *proxy* 1296x2304 com `ffmpeg` (aplica a rotação) e só então corta silêncios |
| auto-editor levava ~13 min em 4K | Reencode 4K em CPU | Rodar no proxy (cerca de 1 min) |
| Legendas com termos errados ("acedeu") | Modelo `small` | Modelo `medium` + `initial_prompt` com vocabulário contábil |
| Números ("R$ 81 mil") sem tempo | O alinhador não temporiza dígitos | `reparar_tempos()` interpola o tempo entre palavras vizinhas |
| Upload do PC para o Telegram falha | Upload medido em ~6,7 KB/s para `api.telegram.org` | Não enviar vídeo do PC pelo Telegram; abrir pelo Explorer ou outro caminho |
| `print` com emoji quebra no Windows | Terminal cp1252 | Evitar emoji em `print` ou gravar em arquivo |

## Pendências

- Ligar `iphone-sync/monitor.py` e `telegram_bot.py` ao `editor/pipeline.py` (plano automático como fallback).
- Hospedagem pública temporária do vídeo para o Instagram (Cloudinary ou similar) e testar a postagem de ponta a ponta.
- Conferir fatos antes de postar (ex.: limite do MEI de R$ 81 mil/ano, tolerância de 20% = R$ 97.200).
- Tela de CTA, nome e cargo no final: confirmar textos finais com o Maurício.
