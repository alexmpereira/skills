#!/usr/bin/env python3
"""Lê um plano em Markdown e imprime a estrutura que a página espelha, em JSON.

É a parte mecânica da página: título, linha `**Status**:`, seções `##`, subseções
`###` e os blocos de cada uma (parágrafo, lista, tabela, código, citação, título
`####`). Nada aqui interpreta o plano; a leitura do código (Onde / Leitura / Risco)
vem do arquivo `.review.json` que o agente escreve.

Uso:
    python3 extract_plan.py <plano.md> [--out plano.json]

Derivado de `extract_plan.py` da skill plan-review de Dávilos Tavares
(github.com/davilos/skills, CC BY 4.0). Alterado: aceita qualquer plano Markdown
(não só o formato tlc-spec-lean), subseções `###` viram unidades revisáveis,
listas aninhadas, citações e `####` viram blocos, e os ids são slugs dos títulos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

# Ids que não podem sair de um título: `header` é o cabeçalho da página e
# `introducao` o texto entre o título e o primeiro `##`.
RESERVED_IDS = ("header", "introducao")
INTRO_NAME = "Introdução"

FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
TASK_RE = re.compile(r"^\[([ xX])\]\s+(.*)$")
HR_RE = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
STATUS_RE = re.compile(r"^\*\*Status(?:\*\*:|:\*\*)\s*(.*)$")
QUOTE_RE = re.compile(r"^\s*>\s?(.*)$")


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8-sig").splitlines()


def slugify(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")
    return slug[:48].strip("-") or "secao"


class IdAllocator:
    """Ids únicos e determinísticos: o segundo `## Riscos` vira `riscos-2`."""

    def __init__(self) -> None:
        self.used = set(RESERVED_IDS)

    def take(self, base: str) -> str:
        cand, n = base, 2
        while cand in self.used:
            cand, n = f"{base}-{n}", n + 1
        self.used.add(cand)
        return cand


def split_row(line: str) -> list[str]:
    """Quebra uma linha de tabela sem cortar um `|` dentro de crases."""
    cells, buf, in_code, i = [], [], False, 0
    s = line.strip()
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            buf.append("|")
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    cells.append("".join(buf))
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return [c.strip() for c in cells]


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells)


def indent_of(line: str) -> int:
    return len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip())


def parse_list(lines: list[str], i: int) -> tuple[dict, int]:
    """Lista com aninhamento: cada item guarda a profundidade em vez de virar árvore."""
    items: list[dict] = []
    stack: list[int] = []
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            nxt = next((k for k in range(i + 1, len(lines)) if lines[k].strip()), None)
            if nxt is None or not (LIST_RE.match(lines[nxt]) or (items and indent_of(lines[nxt]) > 0 and not FENCE_RE.match(lines[nxt]))):
                break
            i += 1
            continue
        if FENCE_RE.match(line) or HEADING_RE.match(line.strip()) and not line.startswith((" ", "\t")):
            break
        m = LIST_RE.match(line)
        if m:
            ind = indent_of(line)
            while stack and ind < stack[-1]:
                stack.pop()
            if not stack or ind > stack[-1]:
                stack.append(ind)
            marker, text = m.group(2), m.group(3)
            item = {"depth": len(stack) - 1, "ordered": marker[0].isdigit()}
            if item["ordered"]:
                item["n"] = marker
            t = TASK_RE.match(text)
            if t:
                item["task"] = t.group(1).lower()
                text = t.group(2)
            item["text"] = text.strip()
            items.append(item)
            i += 1
            continue
        if items and indent_of(line) > 0:
            items[-1]["text"] += " " + line.strip()
            i += 1
            continue
        break
    return {"type": "list", "items": items}, i


def parse_blocks(lines: list[str]) -> list[dict]:
    """Blocos de uma seção, na ordem do plano: p, list, table, code, quote, h."""
    blocks: list[dict] = []
    para: list[str] = []
    i = 0

    def flush_para() -> None:
        nonlocal para
        if para:
            blocks.append({"type": "p", "text": " ".join(x.strip() for x in para)})
            para = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush_para()
            i += 1
            continue
        fence = FENCE_RE.match(line)
        if fence:
            flush_para()
            mark = fence.group(1)
            lang = stripped[len(mark):].strip()
            body = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(mark):
                body.append(lines[i])
                i += 1
            blocks.append({"type": "code", "lang": lang, "text": "\n".join(body)})
            i += 1
            continue
        if HR_RE.match(line) and not LIST_RE.match(line):
            flush_para()
            i += 1
            continue
        h = HEADING_RE.match(stripped)
        if h:
            flush_para()
            blocks.append({"type": "h", "level": len(h.group(1)), "text": h.group(2)})
            i += 1
            continue
        if stripped.startswith("|"):
            flush_para()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            header = rows[0] if rows else []
            body_rows = [r for r in rows[1:] if not is_separator(r)]
            blocks.append({"type": "table", "header": header, "rows": body_rows})
            continue
        if QUOTE_RE.match(line):
            flush_para()
            quoted = []
            while i < len(lines) and QUOTE_RE.match(lines[i]):
                quoted.append(QUOTE_RE.match(lines[i]).group(1).lstrip("> ").strip())
                i += 1
            blocks.append({"type": "quote", "text": " ".join(q for q in quoted if q)})
            continue
        if LIST_RE.match(line):
            flush_para()
            block, i = parse_list(lines, i)
            blocks.append(block)
            continue
        para.append(line)
        i += 1
    flush_para()
    return blocks


def split_sections(lines: list[str]) -> tuple[str, str, list[str], list[dict]]:
    """Separa título, Status, preâmbulo e seções `##` (com `###` dentro), ignorando `#` em código."""
    title, status = "", ""
    title_seen = status_seen = False
    preamble: list[str] = []
    sections: list[dict] = []
    ids = IdAllocator()
    cur_sec = cur_sub = None
    in_code = False
    for line in lines:
        if FENCE_RE.match(line):
            in_code = not in_code
        h = None if in_code or FENCE_RE.match(line) else HEADING_RE.match(line)
        if h and len(h.group(1)) == 1 and not title_seen and cur_sec is None:
            title, title_seen = h.group(2), True
            continue
        if h and len(h.group(1)) == 2:
            cur_sec = {"id": ids.take(slugify(h.group(2))), "name": h.group(2), "lines": [], "subs": []}
            cur_sub = None
            sections.append(cur_sec)
            continue
        if h and len(h.group(1)) == 3:
            if cur_sec is None:
                cur_sec = {"id": "introducao", "name": INTRO_NAME, "lines": preamble, "subs": [], "intro": True}
                sections.append(cur_sec)
            cur_sub = {"id": ids.take(f"{cur_sec['id']}--{slugify(h.group(2))}"), "name": h.group(2), "lines": []}
            cur_sec["subs"].append(cur_sub)
            continue
        if cur_sec is None:
            m = STATUS_RE.match(line.strip())
            if m and not status_seen and not in_code:
                status, status_seen = m.group(1).strip(), True
                continue
            preamble.append(line)
            continue
        (cur_sub or cur_sec)["lines"].append(line)
    return title, status, preamble, sections


def extract(plan_path: Path) -> dict:
    title, status, preamble, sections = split_sections(read_lines(plan_path))
    result = []
    has_intro = any(s.get("intro") for s in sections)
    if not has_intro and parse_blocks(preamble):
        result.append({"id": "introducao", "name": INTRO_NAME, "intro": True, "blocks": parse_blocks(preamble), "subs": []})
    for s in sections:
        out = {"id": s["id"], "name": s["name"], "blocks": parse_blocks(s["lines"]),
               "subs": [{"id": x["id"], "name": x["name"], "blocks": parse_blocks(x["lines"])} for x in s["subs"]]}
        if s.get("intro"):
            out["intro"] = True
        result.append(out)
    return {"path": str(plan_path), "title": title or plan_path.stem, "has_title": bool(title),
            "status": status, "sections": result}


def is_unit(section: dict) -> bool:
    """Seção revisável: tem texto próprio, ou não tem subseções. Uma seção só com `###` é um grupo."""
    return bool(section["blocks"]) or not section["subs"]


def units(plan: dict) -> list[dict]:
    """Tudo que o revisor valida, na ordem do plano: seções e subseções."""
    out = []
    for s in plan["sections"]:
        if is_unit(s):
            out.append({"key": s["id"], "name": s["name"], "blocks": s["blocks"]})
        for x in s["subs"]:
            out.append({"key": x["id"], "name": x["name"], "blocks": x["blocks"], "parent": s["name"]})
    return out


def _h(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


def fingerprints(plan: dict) -> dict[str, str]:
    """Impressão digital do texto de cada unidade: muda quando o texto validado muda."""
    return {u["key"]: _h([u["name"], u["blocks"]]) for u in units(plan)}


def plan_hash(plan_path: Path) -> str:
    return hashlib.sha256(plan_path.read_bytes()).hexdigest()[:12]


def utf8_stdio() -> None:
    """Console do Windows em cp1252 quebra no primeiro acento."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def main() -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("plan", help="caminho do plano .md")
    ap.add_argument("--out", help="grava o JSON neste arquivo em vez de imprimir")
    args = ap.parse_args()
    plan = Path(args.plan)
    if not plan.is_file():
        print(f"extract_plan: {plan} não encontrado", file=sys.stderr)
        return 1
    payload = json.dumps(extract(plan), ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
