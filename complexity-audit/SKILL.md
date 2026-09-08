---
name: complexity-audit
description: Audita o ferramental de métricas de complexidade de um projeto PHP ou TypeScript - detecta o que já existe, instala o que falta (phpmd, phpcs, PhpMetrics, PHPStan+cognitive-complexity; ESLint, typescript-eslint, eslint-plugin-sonarjs, jscpd), executa a medição sem invadir a configuração do projeto e gera relatório unificado de complexidade ciclomática e cognitiva com ranking de ofensores e plano de baseline. Use quando o pedido for medir/auditar complexidade, configurar ferramenta de métricas, gerar relatório de qualidade de código, descobrir os piores arquivos do projeto, ou mencionar phpmd, phpcs, phpmetrics, phpstan, sonarjs, cognitive complexity, complexidade ciclomática ou "onde está a dívida técnica".
---

# Auditoria de Complexidade (PHP · TypeScript)

Você configura e executa medição de complexidade em projetos PHP e TypeScript, e entrega um relatório único e comparável entre as duas stacks.

Princípio que governa tudo: **medir sem invadir**. A auditoria não altera a configuração de lint do projeto, não muda regras que a equipe já acordou e não quebra o build. Toda a configuração da medição vive isolada em `build/complexity/`. Integrar as regras ao lint do projeto é uma **segunda etapa, separada e explícita** — nunca um efeito colateral da medição.

---

## 1. Escopo

**Faz:** detecta ferramental existente, instala o que falta, executa a medição, normaliza as saídas num relatório único, ranqueia ofensores e propõe baseline.

**Não faz:**
- Não refatora código. Encontrou complexidade alta? O relatório aponta; a refatoração é da skill `low-complexity-expert` (§10).
- Não altera `eslint.config.*`, `phpcs.xml`, `phpstan.neon` ou `phpmd.xml` do projeto, a menos que seja pedido explicitamente como etapa separada.
- Não mexe em CI/CD, hooks de git ou `package.json` scripts sem pedido explícito.
- Não commita nada.

---

## 2. Guardrails de execução (INEGOCIÁVEL)

1. **Confirme antes de instalar.** Instalação altera `composer.json`/`package.json` e o lockfile, e exige rede. Apresente o plano (§5) e espere o "ok". Uma confirmação cobre a instalação inteira — não pergunte pacote por pacote.
2. **Nunca instale global.** Sempre `--dev` (Composer) ou `-D` (npm/pnpm/yarn). Nunca `npm i -g`, nunca `composer global require`.
3. **Respeite o gerenciador de pacotes do projeto.** Detecte pelo lockfile e use aquele. Nunca rode `npm install` num projeto com `pnpm-lock.yaml`.
4. **Nunca sobrescreva config existente.** Se `phpcs.xml` ou `eslint.config.mjs` já existem, leia — não substitua. A medição usa config própria em `build/complexity/`.
5. **Exit code diferente de zero não é falha.** Estas ferramentas sinalizam violações pelo código de saída (§7). Trate como dado, não como erro.
6. **Exclua o que não é código seu:** `vendor/`, `node_modules/`, `dist/`, `build/`, `coverage/`, `storage/`, `bootstrap/cache/`, migrations, código gerado, snapshots e fixtures de teste.
7. **Não confie em nome de regra de memória.** Nomes de regra e sniffs mudam entre versões major. Verifique antes de escrever a config (§6.3) — é um comando, não um palpite.
8. **Sem rede? Degrade, não falhe.** Rode com o que já existe no projeto e diga no relatório qual métrica ficou faltando.
9. **Adicione `build/complexity/` ao `.gitignore`** — ou pergunte, se o projeto versiona artefatos de build de propósito.

---

## 3. Fase 1 · Inventário

Antes de qualquer instalação, produza o inventário. Nunca instale o que já existe.

### 3.1 Identificar as stacks

| Sinal | Stack |
|---|---|
| `composer.json` | PHP |
| `package.json` com `typescript` ou arquivos `.ts`/`.tsx` | TypeScript |
| Ambos | Rode as duas trilhas e unifique num só relatório |

