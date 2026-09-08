---
name: gauntlet-loop
description: Ciclo de verificação adversarial para agentes em projetos PHP e TypeScript - encadeia typecheck, testes, análise estática, complexidade, cobertura do diff e teste de mutação (Infection no PHP, Stryker no TypeScript) num loop de feedback com orçamento de iterações, detecção de estagnação e guardrails anti-fraude. Detecta e instala o ferramental padronizado, executa e gera relatório visual. Use quando o pedido for validar/garantir uma implementação, rodar o gauntlet, configurar teste de mutação, verificar se os testes realmente testam algo, ou mencionar Infection, Stryker, MSI, mutation testing, cobertura de diff, "loop de verificação" ou "garantir que a tarefa está pronta".
---

# Gauntlet Loop

Um agente que escreve o código **e** os testes tem um conflito de interesse: o caminho mais curto para "verde" é um teste que não asseria nada. Suíte passando, nesse cenário, não é evidência de nada.

O Gauntlet Loop resolve isso com verificação adversarial em cadeia. Cada estágio é um portão que tenta reprovar o trabalho; o loop só termina quando todos passam sem que nenhum tenha sido enfraquecido.

O centro do gauntlet é o **teste de mutação**: a ferramenta altera seu código de propósito (troca `>` por `>=`, inverte condição, remove linha) e verifica se algum teste quebra. Teste que não quebra com o código sabotado não testa nada. Essa é a única métrica que mede a **qualidade da asserção**, não a execução — e é por isso que ela é o portão final.

---

## 1. Escopo

**Faz:** detecta e instala o ferramental padronizado, configura, executa o loop em cadeia, gera relatório visual, devolve feedback estruturado ao agente e para com relatório honesto quando não converge.

**Não faz:**
- Não escreve a feature. Ele verifica o que foi escrito.
- Não refatora — complexidade alta vai para `low-complexity-expert` (§13).
- Não altera thresholds, ignores ou testes para passar (§3). Essa é a proibição central.
- Não commita, não mexe em CI sem pedido explícito.
- Não roda o estágio de mutação a cada edição — ele custa minutos (§4).

---

## 2. Onde os artefatos vivem

Tudo em `build/gauntlet/` (adicione ao `.gitignore`). Configs de ferramenta na raiz **só** quando a ferramenta exige (`infection.json5`, `stryker.config.mjs`) — nesses casos, se o arquivo já existe, leia e estenda, nunca sobrescreva.

---

## 3. Guardrails anti-fraude (INEGOCIÁVEL)

Um portão só vale se não puder ser movido por quem está sendo avaliado. Estas são as formas conhecidas de burlar o gauntlet, e todas são proibidas:

**Proibido, sem exceção:**
1. **Baixar threshold** para passar — `minMsi`, `thresholds.break`, nível do PHPStan, meta de cobertura.
2. **Suprimir diagnóstico** — `@ts-ignore`, `@ts-expect-error`, `@phpstan-ignore-line`, `@codeCoverageIgnore`, `@infection-ignore-all`, `eslint-disable`, entradas em `ignoreErrors` ou em baseline.
3. **Apagar, pular ou renomear teste que falha** — `.skip`, `.todo`, `markTestSkipped`, `$this->markTestIncomplete`, comentar o teste, tirar do glob.
4. **Enfraquecer asserção** — trocar valor esperado por `expect.anything()`, `assertTrue(true)`, remover asserção, afrouxar comparação estrita.
5. **Mockar o que está sob teste** para o teste passar.
6. **Excluir do escopo de mutação** o arquivo que você acabou de escrever.
7. **Declarar pronto com portão vermelho.**

**Quando o portão está genuinamente errado** — teste instável (*flaky*), falso positivo de análise estática, mutante equivalente que nenhum teste pode matar — **pare e reporte**, com o mutante ou o erro exato como evidência, e proponha a supressão para o usuário aprovar. Supressão é decisão dele, nunca sua. Registre no relatório como `supressão pendente de aprovação`.

