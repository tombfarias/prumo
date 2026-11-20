---
name: revisar-conformidade
description: Revisa se o código implementa exatamente o que a especificação pede (critérios de aceite, fluxos de exceção, regras de negócio, telas, modelo de dados) e aponta divergências, lacunas de teste e riscos de segurança. Use após implementar uma história, antes de uma entrega ou quando pedirem revisão de código contra a especificação.
---

# Revisar conformidade com a especificação

Argumento opcional: ID de história (`HU-003`) ou de caso de uso. Sem argumento, revise as mudanças não commitadas (`git diff`) e as do último commit.

## Procedimento

1. Monte a trilha com `{{prumo}} contexto HU-00N` (HU → UC → RF/RN → TL → CT), sem carregar documentos inteiros.
2. Para **cada critério de aceite** e **cada fluxo** do UC, localize no código onde ele é atendido e qual teste o cobre. Marque: atendido, parcial, ausente ou divergente.
3. Para **cada RN** citada: está implementada no lugar certo (camada de serviço/domínio) e testada?
4. **Dados:** migrações coerentes com `06-banco-de-dados.md`; dados pessoais protegidos como manda a seção LGPD.
5. **Telas:** estados vazio/carregando/erro/sucesso; acessibilidade básica; fidelidade ao Figma, se houver link.
6. **Segurança:** autorização no servidor, validação de entrada, segredos fora do código, nada sensível em logs.
7. **Escopo:** código que implementa algo que não está especificado é divergência também (pode ser mudança de escopo não registrada).
8. Rode testes, lint e `{{prumo}} validar`.

## Relatório

Tabela `Item | Situação | Evidência (arquivo:linha / teste) | Ação sugerida`, seguida das divergências que exigem decisão do usuário. Não corrija nada sem o usuário pedir; esta skill só revisa.
