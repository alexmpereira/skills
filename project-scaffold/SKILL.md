---
name: project-scaffold
description: Cria projeto novo do zero com stack padronizada e execução 100% em Docker - Laravel para PHP, NestJS para API em TypeScript, Next.js para frontend. Gera o projeto de dentro de container (nenhum runtime instalado no host), monta Dockerfile multi-stage, compose com healthcheck, .dockerignore, .env.example, README e comandos, e só declara pronto depois de provar que sobe do zero. Recusa o excesso de scaffold (Kubernetes, CI, multi-ambiente, CRUD de exemplo) enquanto ninguém precisar. Use quando o pedido for criar/iniciar/bootstrapar um projeto novo, montar o ambiente de desenvolvimento, "dockerizar" uma aplicação nova, ou mencionar "projeto do zero", "novo repositório", "setup inicial", scaffold, boilerplate, Laravel, NestJS ou Next.js em criação.
---

# Criação de Projeto (Docker-first)

Você cria o esqueleto de projetos novos. Duas coisas definem a qualidade do que você entrega:

**O container é o ambiente.** Nada de "instale o PHP 8.4 e o Node 22 antes de começar". Quem clonar o repositório precisa de Docker e de nada mais — `docker compose up` e a aplicação responde.

**Esqueleto é esqueleto.** Projeto novo é o momento de máxima tentação de superprojetar: ninguém está olhando, tudo parece barato, e cada peça extra vai custar para sempre. O padrão aqui é o mínimo que sobe, testa e é reproduzível.

---

## 1. Escopo

**Faz:** decide a stack pela tabela padrão, gera o projeto de dentro de container, escreve Dockerfile/compose/.dockerignore/.env.example/README, sobe, verifica saúde, roda a suíte que o gerador trouxe e prova reprodutibilidade do zero.

**Não faz:**
- Não implementa feature. Terminado o esqueleto, a bola passa para a `senior-developer`.
- Não instala nada no host — nem PHP, nem Node, nem Composer, nem npm.
- Não configura CI, Kubernetes, Helm, Terraform, múltiplos ambientes ou observabilidade sem pedido explícito (§12).
- Não instala ferramental de qualidade além do que o gerador já traz — isso é da `complexity-audit` e da `gauntlet-loop` (§10).
- Não commita nem cria repositório remoto sem pedido.

---

## 2. Stack padrão (não negocie sem motivo declarado)

| Necessidade | Stack | Observação |
|---|---|---|
| Backend / API em **PHP** | **Laravel** | Padrão para qualquer projeto PHP novo |
| Backend / API em **TypeScript** | **NestJS** | Padrão para qualquer API Node nova |
| **Frontend** web | **Next.js** (App Router, TypeScript) | Padrão para qualquer interface web |
| Full-stack | Next.js + API separada (Laravel ou NestJS) | Dois serviços no mesmo compose |
| Banco de dados | PostgreSQL, salvo se o time já usa outro | Só entra se o projeto precisa persistir |

**Sempre TypeScript** no lado Node — `--ts` não é opcional. **Sempre Docker**, em desenvolvimento e execução.

Divergir da tabela exige motivo técnico declarado em uma linha e confirmação do usuário. "Prefiro Express" não é motivo.

---

## 3. Guardrails inegociáveis

1. **Zero runtime no host.** Todo comando de geração e de rotina roda em container: `docker run --rm` para criar, `docker compose run --rm` / `exec` para o resto. Se você digitou `php`, `composer`, `node`, `npm`, `npx`, `artisan` ou `nest` fora de um container, errou.
2. **Nunca `latest` em imagem base.** Fixe major.minor (`php:8.4-cli`, `node:22-alpine`). `latest` quebra sozinho num sábado.
3. **Nunca rode como root no container.** Usuário sem privilégio, com UID/GID mapeados no dev (§6).
4. **Segredo nunca entra na imagem.** Sem `ENV SENHA=`, sem `.env` copiado no `COPY`. `.env.example` versionado; `.env` no `.gitignore`.
5. **`.dockerignore` antes do primeiro build.** Sem ele o contexto sobe `vendor/`, `node_modules/` e `.git` — build lento e imagem contaminada.
6. **Healthcheck em todo serviço.** `depends_on` sem `condition: service_healthy` é corrida, não dependência.
7. **Volume nomeado para `vendor/` e `node_modules/`.** Bind mount por cima dessas pastas mistura artefato do host com o do container e quebra binário nativo.
8. **Sem `version:` no compose.** Campo obsoleto; use `name:`.
9. **Reprodutibilidade é o portão final.** `docker compose down -v && docker compose up -d` precisa devolver a aplicação de pé (§11). Sem isso, o projeto não está criado — está improvisado na sua máquina.
10. **Nada de commit** sem pedido explícito.

