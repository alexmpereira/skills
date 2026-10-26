#!/usr/bin/env node
/*
 * Carrega a página gerada num DOM simulado e confere que ela mostra o plano inteiro.
 * Uso: node check_page.cjs <pagina.html> [caminho do jsdom]
 *   jsdom: o caminho explícito, se passado (relativo à pasta atual); senão, o que
 *   `require("jsdom")` achar a partir da pasta atual. Se não achar, instale num lugar
 *   descartável: npm install --prefix <pasta tmp> jsdom, e passe <pasta tmp>/node_modules/jsdom.
 * Sai com 1 em erro de execução ou se faltar seção, subseção, anotação ou pedaço do plano; 2 em uso errado.
 *
 * Derivado de `check_page.cjs` da skill plan-review de Dávilos Tavares
 * (github.com/davilos/skills, CC BY 4.0). Alterado: unidades por seção/subseção de
 * qualquer plano Markdown, pedidos de ajuste e mensagens em português.
 */
const fs = require('fs')
const path = require('path')
const [htmlPath, jsdomPath] = process.argv.slice(2)
if (!htmlPath) {
  console.error('uso: node check_page.cjs <pagina.html> [caminho do jsdom]')
  process.exit(2)
}
function loadJsdom() {
  if (jsdomPath) return require(path.resolve(process.cwd(), jsdomPath))
  try {
    return require(require.resolve('jsdom', { paths: [process.cwd()] }))
  } catch (_e) {
    try {
      return require('jsdom')
    } catch (_e2) {
      console.error(
        'check_page: jsdom não encontrado a partir de ' + process.cwd() + '.\n' +
          'Instale num lugar descartável e passe o caminho:\n' +
          '  npm install --prefix <pasta tmp> jsdom\n' +
          '  node check_page.cjs <pagina.html> <pasta tmp>/node_modules/jsdom',
      )
      process.exit(2)
    }
  }
}
const jsdom = loadJsdom()
const html = fs.readFileSync(htmlPath, 'utf8')

function open(beforeParse) {
  const errs = []
  const vc = new jsdom.VirtualConsole().on('jsdomError', (e) => errs.push(e.message))
  const dom = new jsdom.JSDOM('<!doctype html><html><body>' + html + '</body></html>', {
    runScripts: 'dangerously',
    virtualConsole: vc,
    beforeParse,
  })
  return { w: dom.window, d: dom.window.document, errs }
}

const fail = []
const expected = {}
const { w, d, errs } = open()
const data = w.__PLAN_PAGE__
if (!data) fail.push('a página não expôs window.__PLAN_PAGE__ (o script quebrou antes?)')
const q = (s) => d.querySelectorAll(s).length

function unitsOf(P) {
  const out = []
  for (const s of P.sections) {
    if (s.blocks.length || !s.subs.length) out.push(s.id)
    for (const x of s.subs) out.push(x.id)
  }
  return out
}