### 3.2 PHP — o que procurar

```bash
# Dependências já declaradas
grep -E 'phpmd|codesniffer|phpmetrics|phpstan|cognitive|psalm|rector' composer.json

# Configs existentes
ls -1 phpmd.xml* phpcs.xml* .phpcs.xml* phpstan.neon* psalm.xml* .phpmetrics* 2>/dev/null

# Binários instalados
ls -1 vendor/bin/ 2>/dev/null | grep -E 'phpmd|phpcs|phpmetrics|phpstan|psalm'
```

Descubra também **onde está o código**: `src/` (padrão/Symfony), `app/` (Laravel — confirme por `artisan`), ou o `autoload.psr-4` do `composer.json`. Nunca assuma `src/`.

### 3.3 TypeScript — o que procurar

```bash
# Dependências já declaradas
grep -E '"eslint"|typescript-eslint|@typescript-eslint|sonarjs|biome|oxlint|jscpd' package.json

# Formato de config do ESLint — decide como a config da medição é escrita
ls -1 eslint.config.* .eslintrc* biome.json* 2>/dev/null

# Gerenciador de pacotes
ls -1 pnpm-lock.yaml yarn.lock package-lock.json bun.lock* 2>/dev/null

# Monorepo?
ls -1 pnpm-workspace.yaml turbo.json nx.json 2>/dev/null
```

Distinção que importa: `eslint.config.*` é **flat config** (ESLint 9+); `.eslintrc*` é o formato **legado**. A sintaxe da config de medição muda entre os dois.

**Se o projeto usa Biome** (`biome.json`): ele já tem `complexity/noExcessiveCognitiveComplexity` nativo. Prefira ativá-lo numa config isolada a instalar ESLint só para medir — não introduza um segundo linter num projeto que escolheu Biome.

### 3.4 Saída da Fase 1

| Métrica | PHP | TypeScript |
|---|---|---|
| Ciclomática | ✅ phpmd 2.15 | ❌ ausente |
| Cognitiva | ❌ ausente | ❌ ausente |
| Aninhamento | ❌ ausente | ❌ ausente |
| Duplicação | ❌ ausente | ❌ ausente |
| Relatório visual | ❌ ausente | — |

---

## 4. Ferramental de referência

Versões verificadas em **2026-09-08**. Confirme com `npm view <pkg> version` / Packagist antes de fixar — e registre no relatório a versão realmente resolvida.

### PHP

| Ferramenta | Pacote | Versão | Mede |
|---|---|---|---|
| PHPMD | `phpmd/phpmd` | 2.15.0 | Ciclomática, NPath, tamanho de método/classe, complexidade de código |
| PHP_CodeSniffer | `squizlabs/php_codesniffer` | 4.0.4 (linha 3.x: 3.13.6) | Ciclomática e nível de aninhamento, por sniff |
| PhpMetrics | `phpmetrics/phpmetrics` | 2.11.0 estável (3.0 em RC) | Ciclomática, índice de manutenibilidade, Halstead, acoplamento, LCOM + **relatório HTML** |
| PHPStan + extensão | `phpstan/phpstan` + `tomasvotruba/cognitive-complexity` | 1.2.0 (extensão) | **Complexidade cognitiva** por função e por classe |

Por que os quatro: phpmd, phpcs e PhpMetrics medem **ciclomática** (contagem de caminhos). Nenhum deles mede **cognitiva** (esforço de leitura) — essa lacuna só é coberta pela extensão do PHPStan. Sem ela, metade da pergunta fica sem resposta.

### TypeScript

| Ferramenta | Pacote | Versão | Mede |
|---|---|---|---|
| ESLint | `eslint` | 10.10.0 | Base de execução; regras nativas `complexity`, `max-depth`, `max-params`, `max-lines-per-function`, `max-nested-callbacks` |
| typescript-eslint | `typescript-eslint` | 8.70.0 | Parser de TS — sem ele o ESLint não lê `.ts`/`.tsx` |
| SonarJS | `eslint-plugin-sonarjs` | 4.2.0 (peer: ESLint 8/9/10) | **`sonarjs/cognitive-complexity`** — a métrica cognitiva do SonarSource, mesma definição usada no SonarQube |
| jscpd | `jscpd` | 5.2.0 | Duplicação (opcional, mas duplicação alta costuma andar junto com complexidade alta) |

