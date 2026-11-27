---
name: desenvolver-wordpress
description: Monta e desenvolve o projeto WordPress (tema de blocos, plugin de funcionalidades, blocos, REST, WooCommerce) com wp-env, PHP_CodeSniffer e PHPUnit, seguindo a especificação. Use ao iniciar o código, criar tipo de post, campo, bloco, rota REST, tela do painel ou personalização do WooCommerce.
---

# Desenvolver em WordPress

Siga também `implementar-historia` (trilha HU → UC/RF/RN, testes primeiro). Aqui ficam só as decisões do WordPress.
Prefixo de funções, opções e meta: `{{prefixo}}_`; text domain e handles: `{{slug}}`. Pastas: `wp-content/themes/{{slug}}/` e `wp-content/plugins/{{slug}}-funcionalidades/`.

## 1. Montagem inicial (uma vez)

1. `composer.json` na raiz, com as ferramentas de desenvolvimento:
   `composer require --dev wp-coding-standards/wpcs:^3.0 phpcompatibility/phpcompatibility-wp:"*" phpunit/phpunit:^9.6 yoast/phpunit-polyfills:^2.0 brain/monkey:^2.6`
   (aceite o plugin `dealerdirect/phpcodesniffer-composer-installer` em `config.allow-plugins`) e o script
   `"scripts": {"test": "phpunit", "lint": "phpcs", "format": "phpcbf"}`.
2. `phpcs.xml.dist`:
   ```xml
   <?xml version="1.0"?>
   <ruleset name="{{slug}}">
     <file>wp-content/themes/{{slug}}</file>
     <file>wp-content/plugins/{{slug}}-funcionalidades</file>
     <arg name="extensions" value="php"/>
     <arg value="s"/>
     <exclude-pattern>*/vendor/*</exclude-pattern>
     <exclude-pattern>*/build/*</exclude-pattern>
     <exclude-pattern>*/node_modules/*</exclude-pattern>
     <config name="testVersion" value="8.1-"/>
     <config name="minimum_wp_supported_version" value="6.5"/>
     <rule ref="WordPress"/>
     <rule ref="PHPCompatibilityWP"/>
     <rule ref="WordPress.WP.I18n">
       <properties><property name="text_domain" type="array"><element value="{{slug}}"/></property></properties>
     </rule>
     <rule ref="WordPress.NamingConventions.PrefixAllGlobals">
       <properties><property name="prefixes" type="array"><element value="{{prefixo}}"/></property></properties>
     </rule>
   </ruleset>
   ```
3. `.wp-env.json` (precisa de Docker; `npx @wordpress/env start` sobe em `http://localhost:8888`, admin/password):
   ```json
   {
     "phpVersion": "8.2",
     "themes": ["./wp-content/themes/{{slug}}"],
     "plugins": ["./wp-content/plugins/{{slug}}-funcionalidades"],
     "config": {"WP_DEBUG": true, "WP_DEBUG_LOG": true, "DISALLOW_FILE_EDIT": true}
   }
   ```
   Com loja, acrescente `"https://downloads.wordpress.org/plugin/woocommerce.zip"` em `plugins`.
4. `.gitignore`: `vendor/`, `node_modules/`, `build/`, `wp-content/uploads/`, `wp-content/upgrade/`, `wp-config.php`
   e os plugins/temas de terceiros (versione só as duas pastas do projeto).
5. Em `projeto.prumo.json`, copie `comandos_sugeridos` para `comandos` (o hook passa a rodar phpcbf e phpcs a cada edição).

## 2. Tema (apresentação)

- Tema de blocos: `theme.json` (cores, fontes, espaçamentos e larguras **do Figma**), `templates/*.html`, `parts/`
  (cabeçalho, rodapé), `patterns/` (seções reutilizáveis que o cliente insere). Cabeçalho do tema em `style.css`.
- `functions.php` pequeno: suportes do tema, enfileirar assets, registrar padrões. Nada de regra de negócio.
- Tela do Figma → padrão de blocos ou template; use `implementar-tela-figma` e confira em `localhost:8888`.
- Tema comprado pelo cliente: tema filho (`Template:` no `style.css`), só sobrescrevendo o necessário.