if (data) {
  const P = data.PLAN
  const G = data.PAGE_DATA || {}
  const units = unitsOf(P)
  const want = {
    sections: P.sections.length,
    subsections: P.sections.reduce((n, s) => n + s.subs.length, 0),
    reviewSlots: units.length,
    notes: Object.keys(G.notes || {}).length,
  }
  const got = {
    sections: q('section.sec'),
    subsections: q('.sub'),
    reviewSlots: q('[data-rk]'),
    notes: q('.anota'),
  }
  for (const k of Object.keys(want)) {
    if (want[k] !== got[k]) fail.push(`${k}: esperado ${want[k]}, a página mostra ${got[k]}`)
    expected[k] = want[k]
  }
  if (q('.toc a') !== P.sections.length + want.subsections)
    fail.push(`índice: esperado ${P.sections.length + want.subsections} links, a página mostra ${q('.toc a')}`)

  // Todo link interno (#secao, #secao--sub) precisa de alvo.
  const broken = [...d.querySelectorAll('a[href^="#"]')]
    .map((a) => a.getAttribute('href'))
    .filter((h) => h.length > 1 && !d.getElementById(h.slice(1)))
  if (broken.length) fail.push('links internos sem alvo: ' + [...new Set(broken)].join(', '))

  // Cobertura, ponta 2: cada pedaço do plano aparece no texto da sua unidade e na ordem do plano.
  // O texto de uma seção não inclui as subseções, as anotações do agente nem os pedidos de ajuste:
  // um pedaço achado ali não provaria que o plano está na página.
  const flat = (el) => (el ? el.textContent.replace(/\s+/g, ' ') : '')
  const textOf = (id) => {
    if (id === 'header') return flat(d.querySelector('header.head'))
    const el = d.getElementById(id)
    if (!el) return null
    const copy = el.cloneNode(true)
    copy.querySelectorAll('.sub, .anota, .rv, .rv-note, .rv-form').forEach((x) => x.remove())
    return flat(copy)
  }
  const cov = P.coverage || []
  if (!cov.length) fail.push('a página não tem a lista de cobertura (montada por um build antigo?)')
  const cursor = {}
  const texts = {}
  let shown = 0
  const problems = []
  for (const [line, sec, kind, piece] of cov) {
    if (!(sec in texts)) texts[sec] = textOf(sec)
    const t = texts[sec]
    if (t == null) {
      problems.push(`linha ${line}: a unidade ${sec} não existe na página`)
      continue
    }
    if (kind === 'th') {
      if (t.includes(piece)) shown++
      else problems.push(`linha ${line} não aparece em ${sec}: ${JSON.stringify(piece.slice(0, 80))}`)
      continue
    }
    const at = t.indexOf(piece, cursor[sec] || 0)
    if (at === -1) {
      problems.push(
        t.includes(piece)
          ? `linha ${line} aparece fora da ordem do plano em ${sec}: ${JSON.stringify(piece.slice(0, 80))}`
          : `linha ${line} não aparece em ${sec}: ${JSON.stringify(piece.slice(0, 80))}`,
      )
      continue
    }
    cursor[sec] = at + piece.length
    shown++
  }
  for (const p of problems.slice(0, 10)) fail.push('cobertura: ' + p)
  if (problems.length > 10) fail.push(`cobertura: mais ${problems.length - 10} problema(s)`)
  expected.planCoverage = `${shown}/${cov.length} (na unidade certa e na ordem)`
  if (!P.hash) fail.push('a página não carrega o hash do plano')
  const visible = flat(d.querySelector('.page'))
  if (/\$\d/.test(visible)) fail.push('sobrou um $N literal no texto (substituição com grupo errado)')
}

