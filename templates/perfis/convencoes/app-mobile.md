## Convenções do perfil: aplicativo mobile

### Estrutura sugerida (Expo)

```text
app/                     # rotas do Expo Router (telas)
  (auth)/ (abas)/
componentes/             # componentes reutilizáveis
servicos/                # chamadas à API, armazenamento local
hooks/ tema/             # hooks e tokens de design (cores, tipografia, espaçamento)
tests/
```

Início rápido: `npx create-expo-app@latest` (alternativa: `flutter create`).

### Padrões

- Telas seguem o Figma (skill `implementar-tela-figma`); tokens do design system centralizados em `tema/`.
- Estados vazio, carregando, erro e sem conexão em todas as telas que dependem de rede.
- Áreas seguras (notch), tamanhos de toque ≥ 44 pt, suporte a fonte ampliada.
- Tokens de acesso no armazenamento seguro do sistema (`expo-secure-store`), nunca em AsyncStorage.
- Permissões (câmera, localização, notificações) pedidas no momento do uso, com explicação.
- Publicação: registre em 11-entrega.md as contas das lojas (em nome do cliente), ícones, capturas e política de privacidade.

### Testes

- Testes de componentes com Jest + Testing Library; e2e das jornadas principais com Maestro.
- Comandos sugeridos: formatar `npx prettier --write {arquivo}`, lint `npx eslint {arquivo}`, testar `npm test`.