## 3. Plugin de funcionalidades (regras)

- Arquivo principal com cabeçalho (`Plugin Name`, `Text Domain: {{slug}}`, `Requires PHP: 8.1`), `defined( 'ABSPATH' ) || exit;`,
  classes em `includes/` com namespace e ganchos registrados em um ponto só.
- Entidades do `06-banco-de-dados.md` viram **tipo de post + meta + taxonomia** (`register_post_type`, `register_post_meta`
  com `show_in_rest` e `sanitize_callback`, `register_taxonomy`). Tabela própria só para volume alto ou consultas pesadas:
  `$wpdb->prefix`, `dbDelta()` na ativação e versão do schema em uma opção. Registre a escolha num ADR.
- Blocos: `npx @wordpress/create-block@latest <nome> --no-plugin` dentro do plugin; build com `@wordpress/scripts`;
  registre pelo `block.json` (`register_block_type( __DIR__ . '/build/<nome>' )`).
- REST: `register_rest_route( '{{slug}}/v1', ... )` com `args` validados e `permission_callback` real.
- Painel: telas com Settings API ou blocos; configurações em `get_option`/`update_option` com prefixo e `autoload` desligado se grandes.
- Tarefas agendadas: WP-Cron (`wp_schedule_event`) ou Action Scheduler (com WooCommerce); sempre idempotentes.

## 4. WooCommerce (se houver loja)

- Declare compatibilidade com HPOS no plugin:
  ```php
  add_action( 'before_woocommerce_init', function () {
      if ( class_exists( \Automattic\WooCommerce\Utilities\FeaturesUtil::class ) ) {
          \Automattic\WooCommerce\Utilities\FeaturesUtil::declare_compatibility( 'custom_order_tables', __FILE__, true );
      }
  } );
  ```
- Pedidos e produtos só pelo CRUD (`wc_get_order()`, `wc_get_product()`, `->get_meta()`, `->update_meta_data()` + `->save()`).
- Checkout e carrinho em blocos (padrão atual) ignoram hooks do checkout clássico: personalize com as APIs de extensão
  dos blocos/Store API, ou registre no ADR que a loja usa o checkout clássico.
- Sobrescrita de template (`woocommerce/` no tema) só sem hook equivalente; confira a versão no cabeçalho após cada atualização.
- Pagamento: plugin oficial do gateway; dados de cartão nunca passam pelo código do projeto. Fretes, cupons e impostos pela configuração do WooCommerce antes de código próprio.

## 5. Segurança (o phpcs aponta; não silencie)

- Entrada: `sanitize_text_field( wp_unslash( $_POST['x'] ?? '' ) )`, `absint`, `sanitize_email`... Saída: `esc_html`, `esc_attr`, `esc_url`, `wp_kses_post`.
- Alteração de dados: nonce (`wp_nonce_field` + `check_admin_referer`/`check_ajax_referer`) e `current_user_can( '<capacidade>' )`.
- SQL só com `$wpdb->prepare()`. Upload com `wp_handle_upload` e `wp_check_filetype_and_ext`.
- `// phpcs:ignore` só com justificativa na mesma linha e registro em `12-seguranca.md`.

## 6. Testes e entrega

- Unitário (rápido, sem WordPress): PHPUnit + Brain Monkey (`Monkey\setUp()`/`tearDown()`, `Functions\expect( 'get_option' )`). `composer test`.
- Integração: no wp-env, `npx @wordpress/env run cli --env-cwd=wp-content/plugins/{{slug}}-funcionalidades phpunit`
  (o bootstrap usa `getenv( 'WP_TESTS_DIR' )`, que o wp-env define).
- Antes de entregar: `composer lint` sem erros, teste com os plugins do cliente ativos, Lighthouse, e o roteiro de `11-entrega.md`
  (migração com `wp search-replace --dry-run` primeiro, backup antes, permalinks, cache, SMTP).