// Revisão pela página: roda de novo com um window.claude falso (db + user) e exercita o fluxo.
async function checkReviewFlow() {
  const store = {}
  const writes = []
  let listener = null
  const snap = () => ({ docs: Object.keys(store).map((id) => ({ id, exists: true, data: () => store[id] })) })
  const fakeDb = {
    collection: () => ({
      onSnapshot: (next) => {
        listener = next
        setTimeout(() => next(snap()), 0)
        return () => {}
      },
    }),
    doc: (p) => ({
      set: (body) => {
        writes.push({ path: p, data: body })
        store[p.split('/')[1]] = body
        if (listener) listener(snap())
        return Promise.resolve()
      },
    }),
  }
  const fakeUser = { canEdit: async () => true, id: async () => 'u_teste' }
  const page = open((win) => {
    win.claude = { use: async (n) => (n === 'db' ? fakeDb : n === 'user' ? fakeUser : null) }
  })
  const d2 = page.d
  const P2 = page.w.__PLAN_PAGE__.PLAN
  const tick = () => new Promise((r) => setTimeout(r, 20))
  await tick()
  await tick()
  const out = []
  const keys = unitsOf(P2)
  const key = keys[0]
  const badge = (k) => (d2.querySelector(`[data-rk="${k}"] .badge`) || { textContent: '(sem selo)' }).textContent
  const last = () => writes[writes.length - 1] || { path: '', data: {} }
  // Clica no botão da ação; se ele não existe, registra a falha em vez de quebrar o verificador.
  const click = async (k, act, label) => {
    const b = d2.querySelector(`[data-key="${k}"][data-act="${act}"]`)
    if (!b) {
      out.push(`revisão: o botão "${label}" não aparece em ${k} quando deveria`)
      return false
    }
    b.click()
    await tick()
    return true
  }
  if (!(await click(key, 'validate', 'Validar'))) return { out, errs: page.errs, writes: writes.length }
  if (last().path !== 'review/' + key || last().data.state !== 'validated')
    out.push(`revisão: Validar não gravou review/${key} como validated`)
  else if (last().data.fp !== P2.fingerprints[key]) out.push('revisão: a impressão digital gravada não é a do texto atual')
  if (badge(key) !== 'validada') out.push(`revisão: depois de validar, o selo diz "${badge(key)}"`)
  if (await click(key, 'undo', 'Desfazer')) {
    if (last().data.state !== 'pending') out.push('revisão: Desfazer não gravou pending')
    if (badge(key) !== 'não revisada') out.push(`revisão: depois de desfazer, o selo diz "${badge(key)}"`)
  }

  // Pedido de ajuste: abre o formulário, recusa vazio, grava a nota e mostra o pedido.
  await click(key, 'ask', 'Pedir ajuste')
  const form = d2.querySelector(`[data-rk-form="${key}"]`)
  if (!form || form.hidden) out.push('revisão: Pedir ajuste não abriu o formulário')
  else {
    const before = writes.length
    await click(key, 'send', 'Enviar pedido')
    if (writes.length !== before) out.push('revisão: um pedido vazio foi gravado')
    if (form.hidden) out.push('revisão: o formulário fechou ao recusar um pedido vazio')
    form.querySelector('textarea').value = 'Faltou dizer como reverter a migração.'
    await click(key, 'send', 'Enviar pedido')
    if (last().data.state !== 'changes' || last().data.note !== 'Faltou dizer como reverter a migração.')
      out.push('revisão: Enviar pedido não gravou state changes com a nota')
    if (badge(key) !== 'ajuste pedido') out.push(`revisão: depois do pedido, o selo diz "${badge(key)}"`)
    const nt = d2.querySelector(`[data-rk-note="${key}"]`)
    if (!nt || nt.hidden || !nt.textContent.includes('reverter a migração')) out.push('revisão: a nota do pedido não aparece na unidade')
    if (!d2.querySelector('#rail-req a[href="#' + key + '"]')) out.push('revisão: o pedido não aparece em "Ajustes pedidos" no painel')
  }

  // Validação feita num texto antigo: impressão digital diferente da atual.
  const other = keys[keys.length - 1]
  if (!listener) {
    out.push('revisão: a página não assinou a coleção review (onSnapshot)')
    return { out, errs: page.errs, writes: writes.length }
  }
  store[other] = { state: 'validated', fp: 'impressao-antiga', at: '2026-01-01T00:00:00Z' }
  listener(snap())
  await tick()
  if (!/mudou desde então/.test(badge(other))) out.push(`revisão: validação de texto antigo aparece como "${badge(other)}"`)

  // Nota vinda do registro é dado de terceiro: nunca vira HTML.
  store[key] = { state: 'changes', note: '<img src=x onerror=alert(1)>', fp: P2.fingerprints[key] }
  listener(snap())
  await tick()
  if (d2.querySelector(`[data-rk-note="${key}"] img`)) out.push('revisão: a nota do pedido foi interpretada como HTML')
  return { out, errs: page.errs, writes: writes.length }
}

;(async () => {
  if (data) {
    const r = await checkReviewFlow()
    for (const m of r.out) fail.push(m)
    for (const e of r.errs) fail.push('erro de execução (com db falso): ' + e)
    expected.reviewFlow = r.out.length ? 'falhou' : `ok (${r.writes} gravações simuladas)`
  }
  for (const e of errs) fail.push('erro de execução: ' + e)
  console.log(JSON.stringify({ ok: fail.length === 0, expected, fail }, null, 2))
  process.exit(fail.length ? 1 : 0)
})()