SonarJS é a escolha por confiabilidade: implementa a especificação de complexidade cognitiva da SonarSource, que é a referência da indústria — o número é comparável ao que um SonarQube reportaria.

---

## 5. Fase 2 · Plano e confirmação

Apresente exatamente isto e espere a confirmação:

```markdown
## Plano de auditoria

**Stacks:** PHP (app/) · TypeScript (src/)
**Gerenciadores:** Composer · pnpm (detectado por pnpm-lock.yaml)

**Já existe (não será tocado):** phpmd 2.15.0, eslint 10.10.0

**Será instalado como dev-dependency:**
- Composer: phpmetrics/phpmetrics ^2.11, phpstan/phpstan, tomasvotruba/cognitive-complexity ^1.2
- pnpm: eslint-plugin-sonarjs ^4.2, typescript-eslint ^8.70

**Impacto:** composer.json + composer.lock, package.json + pnpm-lock.yaml.
Nenhuma config de lint existente será alterada.

**Artefatos:** build/complexity/ (será adicionado ao .gitignore)

Confirma?
```

### Três modos de operação

Ofereça o modo B quando o projeto for sensível a mudança de lockfile.

| Modo | Como | Quando |
|---|---|---|
| **A · dev-dependency** (padrão) | `composer require --dev` / `pnpm add -D` | Auditoria vai virar rotina do time |
| **B · isolado, sem tocar no lockfile** | PHARs e `npm i --prefix build/complexity/.tools --no-save` | Medição pontual; repo sob congelamento; lockfile sensível |
| **C · só o que já existe** | Roda com o ferramental presente | Sem rede, ou instalação recusada. Declare no relatório a métrica faltante |

Comandos do modo B:

```bash
mkdir -p build/complexity/.tools

# PHP — PHARs (confirme o asset da release antes de baixar)
curl -sL -o build/complexity/.tools/phpmd.phar \
  https://github.com/phpmd/phpmd/releases/download/2.15.0/phpmd.phar
curl -sL -o build/complexity/.tools/phpmetrics.phar \
  https://github.com/phpmetrics/PhpMetrics/releases/download/v2.11.0/phpmetrics.phar

# TypeScript — instalação fora do projeto, package.json e lockfile intactos
npm i --prefix build/complexity/.tools --no-save \
  eslint typescript-eslint eslint-plugin-sonarjs
```

Limitação honesta do modo B em PHP: a complexidade **cognitiva** depende da extensão do PHPStan, que precisa do Composer. Via PHAR você tem ciclomática e manutenibilidade, não cognitiva. Diga isso no relatório em vez de omitir a lacuna.

---

## 6. Fase 3 · Instalação e configuração isolada

### 6.1 Instalar (modo A)

```bash
# PHP — só o que o inventário apontou como ausente
composer require --dev phpmd/phpmd squizlabs/php_codesniffer
composer require --dev "phpmetrics/phpmetrics:^2.11"
composer require --dev phpstan/phpstan tomasvotruba/cognitive-complexity

# TypeScript — use o gerenciador detectado
pnpm add -D eslint typescript-eslint eslint-plugin-sonarjs jscpd
# npm i -D … | yarn add -D … | bun add -d …
```

### 6.2 Limites de referência

Alinhados com a skill `low-complexity-expert` — o mesmo padrão medido aqui e cobrado lá.

| Métrica | Limite | Onde é medido |
|---|---|---|
| Complexidade ciclomática (função) | ≤ 5 | phpmd, phpcs, ESLint `complexity` |
| Complexidade cognitiva (função) | ≤ 7 | PHPStan cognitive, `sonarjs/cognitive-complexity` |
| Complexidade cognitiva (classe) | ≤ 50 | PHPStan cognitive |
| Nível de aninhamento | ≤ 2 | phpcs `NestingLevel`, ESLint `max-depth` |
| Parâmetros | ≤ 3 | ESLint `max-params`, phpmd |
| Linhas por função | ≤ 20 | ESLint `max-lines-per-function`, phpmd |

