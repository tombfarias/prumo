<p align="center"><img src="assets/prumo.png" width="96" alt=""></p>

# Prumo

**Especificação primeiro, código alinhado.** O Prumo é um sistema para projetos freelance que gera documentação de especificação detalhada (visão, requisitos, casos de uso, UML, banco de dados, arquitetura, backlog, testes, segurança, proposta), monta o kit de agentes de IA de cada projeto (skills, subagentes e hooks do Claude Code, com instruções para Codex, Gemini, Copilot e Cursor) e mantém tudo coerente com o código por meio de IDs rastreáveis.

O nome vem do fio de prumo, a ferramenta que mantém a obra alinhada. No Prumo, o que fica alinhado é o código com a especificação.

## O que ele faz

| | |
|---|---|
| **Perfis de projeto** | API REST, aplicação web full-stack, sistema de gestão, site institucional, automação/bot, app mobile e mínimo, cada um com documentos, stack sugerida e convenções próprias |
| **Especificação rastreável** | IDs `RF`, `RN`, `UC`, `TL`, `HU`, `CT`, `SEG`, `ADR`, `CM` ligados entre si e ao código; matriz de rastreabilidade gerada |
| **UML e banco em Mermaid** | Classes, sequência, estados, atividades, componentes, implantação e diagrama ER, validados automaticamente |
| **Kit de agentes** | Até 16 skills (do levantamento de requisitos à revisão de segurança), 4 subagentes e 7 hooks em cada projeto criado |
| **Guarda-corpos** | Hooks bloqueiam comandos destrutivos, acesso a `.env` e edição de documentos aprovados pelo cliente |
| **Mudanças significativas** | Ao fim de uma mudança relevante, o Claude é obrigado a atualizar a documentação e procurar falhas de segurança |
| **Economia de tokens** | `prumo contexto HU-003` carrega só a trilha necessária; regras e bloqueios de leitura evitam desperdício |
| **Claude pelo terminal** | `prumo claude <tarefa>` e o módulo PowerShell (`Send-Claude`, `Invoke-PrumoTarefa`) disparam o Claude Code sem abrir o editor |
| **Figma** | Servidor MCP do Figma configurado, inventário de telas sincronizado pela API e diagramas publicados no FigJam |
| **Gestão freelance** | Orçamento a partir das estimativas do backlog, horas trabalhadas registradas pelos hooks, proposta e checklist de entrega |
| **Interface gráfica** | Leve, em HTML/CSS/JS puro, com modo claro e escuro; abre em janela própria |
| **Executável** | `prumo.exe` e `prumo-app.exe` para Windows, gerados pelo GitHub Actions ou pelo `build.ps1` |

## Começo rápido

```powershell
git clone https://github.com/tombfarias/prumo D:\SistemaCodigo
cd D:\SistemaCodigo
powershell -ExecutionPolicy Bypass -File .\powershell\instalar.ps1 -AdicionarAoPath   # opcional

prumo novo D:\Projetos\loja-da-ana --perfil web-fullstack --nome "Loja da Ana" --cliente "Ana Doces"
cd D:\Projetos\loja-da-ana
prumo claude especificar        # ou abra o Claude Code e use /especificar-projeto
prumo status
```

Requisitos: Python 3.9+ (ou o executável), Git e, para as tarefas com IA, o [Claude Code](https://docs.claude.com/en/docs/claude-code/overview).

## Documentação

| Guia | Conteúdo |
|---|---|
| [Instalação](docs/instalacao.md) | Python ou executável, PowerShell, PATH, Claude Code |
| [Guia rápido](docs/guia-rapido.md) | Do zero ao primeiro projeto especificado |
| [Fluxo de trabalho freelance](docs/fluxo-de-trabalho.md) | Do primeiro contato com o cliente à entrega |
| [Referência de comandos](docs/comandos.md) | Todos os comandos e opções da CLI |
| [Interface gráfica](docs/interface-grafica.md) | Telas, atalhos e funcionamento |
| [PowerShell e Claude](docs/powershell-e-claude.md) | `prumo claude`, `Send-Claude`, `Invoke-PrumoTarefa`, automação |
| [Agentes, skills e hooks](docs/agentes-skills-hooks.md) | O que é instalado em cada projeto e como personalizar |
| [Rastreabilidade](docs/rastreabilidade.md) | Convenção de IDs, matriz, contexto compacto |
| [Figma](docs/figma.md) | MCP, inventário de telas, FigJam |
| [Segurança e mudanças](docs/seguranca-e-mudancas.md) | Mudanças significativas, revisão de segurança, aprovação e controle de escopo |
| [Economia de tokens](docs/economia-de-tokens.md) | Como o Prumo reduz o consumo sem perder qualidade |
| [Configuração](docs/configuracao.md) | `projeto.prumo.json` e `config/freelancer.json` |
| [Perfis e modelos](docs/perfis-e-modelos.md) | Perfis disponíveis, documentos e como criar novos |
| [Executável](docs/executavel.md) | Geração do `.exe` local e pelo GitHub Actions |
| [Solução de problemas](docs/solucao-de-problemas.md) | Erros comuns e como resolver |
| [Arquitetura do Prumo](docs/arquitetura-do-prumo.md) | Para quem vai evoluir o próprio Prumo |

## Licença

Ainda sem licença definida: por padrão, todos os direitos ficam com o autor. Para permitir reuso, adicione um arquivo `LICENSE` (por exemplo, MIT).
