# Escritório Fedrizzi

Repositório central de projetos do Escritório de Contabilidade Fedrizzi.
Backup completo: em caso de formatação ou troca de máquina, basta clonar.

```bash
git clone git@github.com:mauriciofedrizzi/escritorio-fedrizzi.git
```

## Projeto principal: Reels automáticos para o Instagram

Fluxo: **tema do dia -> roteiro -> gravar no iPhone -> edição automática -> postar**.

| Pasta / arquivo | O que faz |
|---|---|
| `agente-conteudo/` | Busca temas (Google Trends, portais, Virlo.ai) e gera roteiros (`pipeline.py buscar`, `roteiro.py`) |
| `editor/` | **Editor de vídeo profissional** (cortes, legendas, cards animados, câmera, sons). Ver [docs/EDITOR.md](docs/EDITOR.md) |
| `planos/` | Plano de edição de cada vídeo (JSON). Ver [docs/EDITOR.md](docs/EDITOR.md) |
| `iphone-sync/monitor.py` | Vigia as pastas de entrada (iCloud / Telegram Desktop) e copia vídeos novos |
| `telegram_bot.py`, `enviar_telegram.py` | Bot do Telegram (recebe vídeos até 20 MB; envia arquivos) |
| `instagram/postar.py` | Posta Reels pela API oficial do Meta (Graph API) |
| `editar_video.py` | Editor antigo (legenda simples). Substituído por `editor/` |

Documentação completa do pipeline, decisões e problemas conhecidos: [docs/PIPELINE.md](docs/PIPELINE.md).

## Segurança (leia antes de commitar)

- Credenciais ficam **somente** no arquivo `.env` local (ignorado pelo git). Nunca colocar senhas ou tokens em `.env.example`, nos docs ou no chat.
- Não usar `git add -A`: conferir com `git status` antes. Vídeos, `.env`, IDs de chat e logos brutos estão no `.gitignore`.
