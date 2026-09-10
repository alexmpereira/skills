---
name: project-diary
description: Mantém um diário de aprendizado versionado no projeto (docs/DIARIO.md) para que armadilhas, decisões com trade-off, becos sem saída e correções do usuário não sejam redescobertos a cada tarefa - com gatilhos estritos de registro, validade declarada por entrada e promoção de regra recorrente para as instruções do repositório. A consulta ao diário é obrigatória antes de começar; o registro só ocorre quando um gatilho dispara. Use quando o pedido for registrar/consultar um aprendizado ou decisão, quando mencionar "diário", "lição aprendida", "não repetir esse erro", "ADR", "por que fizemos assim", "já tentamos isso?", ou ao iniciar/encerrar uma tarefa de desenvolvimento.
---

# Diário de Aprendizado do Projeto

O custo que este diário evita é sempre o mesmo: **redescobrir**. A armadilha que consumiu duas horas ontem consome duas horas de novo daqui a três meses, com outra pessoa — ou com você, sem lembrar.

E o motivo pelo qual quase todo diário de projeto morre também é sempre o mesmo: ele é escrito e nunca lido. Um diário só *write-only* é custo puro. Por isso a regra central aqui não é sobre escrever:

> **Consultar é obrigatório. Registrar é excepcional.**

---

## 1. Escopo

**Faz:** consulta o diário no início da tarefa, registra entrada quando um gatilho da §4 dispara, mantém as entradas vivas (remove obsoleto, consolida repetido, promove regra recorrente).

**Não faz:**
- Não narra a tarefa. Isso é changelog, e o git já faz.
- Não duplica o que o código, o `git log`, o PR ou o `CLAUDE.md` já dizem.
- Não vira lista de TODO nem backlog.
- Não registra credencial, token, dado pessoal, IP interno ou trecho de dado de cliente.
- Não commita sozinho.

---

## 2. Onde vive

`docs/DIARIO.md`, **versionado no git** — é conhecimento do time, não memória privada do agente.

Passou de ~300 linhas? Divida por ano em `docs/diario/AAAA.md` e mantenha `docs/DIARIO.md` como índice do ano corrente. Mais estrutura que isso não se paga.

Entradas em ordem **mais recente primeiro** — o topo é a parte lida.

---

## 3. Consulta (obrigatória, antes de começar)

Na fase de reconhecimento de qualquer tarefa, antes de escrever código:

```bash
ls docs/DIARIO.md docs/diario/ 2>/dev/null
grep -ri -E '<módulo>|<arquivo>|<ferramenta>|<erro>' docs/DIARIO.md docs/diario/ 2>/dev/null
```

Busque pelos termos do escopo: nome do módulo, do arquivo, da biblioteca, da ferramenta, da mensagem de erro.

Então **declare uma das duas coisas** no relatório da tarefa:
- `Diário: aplicada a entrada "<título>" (<data>) — <o que ela mudou na sua abordagem>.`
- `Diário: sem entrada para este escopo.`

Essa declaração é o que impede o diário de virar depósito. Sem ela, não há prova de que foi lido.

**Entrada do diário conflita com o que você ia fazer?** O diário vence, salvo se estiver vencido (§5) ou se o usuário decidir o contrário. Nesse caso, registre a mudança de rumo como entrada nova e apague a antiga.

---

## 4. Gatilhos de registro

Registre **somente** quando um destes disparar:

| Gatilho | Exemplo do que vira entrada |
|---|---|
| **Armadilha** — custou tempo e não é dedutível lendo o código | Migração falha silenciosamente se rodar antes do seed de tenants |
| **Decisão com trade-off** | Escolhemos fila em vez de chamada síncrona; custo: perda de erro imediato para o usuário |
| **Beco sem saída** | Tentamos X, não funciona por Y — não tentar de novo |
| **Correção do usuário sobre como trabalhar** | "Aqui a gente valida no form request, nunca no controller" |
| **Causa surpreendente de bug** | O timeout vinha do proxy, não da aplicação |
| **Ambiente / ferramenta** | O comando só funciona com a flag Z nesta versão; sem ela falha sem mensagem |
| **Contrato externo instável** | A API do parceiro devolve 200 com corpo de erro |

**Não registre:** o que o código já diz · o que o `git log` ou o PR registram · andamento de tarefa · preferência de estilo já coberta por lint · nada que você não confirmou.

**Régua de decisão:** *outra pessoa perderia tempo real por não saber disto?* Não → não registra.

Uma tarefa normal termina com **zero ou uma** entrada. Três entradas numa tarefa é sinal de que você está narrando, não aprendendo.

