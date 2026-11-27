## Profile conventions: mobile app

### Suggested structure (Expo)

```text
app/                     # Expo Router routes (screens)
  (auth)/ (tabs)/
components/              # reusable components
services/                # API calls, local storage
hooks/ theme/            # hooks and design tokens (colors, typography, spacing)
tests/
```

Quick start: `npx create-expo-app@latest` (alternative: `flutter create`).

### Patterns

- Screens follow Figma (skill `implementar-tela-figma`); design system tokens centralized in `theme/`.
- Empty, loading, error and offline states on every screen that depends on the network.
- Safe areas (notch), touch targets ≥ 44 pt, support for larger fonts.
- Access tokens in the system's secure storage (`expo-secure-store`), never in AsyncStorage.
- Permissions (camera, location, notifications) requested at the moment of use, with an explanation.
- Publishing: record in 11-entrega.md the store accounts (in the client's name), icons, screenshots and privacy policy.

### Tests

- Component tests with Jest + Testing Library; e2e of the main journeys with Maestro.
- Suggested commands: format `npx prettier --write {arquivo}`, lint `npx eslint {arquivo}`, test `npm test`.
