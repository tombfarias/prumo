## Convenções do perfil: WordPress

### Estrutura sugerida

```text
wp-content/themes/{{slug}}/                  # tema de blocos: theme.json, templates/, parts/, patterns/, functions.php
wp-content/plugins/{{slug}}-funcionalidades/  # tipos de post, taxonomias, campos, blocos, REST, integrações, WooCommerce
tests/                                       # PHPUnit (unitário com Brain Monkey; integração no wp-env)
composer.json  phpcs.xml.dist  .wp-env.json  package.json
```

O repositório guarda só o código do projeto: núcleo do WordPress, plugins de terceiros e `uploads/` ficam fora do git
(o wp-env e o `.gitignore` cuidam disso). Montagem inicial (composer, phpcs, wp-env, testes): skill `desenvolver-wordpress`.
Início rápido: `npx @wordpress/env start` (precisa de Docker) e, para cada bloco, `npx @wordpress/create-block@latest`.

### Padrões

- **Tema só apresenta; plugin guarda as regras.** Tipos de post, taxonomias, campos, shortcodes e integrações ficam no plugin, para o conteúdo sobreviver a uma troca de tema.
- **Prefixo `{{prefixo}}_`** (ou namespace PHP) em funções, classes, hooks, opções e chaves de meta; `{{slug}}` em handles de script e no text domain.
- Use hooks (`add_action`/`add_filter`); nunca edite o núcleo nem plugins de terceiros. Tema comprado: tema filho.
- Estilos e scripts só por `wp_enqueue_style`/`wp_enqueue_script` (ou `block.json`), com versão. Cores, fontes e espaçamentos do Figma vão para o `theme.json`.
- Consultas com `WP_Query`/`get_posts`; SQL direto só com `$wpdb->prepare()`. Tabela própria só com volume alto, criada com `dbDelta()` na ativação.
- Textos com `__()`/`esc_html__()` e o text domain; o painel fica em português para o cliente.
- **WooCommerce:** hooks e CRUD (`wc_get_order()`, `$order->get_meta()`), nunca `get_post_meta` em pedidos (HPOS); declare compatibilidade com HPOS; sobrescreva templates só quando não houver hook.

### Segurança

- Sanitize na entrada (`sanitize_text_field( wp_unslash( ... ) )`), escape na saída e o mais tarde possível (`esc_html`, `esc_attr`, `esc_url`, `wp_kses_post`).
- Toda ação que altera dados confere nonce (`check_admin_referer`, `check_ajax_referer`, `wp_verify_nonce`) **e** permissão (`current_user_can`).
- Rotas REST sempre com `permission_callback` real; `__return_true` só em leitura pública.
- Arquivos PHP começam com `defined( 'ABSPATH' ) || exit;`. Em produção: `DISALLOW_FILE_EDIT`, plugins atualizados, sem plugins abandonados.

### Testes

- O hook formata com `phpcbf` e roda `phpcs` (WordPress Coding Standards) em cada PHP editado; corrija os avisos de segurança, não os silencie.
- `composer test` roda o PHPUnit. Antes de entregar: teste no wp-env com o tema e os plugins do cliente, e Lighthouse nas páginas principais.