⚠️ **Em código legado, esses limites vão gerar centenas de violações.** Isso é esperado e não é motivo para afrouxá-los. A primeira execução é **medição**, não portão de qualidade: severidade `warning`, build nunca quebra. O aperto vem depois, pelo baseline (§9).

### 6.3 Verifique os nomes antes de escrever a config

Um comando, e você deixa de chutar:

```bash
# Sniffs de métrica realmente disponíveis nesta versão do phpcs
vendor/bin/phpcs -e | grep -i -A2 'metrics'

# Regras do plugin realmente disponíveis nesta versão do ESLint
npx eslint --print-config src/index.ts | grep -i 'cognitive\|complexity'
```

Se `Generic.Metrics.*` não existir na sua versão do phpcs (a linha 4.x reorganizou sniffs), não invente: use phpmd para ciclomática e aninhamento e registre no relatório que o phpcs ficou fora.

### 6.4 Configs da medição — todas em `build/complexity/`

`build/complexity/phpcs-metrics.xml`:

```xml
<?xml version="1.0"?>
<ruleset name="Metricas">
  <description>Somente metricas. Nao interfere no phpcs.xml do projeto.</description>
  <rule ref="Generic.Metrics.CyclomaticComplexity">
    <properties>
      <property name="complexity" value="5"/>
      <property name="absoluteComplexity" value="10"/>
    </properties>
  </rule>
  <rule ref="Generic.Metrics.NestingLevel">
    <properties>
      <property name="nestingLevel" value="2"/>
      <property name="absoluteNestingLevel" value="4"/>
    </properties>
  </rule>
</ruleset>
```

`build/complexity/phpstan-cognitive.neon`:

```neon
includes:
    - ../../vendor/tomasvotruba/cognitive-complexity/config/extension.neon
parameters:
    level: 0
    paths:
        - ../../app
    cognitive_complexity:
        function: 7
        class: 50
```

`level: 0` é intencional: aqui só interessa a métrica cognitiva, não a análise estática completa do PHPStan.

`build/complexity/eslint.metrics.mjs`:

```js
// Config exclusiva da medição. Rodada com --no-config-lookup para
// ignorar totalmente o eslint.config do projeto.
import tseslint from 'typescript-eslint';
import sonarjs from 'eslint-plugin-sonarjs';

export default tseslint.config(
  {
    ignores: [
      '**/node_modules/**', '**/dist/**', '**/build/**',
      '**/coverage/**', '**/*.d.ts', '**/*.spec.ts', '**/*.test.ts',
    ],
  },
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: { parser: tseslint.parser },
    plugins: { sonarjs },
    rules: {
      'complexity': ['warn', { max: 5 }],
      'max-depth': ['warn', 2],
      'max-params': ['warn', 3],
      'max-nested-callbacks': ['warn', 2],
      'max-lines-per-function': ['warn', { max: 20, skipBlankLines: true, skipComments: true }],
      'sonarjs/cognitive-complexity': ['warn', 7],
    },
  },
);
```

Config legada (`.eslintrc`), quando o projeto ainda usa esse formato — `build/complexity/.eslintrc.metrics.json`:

```json
{
  "root": true,
  "parser": "@typescript-eslint/parser",
  "plugins": ["sonarjs"],
  "rules": {
    "complexity": ["warn", { "max": 5 }],
    "max-depth": ["warn", 2],
    "max-params": ["warn", 3],
    "max-nested-callbacks": ["warn", 2],
    "max-lines-per-function": ["warn", { "max": 20, "skipBlankLines": true, "skipComments": true }],
    "sonarjs/cognitive-complexity": ["warn", 7]
  }
}
```

---

## 7. Fase 4 · Execução

Códigos de saída — **nenhum destes é falha da auditoria**:

| Ferramenta | Código | Significado |
|---|---|---|
| phpmd | 0 / 1 / 2 | limpo / erro real / violações encontradas |
| phpcs | 0 / 1 / 2 | limpo / violações / erro de execução |
| phpstan | 0 / 1 | limpo / violações |
| eslint | 0 / 1 / 2 | limpo / violações / erro de config |
| jscpd | 0 / 1 | dentro do limite / acima do limite |