Se você chegou perto de uma dessas sete e recuou, diga isso no relatório. É informação útil, não confissão.

---

## 4. Arquitetura do loop

Dois anéis, porque o custo dos estágios difere em duas ordens de grandeza. Rodar mutação a cada edição desperdiça minutos; rodá-la nunca desperdiça a garantia.

### Anel interno — rápido, a cada edição

`Estágio 0 → 1 → 2 → 3`. Segundos a poucas dezenas de segundos. É o loop de trabalho.

### Anel externo — completo, antes de declarar pronto

`Anel interno verde → Estágio 4 → 5 → 6`. Minutos. Só roda quando o interno está inteiramente verde — mutação sobre teste que falha é dinheiro no lixo.

### Orçamento e parada

| Regra | Valor | Por quê |
|---|---|---|
| Iterações do anel interno | máx. **5** | Além disso não é ajuste, é tentativa e erro |
| Iterações do anel externo | máx. **3** | Cada uma custa minutos |
| **Estagnação** | 2 falhas com a **mesma assinatura** | Você está chutando; pare |
| **Regressão** | um portão antes verde ficou vermelho | Pare imediatamente e reporte a causa |

Estourou o orçamento? **Pare e reporte** — o que passou, o que falhou, o que você tentou, e a sua melhor hipótese. Nunca fique em loop, nunca declare vitória parcial como vitória, nunca burle um portão para fechar a conta.

---

## 5. Os estágios

Ordenados por custo crescente: o barato que reprova cedo economiza o caro.

| # | Estágio | Portão | Custo | PHP | TypeScript |
|---|---|---|---|---|---|
| 0 | **Sanidade** | Compila / tipa sem erro | ~1–5 s | `php -l`, PHPStan | `tsc --noEmit` |
| 1 | **Testes** | 100% passando, **zero skip novo** | s | PHPUnit / Pest | Vitest |
| 2 | **Estática** | Zero erro novo no nível acordado | s | PHPStan | ESLint + typescript-eslint |
| 3 | **Complexidade** | Limites da `complexity-audit` | s | phpmd | ESLint + SonarJS |
| 4 | **Cobertura do diff** | ≥ 80% linhas, ≥ 70% branches **no código alterado** | s–min | PHPUnit + PCOV | Vitest + coverage-v8 |
| 5 | **Mutação** | MSI do diff ≥ 80, MSI coberto ≥ 90 | **min** | **Infection** | **Stryker** |
| 6 | Duplicação (opcional) | < 3% | s | jscpd | jscpd |

**Cobertura e mutação medem o diff, não o projeto.** Em base legada, meta global é inalcançável e vira desculpa para desligar o portão. O que você acabou de escrever, porém, não tem desculpa: nasce coberto e testado de verdade.

### Por que MSI é o portão final

**MSI** (*Mutation Score Indicator*) = mutantes mortos ÷ mutantes gerados. Dois números importam:

- **MSI** — sobre todos os mutantes. Penaliza código não coberto.
- **MSI coberto** (`covered MSI`) — só sobre mutantes em linhas cobertas. Isola a pergunta "os testes que existem realmente asserem?".

MSI coberto baixo com cobertura alta é a assinatura exata do teste que executa sem verificar. É o defeito que este gauntlet existe para pegar.

---

## 6. Ferramental padrão (fixo, para todos os projetos)

Versões verificadas em **2026-09-08**. Fixe as *minor* com `^` para o padrão ser reproduzível; confirme a resolvida e registre no relatório.

> ⚠️ Vários destes são majors recentes (PHPUnit 13, Pest 5, TypeScript 7, Vitest 5, Stryker 10). Em projeto existente, **a versão do projeto manda** — nunca faça upgrade de major do runner de teste só para instalar o gauntlet. Adapte o gauntlet, não o projeto.

### PHP

