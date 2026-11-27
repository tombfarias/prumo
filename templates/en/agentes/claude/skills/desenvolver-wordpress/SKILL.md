---
name: desenvolver-wordpress
description: Sets up and develops the WordPress project (block theme, features plugin, blocks, REST, WooCommerce) with wp-env, PHP_CodeSniffer and PHPUnit, following the specification. Use when starting the code, creating a post type, field, block, REST route, admin screen or WooCommerce customization.
---

# Develop in WordPress

Also follow `implementar-historia` (HU → UC/RF/RN trail, tests first). This file holds only the WordPress decisions.
Prefix for functions, options and meta: `{{prefixo}}_`; text domain and handles: `{{slug}}`. Folders: `wp-content/themes/{{slug}}/` and `wp-content/plugins/{{slug}}-features/`.

## 1. Initial setup (once)

1. `composer.json` at the root, with the development tools:
   `composer require --dev wp-coding-standards/wpcs:^3.0 phpcompatibility/phpcompatibility-wp:"*" phpunit/phpunit:^9.6 yoast/phpunit-polyfills:^2.0 brain/monkey:^2.6`
   (allow the `dealerdirect/phpcodesniffer-composer-installer` plugin in `config.allow-plugins`) and the script
   `"scripts": {"test": "phpunit", "lint": "phpcs", "format": "phpcbf"}`.
2. `phpcs.xml.dist`:
   ```xml
   <?xml version="1.0"?>
   <ruleset name="{{slug}}">
     <file>wp-content/themes/{{slug}}</file>
     <file>wp-content/plugins/{{slug}}-features</file>
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
3. `.wp-env.json` (needs Docker; `npx @wordpress/env start` runs it at `http://localhost:8888`, admin/password):
   ```json
   {
     "phpVersion": "8.2",
     "themes": ["./wp-content/themes/{{slug}}"],
     "plugins": ["./wp-content/plugins/{{slug}}-features"],
     "config": {"WP_DEBUG": true, "WP_DEBUG_LOG": true, "DISALLOW_FILE_EDIT": true}
   }
   ```
   With a store, add `"https://downloads.wordpress.org/plugin/woocommerce.zip"` to `plugins`.
4. `.gitignore`: `vendor/`, `node_modules/`, `build/`, `wp-content/uploads/`, `wp-content/upgrade/`, `wp-config.php`
   and third-party plugins/themes (commit only the project's two folders).
5. In `projeto.prumo.json`, copy `comandos_sugeridos` to `comandos` (the hook then runs phpcbf and phpcs on each edit).

## 2. Theme (presentation)

- Block theme: `theme.json` (colors, fonts, spacing and widths **from Figma**), `templates/*.html`, `parts/`
  (header, footer), `patterns/` (reusable sections the client inserts). Theme header in `style.css`.
- Small `functions.php`: theme supports, enqueue assets, register patterns. No business rules.
- Figma screen → block pattern or template; use `implementar-tela-figma` and check at `localhost:8888`.
- Theme bought by the client: child theme (`Template:` in `style.css`), overriding only what is needed.

## 3. Features plugin (rules)

- Main file with header (`Plugin Name`, `Text Domain: {{slug}}`, `Requires PHP: 8.1`), `defined( 'ABSPATH' ) || exit;`,
  classes in `includes/` with a namespace and hooks registered in a single place.
- Entities in `06-banco-de-dados.md` become **post type + meta + taxonomy** (`register_post_type`, `register_post_meta`
  with `show_in_rest` and `sanitize_callback`, `register_taxonomy`). A custom table only for high volume or heavy queries:
  `$wpdb->prefix`, `dbDelta()` on activation and the schema version in an option. Record the choice in an ADR.
- Blocks: `npx @wordpress/create-block@latest <name> --no-plugin` inside the plugin; build with `@wordpress/scripts`;
  register through `block.json` (`register_block_type( __DIR__ . '/build/<name>' )`).
- REST: `register_rest_route( '{{slug}}/v1', ... )` with validated `args` and a real `permission_callback`.
- Admin: screens with the Settings API or blocks; settings in `get_option`/`update_option` with a prefix and `autoload` off if large.
- Scheduled tasks: WP-Cron (`wp_schedule_event`) or Action Scheduler (with WooCommerce); always idempotent.

## 4. WooCommerce (if there is a store)

- Declare HPOS compatibility in the plugin:
  ```php
  add_action( 'before_woocommerce_init', function () {
      if ( class_exists( \Automattic\WooCommerce\Utilities\FeaturesUtil::class ) ) {
          \Automattic\WooCommerce\Utilities\FeaturesUtil::declare_compatibility( 'custom_order_tables', __FILE__, true );
      }
  } );
  ```
- Orders and products only through the CRUD (`wc_get_order()`, `wc_get_product()`, `->get_meta()`, `->update_meta_data()` + `->save()`).
- Block checkout and cart (current default) ignore classic checkout hooks: customize with the extension APIs
  of the blocks/Store API, or record in an ADR that the store uses the classic checkout.
- Template override (`woocommerce/` in the theme) only without an equivalent hook; check the version in the header after each update.
- Payment: the gateway's official plugin; card data never goes through the project's code. Shipping, coupons and taxes through the WooCommerce settings before custom code.

## 5. Security (phpcs flags it; do not silence it)

- Input: `sanitize_text_field( wp_unslash( $_POST['x'] ?? '' ) )`, `absint`, `sanitize_email`... Output: `esc_html`, `esc_attr`, `esc_url`, `wp_kses_post`.
- Data changes: nonce (`wp_nonce_field` + `check_admin_referer`/`check_ajax_referer`) and `current_user_can( '<capability>' )`.
- SQL only with `$wpdb->prepare()`. Upload with `wp_handle_upload` and `wp_check_filetype_and_ext`.
- `// phpcs:ignore` only with a justification on the same line and a record in `12-seguranca.md`.

## 6. Tests and delivery

- Unit (without WordPress, runs in seconds): PHPUnit + Brain Monkey (`Monkey\setUp()`/`tearDown()`, `Functions\expect( 'get_option' )`). `composer test`.
- Integration: in wp-env, `npx @wordpress/env run cli --env-cwd=wp-content/plugins/{{slug}}-features phpunit`
  (the bootstrap uses `getenv( 'WP_TESTS_DIR' )`, which wp-env sets).
- Before delivering: `composer lint` with no errors, test with the client's plugins active, Lighthouse, and the `11-entrega.md` checklist
  (migration with `wp search-replace --dry-run` first, backup before, permalinks, cache, SMTP).
