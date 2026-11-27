## Profile conventions: WordPress

### Suggested structure

```text
wp-content/themes/{{slug}}/          # block theme: theme.json, templates/, parts/, patterns/, functions.php
wp-content/plugins/{{slug}}-features/ # post types, taxonomies, fields, blocks, REST, integrations, WooCommerce
tests/                               # PHPUnit (unit with Brain Monkey; integration in wp-env)
composer.json  phpcs.xml.dist  .wp-env.json  package.json
```

The repository keeps only the project's code: WordPress core, third-party plugins and `uploads/` stay out of git
(wp-env and `.gitignore` handle it). Initial setup (composer, phpcs, wp-env, tests): skill `desenvolver-wordpress`.
Quick start: `npx @wordpress/env start` (needs Docker) and, for each block, `npx @wordpress/create-block@latest`.

### Patterns

- **The theme only presents; the plugin keeps the rules.** Post types, taxonomies, fields, shortcodes and integrations live in the plugin, so the content survives a theme change.
- **Prefix `{{prefixo}}_`** (or a PHP namespace) on functions, classes, hooks, options and meta keys; `{{slug}}` on script handles and in the text domain.
- Use hooks (`add_action`/`add_filter`); never edit core or third-party plugins. Bought theme: child theme.
- Styles and scripts only through `wp_enqueue_style`/`wp_enqueue_script` (or `block.json`), with a version. Figma colors, fonts and spacing go into `theme.json`.
- Queries with `WP_Query`/`get_posts`; direct SQL only with `$wpdb->prepare()`. Custom table only with high volume, created with `dbDelta()` on activation.
- Texts with `__()`/`esc_html__()` and the text domain; the admin stays in the client's language.
- **WooCommerce:** hooks and CRUD (`wc_get_order()`, `$order->get_meta()`), never `get_post_meta` on orders (HPOS); declare HPOS compatibility; override templates only when there is no hook.

### Security

- Sanitize on input (`sanitize_text_field( wp_unslash( ... ) )`), escape on output and as late as possible (`esc_html`, `esc_attr`, `esc_url`, `wp_kses_post`).
- Every action that changes data checks a nonce (`check_admin_referer`, `check_ajax_referer`, `wp_verify_nonce`) **and** permission (`current_user_can`).
- REST routes always with a real `permission_callback`; `__return_true` only for public reads.
- PHP files start with `defined( 'ABSPATH' ) || exit;`. In production: `DISALLOW_FILE_EDIT`, plugins updated, no abandoned plugins.

### Tests

- The hook formats with `phpcbf` and runs `phpcs` (WordPress Coding Standards) on each edited PHP file; fix the security warnings, do not silence them.
- `composer test` runs PHPUnit. Before delivering: test in wp-env with the client's theme and plugins, and Lighthouse on the main pages.