| Papel | Pacote | Versão | Obrigatório |
|---|---|---|---|
| Testes | `phpunit/phpunit` | 13.3.2 | Sim (ou Pest) |
| Testes (alt.) | `pestphp/pest` | 5.1.4 | — |
| **Mutação** | `infection/infection` | **0.35.4** | **Sim** |
| Estática | `phpstan/phpstan` | 2.2.13 | Sim |
| Cognitiva | `tomasvotruba/cognitive-complexity` | 1.2.0 | Recomendado |
| Complexidade | `phpmd/phpmd` | 2.15.0 | Recomendado |
| Estilo | `laravel/pint` 1.31.1 · `friendsofphp/php-cs-fixer` 3.95.25 | — | Opcional |

**Driver de cobertura é pré-requisito do Infection.** Sem Xdebug ou PCOV ele não roda. PCOV é bem mais rápido para cobertura; Xdebug serve se você também depura. Verifique antes de instalar o resto:

```bash
php -m | grep -iE 'xdebug|pcov' || echo "FALTA driver de cobertura"
```

### TypeScript

| Papel | Pacote | Versão | Obrigatório |
|---|---|---|---|
| Testes | `vitest` | 5.0.0 | Sim (ou Jest) |
| Cobertura | `@vitest/coverage-v8` | 5.0.0 | Sim |
| **Mutação** | `@stryker-mutator/core` | **10.0.0** | **Sim** |
| Runner de mutação | `@stryker-mutator/vitest-runner` | 10.0.0 | Sim |
| Checker de tipos | `@stryker-mutator/typescript-checker` | 10.0.0 | Recomendado |
| Tipagem | `typescript` | 7.0.2 | Sim |
| Estática/complexidade | `eslint` 10.10.0 · `typescript-eslint` 8.70.0 · `eslint-plugin-sonarjs` 4.2.0 | — | Sim |

O `typescript-checker` do Stryker descarta mutantes que não compilam antes de rodar a suíte — corta minutos de execução inútil. Vale sempre.

Se o projeto usa **Jest**, troque o runner por `@stryker-mutator/jest-runner`. Não migre o projeto para Vitest por causa do gauntlet.

---

## 7. Fase 1 · Inventário

Nunca instale o que já existe.

```bash
# PHP
grep -E 'phpunit|pest|infection|phpstan|phpmd' composer.json
ls -1 phpunit.xml* infection.json5 infection.json phpstan.neon* 2>/dev/null
ls -1 vendor/bin/ 2>/dev/null | grep -E 'phpunit|pest|infection|phpstan'
php -m | grep -iE 'xdebug|pcov'

# TypeScript
grep -E '"vitest"|"jest"|stryker|"typescript"|"eslint"' package.json
ls -1 stryker.config.* vitest.config.* jest.config.* tsconfig.json 2>/dev/null
ls -1 pnpm-lock.yaml yarn.lock package-lock.json bun.lock* 2>/dev/null
```

Descubra também: **diretório de código** (`autoload.psr-4` no PHP; `include` do tsconfig no TS — nunca assuma `src/`), **runner de teste em uso**, e a **branch de integração** (`main`/`master`/`develop`), que define a base do diff.

Saída: tabela do que existe, do que falta e do que é bloqueante.

---

## 8. Fase 2 · Plano e instalação

Confirme antes de instalar — altera lockfile e exige rede. Uma confirmação cobre tudo.

```bash
# PHP — só o ausente
composer require --dev infection/infection phpstan/phpstan phpmd/phpmd
composer require --dev tomasvotruba/cognitive-complexity

# Driver de cobertura, se faltar (fora do Composer)
pecl install pcov          # e habilite extension=pcov.so no php.ini
# ou XDEBUG_MODE=coverage com Xdebug já instalado

# TypeScript — use o gerenciador detectado no inventário
pnpm add -D @stryker-mutator/core @stryker-mutator/vitest-runner \
            @stryker-mutator/typescript-checker
pnpm add -D vitest @vitest/coverage-v8
pnpm add -D eslint typescript-eslint eslint-plugin-sonarjs
```

