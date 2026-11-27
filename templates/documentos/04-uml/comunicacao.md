# Diagramas de Comunicação — {{projeto}}

<!--
Mesma interação de um diagrama de sequência, mas com foco nos vínculos entre objetos.
Use quando importa "quem fala com quem" (acoplamento), não a linha do tempo. Mensagens numeradas (1, 1.1, 2...).
Título de cada seção: "## Comunicação — UC-001 Nome". Sintaxe: flowchart com rótulos nas arestas.
-->

## Comunicação — UC-001 [PREENCHER: nome]

```mermaid
flowchart LR
    u(["usuario : Usuario"])
    f["tela : Frontend"]
    a["api : API"]
    s["servico : ServicoPedido"]
    b[("banco : Banco")]
    u -- "1: enviar formulario" --> f
    f -- "2: POST /pedidos" --> a
    a -- "2.1: criar(dados)" --> s
    s -- "2.1.1: salvar(pedido)" --> b
    a -. "3: 201 Created" .-> f
```

[PREENCHER: notas sobre acoplamento ou objetos com muitos vínculos]
