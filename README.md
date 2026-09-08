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

O Claude Code aceita instruções personalizadas via um arquivo `CLAUDE.md` na raiz de qualquer repositório.

1. Escolha a skill desejada.
2. Copie apenas o texto das regras (ignorando o cabeçalho YAML inicial se houver).
3. Cole o conteúdo no arquivo `CLAUDE.md` na raiz do seu projeto. 
   - Sempre que o Claude Code interagir no projeto, ele lerá essas instruções para seguir suas diretrizes.

### 3. GitHub Copilot / ChatGPT / Claude Web

Para essas ferramentas baseadas em chat web ou IDE (como Copilot Chat), você usa o recurso de **Custom Instructions** (Instruções Customizadas) ou **System Prompt**.

1. Abra as configurações da sua ferramenta preferida (ex: *Settings > Custom Instructions* no ChatGPT ou as definições de sistema no console da API do Claude/OpenAI).
2. Cole o conteúdo da skill no campo onde você configura como a IA deve agir e responder.
3. No **GitHub Copilot** (VS Code, IntelliJ, etc.), você pode adicionar essas instruções no arquivo de configuração do seu Workspace/Settings para ditar o comportamento do chat, ou adicionar em um arquivo genérico de instruções do projeto e mencionar o arquivo no chat (ex: `@workspace`).

---

## 🛠 Skills Disponíveis

### 1. [Especialista em Baixa Complexidade](./low-complexity-expert/SKILL.md)
Garante que todo código gerado ou revisado priorize a baixa complexidade cognitiva e ciclomática. Ensina o agente a evitar switches enormes, aplicar early returns e manter os princípios de Clean Architecture.

### 2. [Especialista Financeiro Didático](./financial_specialist/SKILL.md)
Especialista Financeiro para criação de textos didáticos, analogias e conteúdo para o Dicionário/FAQ de investimentos. Focado em explicações acessíveis, didática de professor e matemática de padaria.

---

*Repositório preparado para centralizar o conhecimento de seus agentes! Você pode adicionar novas pastas no mesmo formato à medida que criar novos prompts/skills.*