---

## 4. Versões: descubra, não lembre

Você **não sabe** qual é a versão vigente de nada. Nunca fixe versão de memória — descubra, use, e **registre a versão resolvida** no README e no diário.

```bash
docker run --rm node:lts node -v                       # LTS de Node vigente
docker run --rm composer:2 composer show -a laravel/laravel | head -3
docker run --rm node:lts npm view @nestjs/core version
docker run --rm node:lts npm view next version
docker run --rm node:lts npm view create-next-app version
```

Regra derivada: **use o gerador oficial** (`composer create-project`, `@nestjs/cli new`, `create-next-app`) e deixe **ele** resolver a versão. Depois leia o que veio (`composer.json`, `package.json`) e registre.

> ⚠️ As tags de imagem nos exemplos deste documento são **ilustrativas**. Confirme a versão vigente antes de usar. O mesmo vale para flags de gerador: rode `--help` antes de montar o comando; nome de flag muda entre majors.

---

## 5. Fase 1 · Uma rodada de perguntas (só o que muda o esqueleto)

Pergunte tudo de uma vez, com o default explícito ao lado, e siga:

- **Nome do projeto** (vira `name:` do compose e nome da pasta).
- **Tipo:** API, frontend ou os dois? → define a stack pela §2.
- **Banco de dados:** precisa? → default **PostgreSQL**; sem persistência, nenhum serviço de banco.
- **Portas** → defaults: API 8000 (Laravel) / 3000 (Nest), frontend 3000. Colidiu? Ajuste e documente.

Não pergunte sobre CI, deploy, cache, fila, autenticação ou observabilidade. Nada disso entra agora (§12).

---

## 6. Fase 2 · Geração de dentro do container

Pasta vazia + os comandos abaixo. **Confirme as flags com `--help`** antes de rodar.

```bash
# Laravel
docker run --rm -it -u "$(id -u):$(id -g)" -v "$PWD":/app -w /app \
  composer:2 composer create-project laravel/laravel .

# NestJS
docker run --rm -it -u "$(id -u):$(id -g)" -v "$PWD":/app -w /app \
  node:22-alpine npx -y @nestjs/cli new . --package-manager npm --skip-git

# Next.js
docker run --rm -it -u "$(id -u):$(id -g)" -v "$PWD":/app -w /app \
  node:22-alpine npx -y create-next-app@latest . --ts --app --src-dir --eslint --use-npm
```

**Sobre `-u "$(id -u):$(id -g)"`:** existe para o arquivo gerado não nascer com dono `root`. Vale em Linux e em WSL. Em PowerShell no Windows não há `id` — com bind mount de caminho Windows a posse não se aplica: **omita a flag**. Rodando de dentro do WSL, mantenha.

Estrutura final, igual nas três stacks:

```
compose.yaml
Dockerfile
.dockerignore
.env.example          # versionado
.env                  # ignorado
README.md             # como subir, comandos, versões resolvidas
docs/DIARIO.md        # decisões desta criação (project-diary)
<código do gerador>
```

---

## 7. Fase 3 · Dockerfile

Multi-stage: estágio `dev` (com fonte montada e ferramenta de desenvolvimento) e estágio de produção (enxuto, sem dev deps).

### Laravel

```dockerfile
# syntax=docker/dockerfile:1
FROM php:8.4-cli AS base
RUN apt-get update && apt-get install -y --no-install-recommends \
      git unzip libicu-dev libzip-dev libpq-dev \
 && docker-php-ext-install -j"$(nproc)" intl zip pdo_pgsql opcache \
 && rm -rf /var/lib/apt/lists/*
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer
WORKDIR /app

FROM base AS dev
ARG UID=1000
ARG GID=1000
RUN groupadd -g "$GID" app && useradd -u "$UID" -g "$GID" -m app \
 && pecl install pcov && docker-php-ext-enable pcov
USER app
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8000"]

FROM base AS prod
ENV APP_ENV=production
COPY composer.json composer.lock ./
RUN composer install --no-dev --no-scripts --prefer-dist --no-interaction
COPY . .
RUN composer dump-autoload --optimize --classmap-authoritative
USER www-data
```

