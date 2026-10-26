"""Cobertura do plano: prova que a página carrega todo o texto do plano, no lugar e na ordem.

Relê o plano linha a linha, sem usar o parser de blocos de extract_plan, e quebra em
pedaços de conteúdo (cada linha de parágrafo, item de lista, célula de tabela, linha
de código, título), cada um marcado com a unidade a que pertence. Confere nas duas pontas:

- `missing_in_data`: o pedaço está nos dados extraídos (pega bug do extract_plan);
- `rendered_pieces`: a forma que o pedaço toma no texto da página depois do md() do
  template, com a unidade e o tipo; check_page.cjs procura cada um dentro da unidade
  certa e na ordem do plano (pega bug do template).

Derivado de `coverage.py` da skill plan-review de Dávilos Tavares
(github.com/davilos/skills, CC BY 4.0). Alterado: unidades por `##`/`###` de qualquer
plano, Markdown inline ampliado (link, itálico, tachado) e citações.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from extract_plan import (FENCE_RE, HEADING_RE, HR_RE, LIST_RE, QUOTE_RE, STATUS_RE, TASK_RE,
                          IdAllocator, read_lines, slugify, split_row)

SEPARATOR = re.compile(r"\|?[\s:\-|]+\|?")

# Mesmo recorte do md() do template: código, imagem e link são tokens atômicos;
# negrito, tachado e itálico só valem no texto fora deles.
TOKEN = re.compile(r"`([^`]+)`|!\[([^\]]*)\]\(([^)]+)\)|\[([^\]]+)\]\(([^)]+)\)")
BOLD = re.compile(r"\*\*(?=\S)(.+?)\*\*")
STRIKE = re.compile(r"~~(?=\S)(.+?)~~")
# re.ASCII: o `\w` do JavaScript não reconhece acento; sem isso `café_x_` divergiria da página.
ITAL_STAR = re.compile(r"(^|[^*\w])\*(?=\S)([^*]+?)\*(?![*\w])", re.ASCII)
ITAL_UNDER = re.compile(r"(^|[^\w])_(?=\S)([^_]+?)_(?!\w)", re.ASCII)

# Markdown que o md() não desenha: a página mostra o texto cru, sem perder conteúdo.
UNSUPPORTED = [
    (re.compile(r"<[a-zA-Z/][^>]*>"), "HTML"),
    (re.compile(r"\[[^\]]+\]\[[^\]]*\]"), "link por referência [texto][id]"),
    (re.compile(r"\[\^[^\]]+\]"), "nota de rodapé [^n]"),
    (re.compile(r"^\s*(=+|-+)\s*$"), "título sublinhado (setext)"),
]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _fmt_plain(t: str) -> str:
    t = BOLD.sub(r"\1", t)
    t = STRIKE.sub(r"\1", t)
    t = ITAL_STAR.sub(r"\1\2", t)
    return ITAL_UNDER.sub(r"\1\2", t)


def rendered_form(piece: str) -> str:
    """O texto que um pedaço vira na página (textContent depois do md())."""
    out, pos = [], 0
    for m in TOKEN.finditer(piece):
        out.append(_fmt_plain(piece[pos:m.start()]))
        if m.group(1) is not None:
            out.append(m.group(1))
        elif m.group(3) is not None:
            out.append(m.group(2))
        else:
            out.append(_fmt_plain(m.group(4)))
        pos = m.end()
    out.append(_fmt_plain(piece[pos:]))
    return norm("".join(out))


def plan_pieces(plan_path: Path) -> list[dict]:
    """Todo o conteúdo do plano: {line, sec, kind, text}; kind `th` = título ou cabeçalho de tabela."""
    out: list[dict] = []
    ids = IdAllocator()
    fence = None
    sec, parent, title_seen, first_sec, status_seen = "header", None, False, False, False
    table_row = 0
    for i, line in enumerate(read_lines(plan_path), 1):
        s = line.strip()

        def add(text: str, kind: str = "text") -> None:
            if text.strip():
                out.append({"line": i, "sec": sec, "kind": kind, "text": text.strip()})

        if not s.startswith("|"):
            table_row = 0
        f = FENCE_RE.match(line)
        if fence:
            if f and s.startswith(fence):
                fence = None
            else:
                add(s)
            continue
        if f:
            fence = f.group(1)
            continue
        if not s or (HR_RE.match(line) and not LIST_RE.match(line)) or (s.startswith("|") and SEPARATOR.fullmatch(s)):
            continue
        h = HEADING_RE.match(s)
        if h and len(h.group(1)) == 1 and not title_seen and not first_sec:
            title_seen = True
            sec = "header"
            add(h.group(2))
            continue
        if h and len(h.group(1)) == 2:
            first_sec = True
            sec = parent = ids.take(slugify(h.group(2)))
            add(h.group(2), "th")
            continue
        if h and len(h.group(1)) == 3:
            if parent is None:
                parent = "introducao"
                first_sec = True
            sec = ids.take(f"{parent}--{slugify(h.group(2))}")
            add(h.group(2), "th")
            continue
        if not first_sec:
            st = STATUS_RE.match(s)
            if st and not status_seen:
                status_seen = True
                if st.group(1).strip():
                    out.append({"line": i, "sec": "header", "kind": "status", "text": st.group(1).strip()})
                continue
            sec = "introducao"
        if h:
            add(h.group(2))
            continue
        if s.startswith("|"):
            table_row += 1
            for c in split_row(s):
                add(c, "th" if table_row == 1 else "text")
            continue
        q = QUOTE_RE.match(line)
        if q:
            add(q.group(1).lstrip("> "))
            continue
        m = LIST_RE.match(line)
        if m:
            text = m.group(3)
            t = TASK_RE.match(text)
            add(t.group(2) if t else text)
            continue
        add(s)
    return out


def missing_in_data(plan_path: Path, data: dict) -> list[tuple[int, str]]:
    flat = norm(json.dumps(data, ensure_ascii=False).replace('\\"', '"').replace("\\\\", "\\"))
    return [(p["line"], p["text"]) for p in plan_pieces(plan_path) if norm(p["text"]) not in flat]


def rendered_pieces(plan_path: Path) -> list[list]:
    """[linha, unidade, tipo, texto renderizado] na ordem do plano."""
    out = []
    for p in plan_pieces(plan_path):
        text = rendered_form(p["text"])
        if text:
            out.append([p["line"], p["sec"], "text" if p["kind"] == "status" else p["kind"], text])
    return out


def unsupported_markdown(plan_path: Path) -> list[tuple[int, str]]:
    found, fence = [], None
    for i, line in enumerate(read_lines(plan_path), 1):
        f = FENCE_RE.match(line)
        if fence:
            if f and line.strip().startswith(fence):
                fence = None
            continue
        if f:
            fence = f.group(1)
            continue
        code_free = re.sub(r"`[^`]*`", "", line)
        for rx, name in UNSUPPORTED:
            if rx.search(code_free) and not (name.startswith("título") and HR_RE.match(line)):
                found.append((i, name))
    return found