Encadeie com `|| true` para o pipeline não abortar, mas **leia o código** e distinga "violação" de "erro de execução" — se phpcs retornar 2 ou eslint retornar 2, é problema de config, não métrica.

```bash
mkdir -p build/complexity

# ---------- PHP (ajuste app/ conforme a Fase 1) ----------
vendor/bin/phpmd app json codesize,design \
  --reportfile build/complexity/phpmd.json || true

vendor/bin/phpcs app \
  --standard=build/complexity/phpcs-metrics.xml \
  --report=json --report-file=build/complexity/phpcs.json || true

vendor/bin/phpmetrics \
  --report-html=build/complexity/phpmetrics-html \
  --report-json=build/complexity/phpmetrics.json app || true

vendor/bin/phpstan analyse \
  -c build/complexity/phpstan-cognitive.neon \
  --error-format=json --no-progress \
  > build/complexity/phpstan.json || true

# ---------- TypeScript ----------
npx eslint . \
  --config build/complexity/eslint.metrics.mjs \
  --no-config-lookup \
  --format json --output-file build/complexity/eslint.json \
  --no-error-on-unmatched-pattern || true

npx jscpd src \
  --reporters json --output build/complexity/jscpd \
  --min-lines 10 --threshold 100 || true
```

Se algum comando falhar por erro de execução, vá para §11 antes de seguir.

---

## 8. Fase 5 · Relatório unificado

Grave em `build/complexity/REPORT.md` e apresente o resumo no chat. A tabela de ofensores é o coração — ela é o que gera ação.

```markdown
# Relatório de Complexidade — <projeto>
Gerado em <data> · PHP <versão> · Node <versão>

## Ferramental
| Ferramenta | Versão | Status |
|---|---|---|
| phpmd | 2.15.0 | já existia |
| tomasvotruba/cognitive-complexity | 1.2.0 | instalado nesta auditoria |
| eslint-plugin-sonarjs | 4.2.0 | instalado nesta auditoria |
| phpcs | — | indisponível: sniffs Generic.Metrics ausentes na 4.x |

## Panorama
| Métrica | Limite | PHP (app/) | TypeScript (src/) |
|---|---|---|---|
| Unidades analisadas | — | 412 | 288 |
| Ciclomática > 5 | ≤ 5 | 47 (11%) | 23 (8%) |
| Cognitiva > 7 | ≤ 7 | 31 (8%) | 19 (7%) |
| Aninhamento > 2 | ≤ 2 | 22 | 14 |
| Pior caso | — | 34 (`OrderService::process`) | 41 (`checkout.ts`) |
| Duplicação | < 3% | — | 4,2% |

## Top 10 ofensores
| # | Local | Unidade | Cicl. | Cogn. | Aninh. | Ferramenta |
|---|---|---|---|---|---|---|
| 1 | `app/Services/OrderService.php:88` | `process()` | 34 | 52 | 6 | phpmd, phpstan |
| 2 | `src/checkout/checkout.ts:140` | `handleSubmit()` | 22 | 41 | 5 | eslint, sonarjs |

## Índice de manutenibilidade (PhpMetrics)
Arquivos abaixo de 65 (faixa de risco): 18. Relatório navegável em
`build/complexity/phpmetrics-html/index.html`.

## Leitura
<2–4 frases: onde a complexidade está concentrada, se é dívida difusa ou
localizada em poucos arquivos, e qual métrica está pior.>

## Próximos passos
1. Congelar baseline (§9) para impedir piora.
2. Refatorar os 3 primeiros ofensores com a skill `low-complexity-expert`.
3. <Etapa opcional, só se pedido: integrar as regras ao lint do projeto.>
```

Regras do relatório: ordene por gravidade (maior cognitiva primeiro — ela reflete melhor o esforço de leitura que a ciclomática); todo caminho no formato `arquivo:linha` para ser clicável; **nunca invente número** — métrica que a ferramenta não produziu entra como `—` com a razão registrada na tabela de ferramental.

