---
name: revisar-seguranca
description: Procura falhas de segurança nas mudanças recentes (controle de acesso, injeção, segredos, dependências, configuração, dados pessoais), seguindo o OWASP Top 10, e registra os achados SEG-xxx em docs/12-seguranca.md. Use quando o hook do Prumo pedir após uma mudança significativa, antes de uma entrega ou quando pedirem revisão de segurança.
---

# Revisar a segurança

Escopo padrão: os arquivos que o hook informou ou, sem essa lista, as mudanças não commitadas e o último commit (`git diff`, `git diff HEAD~1`). Antes de uma entrega, revise o projeto inteiro.

## 1. Varredura automática

1. Rode `{{prumo}} seguranca` (procura segredos no código, SQL/shell montados com entrada externa, `eval`, desativação de TLS, CORS aberto, modo debug, HTML sem escape e afins). Trate cada resultado: confirme ou descarte como falso positivo, com justificativa.
2. Audite as dependências com a ferramenta da stack, se disponível: `npm audit --omit=dev`, `pnpm audit`, `pip-audit`, `composer audit`, `dotnet list package --vulnerable`, `flutter pub outdated`.

## 2. Revisão manual dos arquivos alterados

Para cada arquivo, verifique o que se aplica:

- **Controle de acesso (A01):** toda rota/ação checa autenticação **e** autorização no servidor; IDs vindos do cliente são conferidos contra o dono do recurso (IDOR).
- **Injeção (A03):** consultas parametrizadas/ORM; nada de entrada do usuário concatenada em SQL, shell, caminhos de arquivo, HTML ou templates.
- **Autenticação (A07):** senhas com bcrypt/argon2; tokens com expiração; proteção contra força bruta; recuperação de senha sem vazar se o e-mail existe.
- **Dados (A02, LGPD):** dados pessoais e segredos não aparecem em logs, respostas de erro ou no frontend; HTTPS; o que é sensível está criptografado.
- **Configuração (A05):** debug desligado em produção, CORS restrito, cabeçalhos de segurança, mensagens de erro genéricas para o usuário.
- **Entrada e arquivos:** validação por schema; uploads com limite de tamanho, tipo verificado e nome gerado pelo servidor; nada de seguir URLs arbitrárias do usuário no servidor (SSRF, A10).
- **Segredos (A08):** nenhuma chave no código ou no histórico do git; tudo em variáveis de ambiente documentadas em `.env.example`.
- **Abuso (A04):** limites de taxa em login, cadastro, envio de e-mail/SMS e endpoints caros.

## 3. Registrar

Em `docs/12-seguranca.md`:

- Cada achado confirmado vira `### SEG-00N — Título` com gravidade (Crítica, Alta, Média, Baixa), status, o que ele **afeta** (HU/UC), evidência (`arquivo:linha`) e correção proposta.
- Atualize a superfície de ataque e a tabela de ameaças se surgiram pontos de entrada novos.
- Adicione uma linha ao histórico de revisões (data, escopo, ferramentas, quantidade de achados).

## 4. Corrigir ou escalar

- Achados **Críticos ou Altos**: informe o usuário imediatamente, com a correção sugerida. Corrija se a correção for local e não mudar comportamento especificado; caso contrário, peça autorização.
- Não marque como corrigido sem um teste ou uma evidência da correção.
- Rode `{{prumo}} validar` ao final e resuma: achados por gravidade, o que foi corrigido e o que depende do usuário.
