# Segurança — {{projeto}}

<!--
Documento vivo. Atualizado a cada mudança significativa pela skill `revisar-seguranca`
(o hook do Prumo pede a revisão automaticamente). Achados usam IDs SEG-001, SEG-002...
e citam a história ou o caso de uso afetado, para entrar na rastreabilidade.
Gravidade: Crítica, Alta, Média, Baixa. Status: aberto, em correção, corrigido, aceito (risco assumido).
-->

## 1. Superfície de ataque

| Ponto de entrada | Exposição | Autenticação | Dados tratados |
|---|---|---|---|
| [PREENCHER: API pública, formulário, webhook, painel admin...] | [PREENCHER: internet / rede interna] | [PREENCHER] | [PREENCHER] |

## 2. Ameaças e controles

<!-- Use STRIDE como roteiro: falsificação de identidade, adulteração, repúdio, vazamento de informação,
negação de serviço, elevação de privilégio. -->

| Ameaça | Onde | Controle adotado | Verificado em |
|---|---|---|---|
| [PREENCHER: acesso a dados de outro cliente (IDOR)] | [PREENCHER] | [PREENCHER: checagem de dono em toda consulta] | [PREENCHER: CT-xxx] |

## 3. Checklist base (OWASP Top 10)

- [ ] Controle de acesso verificado no servidor em toda rota/ação (A01)
- [ ] Senhas com hash forte; dados sensíveis criptografados em trânsito e em repouso (A02)
- [ ] Consultas parametrizadas / ORM; nenhuma concatenação de entrada em SQL, shell ou HTML (A03)
- [ ] Limites de taxa e regras de negócio contra abuso (A04)
- [ ] Configuração segura: sem modo debug em produção, CORS restrito, cabeçalhos de segurança (A05)
- [ ] Dependências auditadas e atualizadas (A06)
- [ ] Autenticação: sessão/JWT com expiração, proteção contra força bruta (A07)
- [ ] Integridade: segredos fora do código, pipeline de deploy protegido (A08)
- [ ] Logs de segurança sem dados sensíveis; alertas para falhas repetidas (A09)
- [ ] Requisições a URLs externas validadas (SSRF) (A10)

## 4. Achados

### SEG-001 — [PREENCHER: título do achado]

**Gravidade:** [PREENCHER] · **Status:** aberto · **Afeta:** [PREENCHER: HU-xxx / UC-xxx]

- **Descrição:** [PREENCHER]
- **Evidência:** [PREENCHER: arquivo:linha]
- **Correção:** [PREENCHER]

## 5. Histórico de revisões

| Data | Escopo revisado | Ferramentas | Achados |
|---|---|---|---|
| {{data}} | Criação do documento | — | — |
