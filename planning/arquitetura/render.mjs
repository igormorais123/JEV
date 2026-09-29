import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import crypto from 'node:crypto';
import { renderDiagram } from './diagrams.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../..');
const source = path.join(root, 'docs/ARQUITETURA-DO-JEV-REVISAO.md');
const assets = path.join(root, 'docs/arquitetura-assets');
const output = path.join(root, 'output');
const modules = process.env.JEV_DOC_NODE_MODULES || path.join(here, 'node_modules');
const localRequire = createRequire(path.join(modules, '_loader.cjs'));
const MarkdownIt = localRequire('markdown-it');
const browserModules = process.env.JEV_DOC_BROWSER_MODULES || modules;
const browserRequire = createRequire(path.join(browserModules, '_loader.cjs'));
const { chromium } = browserRequire('playwright');
const css = fs.readFileSync(path.join(here, 'style.css'), 'utf8');
const raw = fs.readFileSync(source, 'utf8');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const md = new MarkdownIt({ html: true, typographer: false });
const diagrams = [];
const escape = value => value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
md.renderer.rules.fence = (tokens, index) => {
  const token = tokens[index];
  if (token.info.trim() !== 'mermaid') return `<pre><code>${escape(token.content)}</code></pre>`;
  const id = `diagrama-${String(diagrams.length + 1).padStart(2, '0')}`;
  diagrams.push({ id, source: token.content });
  return `<div class="diagram" data-diagram="${id}"><pre>${escape(token.content)}</pre></div>`;
};
const imageRenderer = md.renderer.rules.image;
md.renderer.rules.image = (tokens, index, options, env, self) => {
  const token = tokens[index];
  const file = path.resolve(path.dirname(source), token.attrGet('src'));
  if (!file.startsWith(assets + path.sep)) throw new Error('Image outside architecture assets');
  const ext = path.extname(file).slice(1);
  token.attrSet('src', `data:image/${ext === 'svg' ? 'svg+xml' : ext};base64,${fs.readFileSync(file).toString('base64')}`);
  return imageRenderer(tokens, index, options, env, self);
};
// Relative Markdown links remain portable in the HTML under output/.
const linkRenderer = md.renderer.rules.link_open || ((t, i, o, e, s) => s.renderToken(t, i, o));
md.renderer.rules.link_open = (tokens, index, options, env, self) => {
  const href = tokens[index].attrGet('href');
  if (href && !/^(?:https?:|#)/.test(href)) {
    const target = path.resolve(path.dirname(source), href);
    if (!fs.existsSync(target)) throw new Error(`Broken source link: ${href}`);
    tokens[index].attrSet('href', path.relative(output, target).replaceAll('\\', '/'));
  }
  return linkRenderer(tokens, index, options, env, self);
};
const pieces = raw.split(/<!-- page: ([a-z-]+) -->\s*/);
const pages = [];
for (let i = 1; i < pieces.length; i += 2) {
  const layout = pieces[i];
  const content = md.render(pieces[i + 1]);
  const blocks = content.split(/(?=<h3>)/);
  const main = blocks.shift();
  const cards = blocks.length ? `<div class="cards">${blocks.map(b => `<article class="card">${b}</article>`).join('')}</div>` : '';
  pages.push(`<section class="page ${layout}" data-page="${pages.length + 1}"><div class="main">${main}</div>${cards}<footer><span>INTEIA · Professor Igor Vasconcelos</span><span>${String(pages.length + 1).padStart(2, '0')}</span></footer></section>`);
}
fs.mkdirSync(path.join(output, 'pdf'), { recursive: true });
const htmlPath = path.join(output, 'arquitetura-jev.html');
const pdfPath = path.join(output, 'pdf/ARQUITETURA-DO-JEV-REVISAO.pdf');
const html = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Arquitetura do JEV — Professor Igor Vasconcelos · INTEIA</title><meta name="author" content="Professor Igor Vasconcelos"><meta name="viewport" content="width=device-width,initial-scale=1"><style>${css}</style></head><body>${pages.join('')}</body></html>`;
const executablePath = process.env.JEV_DOC_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const browser = await chromium.launch({ executablePath, headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1400, height: 1000 }, deviceScaleFactor: 1 });
  await page.setContent(html, { waitUntil: 'load' });
  const rendered = diagrams.map((entry,index)=>({id:entry.id,svg:renderDiagram(entry.source,index,`Fluxo ${index+1}`)}));
  const svgs = await page.evaluate(async entries => {
    const results = [];
    for (const entry of entries) {
      const { svg } = entry;
      const host = document.querySelector(`[data-diagram="${entry.id}"]`);
      host.innerHTML = svg;
      host.querySelector('svg').setAttribute('role', 'img');
      host.querySelector('svg').setAttribute('aria-label', host.closest('section').querySelector('h2').textContent);
      results.push({ id: entry.id, svg: host.innerHTML });
    }
    for (const script of document.querySelectorAll('script')) script.remove();
    await document.fonts.ready;
    await Promise.all([...document.images].map(img => img.decode()));
    return results;
  }, rendered);
  for (const item of svgs) fs.writeFileSync(path.join(assets, `${item.id}.svg`), item.svg);
  // All technical diagrams and the cover are embedded; the resulting HTML is script-free.
  const finalHTML = '<!doctype html>\n' + await page.locator('html').evaluate(e => e.outerHTML);
  fs.writeFileSync(htmlPath, finalHTML);
  await page.emulateMedia({ media: 'print' });
  const layout = await page.evaluate(() => [...document.querySelectorAll('.page')].map(section => {
    const box = section.getBoundingClientRect();
    const children = [...section.querySelectorAll('.main,.cards')].map(e => e.getBoundingClientRect());
    const bottom = Math.max(...children.map(b => b.bottom));
    const diagram = section.querySelector('.diagram svg');
    let diagramFontPt = null;
    if (diagram) {
      const rect = diagram.getBoundingClientRect();
      diagramFontPt = +(17 * Math.min(rect.width / diagram.viewBox.baseVal.width, rect.height / diagram.viewBox.baseVal.height) * .75).toFixed(2);
    }
    return { page: +section.dataset.page, title: section.querySelector('h1,h2').innerText.replaceAll('\n', ' '), contentBottom: +(bottom - box.top).toFixed(1), contentLimit: +(box.height - 48).toFixed(1), overflow: !section.classList.contains('cover') && bottom > box.bottom - 48, diagramFontPt };
  }));
  const diagramChecks = await page.evaluate(() => [...document.querySelectorAll('.diagram svg')].map(svg => {
    const textOverflow = [];
    for (const group of svg.querySelectorAll('[data-node]')) {
      const shape = group.firstElementChild.getBBox();
      for (const text of group.querySelectorAll('text')) {
        const b = text.getBBox();
        if (b.x < shape.x + 2 || b.y < shape.y + 2 || b.x + b.width > shape.x + shape.width - 2 || b.y + b.height > shape.y + shape.height - 2) {
          textOverflow.push({ node: group.dataset.node, text: text.textContent });
        }
      }
    }
    return { id: svg.closest('[data-diagram]').dataset.diagram, nodes: svg.querySelectorAll('[data-node]').length, edges: svg.querySelectorAll('[data-edge]').length, textOverflow };
  }));
  if (diagramChecks.some(d => d.textOverflow.length)) throw new Error(`Diagram text overflow: ${JSON.stringify(diagramChecks.filter(d => d.textOverflow.length))}`);
  const failures = layout.filter(x => x.overflow);
  if (failures.length) throw new Error(`Page overflow: ${JSON.stringify(failures)}`);
  await page.pdf({ path: pdfPath, format: 'A4', landscape: true, printBackground: true, preferCSSPageSize: true, displayHeaderFooter: false, tagged: true });
  const manifest = { source: path.relative(root, source).replaceAll('\\', '/'), source_sha256: hash(fs.readFileSync(source)), pages: pages.length, diagrams: diagrams.length,
    html_sha256: hash(fs.readFileSync(htmlPath)), pdf_sha256: hash(fs.readFileSync(pdfPath)), cover_sha256: hash(fs.readFileSync(path.join(assets, 'capa.png'))), diagramChecks, layout };
  fs.writeFileSync(path.join(here, 'validacao-layout.json'), JSON.stringify(manifest, null, 2) + '\n');
  console.log(JSON.stringify({ pdf: pdfPath, pages: pages.length, diagrams: diagrams.length, smallestDiagramFontPt: Math.min(...layout.map(x => x.diagramFontPt).filter(Boolean)), overflow: failures.length }));
} finally { await browser.close(); }