---

## 9. Fase 6 · Baseline e aperto progressivo

Limite estrito em projeto legado só funciona com baseline. Sem isso, ou o time desliga a regra, ou passa a ignorar centenas de avisos — os dois resultados matam a medição.

1. **Congele o estado atual.** Salve `build/complexity/baseline.json` com a contagem de violações por métrica e o pior caso de cada arquivo.
2. **O portão é "não piorar".** A regra de CI passa se a contagem não subiu. Não exige que ninguém pare tudo para refatorar.
3. **Aperte na cadência do time.** A cada ciclo, baixe o teto do pior caso. `34 → 25 → 15 → 8`.
4. **Regra do escoteiro:** arquivo tocado numa feature sai dela com complexidade menor ou igual à que entrou.

O PHPStan tem baseline nativo (`--generate-baseline`) — use-o se o projeto já usa PHPStan. Do lado TS, a contagem no `baseline.json` cumpre o mesmo papel.

Integrar as regras ao lint do projeto e ao CI é **etapa separada**, feita só quando pedida, e sempre com severidade `warn` no primeiro ciclo.

---

## 10. Fronteira com `low-complexity-expert`

| | Papel | Entrega |
|---|---|---|
| `complexity-audit` | **Mede.** Encontra e ranqueia onde está a dívida | Relatório, ranking, baseline |
| `low-complexity-expert` | **Corrige.** Refatora reduzindo ICP | Código refatorado, ICP antes → depois |

Fluxo natural: esta skill produz o Top 10 → você escolhe um item → a `low-complexity-expert` refatora → rode a auditoria de novo e compare com o baseline. A medição é o que transforma "esse código é ruim" em "esse método tem cognitiva 52, alvo 7".

---

## 11. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `vendor/bin/...: not found` | `composer install` não rodou | Rode `composer install` antes |
| phpcs: `Referenced sniff not found` | Sniff ausente/renomeado nesta versão | Verifique com `phpcs -e` (§6.3); caia para phpmd |
| ESLint código 2 + `Failed to load plugin` | Plugin não resolvido a partir do cwd | Modo A: instale no projeto. Modo B: rode o binário de `.tools/` |
| `sonarjs/cognitive-complexity` "rule not found" | Regra renomeada/removida na versão instalada | Confirme com `--print-config` (§6.3) e ajuste o nome |
| ESLint não reporta nada | Config flat vs legado trocados, ou `files` não casa | Cheque §3.3 e rode com `--debug` |
| PhpMetrics quebra em PHP 8.4 | Estável 2.11 vs. v3 em RC | Teste `^3.0@rc`; se falhar, registre a lacuna |
| Análise levando minutos | Rodando em `vendor/`/`node_modules/` | Reveja as exclusões (§2.6) |
| Monorepo mede um pacote só | Escopo apontando para a raiz | Rode por workspace e agregue por pacote no relatório |

---

## 12. Checklist de autoverificação

- [ ] Inventário feito **antes** de instalar; nada duplicado.
- [ ] Confirmação obtida antes de alterar lockfile.
- [ ] Gerenciador de pacotes do projeto respeitado.
- [ ] Nenhuma dependência global.
- [ ] Nenhuma config existente do projeto foi alterada.
- [ ] Toda config de medição está em `build/complexity/`.
- [ ] Nomes de regra e sniff verificados por comando, não por memória (§6.3).
- [ ] Exclusões aplicadas (`vendor/`, `node_modules/`, `dist/`, gerados, testes).
- [ ] Diretório de código real detectado (não assumi `src/`).
- [ ] **Ciclomática e cognitiva** presentes no relatório — ou a lacuna registrada com a razão.
- [ ] Exit codes interpretados; "violação" distinguida de "erro de execução".
- [ ] Nenhum número inventado; ausência marcada como `—`.
- [ ] Ofensores ordenados por gravidade, com `arquivo:linha`.
- [ ] Baseline proposto; primeira execução não quebra build.
- [ ] `build/complexity/` no `.gitignore` (ou a exceção combinada).
- [ ] Nada commitado.
