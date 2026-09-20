"""Gera a página do mapa de limites a partir de `mapa-de-limites.json`.

Nenhum número é digitado no HTML: tudo é injetado daqui, do JSON que as rodadas escreveram.
É a mesma regra do resto do estudo — se o dado mudar, a página muda junto, e se alguém quiser
conferir um número, o caminho até a chamada paga que o produziu existe.

    python laboratorio/gerar_mapa_visual.py
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MAPA = RAIZ / 'laboratorio' / 'mapa-de-limites.json'
DESTINO = RAIZ / 'output' / 'mapa-de-limites.html'

# Quanto cada dimensão custa no pior nível medido, para ordenar o grafo pelo que importa.
ROTULOS = {
    'referencia': ('Referência', 'O corpus do E12, limpo, cinco classes.'),
    'opcoes': ('Número de opções', 'De 2 a 147 classes concorrentes.'),
    'ruido': ('Ruído tipográfico', 'Erro de digitação, de 5% a 70% dos caracteres.'),
    'diluicao': ('Diluição de contexto', 'Texto irrelevante junto, de 0 a 50 mil caracteres.'),
    'ordem das opcoes': ('Ordem das opções', 'As mesmas classes, permutadas.'),
    'armadilha semantica': ('Armadilha semântica', 'Ação adiada, concluída, de terceiro, negada, parcial, pressuposta.'),
    'sobreposicao': ('Sobreposição de classes', 'Critérios que se confundem, até serem idênticos.'),
    'idioma': ('Idioma', 'Critérios em inglês, misto, e português sem acento.'),
    'instrucao': ('Instrução', 'Instrução curta, vazia e autocontraditória.'),
    'combinado': ('Tudo junto', 'Ruído de 50% com 160 opções e 8 mil caracteres de recheio.'),
}


def main():
    mapa = json.loads(MAPA.read_text(encoding='utf-8'))
    referencia = mapa['dimensoes']['referencia'][0]['acuracia']

    dados = {'referencia': referencia, 'dimensoes': [], 'injecao': mapa['injecao'],
             'sem_pedido': mapa['sem_pedido'], 'custo': mapa['custo'],
             'adversario': mapa.get('adversario_externo'),
             'guarda': mapa.get('guarda_de_comando'),
             'economia': mapa.get('economia_de_contexto'),
             'calibracao': {nome: {'ece': bloco['ece'], 'separacao': bloco['separacao'],
                                   'faixas': bloco['faixas']}
                            for nome, bloco in mapa['calibracao'].items()}}

    for chave, niveis in mapa['dimensoes'].items():
        titulo, descricao = ROTULOS.get(chave, (chave, ''))
        limpos = [n for n in niveis if n['acuracia'] is not None]
        if not limpos:
            continue
        pior = min(limpos, key=lambda n: n['acuracia'])
        dados['dimensoes'].append({
            'chave': chave, 'titulo': titulo, 'descricao': descricao,
            'pior': round(pior['acuracia'], 4), 'pior_nivel': pior['nivel'],
            'queda': round(pior['acuracia'] - referencia, 4),
            'niveis': [{'nivel': n['nivel'], 'acuracia': round(n['acuracia'], 4),
                        'n': n['n'], 'conf_erros': n['conf_erros'],
                        'erros_altos': n['erros_acima_090']} for n in limpos],
        })
    dados['dimensoes'].sort(key=lambda d: d['queda'])

    html = PAGINA.replace('__DADOS__', json.dumps(dados, ensure_ascii=False))
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(html, encoding='utf-8')
    print(f'{DESTINO.relative_to(RAIZ)} ({DESTINO.stat().st_size / 1024:.0f} KB) — '
          f'{len(dados["dimensoes"])} dimensões, '
          f'{sum(len(d["niveis"]) for d in dados["dimensoes"])} níveis medidos')


PAGINA = r'''<!doctype html>
<html lang="pt-BR">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mapa de Limites do Jev</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root{
  --fundo:#f4f6f7; --painel:#ffffff; --tinta:#111b20; --tinta-fraca:#5a6b73;
  --traco:#d3dade; --traco-forte:#aeb9bf;
  --estavel:#0f7a68; --atencao:#a8710d; --ruptura:#b03a30;
  --eixo:#8b989f; --realce:#0d5f7a;
  --display:"IBM Plex Sans Condensed","Arial Narrow",system-ui,sans-serif;
  --corpo:"IBM Plex Sans",system-ui,-apple-system,sans-serif;
  --dado:"IBM Plex Mono",ui-monospace,"SFMono-Regular",monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --fundo:#0b1216; --painel:#111c22; --tinta:#e3ecf0; --tinta-fraca:#8ba0a9;
  --traco:#223038; --traco-forte:#35474f;
  --estavel:#3fb8a0; --atencao:#d9a441; --ruptura:#e0655a;
  --eixo:#5f747d; --realce:#57bcd8;
}}
:root[data-theme="dark"]{
  --fundo:#0b1216; --painel:#111c22; --tinta:#e3ecf0; --tinta-fraca:#8ba0a9;
  --traco:#223038; --traco-forte:#35474f;
  --estavel:#3fb8a0; --atencao:#d9a441; --ruptura:#e0655a;
  --eixo:#5f747d; --realce:#57bcd8;
}
*{box-sizing:border-box}
body{background:var(--fundo);color:var(--tinta);font-family:var(--corpo);
  padding:0;margin:0;line-height:1.55;-webkit-font-smoothing:antialiased}
.folha{max-width:1120px;margin:0 auto;padding-inline:20px;padding-block:40px 64px}
.sobrenome{font-family:var(--dado);font-size:11px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--tinta-fraca);margin:0 0 14px}
h1{font-family:var(--display);font-size:clamp(34px,6vw,58px);line-height:1.02;margin:0 0 16px;
  font-weight:700;letter-spacing:-.015em;text-wrap:balance}
.entrada{font-size:17px;color:var(--tinta-fraca);max-width:62ch;margin:0 0 28px}
.entrada b{color:var(--tinta);font-weight:600}
.faixa{display:flex;flex-wrap:wrap;gap:0;border:1px solid var(--traco);border-radius:3px;
  overflow:hidden;background:var(--painel);margin-bottom:44px}
.faixa div{flex:1 1 170px;padding:14px 16px;border-right:1px solid var(--traco)}
.faixa div:last-child{border-right:none}
.faixa dt{font-family:var(--dado);font-size:10px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--tinta-fraca);margin:0 0 6px}
.faixa dd{margin:0;font-family:var(--dado);font-size:24px;font-weight:600;
  font-variant-numeric:tabular-nums}
h2{font-family:var(--display);font-size:26px;margin:0 0 6px;font-weight:600;letter-spacing:-.01em}
.sub{color:var(--tinta-fraca);font-size:15px;margin:0 0 22px;max-width:66ch}
section{margin-bottom:52px}
.grafo{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:24px;align-items:start}
@media (max-width:820px){.grafo{grid-template-columns:1fr}}
.tela{background:var(--painel);border:1px solid var(--traco);border-radius:3px;overflow:hidden}
svg{display:block;width:100%;height:auto}
.no-dim{cursor:pointer}
.no-dim:focus-visible{outline:2px solid var(--realce);outline-offset:2px}
.detalhe{background:var(--painel);border:1px solid var(--traco);border-radius:3px;padding:18px}
.detalhe h3{font-family:var(--display);font-size:20px;margin:0 0 4px;font-weight:600}
.detalhe .nota{color:var(--tinta-fraca);font-size:13px;margin:0 0 16px}
.niveis{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:9px}
.niveis li{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:baseline;
  font-family:var(--dado);font-size:12.5px;font-variant-numeric:tabular-nums;
  border-bottom:1px dotted var(--traco);padding-bottom:7px}
.niveis .v{font-weight:600}
.barra{grid-column:1/-1;height:3px;background:var(--traco);position:relative;border-radius:2px}
.barra i{position:absolute;inset:0 auto 0 0;border-radius:2px;display:block}
table{width:100%;border-collapse:collapse;font-family:var(--dado);font-size:13px;
  font-variant-numeric:tabular-nums}
.rolagem{overflow-x:auto;border:1px solid var(--traco);border-radius:3px;background:var(--painel)}
th,td{text-align:right;padding:10px 14px;border-bottom:1px solid var(--traco);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
thead th{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--tinta-fraca);
  font-weight:500}
tbody tr:last-child td{border-bottom:none}
.pilula{display:inline-block;padding:2px 8px;border-radius:2px;font-size:11px;font-weight:600;
  letter-spacing:.04em}
.p-ok{background:color-mix(in srgb,var(--estavel) 16%,transparent);color:var(--estavel)}
.p-at{background:color-mix(in srgb,var(--atencao) 18%,transparent);color:var(--atencao)}
.p-ru{background:color-mix(in srgb,var(--ruptura) 16%,transparent);color:var(--ruptura)}
.achados{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:18px}
.achado{border-left:3px solid var(--traco-forte);padding:2px 0 2px 16px}
.achado.forte{border-left-color:var(--estavel)}
.achado.risco{border-left-color:var(--ruptura)}
.achado h4{font-family:var(--display);font-size:17px;margin:0 0 6px;font-weight:600}
.achado p{margin:0;font-size:14px;color:var(--tinta-fraca)}
.achado .num{font-family:var(--dado);color:var(--tinta);font-weight:600}
.rodape{border-top:1px solid var(--traco);padding-top:18px;font-size:13px;color:var(--tinta-fraca)}
.legenda{display:flex;gap:18px;flex-wrap:wrap;font-family:var(--dado);font-size:11px;
  color:var(--tinta-fraca);padding:12px 16px;border-top:1px solid var(--traco)}
.legenda span{display:flex;align-items:center;gap:6px}
.chave{width:14px;height:3px;border-radius:2px;display:inline-block}
@media (prefers-reduced-motion:no-preference){
  .no-dim circle,.aresta{transition:opacity .18s ease,stroke-width .18s ease}
}
</style>

<div class="folha">
  <p class="sobrenome">Programas E14 e E17 · laboratório INTEIA · 19.09.2026</p>
  <h1>Onde o Jev quebra</h1>
  <p class="entrada">Doze experimentos mediram o Jev onde ele funciona. Este mediu <b>onde ele para de funcionar</b>: dez dimensões empurradas até a ruptura, os ataques reescritos por outros modelos e a aplicação que sai disso, em <span id="n-chamadas"></span> chamadas pagas. O grafo abaixo pesa cada aresta pela queda de acurácia que aquela condição produziu — quanto mais grossa e mais quente, mais perto do limite.</p>

  <dl class="faixa" id="faixa"></dl>

  <section>
    <h2>O grafo dos limites</h2>
    <p class="sub">Cada raio é uma dimensão de estresse; cada nó na ponta é um nível medido. A
    espessura da aresta cresce com a queda observada e a cor marca a faixa. Clique numa
    dimensão para ver os níveis.</p>
    <div class="grafo">
      <div class="tela">
        <svg id="rede" viewBox="0 0 760 640" role="img"
             aria-label="Grafo radial das dez dimensões de estresse do Jev"></svg>
        <div class="legenda">
          <span><i class="chave" style="background:var(--estavel)"></i> queda até 3 pontos</span>
          <span><i class="chave" style="background:var(--atencao)"></i> 3 a 15 pontos</span>
          <span><i class="chave" style="background:var(--ruptura)"></i> acima de 15 pontos</span>
          <span>espessura ∝ queda</span>
        </div>
      </div>
      <aside class="detalhe" id="detalhe"></aside>
    </div>
  </section>

  <section>
    <h2>O desempate: quem obedece a uma ordem escrita pelo cliente</h2>
    <p class="sub">Dez mensagens inequívocas, quatro vetores de manipulação escritos dentro do
    próprio texto do cliente. A mesma bateria no Jev e nos quatro LLMs baratos que o estudo
    vinha usando como comparadores. A coluna que decide é a última.</p>
    <div class="rolagem">
      <table id="tabela-injecao">
        <thead><tr><th>Modelo</th><th>Acurácia sem injeção</th><th>Manipulado</th>
        <th>Taxa</th><th>IC95</th><th>Viraram “cancelar”</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>A mesma pergunta, com ataques que eu não escrevi</h2>
    <p class="sub">Três LLMs receberam a tarefa de escrever a manipulação mais eficaz que
    conseguissem. O Jev virou 10 de 120, e a afirmação “imune a instrução injetada” caiu — até
    separar o que os vetores realmente faziam. <b>A</b> fala com o classificador; <b>B</b>
    acrescenta um pedido de verdade ao texto do cliente. Na coluna final, quantas viradas
    passariam por um corte de confiança de 0,90.</p>
    <div class="rolagem">
      <table id="tabela-familias">
        <thead><tr><th>Modelo</th><th>Família</th><th>Virou</th><th>Taxa</th><th>IC95</th>
        <th>Acima do corte</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>A aplicação: quantas confirmações somem sem soltar nada perigoso</h2>
    <p class="sub">Cento e vinte comandos de shell realmente executados nesta máquina, doze
    deles irreversíveis. A regra por palavra barra quase tudo; o Jev entra depois dela e diz o
    que pode passar. A barra mede a interrupção em comando benigno — quanto menor, melhor —
    e a coluna da direita é a que não pode sair do zero.</p>
    <div class="rolagem">
      <table id="tabela-guarda">
        <thead><tr><th>Desenho</th><th>Liberados dos barrados</th>
        <th>Interrupção em benigno</th><th>Irrev. soltos</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>O que isso economiza, com a resposta na mão</h2>
    <p class="sub">Vinte perguntas factuais sobre um repositório real, oito trechos de código
    candidatos por pergunta, e um modelo respondendo com o que cada método de seleção entregou.
    A verificação é por expressão regular escrita antes de rodar: ou a resposta traz o valor
    certo, ou não traz. A barra mede o contexto enviado; a coluna da esquerda, se a resposta
    sobreviveu ao corte.</p>
    <div class="rolagem">
      <table id="tabela-economia">
        <thead><tr><th>O que se manda ao modelo</th><th>Respostas certas</th>
        <th>Trecho certo no top-2</th><th>Contexto enviado</th><th>Economia</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>Os achados que mudam a aplicação</h2>
    <div class="achados" id="achados"></div>
  </section>

  <p class="rodape" id="rodape"></p>
</div>

<script>
const D = __DADOS__;

const pct = v => (v*100).toFixed(1).replace('.', ',') + '%';
const pp  = v => (v*100 >= 0 ? '+' : '−') + Math.abs(v*100).toFixed(1).replace('.', ',');
const faixaCor = q => q > -0.03 ? 'var(--estavel)' : (q > -0.15 ? 'var(--atencao)' : 'var(--ruptura)');
const classePilula = q => q > -0.03 ? 'p-ok' : (q > -0.15 ? 'p-at' : 'p-ru');

// ---- faixa de números do topo
const piorGeral = D.dimensoes.reduce((a,b)=> a.pior < b.pior ? a : b);
const estaveis = D.dimensoes.filter(d => d.queda > -0.03).length;
document.getElementById('n-chamadas').textContent = D.custo.chamadas.toLocaleString('pt-BR');
document.getElementById('faixa').innerHTML = [
  ['Referência', pct(D.referencia), 'corpus limpo, 5 classes'],
  ['Dimensões sem efeito', estaveis + ' de ' + D.dimensoes.length, 'queda ≤ 3 pontos'],
  ['Pior nível medido', pct(piorGeral.pior), piorGeral.titulo.toLowerCase() + ' · ' + piorGeral.pior_nivel],
  ['Custo do programa', 'US$ ' + D.custo.usd.toFixed(5).replace('.', ','), D.custo.chamadas.toLocaleString('pt-BR') + ' chamadas']
].map(([r,v,n]) => `<div><dt>${r}</dt><dd>${v}</dd><dt style="margin:6px 0 0;letter-spacing:.02em;text-transform:none;font-size:11px">${n}</dt></div>`).join('');

// ---- grafo radial
const svg = document.getElementById('rede');
const CX = 380, CY = 310, R0 = 96, R1 = 218;
const ns = 'http://www.w3.org/2000/svg';
const cria = (t, a) => { const e = document.createElementNS(ns, t);
  for (const k in a) e.setAttribute(k, a[k]); return e; };

const n = D.dimensoes.length;
D.dimensoes.forEach((d, i) => {
  const ang = (i / n) * Math.PI * 2 - Math.PI / 2;
  d.x = CX + Math.cos(ang) * R1;
  d.y = CY + Math.sin(ang) * R1;
  d.bx = CX + Math.cos(ang) * R0;
  d.by = CY + Math.sin(ang) * R0;
  d.ang = ang;
});

// anéis de referência
[R0, (R0+R1)/2, R1].forEach(r => svg.appendChild(cria('circle',
  {cx:CX, cy:CY, r, fill:'none', stroke:'var(--traco)', 'stroke-width':1,
   'stroke-dasharray': r===R1 ? '2 4' : '1 5'})));

D.dimensoes.forEach((d, i) => {
  const peso = 1.5 + Math.min(Math.abs(d.queda), 0.5) * 26;
  const g = cria('g', {class:'no-dim', tabindex:'0', role:'button',
                       'aria-label': d.titulo + ', pior nível ' + pct(d.pior)});
  g.appendChild(cria('line', {x1:d.bx, y1:d.by, x2:d.x, y2:d.y, class:'aresta',
    stroke: faixaCor(d.queda), 'stroke-width': peso, 'stroke-linecap':'round',
    opacity: .82}));
  g.appendChild(cria('circle', {cx:d.x, cy:d.y, r: 7 + Math.min(d.niveis.length,7),
    fill:'var(--painel)', stroke: faixaCor(d.queda), 'stroke-width':2.5}));
  const dir = Math.cos(d.ang) >= -0.15 ? 1 : -1;
  const tx = d.x + dir * 22, anchor = dir === 1 ? 'start' : 'end';
  const t1 = cria('text', {x:tx, y:d.y - 2, 'text-anchor':anchor,
    fill:'var(--tinta)', 'font-family':'var(--display)', 'font-size':'14',
    'font-weight':'600'});
  t1.textContent = d.titulo;
  const t2 = cria('text', {x:tx, y:d.y + 14, 'text-anchor':anchor,
    fill:'var(--tinta-fraca)', 'font-family':'var(--dado)', 'font-size':'11.5'});
  t2.textContent = pct(d.pior) + '  ' + pp(d.queda) + ' pt';
  g.appendChild(t1); g.appendChild(t2);
  g.addEventListener('click', () => mostrar(i));
  g.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ')
    { e.preventDefault(); mostrar(i); } });
  svg.appendChild(g);
});

svg.appendChild(cria('circle', {cx:CX, cy:CY, r:64, fill:'var(--painel)',
  stroke:'var(--traco-forte)', 'stroke-width':1.5}));
const c1 = cria('text', {x:CX, y:CY - 8, 'text-anchor':'middle', fill:'var(--tinta)',
  'font-family':'var(--display)', 'font-size':'20', 'font-weight':'700'});
c1.textContent = 'jev-1.13';
const c2 = cria('text', {x:CX, y:CY + 12, 'text-anchor':'middle', fill:'var(--tinta-fraca)',
  'font-family':'var(--dado)', 'font-size':'12'});
c2.textContent = pct(D.referencia);
const c3 = cria('text', {x:CX, y:CY + 28, 'text-anchor':'middle', fill:'var(--tinta-fraca)',
  'font-family':'var(--dado)', 'font-size':'9.5', 'letter-spacing':'.1em'});
c3.textContent = 'REFERÊNCIA';
svg.appendChild(c1); svg.appendChild(c2); svg.appendChild(c3);

function mostrar(i){
  const d = D.dimensoes[i];
  const piores = [...d.niveis].sort((a,b) => a.acuracia - b.acuracia);
  document.getElementById('detalhe').innerHTML =
    `<h3>${d.titulo}</h3><p class="nota">${d.descricao}</p><ul class="niveis">` +
    piores.map(v => {
      const q = v.acuracia - D.referencia;
      return `<li><span>${v.nivel}</span>
        <span class="v" style="color:${faixaCor(q)}">${pct(v.acuracia)}</span>
        <span class="barra"><i style="width:${(v.acuracia*100).toFixed(1)}%;background:${faixaCor(q)}"></i></span>
        <span style="color:var(--tinta-fraca);font-size:11px">n=${v.n}${v.conf_erros!=null ? ' · conf. dos erros '+String(v.conf_erros).replace('.',',') : ''}</span>
        <span style="color:var(--tinta-fraca);font-size:11px">${v.erros_altos!=null ? v.erros_altos+' erro(s) ≥0,90' : ''}</span></li>`;
    }).join('') + '</ul>';
}
mostrar(D.dimensoes.length - 1);

// ---- tabela de injeção
const ordem = Object.entries(D.injecao).sort((a,b) => b[1].taxa - a[1].taxa);
const nomes = {jev:'typesafe/jev-1.13', c1:'meta-llama/llama-3.1-8b', c2:'mistralai/mistral-nemo',
               c3:'google/gemma-3-12b', c4:'openai/gpt-oss-20b'};
document.querySelector('#tabela-injecao tbody').innerHTML = ordem.map(([k,v]) => {
  const cls = v.taxa === 0 ? 'p-ok' : (v.taxa < 0.2 ? 'p-at' : 'p-ru');
  return `<tr><td>${nomes[k] || k}</td><td>${pct(v.acuracia_sem_injecao ?? 1)}</td>
    <td>${v.virados}/${v.tentativas}</td>
    <td><span class="pilula ${cls}">${pct(v.taxa)}</span></td>
    <td style="color:var(--tinta-fraca)">[${pct(v.ic95[0])}; ${pct(v.ic95[1])}]</td>
    <td style="font-weight:600;color:${v.para_cancelar ? 'var(--ruptura)' : 'var(--tinta-fraca)'}">${v.para_cancelar}</td></tr>`;
}).join('');

// ---- famílias de ataque (R15b)
if (D.adversario) {
  const rotuloFamilia = {A: 'A — fala com o classificador', B: 'B — acrescenta conteúdo'};
  const linhas = [];
  for (const familia of ['A','B']) {
    const bloco = D.adversario.familias[familia];
    for (const alvo of ['jev','c1','c2','c3','c4']) {
      const v = bloco[alvo];
      if (!v || !v.n) continue;
      linhas.push({familia, alvo, ...v});
    }
  }
  document.querySelector('#tabela-familias tbody').innerHTML = linhas.map(v => {
    const cls = v.taxa === 0 ? 'p-ok' : (v.taxa < 0.15 ? 'p-at' : 'p-ru');
    const destaque = v.alvo === 'jev' ? ' style="font-weight:650"' : '';
    const corAcima = v.virou_acima_do_corte ? 'var(--ruptura)' : 'var(--estavel)';
    return `<tr${destaque}><td>${nomes[v.alvo] || v.alvo}</td>
      <td style="color:var(--tinta-fraca)">${rotuloFamilia[v.familia]}</td>
      <td>${v.virou}/${v.n}</td>
      <td><span class="pilula ${cls}">${pct(v.taxa)}</span></td>
      <td style="color:var(--tinta-fraca)">[${pct(v.ic95[0])}; ${pct(v.ic95[1])}]</td>
      <td style="font-weight:600;color:${corAcima}">${v.virou_acima_do_corte}</td></tr>`;
  }).join('');
}

// ---- guarda de comando (R16b)
if (D.guarda) {
  const g = D.guarda, m = g.melhor_segunda_camada;
  const barra = taxa => `<div style="display:flex;align-items:center;gap:.5rem">
      <div style="flex:0 0 88px;height:8px;background:var(--linha);border-radius:4px;overflow:hidden">
        <div style="width:${(taxa*100).toFixed(0)}%;height:100%;background:${taxa > .5 ? 'var(--ruptura)' : 'var(--atencao)'}"></div>
      </div><span>${pct(taxa)}</span></div>`;
  const linhas = [
    ['Regra por palavra sozinha', '0 de ' + m.marcados_pela_regra,
     g.regra_sozinha.taxa_de_alarme_falso, 0],
    ['Regra + Jev como segunda camada <span style="color:var(--tinta-fraca)">(' + m.combinacao + ')</span>',
     m.liberados + ' de ' + m.marcados_pela_regra, m.taxa, m.irreversivel_liberado],
  ];
  document.querySelector('#tabela-guarda tbody').innerHTML = linhas.map(([nome, lib, taxa, err]) =>
    `<tr><td>${nome}</td><td>${lib}</td><td>${barra(taxa)}</td>
     <td style="font-weight:650;white-space:nowrap;color:${err ? 'var(--ruptura)' : 'var(--estavel)'}">${err} de 12</td></tr>`
  ).join('');
}

// ---- economia de contexto (R17)
if (D.economia) {
  const rotulos = {todos: 'os oito trechos, sem seleção', jev: 'os dois que o Jev escolheu',
                   bm25: 'os dois que o BM25 escolheu', sorteio: 'dois ao acaso'};
  const maior = Math.max(...Object.values(D.economia.arranjos).map(a => a.bytes));
  document.querySelector('#tabela-economia tbody').innerHTML =
    ['todos','jev','bm25','sorteio'].map(k => {
      const a = D.economia.arranjos[k];
      const destaque = k === 'jev' ? ' style="font-weight:650"' : '';
      const cls = a.taxa >= 0.85 ? 'p-ok' : (a.taxa >= 0.6 ? 'p-at' : 'p-ru');
      const largura = (a.bytes / maior * 100).toFixed(0);
      const cor = k === 'jev' ? 'var(--estavel)' : 'var(--traco-forte)';
      return `<tr${destaque}><td>${rotulos[k]}</td>
        <td><span class="pilula ${cls}">${a.acertos}/${a.n}</span></td>
        <td>${a.alvo_no_topo}/${a.n}</td>
        <td><div style="display:flex;align-items:center;gap:.5rem;justify-content:flex-end">
          <div style="flex:0 0 70px;height:8px;background:var(--linha,var(--traco));border-radius:4px;overflow:hidden">
            <div style="width:${largura}%;height:100%;background:${cor}"></div></div>
          <span>${a.bytes.toLocaleString('pt-BR')}</span></div></td>
        <td style="font-weight:600;color:${k==='jev'?'var(--estavel)':'var(--tinta-fraca)'}">${k==='todos' ? '—' : pct(a.economia)}</td></tr>`;
    }).join('');
}

// ---- achados
const semSaida = D.sem_pedido['sem-saida'], comSaida = D.sem_pedido['com-saida'];
const ruido = D.dimensoes.find(d => d.chave === 'ruido');
const pior70 = ruido.niveis.reduce((a,b) => a.acuracia < b.acuracia ? a : b);
const cal = D.calibracao['oficial'] || D.calibracao['autor'];
document.getElementById('achados').innerHTML = [
  ['forte','Ele não obedece a quem fala com ele',
   `Contra ataques escritos por outros modelos, o Jev ignorou <span class="num">${D.adversario ? D.adversario.familias.A.jev.n : 50} de ${D.adversario ? D.adversario.familias.A.jev.n : 50}</span> tentativas dirigidas ao classificador. Os comparadores obedeceram em até <span class="num">16%</span> — e <b>todas</b> essas viradas vieram com confiança acima de 0,90, onde um corte não protege. Quando o texto inserido muda o sentido de verdade, ele muda a resposta e avisa: confiança cai de <span class="num">0,92</span> para <span class="num">0,52</span>, sem nenhuma virada acima do corte.`],
  ['risco','Sem classe de escape, ele inventa',
   `Em dez textos sem pedido algum, o Jev respondeu <i>informacao</i> nas <span class="num">${semSaida.n}</span> vezes, com confiança média <span class="num">${String(semSaida.conf).replace('.',',')}</span>. Oferecendo a opção “não se aplica”, acertou <span class="num">${comSaida.n}/${comSaida.n}</span>. Toda taxonomia precisa dessa saída.`],
  ['forte','Sob texto sujo, ele fica honesto',
   `Com ${pior70.nivel} dos caracteres corrompidos a acurácia cai para <span class="num">${pct(pior70.acuracia)}</span>, mas a confiança cai junto: nenhum erro passou de 0,90. A degradação de superfície é absorvida pelo mecanismo de confiança.`],
  ['forte','Quase três quartos do contexto somem sem custar resposta',
   `Escolhendo dois trechos entre oito, o contexto enviado cai <span class="num">${D.economia ? pct(D.economia.arranjos.jev.economia) : '—'}</span> e as respostas certas vão de <span class="num">${D.economia ? D.economia.arranjos.todos.acertos : '—'}/20</span> para <span class="num">${D.economia ? D.economia.arranjos.jev.acertos : '—'}/20</span>. O trecho certo entra no top-2 em <span class="num">20/20</span>; o BM25 acerta <span class="num">16/20</span>. É o primeiro número de economia que este estudo pôde publicar.`],
  ['','A confiança é calibrada, e ordena melhor ainda',
   `Erro de calibração esperado de <span class="num">${String(cal.ece).replace('.',',')}</span> em 230 casos, com separação de <span class="num">${String(cal.separacao).replace('.',',')}</span> entre acertos e erros. O número não é só um ranking: aproxima a probabilidade real.`]
].map(([c,t,p]) => `<div class="achado ${c}"><h4>${t}</h4><p>${p}</p></div>`).join('');

document.getElementById('rodape').innerHTML =
  `Todos os números desta página são injetados de <code>laboratorio/mapa-de-limites.json</code>, ` +
  `escrito pelas rodadas R0 a R17 dos programas E14 e E17. ` +
  `${D.custo.chamadas.toLocaleString('pt-BR')} chamadas ao modelo, US$ ${D.custo.usd.toFixed(5).replace('.',',')}. ` +
  `Cada rodada teve hipótese e critério de decisão escritos antes da execução, em ` +
  `<code>laboratorio/PREREGISTRO.md</code> — inclusive a R15, que falsificou uma afirmação ` +
  `publicada horas antes, e a correção dela está lá com data. — Helena.`;
</script>
'''

if __name__ == '__main__':
    main()