Regras: `--dev`/`-D` sempre, global nunca; respeite o gerenciador do lockfile; não faça upgrade de major do runner existente.

---

## 9. Fase 3 · Configuração

### `infection.json5` (raiz — exigido pela ferramenta)

```json5
{
  $schema: "vendor/infection/infection/resources/schema.json",
  source: {
    directories: ["app"],
    excludes: ["Console", "Providers", "Http/Middleware"]
  },
  timeout: 10,
  logs: {
    html: "build/gauntlet/infection.html",
    json: "build/gauntlet/infection.json",
    summary: "build/gauntlet/infection-summary.txt"
  },
  mutators: { "@default": true },
  minMsi: 80,
  minCoveredMsi: 90
}
```

`excludes` cobre apenas *bootstrap* e configuração — **nunca** o arquivo que você acabou de escrever (§3.6).

### `stryker.config.mjs` (raiz — exigido pela ferramenta)

```js
export default {
  packageManager: 'pnpm',
  testRunner: 'vitest',
  plugins: [
    '@stryker-mutator/vitest-runner',
    '@stryker-mutator/typescript-checker',
  ],
  checkers: ['typescript'],
  tsconfigFile: 'tsconfig.json',
  mutate: [
    'src/**/*.ts',
    '!src/**/*.{spec,test}.ts',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
  ],
  reporters: ['html', 'json', 'clear-text', 'progress'],
  htmlReporter: { fileName: 'build/gauntlet/stryker.html' },
  jsonReporter: { fileName: 'build/gauntlet/stryker.json' },
  thresholds: { high: 90, low: 80, break: 80 },
  concurrency: 4,
  incremental: true,
  incrementalFile: 'build/gauntlet/.stryker-incremental.json',
};
```

`incremental: true` reaproveita o resultado anterior e é o que torna a mutação viável dentro de um loop.

### Verifique as flags antes de montar os comandos

Nomes de flag mudam entre majors. Um comando resolve:

```bash
vendor/bin/infection --help | grep -E 'git-diff|min-msi|logger-html|threads'
npx stryker run --help | grep -E 'since|incremental|concurrency'
```

Flag ausente na sua versão? Ajuste — não invente parâmetro.

---

## 10. Fase 4 · Execução

Nenhum código de saída diferente de zero é falha da skill: é o portão reprovando.

| Ferramenta | 0 | ≠ 0 |
|---|---|---|
| tsc, PHPStan, ESLint, PHPUnit, Vitest | limpo | violações (ESLint 2 = config quebrada) |
| Infection | MSI atingido | MSI abaixo do mínimo, ou erro |
| Stryker | acima de `break` | abaixo de `break` |

```bash
BASE=origin/main   # branch de integração detectada no inventário
mkdir -p build/gauntlet

# ================= ANEL INTERNO =================
# 0 · Sanidade
npx tsc --noEmit
vendor/bin/phpstan analyse --no-progress

# 1 · Testes
vendor/bin/phpunit --testdox
npx vitest run --reporter=dot

# 2 · Estática + 3 · Complexidade
npx eslint . --format json -o build/gauntlet/eslint.json
vendor/bin/phpmd app json codesize,design --reportfile build/gauntlet/phpmd.json || true

# ================= ANEL EXTERNO =================
# 4 · Cobertura
vendor/bin/phpunit --coverage-clover build/gauntlet/clover.xml \
                   --coverage-html build/gauntlet/coverage-php
npx vitest run --coverage \
    --coverage.reporter=html --coverage.reporter=lcov --coverage.reporter=json-summary \
    --coverage.reportsDirectory=build/gauntlet/coverage-ts

# 5 · Mutação — escopo do diff, o que a torna viável
vendor/bin/infection \
  --git-diff-lines --git-diff-base="$BASE" \
  --min-msi=80 --min-covered-msi=90 \
  --threads=4 --no-interaction --no-progress

npx stryker run --since="$BASE"
```

