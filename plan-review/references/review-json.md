# O arquivo `.review.json`

Fica ao lado do plano, com o mesmo nome: `docs/plans/desconto.md` → `docs/plans/desconto.review.json` (outro caminho com `--data`). Guarda o que a página precisa e o plano não tem: título da página, link do artifact, anotações de código e estado de revisão. Todo campo é opcional; sem o arquivo, a página mostra só o texto do plano.

Texto com crase (`` `x` ``), `**negrito**`, `*itálico*`, `~~tachado~~` e `[link](https://...)` é desenhado nos campos marcados com _(md)_. Escreva no idioma de quem vai revisar.

## Conteúdo

- Unidades e chaves
- Campos de topo
- `notes`: anotações de código
- `review`: estado de revisão
- Campos escritos pelos scripts
- Exemplo mínimo

## Unidades e chaves

Cada `##` e cada `###` do plano é uma **unidade revisável**, com chave igual ao slug do título: `## Contexto` → `contexto`; `### 1. Constantes e regra` dentro de `## Abordagem` → `abordagem--1-constantes-e-regra`. Título repetido ganha sufixo (`riscos`, `riscos-2`). Texto entre o `# Título` e o primeiro `##` vira a unidade `introducao`. Um `##` que só tem `###` dentro, sem texto próprio, é um grupo e não uma unidade.

Para ver as chaves de um plano: `extract_plan.py <plano.md>` lista `id` de cada seção e subseção. Renomear um título muda a chave: o build acusa a chave antiga em `review` e `notes` até alguém decidir o que fazer com ela.

## Campos de topo

| Campo | Tipo | O que é |
|---|---|---|
| `title` | string | nome da aba e do artifact, de 2 a 4 palavras, estável entre publicações |
| `artifact_url` | string | link do artifact; vazio na primeira vez |
| `code_ref` | string | repositório, branch e commit lidos para as anotações (ex.: `loja main @ abc1234`) |
| `tags` | `[{text, warn?}]` | etiquetas no topo; `warn: true` pinta de âmbar (use em "plano em revisão") |
| `notes` | `{chave: anotação}` | leitura do código por unidade (abaixo) |
| `review` | `{chave: estado}` | estado de revisão por unidade (abaixo) |

## `notes`: anotações de código

Uma anotação diz ao revisor **onde** aquela parte do plano toca o código e **o que** você viu lá. Aparece numa caixa tracejada com o aviso "Leitura de quem gerou a página: não faz parte do plano".

| Campo | Obrigatório | O que é |
|---|---|---|
| `onde` | não | referências de código separadas por ` · `: `arquivo[:linhas]` ou `pasta/`, relativas à raiz do projeto (`--root`) |
| `leitura` | `leitura` ou `risco` | _(md)_ o que o código faz hoje nesse ponto, em uma ou duas frases (até 400 caracteres) |
| `risco` | `leitura` ou `risco` | _(md)_ o que pode quebrar se esta parte for feita como o plano diz |

**Formato de `onde`:** só referência, sem prosa. `src/Order/OrderTotal.php:4-7 · src/Order/OrderFreight.php:34 · tests/Order/`. Linhas aceitam `N`, `N-M` e listas `N,M-K`. O build confere no disco: o arquivo existe, a pasta existe, a linha não passa do fim do arquivo. Caminho absoluto, com `..` ou com espaço é recusado. A explicação vai em `leitura`.

**O que não vai numa anotação:** decisão nova, requisito, opinião sobre o plano ou sugestão de mudança. Se a leitura do código mostra que o plano está errado, diga isso ao usuário; a correção vai para o plano, não para a anotação.

## `review`: estado de revisão

| Campo | O que é |
|---|---|
| `state` | `validated` ou `changes` (ajuste pedido); unidade fora do mapa = não revisada |
| `note` | o pedido de ajuste, nas palavras do revisor (só com `changes`) |
| `fp` | impressão digital do texto que o revisor viu; **não escreva à mão** |
| `by`, `at` | id opaco de quem marcou e quando (vêm da página) |

O estado vem de dois lugares: do registro do artifact (o que o revisor marca na página, que sempre ganha) e deste arquivo (quando a página está fora do claude.ai, ou a unidade ainda não foi marcada nela). `sync_review.py` traz o registro para cá.

Quando o usuário valida algo **no chat** ("pode marcar Contexto como validado"), escreva `{"state": "validated"}` sem `fp`: o próximo `--mark-published` grava a impressão digital do texto atual. Com `fp`, se o texto mudar depois, a página mostra "validada · mudou desde então" e o build imprime `RECHECK`.

## Campos escritos pelos scripts

Não edite à mão.

| Campo | Quem escreve | O que é |
|---|---|---|
| `published_plan_hash` | `build_page.py --mark-published` | hash do plano que foi ao ar; o build avisa `STALE` quando o plano atual é outro |
| `published_at` | idem | quando foi publicado |
| `published_fingerprints` | idem | impressão digital de cada unidade na publicação; anotação de unidade que mudou depois ganha "reler: o plano mudou aqui" |
| `review.*.fp`, `by`, `at` | `sync_review.py` e `--mark-published` | ver acima |

## Exemplo mínimo

```json
{
  "title": "Revisão desconto pedido",
  "artifact_url": "",
  "code_ref": "loja main @ abc1234",
  "tags": [{ "text": "plano em revisão", "warn": true }],
  "notes": {
    "abordagem--1-constantes-e-regra": {
      "onde": "src/Order/OrderTotal.php:4-7 · src/Order/OrderFreight.php:34",
      "leitura": "`calculate` hoje só devolve o subtotal; as constantes entram na própria classe, como em `OrderFreight`.",
      "risco": "Nenhum chamador depende do valor sem desconto."
    }
  },
  "review": {
    "contexto": { "state": "validated" }
  }
}
```
