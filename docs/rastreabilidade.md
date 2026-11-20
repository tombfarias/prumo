# Rastreabilidade

O Prumo liga cada requisito ao caso de uso que o atende, à história que o implementa, ao teste que o verifica e ao código que o contém. Tudo por IDs escritos nos próprios documentos.

## Prefixos

| Prefixo | Item | Onde é definido |
|---|---|---|
| `RF-001` | Requisito funcional | 02-requisitos.md |
| `RNF-001` | Requisito não funcional | 02-requisitos.md |
| `RN-001` | Regra de negócio | 02-requisitos.md |
| `UC-001` | Caso de uso | 03-casos-de-uso.md |
| `TL-001` | Tela | 05-interface.md |
| `EP-01` | Épico | 08-backlog.md |
| `HU-001` | História de usuário | 08-backlog.md |
| `CT-001` | Caso de teste | 09-plano-de-testes.md |
| `SEG-001` | Achado de segurança | 12-seguranca.md |
| `ADR-001` | Decisão arquitetural | docs/adr/ |
| `CM-001` | Mudança de escopo | docs/mudancas/ |

## Definição e referência

Um ID é **definido** em um de dois lugares:

1. no início de um título: `### UC-003 — Emitir nota fiscal`. O bloco vai até o próximo título de nível igual ou maior;
2. na primeira coluna de uma linha de tabela: `| RF-007 | O sistema deve... |`. O bloco é a própria linha.

Qualquer outro ID escrito **dentro** de um bloco é uma referência daquele item:

```markdown
### HU-004 — Emitir nota

**Épico:** EP-02 · **Casos de uso:** UC-003 · **Requisitos:** RF-007
```

Aqui HU-004 referencia EP-02, UC-003 e RF-007. Comentários HTML (`<!-- -->`) são ignorados; blocos de código contam como referência, mas nunca como definição.

No código, basta citar o ID num comentário: `// RN-002`, `# CT-005`. O Prumo varre as pastas de `pastas_codigo` (ignorando `node_modules`, `dist`, `.venv` etc.).

## A matriz

`prumo rastreabilidade` gera `docs/rastreabilidade.md` com:

- **Requisitos → casos de uso → histórias → testes → código.** Uma história conta para o requisito se citar o requisito ou um caso de uso que o atende; um teste conta se citar qualquer um deles.
- **Regras de negócio**: onde são aplicadas, testes e código.
- **Casos de uso**: telas e histórias.
- **Histórias**: status, estimativa, testes e código.
- **Problemas encontrados.**

| Problema | Gravidade |
|---|---|
| ID citado mas não definido | erro |
| ID definido duas vezes | erro |
| Requisito (exceto Won't) sem caso de uso nem história | aviso |
| Caso de uso sem história | aviso |
| História sem caso de teste | aviso |
| Tela sem caso de uso | aviso |

As verificações de cobertura só rodam quando o documento de destino existe no projeto: um projeto sem plano de testes não recebe "história sem teste".

## Contexto compacto

`prumo contexto HU-004` imprime somente os blocos ligados à história: ela mesma, os casos de uso, requisitos e regras desses casos de uso, telas, testes e épico, mais a lista de arquivos de código que citam esses IDs. É assim que as skills e o `prumo claude implementar` carregam a especificação sem ler documentos inteiros.

`--profundidade 2` segue as ligações um nível a mais.
