# Diagrama de Objetos — {{projeto}}

<!--
Um retrato do modelo de classes num instante: instâncias concretas com valores, para validar
multiplicidades e regras de negócio (RN) com exemplos reais antes de codificar. Use os nomes de classes.md.
Notação: "nome : Classe"; atributos com valores. Sintaxe: classDiagram com rótulos (https://mermaid.js.org/syntax/classDiagram.html)
-->

## Cenário — [PREENCHER: situação de exemplo, ex.: pedido pago com dois itens] (UC-001)

```mermaid
classDiagram
    direction LR
    class c1["c1 : Cliente"] {
        nome = "Maria Souza"
        ativo = true
    }
    class p1["p1 : Pedido"] {
        numero = 1001
        status = Pago
        total = 150.00
    }
    class i1["i1 : ItemPedido"] {
        quantidade = 2
        preco = 50.00
    }
    class i2["i2 : ItemPedido"] {
        quantidade = 1
        preco = 50.00
    }
    c1 --> p1 : fez
    p1 *-- i1
    p1 *-- i2
```

| Objeto | Regra verificada |
|---|---|
| [PREENCHER: p1] | [PREENCHER: RN-xxx — total = soma dos itens] |
