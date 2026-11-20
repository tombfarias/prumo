## Convenções do perfil: site institucional / landing page

### Estrutura sugerida (Astro)

```text
src/
  pages/                 # uma página por rota
  layouts/               # layout base com SEO
  components/            # seções (hero, serviços, depoimentos, contato)
  content/               # textos em Markdown/coleções de conteúdo
public/                  # imagens otimizadas, favicon, robots.txt
```

Início rápido: `npm create astro@latest`, depois `npx astro add tailwind` e `npx astro add sitemap`.

### Padrões

- Fidelidade ao Figma: implemente seção por seção com a skill `implementar-tela-figma`; textos e imagens finais vêm do cliente (registre pendências no briefing).
- **Desempenho:** imagens em WebP/AVIF com `width`/`height`, carregamento preguiçoso abaixo da dobra, meta de Lighthouse ≥ 90 em todas as categorias.
- **SEO:** `title` e `description` únicos por página, Open Graph, `sitemap.xml`, `robots.txt`, dados estruturados (Organization/LocalBusiness) quando fizer sentido.
- **Acessibilidade:** hierarquia de títulos correta, textos alternativos, contraste AA.
- **Formulário de contato:** validação no cliente e no servidor, proteção contra spam (honeypot ou captcha), aviso de privacidade.
- **LGPD:** banner de cookies só se houver rastreamento (analytics, pixels); política de privacidade linkada no rodapé.

### Testes

- `npm run build` sem erros, verificação de links quebrados e Lighthouse nas páginas principais.
- Comandos sugeridos: formatar `npx prettier --write {arquivo}`, testar `npm run build`.
