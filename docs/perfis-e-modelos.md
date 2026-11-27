# Perfis e modelos

## Perfis

| Perfil | Para | Stack sugerida | Figma |
|---|---|---|---|
| `api-rest` | Backend com API HTTP/JSON, banco e autenticação | Node.js + TypeScript + Fastify + Prisma + PostgreSQL (ou FastAPI) | não |
| `web-fullstack` | Aplicação web com frontend, backend, banco e login | Next.js + TypeScript + Tailwind + Prisma + PostgreSQL + Auth.js | sim |
| `sistema-gestao` | Cadastros, perfis de acesso, relatórios, auditoria | React + Vite + shadcn/ui e NestJS + Prisma (ou Laravel + Filament, Django) | sim |
| `site-institucional` | Site, landing page, portfólio com foco em SEO | Astro + Tailwind (ou Next.js estático, WordPress) | sim |
| `wordpress` | Site ou loja que o cliente edita sozinho | WordPress 6.x + PHP 8.1+, tema de blocos + plugin próprio, wp-env, phpcs (WordPress Coding Standards), PHPUnit; WooCommerce opcional | sim |
| `automacao-bot` | Scripts agendados, integrações, ETL, bots | Python + httpx + Playwright + APScheduler | não |
| `app-mobile` | App Android/iOS | React Native + Expo (ou Flutter) | sim |
| `minimo` | Projeto pequeno, orçamento rápido | a definir | não |

Cada perfil define os documentos incluídos, as pastas de código, os comandos sugeridos (formatar, lint, testar) e as convenções da stack, que entram no `AGENTS.md`.

## Documentos

| Documento | Conteúdo | Perfis |
|---|---|---|
| `00-briefing` | Anotações do cliente, restrições, perguntas, reuniões | todos |
| `01-visao` | Propósito, problema, usuários, escopo dentro/fora, riscos | todos |
| `02-requisitos` | RF, RNF, RN, glossário | todos |
| `03-casos-de-uso` | Atores, diagrama, especificações | todos exceto site e mínimo |
| `04-uml/classes` | Modelo de domínio | api, web, gestão, mobile |
| `04-uml/sequencia` | Sequência por caso de uso | api, web, gestão, automação, mobile |
| `04-uml/estados` | Ciclo de vida | api, web, gestão, mobile |
| `04-uml/atividades` | Processos de negócio | api, web, gestão, automação, mobile |
| `04-uml/componentes` | Componentes e integrações | api, web, gestão, mobile, wordpress |
| `04-uml/implantacao` | Ambientes e infraestrutura | api, web, gestão, automação, mobile, wordpress |
| `05-interface` | Design system, inventário de telas (Figma), navegação | web, gestão, site, mobile, wordpress |
| `06-banco-de-dados` | ER, dicionário, índices, DDL, LGPD, migrações (no WordPress: tipos de post, meta, taxonomias ou tabelas próprias) | api, web, gestão, automação, mobile, wordpress |
| `07-arquitetura` | Stack, pastas, módulos, segurança, operação, ADRs | todos exceto mínimo |
| `08-backlog` | Épicos, histórias, estimativas, marcos, DoR/DoD | todos |
| `09-plano-de-testes` | Estratégia, casos de teste, homologação | todos exceto mínimo |
| `10-proposta-comercial` | Proposta para o cliente | todos |
| `11-entrega` | Implantação, checklist de entrega, operação | todos exceto mínimo |
| `12-seguranca` | Superfície de ataque, ameaças, OWASP, achados, revisões | todos |
| `adr/`, `mudancas/` | Decisões e pedidos de mudança (`_modelo.md` em cada pasta) | todos |

### Perfil `wordpress`

O repositório guarda só o código do projeto: `wp-content/themes/<slug>/` (tema de blocos, apresentação) e `wp-content/plugins/<slug>-funcionalidades/` (tipos de post, campos, blocos, REST, WooCommerce). Os comandos sugeridos usam `composer exec -- phpcbf`/`phpcs` (WordPress Coding Standards, só arquivos `.php`) e `composer test`. A skill `desenvolver-wordpress`, instalada só neste perfil, traz `composer.json`, `phpcs.xml.dist` e `.wp-env.json` prontos, padrões de tema/plugin, WooCommerce (HPOS, CRUD, checkout em blocos) e segurança. O hook bloqueia leitura de `wp-config.php` e comandos destrutivos do WP-CLI.

Documentos que o perfil não traz podem ser adicionados a qualquer momento: `prumo doc --listar` e `prumo doc <id>`.

## Convenções dos modelos

- Orientações ficam em comentários HTML (`<!-- -->`): aparecem para quem edita, mas não contam como lacuna nem como referência.
- Lacunas: `[PREENCHER: dica]`. `prumo status` conta quantas restam por documento.
- Exemplos dos modelos que citam IDs de documentos ausentes no perfil viram "—" na criação do projeto.

## Criar perfis e modelos

O próprio repositório do Prumo traz skills para isso (abra o Claude Code na pasta do Prumo):

- `/criar-perfil`: novo perfil (JSON + convenções + teste);
- `/criar-modelo-documento`: novo documento, com prefixo de ID se necessário.

Manualmente: veja os arquivos em `templates/perfis/` e `templates/documentos/` e rode `python -m unittest discover -s tests -v`, que cria um projeto de cada perfil e valida tudo.
