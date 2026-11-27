## Profile conventions: business website / landing page

### Suggested structure (Astro)

```text
src/
  pages/                 # one page per route
  layouts/               # base layout with SEO
  components/            # sections (hero, services, testimonials, contact)
  content/               # texts in Markdown/content collections
public/                  # optimized images, favicon, robots.txt
```

Quick start: `npm create astro@latest`, then `npx astro add tailwind` and `npx astro add sitemap`.

### Patterns

- Fidelity to Figma: implement section by section with the `implementar-tela-figma` skill; final texts and images come from the client (record pending items in the briefing).
- **Performance:** images in WebP/AVIF with `width`/`height`, lazy loading below the fold, Lighthouse target ≥ 90 in all categories.
- **SEO:** unique `title` and `description` per page, Open Graph, `sitemap.xml`, `robots.txt`, structured data (Organization/LocalBusiness) when it makes sense.
- **Accessibility:** correct heading hierarchy, alt texts, AA contrast.
- **Contact form:** validation on the client and the server, spam protection (honeypot or captcha), privacy notice.
- **Privacy (LGPD/GDPR):** cookie banner only if there is tracking (analytics, pixels); privacy policy linked in the footer.

### Tests

- `npm run build` with no errors, broken link check and Lighthouse on the main pages.
- Suggested commands: format `npx prettier --write {arquivo}`, test `npm run build`.
