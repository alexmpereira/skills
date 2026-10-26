#!/usr/bin/env python3
"""Monta a página HTML de revisão de um plano: plano .md + .review.json + template.

Valida o .review.json contra o plano e contra o código antes de montar. Erro (saída 1)
quando a página afirmaria algo falso ou esconderia parte do plano; aviso quando ela só
fica mais pobre.

Prova também a cobertura: todo pedaço do plano precisa estar nos dados da página
(coverage.py), e a página carrega a lista para o check_page.cjs procurar cada um no
texto renderizado. E carimba a versão: hash do plano e hora da montagem no topo.

Uso:
    python3 build_page.py <plano.md> --out <arquivo.html>
        [--data <arquivo .review.json>]   (padrão: ao lado do plano, <nome>.review.json)
        [--root <raiz do projeto>]        (padrão: diretório atual; base dos caminhos em `onde`)
    python3 build_page.py <plano.md> --mark-published
        (depois de publicar: grava no .review.json o hash do plano que foi ao ar)

Derivado de `build_page.py` da skill plan-review de Dávilos Tavares
(github.com/davilos/skills, CC BY 4.0). Alterado: qualquer plano Markdown, anotações
por unidade (onde / leitura / risco) no lugar de changes/flow/impact/landing,
conferência de arquivo e linha no disco, pedidos de ajuste e mensagens em português.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True  # sem __pycache__ dentro da pasta da skill
sys.path.insert(0, str(Path(__file__).resolve().parent))
from coverage import missing_in_data, rendered_pieces, unsupported_markdown  # noqa: E402
from extract_plan import extract, fingerprints, plan_hash, units, utf8_stdio  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.html"
KNOWN_KEYS = {"title", "artifact_url", "code_ref", "tags", "review", "notes",
              "published_plan_hash", "published_at", "published_fingerprints"}
STATES = ("validated", "changes")
NOTE_FIELDS = ("onde", "leitura", "risco")
LEITURA_MAX = 400
# Item de `onde`: arquivo com linhas opcionais (`src/a.php:10-20,31`) ou pasta terminada em `/`.
WHERE_ITEM = re.compile(r"(?P<path>[\w.@+{}\-/]+?)(?::(?P<lines>\d+(?:[-–]\d+)?(?:,\d+(?:[-–]\d+)?)*))?")


def sidecar_path(plan_path: Path) -> Path:
    return plan_path.with_name(plan_path.stem + ".review.json")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def as_script_json(data) -> str:
    # `</` fecharia o <script>; U+2028/2029 quebram string de JS antigo.
    return (json.dumps(data, ensure_ascii=False)
            .replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def check_where(label: str, where: str, root: Path) -> list[str]:
    """`onde` só aceita referência de código que existe: arquivo (e linhas dentro dele) ou pasta."""
    errors = []
    for item in [x.strip() for x in re.split(r"\s*·\s*", where) if x.strip()]:
        m = WHERE_ITEM.fullmatch(item)
        if not m:
            errors.append(f"{label}.onde tem texto que não é referência de código: {item!r}; "
                          "use arquivo[:linhas] ou pasta/ separados por ' · ' e leve a explicação para `leitura`")
            continue
        rel = m["path"]
        if rel.startswith("/") or re.match(r"^[A-Za-z]:", rel) or ".." in rel.split("/"):
            errors.append(f"{label}.onde usa caminho absoluto ou fora do projeto: {rel!r}; use caminho relativo à raiz")
            continue
        target = root / rel
        if rel.endswith("/"):
            if not target.is_dir():
                errors.append(f"{label}.onde cita a pasta {rel!r}, que não existe em {root}")
            continue
        if not target.is_file():
            errors.append(f"{label}.onde cita {rel!r}, que não existe em {root} (nunca invente arquivo)")
            continue
        if m["lines"]:
            total = line_count(target)
            nums = [int(n) for n in re.findall(r"\d+", m["lines"])]
            over = [n for n in nums if n < 1 or n > total]
            if over:
                errors.append(f"{label}.onde cita {rel}:{m['lines']}, mas o arquivo tem {total} linhas "
                              "(nunca invente número de linha; na dúvida, cite só o arquivo)")
    return errors


def validate(plan: dict, pg: dict, root: Path) -> tuple[list[str], list[str]]:
    errors, warns = [], []
    keys = {u["key"] for u in units(plan)}
    if not plan["has_title"]:
        warns.append("o plano não tem título `# ...`: a página usa o nome do arquivo")
    for k in sorted(set(pg) - KNOWN_KEYS):
        warns.append(f"campo {k!r} não é usado pela página (veja references/review-json.md)")
    title = pg.get("title") or ""
    if title and not 2 <= len(title.split()) <= 4:
        warns.append(f"title = {title!r}: use de 2 a 4 palavras, estável entre publicações")

    for i, t in enumerate(pg.get("tags") or []):
        if not isinstance(t, dict) or not t.get("text"):
            errors.append(f"tags[{i}] precisa ser {{\"text\": ..., \"warn\": opcional}}")

    for key, r in (pg.get("review") or {}).items():
        if key not in keys:
            errors.append(f"review.{key}: não é seção nem subseção do plano atual "
                          "(título renomeado? decida com o usuário se a validação ainda vale e remova a chave)")
            continue
        if not isinstance(r, dict) or r.get("state") not in STATES:
            errors.append(f"review.{key} precisa ser {{\"state\": \"validated\" | \"changes\", ...}}")
        elif r["state"] == "changes" and not (r.get("note") or "").strip():
            warns.append(f"review.{key}: ajuste pedido sem `note`; a página não diz o que ajustar")

    for key, n in (pg.get("notes") or {}).items():
        label = f"notes.{key}"
        if key not in keys:
            errors.append(f"{label}: não é seção nem subseção do plano atual")
            continue
        if not isinstance(n, dict) or not any((n.get(f) or "").strip() for f in ("leitura", "risco")):
            errors.append(f"{label} precisa de `leitura` ou `risco` (`onde` sozinho não explica nada)")
            continue
        for f in set(n) - set(NOTE_FIELDS):
            warns.append(f"{label}.{f} não é usado pela página (campos: onde, leitura, risco)")
        if len(n.get("leitura") or "") > LEITURA_MAX:
            warns.append(f"{label}.leitura tem {len(n['leitura'])} caracteres; até {LEITURA_MAX} (uma ou duas frases)")
        if n.get("onde"):
            errors += check_where(label, n["onde"], root)
    return errors, warns


def staleness(plan: dict, pg: dict) -> tuple[dict, list[str]]:
    """O que mudou no plano desde a validação (por unidade) e desde a publicação (anotações)."""
    now = fingerprints(plan)
    names = {u["key"]: u["name"] for u in units(plan)}
    published = pg.get("published_fingerprints") or {}
    stale_notes, lines = {}, []
    for key, r in (pg.get("review") or {}).items():
        if key not in now or not isinstance(r, dict):
            continue
        changed = bool(r.get("fp")) and r["fp"] != now[key]
        if r.get("state") == "validated" and changed:
            lines.append(f"  RECHECK {key}: validada em outro texto; o revisor precisa validar de novo")
        if r.get("state") == "changes":
            tag = "texto já mudou desde o pedido; confirme com o revisor se foi atendido" if changed else "em aberto"
            lines.append(f"  AJUSTE  {key} ({names[key]}), {tag}: {(r.get('note') or '').strip()[:160]}")
    for key in (pg.get("notes") or {}):
        if key in published and key in now and published[key] != now[key]:
            stale_notes[key] = True
            lines.append(f"  RECHECK notes.{key}: o texto dessa unidade mudou desde a publicação; releia o código e a anotação")
    return stale_notes, lines


def display_path(plan_path: Path, root: Path) -> str:
    try:
        return plan_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return plan_path.name


def mark_published(plan_path: Path, pg_path: Path) -> int:
    pg = load_json(pg_path) if pg_path.exists() else {}
    now = fingerprints(extract(plan_path))
    pg["published_plan_hash"] = plan_hash(plan_path)
    pg["published_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    pg["published_fingerprints"] = now
    # Validação marcada à mão (sem fp) passa a valer para o texto atual; as que já têm fp
    # guardam o texto que o revisor viu e nunca são recalculadas aqui.
    for key, r in (pg.get("review") or {}).items():
        if isinstance(r, dict) and key in now and not r.get("fp"):
            r["fp"] = now[key]
    save_json(pg_path, pg)
    print(f"build_page: {pg_path} marcado como publicado (plano {pg['published_plan_hash']})")
    return 0


def main() -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("plan", help="caminho do plano .md")
    ap.add_argument("--data", help="caminho do .review.json (padrão: ao lado do plano)")
    ap.add_argument("--root", default=".", help="raiz do projeto, base dos caminhos em `onde`")
    ap.add_argument("--out", help="arquivo HTML de saída")
    ap.add_argument("--mark-published", action="store_true",
                    help="grava no .review.json o hash do plano que acabou de ir ao ar")
    args = ap.parse_args()
    if not args.out and not args.mark_published:
        ap.error("passe --out <arquivo.html> ou --mark-published")

    plan_path, root = Path(args.plan), Path(args.root)
    pg_path = Path(args.data) if args.data else sidecar_path(plan_path)
    if not plan_path.is_file():
        print(f"build_page: {plan_path} não encontrado", file=sys.stderr)
        return 1
    if args.mark_published:
        return mark_published(plan_path, pg_path)

    pg = {}
    if pg_path.exists():
        pg = load_json(pg_path)
    else:
        print(f"  WARN  {pg_path} não existe: página só com o texto do plano, sem anotações nem estado", file=sys.stderr)

    current = plan_hash(plan_path)
    published = pg.get("published_plan_hash")
    if published and published != current:
        print(f"  STALE a página publicada ({pg.get('artifact_url') or 'sem link'}) é do plano {published}; "
              f"o plano atual é {current}: monte e publique de novo", file=sys.stderr)

    plan = extract(plan_path)
    plan["path"] = display_path(plan_path, root)
    plan["hash"] = current
    plan["generated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    errors, warns = validate(plan, pg, root)
    # Cobertura, ponta 1: todo pedaço do plano está nos dados extraídos.
    for line, piece in missing_in_data(plan_path, plan):
        errors.append(f"cobertura: {plan_path.name}:{line} não chegou aos dados da página: {piece[:80]!r}")
    # Ponta 2 vai dentro da página: o check_page.cjs procura cada pedaço no texto renderizado.
    plan["coverage"] = rendered_pieces(plan_path)
    for line, what in unsupported_markdown(plan_path):
        warns.append(f"{plan_path.name}:{line} usa {what}, que a página mostra como texto cru")
    plan["stale_notes"], stale_lines = staleness(plan, pg)
    plan["fingerprints"] = fingerprints(plan)

    for w in warns:
        print(f"  WARN  {w}", file=sys.stderr)
    for s in stale_lines:
        print(s, file=sys.stderr)
    for e in errors:
        print(f"  ERROR {e}", file=sys.stderr)
    if errors:
        print(f"build_page: {len(errors)} erro(s); página não montada", file=sys.stderr)
        return 1

    title = pg.get("title") or plan["title"]
    html = (TEMPLATE.read_text(encoding="utf-8")
            .replace("__TITLE__", title.replace("&", "&amp;").replace("<", "&lt;"))
            .replace("__PLAN_JSON__", as_script_json(plan))
            .replace("__PAGE_DATA_JSON__", as_script_json(pg)))
    Path(args.out).write_text(html, encoding="utf-8")
    n_units = len(units(plan))
    print(f"build_page: {args.out} ({len(plan['sections'])} seções, {n_units} unidades revisáveis, "
          f"{len(pg.get('notes') or {})} anotações, {len(plan['coverage'])} pedaços do plano cobertos, "
          f"plano {current}, {len(warns)} aviso(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
