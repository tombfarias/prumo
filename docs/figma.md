# Figma

A integração tem três partes: o **servidor MCP do Figma** para os agentes, a **sincronização do inventário de telas** pela API REST e a **publicação de diagramas no FigJam**.

## Ativação

Perfis com interface (`web-fullstack`, `sistema-gestao`, `site-institucional`, `app-mobile`) já vêm com o Figma ativo. Nos demais: `prumo novo ... --com-figma` ou, num projeto existente, `prumo figma ativar [URL]`.

Ativar significa:

- `.mcp.json` com o servidor remoto oficial (`https://mcp.figma.com/mcp`);
- skills `implementar-tela-figma` e `diagramas-figjam`;
- documento `docs/05-interface.md` com o inventário de telas;
- seção sobre o Figma no `CLAUDE.md`.

## 1. Servidor MCP (agentes)

Na primeira vez, no Claude Code aberto na pasta do projeto: `/mcp` → **figma** → **Authenticate** → permitir no navegador. A partir daí, a skill `implementar-tela-figma` usa as ferramentas do servidor para obter o contexto de design de um frame, a captura da tela e as variáveis (cores, tipografia, espaçamentos), e adapta o resultado aos componentes e tokens do projeto.

```text
/implementar-tela-figma TL-002
prumo claude tela TL-002
prumo claude tela "https://www.figma.com/design/XXXX/Loja?node-id=12-345"
```

## 2. Inventário de telas (API REST)

1. Crie um token pessoal no Figma (Settings → Security → Personal access tokens) com permissão de leitura de arquivos.
2. Defina a variável e sincronize:

```powershell
$env:FIGMA_TOKEN = "figd_..."
prumo figma telas "https://www.figma.com/design/XXXX/Loja"
prumo figma telas --imagens          # baixa um PNG de cada tela para docs/telas/
```

O Prumo lê as páginas do arquivo e lista cada frame de primeiro nível (e os frames dentro de seções), ignorando os ocultos. A tabela entre `<!-- prumo:figma:inicio -->` e `<!-- prumo:figma:fim -->` em `05-interface.md` é reescrita a cada sincronização:

| ID | Tela | Página do Figma | Link | Casos de uso | Imagem |
|---|---|---|---|---|---|

- Os IDs `TL-xxx` são **estáveis**: ficam gravados em `projeto.prumo.json` → `figma.telas` por ID de nó do Figma.
- A coluna **Casos de uso** é sua (ou da skill) e é **preservada** nas sincronizações.
- Telas apagadas no Figma continuam na tabela como "(não encontrada no Figma)", para não quebrar referências.

Na interface gráfica, a aba **Gestão** tem o mesmo recurso (URL, token e opção de baixar imagens).

## 3. Diagramas no FigJam

A skill `diagramas-figjam` (ou `prumo claude figjam`) valida e extrai os diagramas (`prumo diagramas`) e usa a ferramenta de geração de diagramas do servidor MCP para criá-los no FigJam, registrando os links nos documentos. O Mermaid continua sendo a fonte da verdade.