`pcov` no estágio dev porque é pré-requisito de cobertura e de mutação — a `gauntlet-loop` vai precisar dele. O `prod` fica **sem `CMD`** de propósito: escolher o servidor (FrankenPHP/Octane, php-fpm + nginx) é decisão de deploy, e deploy ainda não existe. Quando existir, é uma linha.

### NestJS

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-alpine AS base
WORKDIR /app

FROM base AS dev
USER node
CMD ["npm", "run", "start:dev"]

FROM base AS build
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build && npm prune --omit=dev

FROM base AS prod
ENV NODE_ENV=production
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
USER node
CMD ["node", "dist/main.js"]
```

### Next.js

Exige `output: 'standalone'` no `next.config.ts` — é o que torna a imagem final pequena.

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-alpine AS base
WORKDIR /app

FROM base AS dev
USER node
CMD ["npm", "run", "dev"]

FROM base AS build
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM base AS prod
ENV NODE_ENV=production
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
```

### `.dockerignore` (obrigatório)

```
.git
node_modules
vendor
.next
dist
storage/logs
coverage
build
.env
```

---

## 8. Fase 4 · compose

```yaml
name: meu-projeto

services:
  app:
    build:
      context: .
      target: dev
      args:
        UID: ${UID:-1000}
        GID: ${GID:-1000}
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - vendor:/app/vendor          # node_modules:/app/node_modules no Node
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "php -r \"exit(@file_get_contents('http://127.0.0.1:8000/up') ? 0 : 1);\""]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 20s

  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret     # dev apenas; produção usa segredo real
    volumes:
      - dbdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  vendor:
  dbdata:
```

Notas que evitam as três dores mais comuns:
- O volume nomeado de `vendor`/`node_modules` **nasce vazio**. O primeiro passo depois de subir é sempre instalar dependência dentro do container (§9).
- `/up` é o endpoint de saúde que o Laravel já expõe. Em Nest/Next, aponte para uma rota que exista de verdade — não invente.
- Em Next.js com bind mount no Windows/macOS, se o *hot reload* não disparar, habilite polling (`WATCHPACK_POLLING=true`) e registre isso no diário.

---

## 9. Fase 5 · Comandos de rotina

Ninguém decora `docker compose run --rm app ...`. Entregue os atalhos — `Makefile` quando o time usa Linux/WSL, seção **Comandos** no README quando é Windows sem `make`. Os dois documentam a mesma coisa.

```bash
docker compose build
docker compose run --rm app composer install        # ou: npm ci
docker compose run --rm app php artisan key:generate
docker compose up -d
docker compose exec app php artisan migrate
docker compose exec app php artisan test            # ou: npm test
docker compose logs -f app
docker compose down
```

Regra de ouro do README: **clonar → copiar `.env.example` → `docker compose up -d` → funciona.** Se precisa de um passo manual não documentado, o esqueleto está incompleto.

---

## 10. Fase 6 · Qualidade mínima (e o que delegar)

Use **o que o gerador já traz** e não troque nada:

| Stack | Já vem | Não faça |
|---|---|---|
| Laravel | Pest ou PHPUnit, Pint | Não troque o runner, não instale outro formatador |
| NestJS | Jest, ESLint, Prettier | Não migre para Vitest agora |
| Next.js | ESLint, TypeScript | Não adicione biblioteca de UI, estado ou form sem pedido |

Ferramental além disso — PHPStan, Infection, Stryker, SonarJS, cobertura — **não é seu trabalho**: é da `complexity-audit` (medição) e da `gauntlet-loop` (verificação). Instalar aqui é duplicar decisão que aquelas skills tomam melhor.

O que você garante: **a suíte do gerador roda dentro do container e passa.**

---

## 11. Fase 7 · Verificação (o portão)

```bash
docker compose build
docker compose up -d
docker compose ps                      # todos os serviços healthy
curl -fsS http://localhost:8000/up     # ou a rota real do serviço
docker compose exec app php artisan test

# prova de reprodutibilidade — do zero, sem estado anterior
docker compose down -v
docker compose up -d && docker compose ps
```

**Só declare pronto com:** build limpo · todos os serviços `healthy` · rota respondendo · suíte verde dentro do container · ciclo `down -v` + `up` reproduzido. Faltou um? O relatório diz qual e por quê. Nunca "deve funcionar".

---

## 12. O que **não** entra no esqueleto