**Cobertura do diff:** nem PHPUnit nem Vitest calculam isso nativamente. Duas saídas honestas — cruze o relatório (`clover.xml` / `lcov.info`) com `git diff --unified=0 "$BASE"...HEAD`, ou use `diff-cover` se aceitar uma dependência Python. Não conseguiu medir? Reporte **cobertura por arquivo alterado** e registre a limitação — não apresente cobertura global como se fosse do diff.

Sem git ou sem base (primeiro commit)? Rode escopo completo e diga que o custo é maior.

---

## 11. Relatório visual

Cada ferramenta já gera HTML navegável — o Stryker e o Infection mostram mutante por mutante, com o código sabotado ao lado e o veredicto (morto / sobreviveu). **É onde você entende por que um teste é fraco.**

Gere um índice em `build/gauntlet/index.html` ligando: `infection.html`, `stryker.html`, `coverage-php/index.html`, `coverage-ts/index.html` e o `GAUNTLET.md`.

`build/gauntlet/GAUNTLET.md`:

```markdown
# Gauntlet — <tarefa> · iteração 3/5 · <data>

## Veredicto: 🔴 VERMELHO — barrado no estágio 5

| # | Estágio | Portão | Resultado | Status |
|---|---|---|---|---|
| 0 | Sanidade | 0 erros | 0 | ✅ |
| 1 | Testes | 100% | 48/48 | ✅ |
| 2 | Estática | 0 novos | 0 | ✅ |
| 3 | Complexidade | cicl ≤5 · cogn ≤7 | máx 4 / 6 | ✅ |
| 4 | Cobertura diff | ≥80% / ≥70% | 94% / 81% | ✅ |
| 5 | **Mutação** | MSI ≥80 · coberto ≥90 | **71 / 74** | ❌ |

## Mutantes sobreviventes (o que os testes não pegam)
| Local | Mutação | Por que sobreviveu |
|---|---|---|
| `app/Pricing.php:42` | `>` → `>=` | Nenhum teste no valor de fronteira |
| `src/cart.ts:88` | remoção da linha | Retorno usado só no caminho não testado |

## Leitura
Cobertura 94% com MSI coberto 74 é a assinatura clássica: os testes
executam o código e não verificam o resultado. O gargalo são valores de
fronteira.

## Próximo passo
Um teste por mutante sobrevivente, no valor exato da fronteira. Não afrouxar
minMsi.

**Relatórios:** build/gauntlet/index.html
```

Regras: `arquivo:linha` sempre; **número nunca inventado** — métrica não produzida entra como `—` com a razão; mutantes sobreviventes ordenados por proximidade ao código da tarefa.

---

## 12. Protocolo de retorno ao agente

O gauntlet só ajuda a desenvolver se o feedback for acionável. Grave `build/gauntlet/result.json` como contrato legível por máquina:

```json
{
  "iteration": 3,
  "ring": "external",
  "verdict": "red",
  "blocked_at": "mutation",
  "stagnation": false,
  "stages": [
    { "id": "mutation", "status": "fail",
      "gate": "msi>=80 covered>=90", "actual": "71/74",
      "evidence": "build/gauntlet/infection.json",
      "action": "adicionar teste de fronteira em app/Pricing.php:42" }
  ]
}
```

### O que fazer em cada falha

| Estágio falhou | Ação correta | Fraude que você **não** vai cometer |
|---|---|---|
| 0 · Sanidade | Corrigir o tipo de verdade | `any`, `@ts-ignore`, cast forçado |
| 1 · Testes | Corrigir o código; se o teste é que está errado, **dizer isso** com evidência | `.skip`, apagar, afrouxar asserção |
| 2 · Estática | Corrigir a causa | baseline, `@phpstan-ignore` |
| 3 · Complexidade | Delegar à `low-complexity-expert` | subir o limite |
| 4 · Cobertura | Testar o ramo descoberto | `@codeCoverageIgnore` |
| 5 · **Mutação** | **Um teste por mutante sobrevivente, no valor de fronteira** | baixar `minMsi`, excluir arquivo do `mutate` |

