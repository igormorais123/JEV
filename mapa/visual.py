"""Gera MAPA.html: o grafo do repositório para ver e explorar no navegador.

Um arquivo só, com os dados embutidos (abre direto do disco, sem servidor). Arquivos, conceitos do estudo e,
se ligado, funções; filtros por tipo de nó e de ligação, busca, modo foco na vizinhança e painel com tudo
sobre o nó escolhido. Chamado por gerar_mapa.py depois de gravar grafo.json.
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path

GRUPO_DE_ARESTA = {'importa': 'importa', 'link': 'link', 'cita': 'cita', 'menciona': 'menciona', 'apoia-se em': 'apoia', 'usa': 'usa_s'}


def base_github(raiz: Path) -> str:
    try:
        url = subprocess.run(['git', 'remote', 'get-url', 'origin'], cwd=raiz, capture_output=True, text=True).stdout.strip()
    except OSError:
        return ''
    m = re.match(r'(?:https://github\.com/|git@github\.com:)([^/]+/[^/.]+)', url)
    return f'https://github.com/{m.group(1)}/blob/main/' if m else ''


def curto(texto, limite=360):
    texto = ' '.join(str(texto).split())
    return texto if len(texto) <= limite else texto[:limite - 1] + '…'


def dados_compactos(grafo: dict) -> dict:
    nos, arestas = [], []
    for n in grafo['nos']:
        topo = n['id'].split('/')[0] if '/' in n['id'] else '(raiz)'
        nos.append({'id': n['id'], 'c': 'f', 'g': topo, 'l': n['id'].rsplit('/', 1)[-1], 'd': curto(n['descricao']),
                    'n': n.get('linhas'), 'b': n['bytes'], 't': n['tipo']})
    for c in grafo['conceitos']:
        atributos = {k: curto(v, 500) for k, v in c['atributos'].items() if isinstance(v, str)}
        listas = {k: [curto(x if isinstance(x, str) else x.get('titulo', ''), 200) for x in v][:6]
                  for k, v in c['atributos'].items() if isinstance(v, list)}
        nos.append({'id': c['id'], 'c': 'k', 'g': c['id'][0], 'l': c['id'], 'd': curto(c['titulo'], 200), 'a': atributos, 'm': listas,
                    'w': [[d['papel'], d['arquivo'], d.get('linha')] for d in c['definido_em']], 'p': f"{c['pagina']}#{c['id'].lower()}"})
    for s in grafo['simbolos']:
        nos.append({'id': s['id'], 'c': 's', 'g': s['arquivo'], 'l': s['nome'], 'd': f"{s['tipo']} em {s['arquivo']}:{s['linha']}", 'ln': s['linha']})
    usa_arquivo = Counter()
    for a in grafo['arestas']:
        tipo = a['tipo']
        grupo = GRUPO_DE_ARESTA.get(tipo, 'papel')
        arestas.append([a['de'], a['para'], grupo, a.get('peso') or 1, tipo])
        if tipo == 'usa':
            usa_arquivo[(a['de'], a['para'].split('::')[0])] += 1
    for (a, b), n in usa_arquivo.items():
        arestas.append([a, b, 'usa', n, 'usa'])
    return {'nos': nos, 'arestas': arestas, 'pastas': grafo['pastas']}


def gerar_html(grafo: dict, raiz: Path) -> str:
    dados = dados_compactos(grafo)
    dados['github'] = base_github(raiz)
    embutido = json.dumps(dados, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return MODELO.replace('/*DADOS*/', embutido)


MODELO = r'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mapa do JEV</title>
<style>
:root {
  --fundo: #f6f5f1; --painel: #ffffff; --tinta: #1d1f23; --suave: #5d6470; --linha: #e2e0da; --realce: #2f5bd3;
  --chip: #eef0f4; --sombra: 0 1px 2px rgba(0,0,0,.06), 0 4px 16px rgba(0,0,0,.05); --aresta: 30,35,45;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --fundo: #121418; --painel: #1b1e24; --tinta: #e7e9ee; --suave: #9aa3b2; --linha: #2c3039; --realce: #7ea2ff;
    --chip: #262a32; --sombra: 0 1px 2px rgba(0,0,0,.4); --aresta: 210,215,225;
  }
}
:root[data-theme="dark"] {
  --fundo: #121418; --painel: #1b1e24; --tinta: #e7e9ee; --suave: #9aa3b2; --linha: #2c3039; --realce: #7ea2ff;
  --chip: #262a32; --sombra: 0 1px 2px rgba(0,0,0,.4); --aresta: 210,215,225;
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; background: var(--fundo); color: var(--tinta);
  font: 14px/1.45 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
body { display: grid; grid-template-rows: auto 1fr; overflow: hidden; }
header { display: flex; gap: 12px; align-items: center; padding: 10px 16px; border-bottom: 1px solid var(--linha); background: var(--painel); flex-wrap: wrap; }
header h1 { font-size: 16px; margin: 0; font-weight: 650; white-space: nowrap; }
header .num { color: var(--suave); font-size: 12.5px; }
.busca { position: relative; flex: 1 1 260px; max-width: 520px; }
.busca input { width: 100%; padding: 7px 10px; border: 1px solid var(--linha); border-radius: 8px; background: var(--fundo); color: var(--tinta); font: inherit; }
.sugestoes { position: absolute; top: 100%; left: 0; right: 0; background: var(--painel); border: 1px solid var(--linha); border-radius: 8px;
  box-shadow: var(--sombra); max-height: 360px; overflow: auto; z-index: 20; display: none; margin-top: 4px; }
.sugestoes div { padding: 6px 10px; cursor: pointer; display: flex; gap: 8px; align-items: baseline; }
.sugestoes div:hover, .sugestoes div.ativa { background: var(--chip); }
.sugestoes small { color: var(--suave); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
button, .botao { font: inherit; font-size: 13px; padding: 6px 10px; border-radius: 8px; border: 1px solid var(--linha); background: var(--painel); color: var(--tinta); cursor: pointer; }
button:hover { border-color: var(--realce); }
button.ligado { background: var(--realce); color: #fff; border-color: var(--realce); }
main { display: grid; grid-template-columns: 250px 1fr 360px; min-height: 0; }
main.sem-detalhe { grid-template-columns: 250px 1fr 0; }
aside { background: var(--painel); overflow: auto; min-height: 0; }
#filtros { border-right: 1px solid var(--linha); padding: 12px 14px; }
#detalhe { border-left: 1px solid var(--linha); padding: 14px 16px; }
main.sem-detalhe #detalhe { display: none; }
h2 { font-size: 11.5px; letter-spacing: .06em; text-transform: uppercase; color: var(--suave); margin: 16px 0 6px; font-weight: 650; }
h2:first-child { margin-top: 0; }
label.op { display: flex; align-items: center; gap: 7px; padding: 2px 0; cursor: pointer; font-size: 13px; }
label.op .n { margin-left: auto; color: var(--suave); font-size: 12px; font-variant-numeric: tabular-nums; }
.bola { width: 10px; height: 10px; border-radius: 50%; flex: none; }
.losango { width: 9px; height: 9px; transform: rotate(45deg); flex: none; }
.traco { width: 16px; height: 0; border-top: 2px solid; flex: none; }
.traco.tracejado { border-top-style: dashed; }
.linha-botoes { display: flex; gap: 6px; flex-wrap: wrap; }
#tela { position: relative; min-width: 0; min-height: 0; }
canvas { display: block; width: 100%; height: 100%; cursor: grab; }
canvas.sobre { cursor: pointer; }
#dica { position: absolute; pointer-events: none; background: var(--painel); border: 1px solid var(--linha); border-radius: 8px; padding: 6px 9px;
  box-shadow: var(--sombra); font-size: 12.5px; max-width: 340px; display: none; z-index: 5; }
#dica b { display: block; }
#aviso { position: absolute; left: 12px; bottom: 12px; font-size: 12px; color: var(--suave); background: var(--painel); border: 1px solid var(--linha);
  padding: 5px 9px; border-radius: 8px; }
#detalhe .tipo { display: inline-block; font-size: 11.5px; padding: 2px 8px; border-radius: 99px; background: var(--chip); color: var(--suave); margin-bottom: 6px; }
#detalhe h3 { margin: 2px 0 6px; font-size: 17px; word-break: break-word; }
#detalhe p.desc { margin: 0 0 10px; }
#detalhe dl { margin: 0 0 8px; display: grid; grid-template-columns: max-content 1fr; gap: 3px 10px; font-size: 13px; }
#detalhe dt { color: var(--suave); }
#detalhe dd { margin: 0; word-break: break-word; }
#detalhe a { color: var(--realce); text-decoration: none; }
#detalhe a:hover { text-decoration: underline; }
.grupo-viz { margin: 10px 0; }
.grupo-viz summary { cursor: pointer; font-weight: 600; font-size: 13px; }
.grupo-viz ul { list-style: none; margin: 4px 0 0; padding: 0; }
.grupo-viz li { padding: 2px 0; font-size: 13px; display: flex; gap: 6px; align-items: baseline; }
.grupo-viz li span.id { cursor: pointer; color: var(--realce); word-break: break-all; }
.grupo-viz li small { color: var(--suave); }
.acoes { display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0 12px; }
.fechar { float: right; }
#menu { display: none; }
@media (max-width: 900px) {
  main, main.sem-detalhe { grid-template-columns: 1fr; grid-template-rows: 1fr; }
  #filtros { position: absolute; z-index: 10; top: 0; bottom: 0; left: 0; width: 270px; transform: translateX(-100%); transition: transform .2s; box-shadow: var(--sombra); }
  #filtros.aberto { transform: none; }
  #detalhe { position: absolute; z-index: 10; left: 0; right: 0; bottom: 0; max-height: 55%; border-left: 0; border-top: 1px solid var(--linha); box-shadow: var(--sombra); }
  main { position: relative; }
  #menu { display: inline-block; }
}
</style>
</head>
<body>
<header>
  <button id="menu" aria-label="Filtros">☰</button>
  <h1>Mapa do JEV</h1>
  <span class="num" id="numeros"></span>
  <div class="busca">
    <input id="busca" type="search" placeholder="Buscar arquivo, função, H012, R17, Q042, palavra…" autocomplete="off">
    <div class="sugestoes" id="sugestoes"></div>
  </div>
  <button id="tema" title="Alternar tema claro/escuro">◐</button>
</header>
<main class="sem-detalhe" id="principal">
  <aside id="filtros">
    <h2>Modo</h2>
    <div class="linha-botoes">
      <button id="modo-tudo" class="ligado">Tudo</button>
      <button id="modo-foco">Foco no escolhido</button>
    </div>
    <label class="op" style="margin-top:6px">Profundidade do foco
      <select id="profundidade" style="margin-left:auto"><option>1</option><option selected>2</option><option>3</option></select></label>
    <h2>Arquivos por pasta</h2>
    <div id="f-pastas"></div>
    <h2>Conceitos do estudo</h2>
    <div id="f-conceitos"></div>
    <label class="op"><input type="checkbox" id="f-simbolos"> <span class="bola" style="background:#9aa0aa"></span> Funções e classes <span class="n" id="n-simbolos"></span></label>
    <h2>Ligações</h2>
    <div id="f-arestas"></div>
    <h2>Ações</h2>
    <div class="linha-botoes">
      <button id="reorganizar">Reorganizar</button>
      <button id="centralizar">Enquadrar</button>
      <button id="rotulos">Rótulos: auto</button>
    </div>
    <p style="font-size:12px;color:var(--suave);margin-top:14px">Clique num ponto para ver tudo sobre ele. Role para aproximar, arraste para mover. Tamanho = número de ligações.</p>
  </aside>
  <section id="tela">
    <canvas id="c"></canvas>
    <div id="dica"></div>
    <div id="aviso"></div>
  </section>
  <aside id="detalhe"></aside>
</main>
<script id="dados" type="application/json">/*DADOS*/</script>
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<script>
const D = JSON.parse(document.getElementById('dados').textContent);
const $ = s => document.querySelector(s);
const TIPOS_C = {E: 'Experimentos', R: 'Rodadas', H: 'Hipóteses', Q: 'Perguntas', S: 'Sistemas', V: 'Revisões'};
const CORES_C = {E: '#d9480f', R: '#c2255c', H: '#7048e8', Q: '#1c7ed6', S: '#0ca678', V: '#e8590c'};
const PALETA = ['#8a6d3b', '#5c7cfa', '#20c997', '#f59f00', '#e64980', '#15aabf', '#74b816', '#be4bdb', '#fd7e14', '#4263eb', '#868e96', '#d6336c', '#0b7285', '#e67700', '#5f3dc4', '#2b8a3e'];
const ARESTAS = {
  importa: {nome: 'Import de código', cor: '#4c6ef5', ligado: true},
  usa: {nome: 'Usa função de outro arquivo', cor: '#12b886', ligado: true},
  link: {nome: 'Link entre documentos', cor: '#fab005', ligado: true, tracejado: true},
  papel: {nome: 'Papel no estudo (executa, prova…)', cor: '#e8590c', ligado: true},
  apoia: {nome: 'Apoia-se em (evidência)', cor: '#c2255c', ligado: true},
  cita: {nome: 'Citação entre arquivos', cor: '#adb5bd', ligado: false, tracejado: true},
  menciona: {nome: 'Menção a conceito', cor: '#ced4da', ligado: false, tracejado: true},
  usa_s: {nome: 'Arquivo → função usada', cor: '#12b886', ligado: true, soSimbolos: true},
};
const nos = D.nos, porId = new Map(nos.map(n => [n.id, n]));
const pastas = [...new Set(nos.filter(n => n.c === 'f').map(n => n.g))].sort();
const corPasta = Object.fromEntries(pastas.map((p, i) => [p, PALETA[i % PALETA.length]]));
const arestas = D.arestas.filter(a => porId.has(a[0]) && porId.has(a[1])).map(a => ({s: a[0], t: a[1], g: a[2], w: a[3], tipo: a[4]}));
// arquivo contém funções: liga o símbolo ao seu arquivo quando os símbolos aparecem
nos.filter(n => n.c === 's').forEach(n => arestas.push({s: n.g, t: n.id, g: 'contem', w: 1, tipo: 'contém'}));
const grau = new Map();
arestas.forEach(a => { if (a.g !== 'contem') { grau.set(a.s, (grau.get(a.s) || 0) + 1); grau.set(a.t, (grau.get(a.t) || 0) + 1); } });
nos.forEach(n => { n.grau = grau.get(n.id) || 0; n.r = n.c === 's' ? 2.5 : Math.max(3, Math.min(16, 2.5 + Math.sqrt(n.grau) * 1.25)); });
const vizinhos = new Map();
arestas.forEach(a => {
  if (!vizinhos.has(a.s)) vizinhos.set(a.s, []); if (!vizinhos.has(a.t)) vizinhos.set(a.t, []);
  vizinhos.get(a.s).push({o: a.t, a, sentido: 'sai'}); vizinhos.get(a.t).push({o: a.s, a, sentido: 'chega'});
});

const estado = {pastas: new Set(pastas), conceitos: new Set(Object.keys(TIPOS_C)), simbolos: false,
  arestas: new Set(Object.keys(ARESTAS).filter(k => ARESTAS[k].ligado)), modo: 'tudo', escolhido: null, sobre: null, rotulos: 'auto'};
try { const salvo = JSON.parse(localStorage.getItem('mapa-jev-filtros') || 'null');
  if (salvo) { estado.arestas = new Set(salvo.arestas); estado.simbolos = !!salvo.simbolos; } } catch (e) {}

function corNo(n) { return n.c === 'k' ? CORES_C[n.g] : n.c === 's' ? '#9aa0aa' : corPasta[n.g]; }
function rotuloTipo(n) {
  if (n.c === 'k') return TIPOS_C[n.g].replace(/s$/, '').replace('Hipótese', 'Hipótese').replace('Revisõe', 'Revisão');
  return n.c === 's' ? 'Função ou classe' : 'Arquivo · ' + n.g;
}

// ---------- filtros ----------
function opcao(pai, {id, texto, cor, forma, n, marcado, onchange, tracejado}) {
  const l = document.createElement('label'); l.className = 'op';
  const marca = forma === 'traco' ? `<span class="traco${tracejado ? ' tracejado' : ''}" style="border-color:${cor}"></span>` : `<span class="${forma}" style="background:${cor}"></span>`;
  l.innerHTML = `<input type="checkbox" ${marcado ? 'checked' : ''}> ${marca} <span>${texto}</span> <span class="n">${n ?? ''}</span>`;
  l.querySelector('input').addEventListener('change', e => onchange(e.target.checked));
  pai.appendChild(l);
}
const contaPasta = d3.rollup(nos.filter(n => n.c === 'f'), v => v.length, n => n.g);
pastas.forEach(p => opcao($('#f-pastas'), {texto: p, cor: corPasta[p], forma: 'bola', n: contaPasta.get(p), marcado: true,
  onchange: v => { v ? estado.pastas.add(p) : estado.pastas.delete(p); atualizar(); }}));
const contaC = d3.rollup(nos.filter(n => n.c === 'k'), v => v.length, n => n.g);
Object.entries(TIPOS_C).forEach(([k, t]) => opcao($('#f-conceitos'), {texto: t, cor: CORES_C[k], forma: 'losango', n: contaC.get(k), marcado: true,
  onchange: v => { v ? estado.conceitos.add(k) : estado.conceitos.delete(k); atualizar(); }}));
const contaA = d3.rollup(arestas, v => v.length, a => a.g);
Object.entries(ARESTAS).forEach(([k, e]) => opcao($('#f-arestas'), {texto: e.nome, cor: e.cor, forma: 'traco', tracejado: e.tracejado, n: contaA.get(k),
  marcado: estado.arestas.has(k), onchange: v => { v ? estado.arestas.add(k) : estado.arestas.delete(k); guardar(); atualizar(); }}));
$('#n-simbolos').textContent = nos.filter(n => n.c === 's').length;
$('#f-simbolos').checked = estado.simbolos;
$('#f-simbolos').addEventListener('change', e => { estado.simbolos = e.target.checked; guardar(); atualizar(); });
function guardar() { try { localStorage.setItem('mapa-jev-filtros', JSON.stringify({arestas: [...estado.arestas], simbolos: estado.simbolos})); } catch (e) {} }

// ---------- visibilidade ----------
function noPassa(n) {
  if (n.c === 'f') return estado.pastas.has(n.g);
  if (n.c === 'k') return estado.conceitos.has(n.g);
  return estado.simbolos && estado.pastas.has(n.g.includes('/') ? n.g.split('/')[0] : '(raiz)');
}
function arestaPassa(a) {
  if (a.g === 'contem') return estado.simbolos;
  if (a.g === 'usa_s') return estado.simbolos && estado.arestas.has('usa_s');
  if (a.g === 'usa' && estado.simbolos && estado.arestas.has('usa_s')) return false;
  return estado.arestas.has(a.g);
}
function visiveis() {
  let conj = new Set(nos.filter(noPassa).map(n => n.id));
  let ls = arestas.filter(a => arestaPassa(a) && conj.has(a.s) && conj.has(a.t));
  if (estado.modo === 'foco' && estado.escolhido) {
    const prof = +$('#profundidade').value, perto = new Set([estado.escolhido]);
    let fronteira = [estado.escolhido];
    const adj = new Map(); ls.forEach(a => { (adj.get(a.s) || adj.set(a.s, []).get(a.s)).push(a.t); (adj.get(a.t) || adj.set(a.t, []).get(a.t)).push(a.s); });
    for (let i = 0; i < prof; i++) { const prox = []; fronteira.forEach(x => (adj.get(x) || []).forEach(o => { if (!perto.has(o)) { perto.add(o); prox.push(o); } })); fronteira = prox; }
    conj = perto; ls = ls.filter(a => perto.has(a.s) && perto.has(a.t));
  }
  // o d3 troca source/target pelos objetos do nó: cada visão ganha ligações novas
  return {ns: nos.filter(n => conj.has(n.id)), ls: ls.map(a => ({source: a.s, target: a.t, g: a.g, w: a.w, tipo: a.tipo}))};
}

// ---------- desenho ----------
const canvas = $('#c'), ctx = canvas.getContext('2d');
let largura = 0, altura = 0, transformacao = d3.zoomIdentity, atuais = {ns: [], ls: []}, quad = null;
function medir() {
  const r = canvas.parentElement.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  largura = r.width; altura = r.height; canvas.width = largura * dpr; canvas.height = altura * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); desenhar();
}
// grupos ficam em regiões próprias: pastas num arco, conceitos em outro
const ancoras = {};
(function () {
  const grupos = [...pastas.map(p => 'f:' + p), ...Object.keys(TIPOS_C).map(k => 'k:' + k)];
  grupos.forEach((g, i) => { const ang = (i / grupos.length) * Math.PI * 2; ancoras[g] = [Math.cos(ang) * 520, Math.sin(ang) * 520]; });
})();
function ancoraDe(n) { return n.c === 's' ? null : ancoras[(n.c === 'f' ? 'f:' : 'k:') + n.g]; }
nos.forEach(n => { const a = ancoraDe(n) || [0, 0]; n.x = a[0] + (Math.random() - .5) * 200; n.y = a[1] + (Math.random() - .5) * 200; });

const sim = d3.forceSimulation().alphaDecay(0.03)
  .force('carga', d3.forceManyBody().strength(n => n.c === 's' ? -8 : -40 - n.grau * 0.6).distanceMax(600))
  .force('ligacao', d3.forceLink().id(n => n.id).distance(a => a.g === 'contem' ? 12 : a.g === 'menciona' || a.g === 'cita' ? 90 : 55)
    .strength(a => a.g === 'contem' ? 0.9 : a.g === 'menciona' || a.g === 'cita' ? 0.02 : 0.12))
  .force('colisao', d3.forceCollide(n => n.r + 1.5))
  .force('x', d3.forceX(n => { const a = ancoraDe(n); return a ? a[0] : 0; }).strength(n => n.c === 's' ? 0 : 0.035))
  .force('y', d3.forceY(n => { const a = ancoraDe(n); return a ? a[1] : 0; }).strength(n => n.c === 's' ? 0 : 0.035))
  .on('tick', () => { quad = null; desenhar(); });

function atualizar(reiniciar = true) {
  atuais = visiveis();
  sim.nodes(atuais.ns); sim.force('ligacao').links(atuais.ls);
  if (reiniciar) sim.alpha(0.5).restart();
  const nf = atuais.ns.filter(n => n.c === 'f').length, nk = atuais.ns.filter(n => n.c === 'k').length;
  $('#aviso').textContent = `${atuais.ns.length} pontos (${nf} arquivos, ${nk} conceitos) · ${atuais.ls.filter(a => a.g !== 'contem').length} ligações visíveis`
    + (estado.modo === 'foco' ? (estado.escolhido ? ` · foco em ${estado.escolhido}` : ' · escolha um ponto para focar') : '');
}

function destacados() {
  const alvo = estado.sobre || estado.escolhido;
  if (!alvo) return null;
  const s = new Set([alvo]); (vizinhos.get(alvo) || []).forEach(v => { if (arestaPassa(v.a)) s.add(v.o); });
  return s;
}
function desenhar() {
  ctx.save(); ctx.clearRect(0, 0, largura, altura);
  ctx.translate(transformacao.x, transformacao.y); ctx.scale(transformacao.k, transformacao.k);
  const dest = destacados(), k = transformacao.k, rgb = getComputedStyle(document.documentElement).getPropertyValue('--aresta').trim();
  for (const a of atuais.ls) {
    const e = ARESTAS[a.g] || {cor: '#999'}, ligada = dest && dest.has(a.source.id) && dest.has(a.target.id) && (a.source.id === (estado.sobre || estado.escolhido) || a.target.id === (estado.sobre || estado.escolhido));
    ctx.beginPath(); ctx.moveTo(a.source.x, a.source.y); ctx.lineTo(a.target.x, a.target.y);
    ctx.strokeStyle = ligada ? e.cor : dest ? `rgba(${rgb},0.04)` : hexAlfa(e.cor, a.g === 'menciona' || a.g === 'cita' ? 0.18 : 0.38);
    ctx.lineWidth = (ligada ? 1.8 : 0.8) / Math.sqrt(k);
    ctx.setLineDash(e.tracejado ? [4 / k, 3 / k] : []); ctx.stroke();
  }
  ctx.setLineDash([]);
  for (const n of atuais.ns) {
    const apagado = dest && !dest.has(n.id);
    ctx.globalAlpha = apagado ? 0.15 : 1; ctx.fillStyle = corNo(n); ctx.beginPath();
    if (n.c === 'k') { const r = n.r * 1.25; ctx.moveTo(n.x, n.y - r); ctx.lineTo(n.x + r, n.y); ctx.lineTo(n.x, n.y + r); ctx.lineTo(n.x - r, n.y); ctx.closePath(); }
    else ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
    ctx.fill();
    if (n.id === estado.escolhido) { ctx.lineWidth = 2.5 / k; ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--tinta'); ctx.stroke(); }
  }
  ctx.globalAlpha = 1;
  const tinta = getComputedStyle(document.documentElement).getPropertyValue('--tinta'), fundo = getComputedStyle(document.documentElement).getPropertyValue('--fundo');
  ctx.font = `${12 / k}px system-ui, sans-serif`; ctx.textBaseline = 'middle'; ctx.lineWidth = 3 / k; ctx.strokeStyle = fundo; ctx.fillStyle = tinta;
  // rótulos: os pontos mais ligados primeiro; um rótulo que colidiria com outro já posto fica de fora
  const ocupados = [], candidatos = atuais.ns.filter(n => (dest && dest.has(n.id)) || estado.rotulos === 'todos' || (estado.rotulos === 'auto' && n.grau > (k > 2.2 ? 0 : k > 1.3 ? 4 : 8)))
    .sort((a, b) => ((dest && dest.has(b.id)) - (dest && dest.has(a.id))) || b.grau - a.grau);
  for (const n of candidatos) {
    const forcar = dest && dest.has(n.id);
    const x = n.x + n.r + 3 / k, w = ctx.measureText(n.l).width, h = 13 / k;
    const caixa = [x, n.y - h / 2, x + w, n.y + h / 2];
    if (!forcar && estado.rotulos !== 'todos' && ocupados.some(o => caixa[0] < o[2] && caixa[2] > o[0] && caixa[1] < o[3] && caixa[3] > o[1])) continue;
    ocupados.push(caixa); ctx.strokeText(n.l, x, n.y); ctx.fillText(n.l, x, n.y);
  }
  ctx.restore();
}
function hexAlfa(hex, a) { const v = parseInt(hex.slice(1), 16); return `rgba(${v >> 16},${(v >> 8) & 255},${v & 255},${a})`; }

// ---------- interação ----------
const zoom = d3.zoom().scaleExtent([0.08, 8]).on('zoom', e => { transformacao = e.transform; desenhar(); });
d3.select(canvas).call(zoom).on('dblclick.zoom', null);
function noEm(px, py) {
  const [x, y] = transformacao.invert([px, py]);
  if (!quad) quad = d3.quadtree(atuais.ns, n => n.x, n => n.y);
  const n = quad.find(x, y, 20 / transformacao.k);
  return n && Math.hypot(n.x - x, n.y - y) <= n.r + 6 / transformacao.k ? n : null;
}
canvas.addEventListener('mousemove', e => {
  const r = canvas.getBoundingClientRect(), n = noEm(e.clientX - r.left, e.clientY - r.top);
  if ((n && n.id) !== estado.sobre) { estado.sobre = n ? n.id : null; desenhar(); }
  canvas.classList.toggle('sobre', !!n);
  const dica = $('#dica');
  if (n) { dica.style.display = 'block'; dica.style.left = Math.min(e.clientX - r.left + 14, largura - 350) + 'px'; dica.style.top = (e.clientY - r.top + 14) + 'px';
    dica.innerHTML = `<b>${esc(n.c === 'k' ? n.id + ' — ' + n.d : n.id)}</b>${n.c !== 'k' ? esc(n.d) : esc(rotuloTipo(n))}<br><small>${n.grau} ligações</small>`; }
  else dica.style.display = 'none';
});
canvas.addEventListener('mouseleave', () => { estado.sobre = null; $('#dica').style.display = 'none'; desenhar(); });
canvas.addEventListener('click', e => {
  const r = canvas.getBoundingClientRect(), n = noEm(e.clientX - r.left, e.clientY - r.top);
  if (n) escolher(n.id, false); else if (estado.modo !== 'foco') { estado.escolhido = null; mostrarDetalhe(null); desenhar(); }
});

function escolher(id, centralizar = true) {
  const n = porId.get(id); if (!n) return;
  if (n.c === 's' && !estado.simbolos) { estado.simbolos = true; $('#f-simbolos').checked = true; }
  if (n.c === 'f' && !estado.pastas.has(n.g)) { estado.pastas.add(n.g); }
  if (n.c === 'k' && !estado.conceitos.has(n.g)) { estado.conceitos.add(n.g); }
  estado.escolhido = id; mostrarDetalhe(n);
  if (estado.modo === 'foco') atualizar(); else if (!atuais.ns.includes(n)) atualizar();
  if (centralizar) setTimeout(() => { if (n.x != null) d3.select(canvas).transition().duration(500).call(zoom.transform, d3.zoomIdentity.translate(largura / 2, altura / 2).scale(Math.max(transformacao.k, 1.4)).translate(-n.x, -n.y)); }, estado.modo === 'foco' ? 400 : 0);
  desenhar();
  try { history.replaceState(null, '', '#' + encodeURIComponent(id)); } catch (e) {}
}
function esc(t) { return String(t ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c])); }
function linkArquivo(caminho, linha, texto) {
  const local = `<a href="${esc(caminho)}" target="_blank" rel="noopener">${esc(texto || caminho)}${linha ? ':' + linha : ''}</a>`;
  const gh = D.github ? ` · <a href="${esc(D.github + caminho)}${linha ? '#L' + linha : ''}" target="_blank" rel="noopener">GitHub</a>` : '';
  return local + gh;
}
const NOMES_ATRIB = {familia: 'família', veredito: 'veredito', medido: 'mediu', previsao: 'previsão', criterio: 'critério', fonte: 'fonte', natureza: 'natureza',
  detalhe: 'detalhe', resposta: 'resposta', fonte_da_resposta: 'origem', confianca: 'confiança', decide: 'decide', rodada_simples: 'rodada simples', teto: 'teto', rotulo_no_codigo: 'no código'};
function mostrarDetalhe(n) {
  const painel = $('#detalhe');
  $('#principal').classList.toggle('sem-detalhe', !n);
  if (!n) { painel.innerHTML = ''; setTimeout(medir, 0); return; }
  let h = `<button class="fechar" id="fechar" aria-label="Fechar">✕</button><span class="tipo" style="border-left:4px solid ${corNo(n)}">${esc(rotuloTipo(n))}</span>`;
  h += `<h3>${esc(n.id)}</h3><p class="desc">${esc(n.d)}</p>`;
  h += '<div class="acoes">';
  if (n.c === 'f') h += linkArquivo(n.id, null, 'Abrir arquivo');
  if (n.c === 's') h += linkArquivo(n.g, n.ln, 'Abrir no arquivo');
  if (n.c === 'k') h += `<a href="${esc(n.p)}" target="_blank">Página do conceito</a>`;
  h += ` <button id="focar">${estado.modo === 'foco' ? 'Sair do foco' : 'Focar vizinhança'}</button></div>`;
  const dl = [];
  if (n.c === 'f') { dl.push(['pasta', esc(n.id.includes('/') ? n.id.slice(0, n.id.lastIndexOf('/')) : '(raiz)')]); dl.push(['tamanho', n.n ? n.n + ' linhas' : (n.b / 1024).toFixed(0) + ' KB']); }
  if (n.a) Object.entries(n.a).forEach(([k, v]) => dl.push([NOMES_ATRIB[k] || k, esc(v)]));
  if (n.m) Object.entries(n.m).forEach(([k, v]) => dl.push([k, v.map(esc).join('<br>')]));
  if (n.w && n.w.length) dl.push(['onde está', n.w.map(([p, a, l]) => `${esc(p)}: ${linkArquivo(a, l, a)}`).join('<br>')]);
  dl.push(['ligações', n.grau]);
  h += '<dl>' + dl.map(([a, b]) => `<dt>${a}</dt><dd>${b}</dd>`).join('') + '</dl>';
  const grupos = {};
  (vizinhos.get(n.id) || []).forEach(v => {
    if (v.a.g === 'contem' && !estado.simbolos) return;
    const chave = (v.sentido === 'sai' ? '→ ' : '← ') + (v.a.tipo === 'usa' && v.a.g === 'usa' ? 'usa funções de' : v.a.tipo);
    (grupos[chave] = grupos[chave] || []).push(v);
  });
  const ordem = Object.keys(grupos).sort((a, b) => grupos[b].length - grupos[a].length);
  ordem.forEach((g, i) => {
    const lista = grupos[g].sort((a, b) => (b.a.w || 1) - (a.a.w || 1) || a.o.localeCompare(b.o));
    h += `<details class="grupo-viz" ${i < 4 ? 'open' : ''}><summary>${esc(g)} (${lista.length})</summary><ul>` +
      lista.slice(0, 80).map(v => { const o = porId.get(v.o); return `<li><span class="bola" style="background:${corNo(o)}"></span><span class="id" data-id="${esc(v.o)}">${esc(v.o)}</span>${v.a.w > 1 ? `<small>${v.a.w}×</small>` : ''}</li>`; }).join('') +
      (lista.length > 80 ? `<li><small>… e mais ${lista.length - 80}</small></li>` : '') + '</ul></details>';
  });
  painel.innerHTML = h;
  painel.querySelectorAll('span.id').forEach(s => s.addEventListener('click', () => escolher(s.dataset.id)));
  $('#fechar').addEventListener('click', () => { estado.escolhido = null; if (estado.modo === 'foco') definirModo('tudo'); mostrarDetalhe(null); desenhar(); });
  $('#focar').addEventListener('click', () => definirModo(estado.modo === 'foco' ? 'tudo' : 'foco'));
  setTimeout(medir, 0);
}
function definirModo(m) {
  estado.modo = m; $('#modo-tudo').classList.toggle('ligado', m === 'tudo'); $('#modo-foco').classList.toggle('ligado', m === 'foco');
  atualizar(); if (estado.escolhido) mostrarDetalhe(porId.get(estado.escolhido));
  setTimeout(enquadrar, m === 'foco' ? 700 : 0);
}
$('#modo-tudo').addEventListener('click', () => definirModo('tudo'));
$('#modo-foco').addEventListener('click', () => definirModo('foco'));
$('#profundidade').addEventListener('change', () => { if (estado.modo === 'foco') { atualizar(); setTimeout(enquadrar, 700); } });
$('#reorganizar').addEventListener('click', () => { atuais.ns.forEach(n => { const a = ancoraDe(n) || [0, 0]; n.x = a[0] + (Math.random() - .5) * 200; n.y = a[1] + (Math.random() - .5) * 200; }); sim.alpha(1).restart(); });
$('#centralizar').addEventListener('click', () => enquadrar());
$('#rotulos').addEventListener('click', e => { estado.rotulos = {auto: 'todos', todos: 'nenhum', nenhum: 'auto'}[estado.rotulos]; e.target.textContent = 'Rótulos: ' + estado.rotulos; desenhar(); });
function enquadrar(animar = true) {
  if (!atuais.ns.length) return;
  const xs = atuais.ns.map(n => n.x), ys = atuais.ns.map(n => n.y);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const k = Math.min(4, 0.9 / Math.max((x1 - x0 + 40) / largura, (y1 - y0 + 40) / altura));
  const alvo = d3.zoomIdentity.translate(largura / 2, altura / 2).scale(k).translate(-(x0 + x1) / 2, -(y0 + y1) / 2);
  animar ? d3.select(canvas).transition().duration(500).call(zoom.transform, alvo) : d3.select(canvas).call(zoom.transform, alvo);
}
$('#menu').addEventListener('click', () => $('#filtros').classList.toggle('aberto'));
$('#tema').addEventListener('click', () => {
  const atual = document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.dataset.theme = atual === 'dark' ? 'light' : 'dark';
  try { localStorage.setItem('mapa-jev-tema', document.documentElement.dataset.theme); } catch (e) {}
  desenhar();
});
try { const t = localStorage.getItem('mapa-jev-tema'); if (t) document.documentElement.dataset.theme = t; } catch (e) {}

// ---------- busca ----------
const normal = t => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
const indice = nos.map(n => [n, normal(n.id + ' ' + n.d + ' ' + (n.a ? Object.values(n.a).join(' ') : ''))]);
let marcada = -1, resultados = [];
function buscar(q) {
  const t = normal(q.trim()); if (!t) return [];
  const palavras = t.split(/\s+/);
  return indice.filter(([, s]) => palavras.every(p => s.includes(p))).map(([n]) => {
    const id = normal(n.id); let p = palavras.reduce((s, w) => s + (id.includes(w) ? 3 : 0) + (normal(n.l) === w ? 6 : 0), 0);
    p += n.c === 'k' ? 2 : n.c === 'f' ? 1 : 0; return [p, n];
  }).sort((a, b) => b[0] - a[0] || a[1].id.length - b[1].id.length).slice(0, 30).map(x => x[1]);
}
function listar() {
  const caixa = $('#sugestoes');
  caixa.innerHTML = resultados.map((n, i) => `<div data-i="${i}" class="${i === marcada ? 'ativa' : ''}"><span class="${n.c === 'k' ? 'losango' : 'bola'}" style="background:${corNo(n)}"></span><span>${esc(n.c === 's' ? n.l : n.id)}</span><small>${esc(n.c === 's' ? n.g : n.d)}</small></div>`).join('');
  caixa.style.display = resultados.length ? 'block' : 'none';
  caixa.querySelectorAll('div').forEach(d => d.addEventListener('mousedown', ev => { ev.preventDefault(); ir(resultados[+d.dataset.i]); }));
}
function ir(n) { if (!n) return; $('#sugestoes').style.display = 'none'; $('#busca').blur(); escolher(n.id); }
$('#busca').addEventListener('input', e => { resultados = buscar(e.target.value); marcada = resultados.length ? 0 : -1; listar(); });
$('#busca').addEventListener('keydown', e => {
  if (e.key === 'ArrowDown') { marcada = Math.min(marcada + 1, resultados.length - 1); listar(); e.preventDefault(); }
  else if (e.key === 'ArrowUp') { marcada = Math.max(marcada - 1, 0); listar(); e.preventDefault(); }
  else if (e.key === 'Enter') ir(resultados[marcada]);
  else if (e.key === 'Escape') { $('#sugestoes').style.display = 'none'; }
});
$('#busca').addEventListener('blur', () => setTimeout(() => $('#sugestoes').style.display = 'none', 150));
document.addEventListener('keydown', e => { if (e.key === '/' && document.activeElement !== $('#busca')) { e.preventDefault(); $('#busca').focus(); } });

// ---------- início ----------
const nf = nos.filter(n => n.c === 'f').length, nk = nos.filter(n => n.c === 'k').length;
$('#numeros').textContent = `${nf} arquivos · ${nk} conceitos · ${nos.length - nf - nk} funções · ${D.arestas.length} ligações`;
window.addEventListener('resize', medir);
// a primeira disposição é calculada antes de aparecer, para a tela abrir parada e enquadrada
medir(); atualizar(false); sim.stop();
for (let i = 0; i < 320; i++) sim.tick();
enquadrar(false); sim.alpha(0.02).restart();
const inicial = decodeURIComponent(location.hash.slice(1));
if (inicial && porId.has(inicial)) setTimeout(() => escolher(inicial), 100);
</script>
</body>
</html>
'''