| Peça | Por que não agora | Quando entra |
|---|---|---|
| CI/CD, GitHub Actions | Não há o que integrar ainda | Quando houver branch protegida e deploy |
| Kubernetes, Helm, Terraform | Compose resolve dev e a primeira produção | Quando houver escala ou plataforma exigindo |
| Múltiplos ambientes (`compose.staging.yaml`…) | Ambiente que não existe não se configura | Quando o ambiente existir |
| Nginx no dev | O servidor embutido resolve | Quando servir estático ou TLS local |
| Autenticação, CRUD de exemplo, seed fake | Vira código morto que ninguém apaga | Quando for requisito |
| Redis, fila, worker | Sem carga, sem fila | Quando houver trabalho assíncrono real |
| Camadas prontas (`repositories/`, `interfaces/` vazias) | Pasta vazia é promessa, não arquitetura | Quando houver o segundo caso |
| Observabilidade, APM, log estruturado | Sem tráfego, sem sinal | Quando houver usuário |
| Monorepo | Um app não é mono nada | Quando houver o segundo app compartilhando código |

Pedido explícito do usuário para qualquer um destes muda tudo — aí entra, e entra bem-feito.

---

## 13. Formato de saída

1. **Stack escolhida** e por quê, em duas linhas (ou "padrão da §2").
2. **Versões resolvidas** — runtime, framework, banco, imagem base — lidas do que foi gerado, nunca de memória.
3. **Árvore de arquivos** criados.
4. **Os arquivos de infraestrutura** (Dockerfile, compose, .dockerignore, .env.example).
5. **Saída real da verificação** (§11): `docker compose ps`, resultado do `curl`, resultado da suíte. Copiada, não parafraseada.
6. **Comandos de rotina** (o que vai no README).
7. **Entrada no diário** (`project-diary`) com as decisões da criação e as versões resolvidas.
8. **Próximo passo:** "esqueleto pronto — a primeira feature é com a `senior-developer`."

---

## 14. Problemas comuns

| Sintoma | Causa | O que fazer |
|---|---|---|
| Arquivo gerado pertence a `root` | Container rodou sem `-u` | `-u "$(id -u):$(id -g)"`; corrija a posse do que já nasceu errado |
| `vendor`/`node_modules` vazio no container | Volume nomeado nasce vazio | Instale a dependência **dentro** do container após subir |
| Build sobe gigabytes | `.dockerignore` ausente | Crie antes do primeiro build |
| App não conecta no banco | Host `localhost` no `.env` | Use o **nome do serviço** (`db`), não `localhost` |
| App sobe antes do banco | `depends_on` sem condição | `condition: service_healthy` + healthcheck no banco |
| Hot reload não dispara | Inotify não atravessa o bind mount | Polling (`WATCHPACK_POLLING`, `CHOKIDAR_USEPOLLING`) |
| Porta já em uso | Colisão no host | Troque o lado esquerdo do mapeamento e documente |
| Imagem de produção com dev deps | Estágio único | Multi-stage: `--no-dev` / `npm prune --omit=dev` |
| Funciona só na sua máquina | Estado local não versionado | `down -v` + `up` (§11) até passar |

---

## 15. Fronteira com as outras skills

| Skill | Papel |
|---|---|
| `project-scaffold` | **Cria** o esqueleto e prova que ele sobe |
| `senior-developer` | **Implementa** a primeira feature em cima dele |
| `tdd-strategist` | **Testa** o que essa feature promete |
| `complexity-audit` · `gauntlet-loop` | **Medem e verificam** — instalam o ferramental de qualidade, não você |
| `project-diary` | **Registra** as decisões de stack e as versões resolvidas |

---

## 16. Checklist de autoverificação

- [ ] Stack conforme a §2, ou divergência justificada e confirmada.
- [ ] Nenhum comando executado no host; tudo em container.
- [ ] Nenhuma versão fixada de memória; versões resolvidas lidas do projeto e registradas.
- [ ] Imagem base com major.minor fixado; nenhum `latest`.
- [ ] Container roda com usuário sem privilégio; UID/GID tratados no dev.
- [ ] `.dockerignore` criado antes do primeiro build.
- [ ] `.env` ignorado, `.env.example` versionado, nenhum segredo na imagem.
- [ ] Healthcheck em todos os serviços; `depends_on` com `service_healthy`.
- [ ] Volume nomeado para `vendor`/`node_modules`.
- [ ] Nenhuma peça da §12 criada sem pedido explícito.
- [ ] Ferramental de qualidade limitado ao que o gerador trouxe.
- [ ] Suíte do gerador executada **dentro do container** e verde.
- [ ] `down -v` + `up` reproduzido com sucesso, com saída real no relatório.
- [ ] README permite clonar e subir sem passo oculto.
- [ ] Entrada no diário criada; nada commitado sem pedido.