### Regras do loop

1. **Um estágio por vez**, sempre o de menor número em vermelho.
2. **Reporte a assinatura da falha** a cada iteração — é o que detecta estagnação.
3. **Após corrigir, rode o anel interno inteiro**, não só o estágio que falhou: correção causa regressão.
4. **Não avance para o anel externo** com o interno vermelho.
5. **Ao parar** (verde, orçamento estourado ou estagnação), entregue o `GAUNTLET.md` e o veredicto em uma frase. Vermelho é resultado legítimo — omitir o motivo não é.

### Quando declarar a tarefa pronta

Somente com **todos os estágios verdes**, no anel externo, **sem nenhuma supressão nova**. Faltou um desses? A tarefa está *bloqueada*, não pronta — e o relatório diz exatamente onde.

---

## 13. Fronteira com as outras skills

| Skill | Papel |
|---|---|
| `gauntlet-loop` | **Verifica** se a implementação e os testes se sustentam sob ataque |
| `complexity-audit` | **Mede** complexidade do projeto e monta baseline |
| `low-complexity-expert` | **Corrige** complexidade refatorando |

O estágio 3 usa os mesmos limites da `complexity-audit` (ciclomática ≤ 5, cognitiva ≤ 7, aninhamento ≤ 2) e delega a correção à `low-complexity-expert`. Nenhuma das três reimplementa a outra.

---

## 14. Problemas comuns

| Sintoma | Causa | O que fazer |
|---|---|---|
| Infection: "no code coverage driver" | Xdebug/PCOV ausente | Instale PCOV, ou `XDEBUG_MODE=coverage` |
| Infection lentíssimo | Escopo total | `--git-diff-lines` + `--threads` |
| Stryker: "cannot find test runner" | Plugin não declarado | Adicione em `plugins` |
| Stryker mata o CI de memória | `concurrency` alto | Reduza para 2 |
| MSI alto e cobertura baixa | Poucas linhas cobertas, bem testadas | Olhe MSI **e** cobertura juntos |
| Cobertura alta e MSI coberto baixo | **Testes sem asserção real** | É exatamente o defeito-alvo: teste fronteiras |
| Mutante que nenhum teste mata | Mutante equivalente (sem efeito observável) | Reporte e proponha supressão para aprovação (§3) |
| Teste passa sozinho, falha na suíte | Estado compartilhado / ordem | Isole; não use `--random-order` para esconder |
| `--since` não pega nada | Base errada | Confirme a branch de integração |

---

## 15. Checklist de autoverificação

- [ ] Inventário antes de instalar; nada duplicado.
- [ ] Confirmação obtida antes de alterar lockfile.
- [ ] Gerenciador do projeto respeitado; nada global; nenhum major do runner alterado.
- [ ] Driver de cobertura verificado antes de configurar o Infection.
- [ ] Flags conferidas por `--help`, não por memória (§9).
- [ ] Diretório de código e branch de integração detectados, não assumidos.
- [ ] **Nenhum threshold baixado. Nenhuma supressão nova. Nenhum teste pulado ou apagado. Nenhuma asserção enfraquecida.** (§3)
- [ ] Nenhum arquivo da tarefa excluído do escopo de mutação.
- [ ] Estágios rodados em ordem; anel externo só com o interno verde.
- [ ] Cobertura e mutação medidas sobre o **diff** — ou a limitação declarada.
- [ ] Mutantes sobreviventes listados com `arquivo:linha` e mutação aplicada.
- [ ] MSI **e** MSI coberto reportados, nunca só um.
- [ ] Nenhum número inventado; ausência marcada como `—`.
- [ ] Orçamento de iterações respeitado; estagnação detectada e reportada.
- [ ] Relatório visual gerado e `index.html` acessível.
- [ ] "Pronto" declarado só com tudo verde e zero supressão nova.
- [ ] Nada commitado.
