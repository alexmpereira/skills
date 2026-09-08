# 🧠 AI Agent Skills Repository

Este repositório contém *Skills* (ou System Prompts personalizados) projetados para estender as capacidades dos seus agentes de IA (Antigravity, Claude Code, GitHub Copilot, ChatGPT, etc.).

As skills ajudam a definir regras arquiteturais, padrões de codificação ou comportamentos específicos que os agentes devem seguir em seus projetos.

## 📦 Como Instalar e Usar

Abaixo estão as instruções de como instalar e configurar essas skills nas principais ferramentas de IA, tanto em Windows quanto em Mac.

### 1. Antigravity IDE (Gemini Agentic Coding)

No Antigravity, as skills possuem um formato especial (`SKILL.md` com um cabeçalho YAML) e podem ser configuradas de forma **Global** (para todos os seus projetos) ou **Local** (para um projeto específico).

**Instalação Global (Mac/Windows):**
1. O diretório global de customizações fica em:
   - **Mac:** `~/.gemini/config`
   - **Windows:** `%USERPROFILE%\.gemini\config`
2. Você pode copiar as pastas das skills (ex: `low-complexity-expert`) para a pasta `skills` dentro do diretório de customização global.
   - O caminho final deve ficar assim: `~/.gemini/config/skills/low-complexity-expert/SKILL.md`
3. Como alternativa (mais avançada), você pode criar um arquivo `skills.json` no diretório global apontando para o caminho deste repositório em sua máquina:
   ```json
   {
     "entries": [
       { "path": "/Caminho/Absoluto/Para/Este/Repositorio/skills" }
     ]
   }
   ```

**Instalação Local (Por Projeto):**
1. Na raiz do projeto onde deseja aplicar as regras, crie uma pasta chamada `.agents` (se não existir).
2. Copie a pasta da skill (ex: `low-complexity-expert`) para dentro de `.agents/skills/`.
3. Outra forma, usando regras genéricas (Rules), é simplesmente copiar o conteúdo (o texto das regras) e colar em um arquivo `AGENTS.md` na raiz da `.agents/` (ou na raiz do próprio projeto).

### 2. Claude Code

O Claude Code carrega skills nativamente. **Mantenha o cabeçalho YAML** — é ele que contém os gatilhos de ativação.

**Como skill (recomendado — carregada sob demanda, sem custo de contexto fixo):**
- **Global (todos os projetos):** copie a pasta da skill para `~/.claude/skills/` (Mac) ou `%USERPROFILE%\.claude\skills\` (Windows).
  - Caminho final: `~/.claude/skills/low-complexity-expert/SKILL.md`
- **Por projeto:** copie a pasta para `.claude/skills/` na raiz do repositório.
- O nome da pasta **deve** ser igual ao campo `name` do YAML.
- Verifique com `/skills` na sessão; invoque manualmente com `/low-complexity-expert`.

**Como instrução permanente (alternativa):** cole o conteúdo das regras em `CLAUDE.md` na raiz do projeto. Use isso apenas quando quiser a regra ativa em **toda** interação — ela consome contexto em todas as mensagens.

### 3. GitHub Copilot / ChatGPT / Claude Web

Para essas ferramentas baseadas em chat web ou IDE (como Copilot Chat), você usa o recurso de **Custom Instructions** (Instruções Customizadas) ou **System Prompt**.

1. Abra as configurações da sua ferramenta preferida (ex: *Settings > Custom Instructions* no ChatGPT ou as definições de sistema no console da API do Claude/OpenAI).
2. Cole o conteúdo da skill no campo onde você configura como a IA deve agir e responder.
3. No **GitHub Copilot** (VS Code, IntelliJ, etc.), você pode adicionar essas instruções no arquivo de configuração do seu Workspace/Settings para ditar o comportamento do chat, ou adicionar em um arquivo genérico de instruções do projeto e mencionar o arquivo no chat (ex: `@workspace`).

---

## 🛠 Skills Disponíveis

### 1. [Especialista em Baixa Complexidade](./low-complexity-expert/SKILL.md)
Escreve e revisa código com orçamento de complexidade mensurável: pontos ICP (CDD) por unidade, aninhamento máximo de 2 níveis, early returns e eliminação de `if/else` encadeado e `switch`. Traz tabela de contagem de ICP, catálogo sintoma→técnica, exemplos antes/depois e formato de saída para os modos *escrever* e *revisar*.

### 2. [Especialista Financeiro Didático](./financial-specialist/SKILL.md)
Produz verbetes de dicionário, respostas de FAQ e explicações de conceito sobre investimentos para leitores iniciantes. Traz método de construção de analogia, "matemática de padaria", templates de saída por tipo de entregável e **guardrails de compliance** (sem recomendação de compra/venda, sem promessa de rentabilidade, sem taxa inventada).

### 3. [Professor Didático Progressivo](./didactic-teacher/SKILL.md)
Faz o agente explicar qualquer assunto em **quatro camadas progressivas** — intuição sem jargão → mecanismo → prática → nível avançado (trade-offs, internals, divergências da comunidade). Simplifica a linguagem, nunca o conteúdo. As camadas 3 e 4 são especializadas por domínio (**técnico** e **financeiro**), e no modo financeiro herda os guardrails de compliance da skill acima. Inclui calibragem de profundidade para não transformar dúvida factual em aula, e a regra "resposta antes da aula" quando você está travado.

> As duas skills financeiras se complementam: `didactic-teacher` explica **para você entender**; `financial-specialist` escreve **para o usuário final do seu produto**.

---

## ✅ Padrão de qualidade das skills

Toda skill deste repositório segue o mesmo contrato — use-o como gabarito ao criar novas:

| Elemento | Por que é obrigatório |
|---|---|
| `name` em kebab-case, igual ao nome da pasta | Requisito de carregamento no Claude Code e no Antigravity |
| `description` com **o que faz + quando usar** (gatilhos explícitos) | É o único texto que o agente lê para decidir se ativa a skill |
| Escopo positivo e negativo | Evita a skill vazar para contextos onde ela piora o resultado |
| Critérios mensuráveis (limites numéricos) | Regra subjetiva não é verificável pelo modelo |
| Processo ordenado | Encadeamento de pensamento reduz variância |
| Formato de saída explícito | Maior causa de resultado inconsistente quando ausente |
| Ao menos um exemplo de referência | Few-shot ancora o padrão de qualidade |
| Checklist de autoverificação | Faz o modelo revisar antes de entregar |
| Guardrails inegociáveis, quando o domínio exigir | Conteúdo financeiro, jurídico ou de saúde precisa de limites duros |

---

*Repositório preparado para centralizar o conhecimento de seus agentes! Você pode adicionar novas pastas no mesmo formato à medida que criar novos prompts/skills.*
