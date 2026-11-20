## Convenções do perfil: aplicação web full-stack

### Estrutura sugerida (Next.js App Router)

```text
src/
  app/                   # rotas; cada pasta = segmento de URL
    (publico)/ (painel)/ # grupos de rotas por área
    api/                 # route handlers, só quando precisar de API pública
  componentes/ui/        # componentes de interface reutilizáveis
  componentes/<dominio>/ # componentes de negócio
  servidor/              # serviços, acesso a dados, server actions
  lib/                   # utilitários, validação (zod), cliente do Prisma
prisma/schema.prisma
tests/                   # unitários (vitest) e e2e (Playwright)
```

Início rápido: `npx create-next-app@latest` (TypeScript, ESLint, Tailwind, App Router, pasta `src/`), `npx prisma init`, `npm init playwright@latest`.

### Padrões

- Server Components por padrão; `"use client"` só onde há interação ou estado no navegador.
- Mutações via server actions ou route handlers, sempre com validação zod e checagem de permissão no servidor.
- Componentes de tela seguem o design do Figma (skill `implementar-tela-figma`); use os tokens do design system, nunca cores ou espaçamentos soltos.
- Cada tela implementa os estados vazio, carregando, erro e sucesso.
- Acessibilidade: elementos semânticos, `label` em todo campo, foco visível, contraste AA.
- Cite a tela e o caso de uso no componente de página (`// TL-002 · UC-004`).

### Segurança

- Autenticação com Auth.js; autorização verificada no servidor em cada ação, não só escondendo botões.
- Nunca exponha segredos em variáveis `NEXT_PUBLIC_*`.

### Testes

- Vitest para lógica; Playwright para as jornadas dos casos de uso Must.
- Comandos sugeridos: formatar `npx prettier --write {arquivo}`, lint `npx eslint {arquivo}`, testar `npm test`.