---

## 5. Formato da entrada

Máximo **12 linhas**. O campo que importa é a **regra prática** — o resto é a evidência que a sustenta.

```markdown
## 2026-09-10 · Migration quebra se rodar antes do seed de tenants

- **Gatilho:** armadilha
- **O que aconteceu:** `migrate:fresh --seed` falha com violação de FK em `orders.tenant_id`.
- **Causa:** a migration de `orders` assume tenant existente; o seeder de tenants roda depois na ordem padrão.
- **Regra prática:** rodar `db:seed --class=TenantSeeder` antes de qualquer migration que referencie tenant.
- **Evidência:** `database/migrations/2026_02_11_create_orders.php:22` · saída em `docs/diario/anexos/`
- **Vence quando:** a ordem dos seeders for corrigida (issue #412).
```

**`Vence quando:` é obrigatório.** Toda entrada declara a condição que a torna obsoleta — data, versão, refatoração ou issue. Entrada sem prazo de validade é entrada que ninguém vai ousar apagar.

---

## 6. Manutenção (o que mantém o diário pequeno)

1. **Venceu, some.** Ao passar por uma entrada cuja condição de validade já ocorreu, apague — e diga no relatório que apagou.
2. **Repetiu três vezes, promova.** Regra que reaparece em três entradas deixou de ser aprendizado e virou padrão do projeto: mova para `CLAUDE.md` / `AGENTS.md` / `CONTRIBUTING.md` e **apague as três**. O diário é área de estágio de conhecimento, não arquivo permanente.
3. **Consolide duplicatas.** Duas entradas sobre a mesma armadilha viram uma, com a data mais recente.
4. **Nunca reescreva a história.** Corrigir um aprendizado errado é entrada nova apontando para a antiga, seguida da remoção da antiga — não edição silenciosa.

---

## 7. Exemplo — a mesma situação, registrada de dois jeitos

### ❌ Sem valor

```markdown
## 2026-09-10 · Implementado desconto de pedidos
Criei a classe OrderTotal com a regra de 10% acima de R$ 500 e escrevi os testes.
Tudo passou. Depois ajustei o arredondamento.
```

Narra a tarefa. O `git log` já conta isso, com mais precisão e sem custo de manutenção. Nada aqui muda a decisão de ninguém amanhã.

### ✅ Com valor

```markdown
## 2026-09-10 · Dinheiro em `float` estoura o teste de fronteira

- **Gatilho:** armadilha
- **O que aconteceu:** desconto de 10% sobre R$ 500,10 dava R$ 450,089999 e reprovava no teste de fronteira.
- **Causa:** `Money` aceitava `float` no construtor; a conversão perdia precisão antes da regra.
- **Regra prática:** todo valor monetário trafega em centavos (`int`) da borda até o banco. `float` só na formatação de saída.
- **Evidência:** `src/Shared/Money.php:18` · teste `tests/Order/OrderTotalTest.php:41`
- **Vence quando:** o projeto adotar um tipo decimal nativo em todo o domínio.
```

Muda a decisão da próxima pessoa, custa seis linhas e sabe dizer quando morre.

---

## 8. Fronteira com as outras skills

| Skill | Relação com o diário |
|---|---|
| `senior-developer` | **Consulta** na fase de reconhecimento e **registra** ao encerrar, se um gatilho disparou |
| `tdd-strategist` | Registra teste instável recorrente e mutante equivalente aprovado pelo usuário |
| `project-scaffold` | Registra as decisões de stack e as versões resolvidas na criação do projeto |
| `gauntlet-loop` | Registra supressão aprovada pelo usuário — com o motivo e a validade |

O diário é do **projeto**, não do agente: escrito em português claro, útil para um humano que chegou hoje.

---

## 9. Checklist de autoverificação

- [ ] O diário foi consultado **antes** de começar, e a declaração (§3) está no relatório.
- [ ] Nenhuma entrada narra a tarefa ou repete o que o git registra.
- [ ] Todo registro corresponde a um gatilho da §4, nomeado na entrada.
- [ ] Toda entrada tem **regra prática** e **`Vence quando:`**.
- [ ] Toda afirmação tem evidência (`arquivo:linha`, comando ou saída real) — nada de memória.
- [ ] Nenhum segredo, credencial ou dado de cliente registrado.
- [ ] Entradas vencidas encontradas no caminho foram removidas.
- [ ] Regra vista pela terceira vez foi promovida para as instruções do repositório e removida daqui.
- [ ] Entrada com no máximo 12 linhas, no topo do arquivo.
- [ ] Nada commitado sem pedido.
