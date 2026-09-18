"""Publica painel estatico e PDF do plano. Sem rede, sem segredos, sem inferencia."""
import csv
import html
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT=Path(__file__).resolve().parent.parent
FONT_DIR=Path('C:/Windows/Fonts')
INK=colors.HexColor('#173330')
GREEN=colors.HexColor('#087769')
MUTED=colors.HexColor('#536966')
PALE=colors.HexColor('#e9f1eb')
LINE=colors.HexColor('#d4ddd5')


def markup(text):
    text=text.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-')
    text=html.escape(text,quote=False)
    def link(match):
        label,url=match.groups()
        if url.startswith('https://'):
            return f'<link href="{html.escape(html.unescape(url),quote=True)}" color="#087769">{label}</link>'
        return f'<font color="#087769">{label}</font>'
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,text)
    text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'`([^`]+)`',r'<font name="Mono" size="8.2">\1</font>',text)
    return text


class PlanDoc(BaseDocTemplate):
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name=='Section':
            title=flowable.getPlainText()
            key='section-'+str(getattr(flowable,'section_key',0))
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title,key,level=0,closed=False)
            self.notify('TOCEntry',(0,title,self.page,key))


def footer(canvas,doc):
    canvas.saveState()
    width,height=A4
    if doc.page>1:
        canvas.setFont('Regular',8)
        canvas.setFillColor(MUTED)
        canvas.drawString(46,height-29,'JEV  /  PLANO CIENTÍFICO  /  HELENA')
        canvas.drawRightString(width-46,height-29,'18.09.2026 · v1.0')
        canvas.setStrokeColor(LINE)
        canvas.line(46,height-37,width-46,height-37)
    canvas.setFillColor(MUTED)
    canvas.setFont('Regular',8)
    canvas.drawString(46,26,'Planejamento + auditoria offline. Ensaios dos sistemas ainda pendentes.')
    canvas.drawRightString(width-46,26,str(doc.page))
    canvas.restoreState()


def build_pdf(markdown):
    pdfmetrics.registerFont(TTFont('Regular',str(FONT_DIR/'segoeui.ttf')))
    pdfmetrics.registerFont(TTFont('Bold',str(FONT_DIR/'segoeuib.ttf')))
    pdfmetrics.registerFont(TTFont('Italic',str(FONT_DIR/'segoeuii.ttf')))
    pdfmetrics.registerFont(TTFont('Mono',str(FONT_DIR/'consola.ttf')))
    pdfmetrics.registerFontFamily('Regular',normal='Regular',bold='Bold',italic='Italic',boldItalic='Bold')
    styles={
      'body':ParagraphStyle('Body',fontName='Regular',fontSize=10,leading=15,textColor=INK,spaceAfter=8,splitLongWords=True),
      'list':ParagraphStyle('List',fontName='Regular',fontSize=10,leading=15,textColor=INK,spaceAfter=7,leftIndent=10,firstLineIndent=-10,splitLongWords=True),
      'section':ParagraphStyle('Section',fontName='Bold',fontSize=18,leading=23,textColor=GREEN,spaceBefore=16,spaceAfter=12,keepWithNext=True),
      'sub':ParagraphStyle('Sub',fontName='Bold',fontSize=12.3,leading=17,textColor=INK,spaceBefore=12,spaceAfter=8,keepWithNext=True),
      'table':ParagraphStyle('Cell',fontName='Regular',fontSize=8.4,leading=12,textColor=INK,splitLongWords=True),
      'tablehead':ParagraphStyle('CellHead',fontName='Bold',fontSize=8.4,leading=12,textColor=INK),
      'small':ParagraphStyle('Small',fontName='Regular',fontSize=9,leading=14,textColor=MUTED,spaceAfter=10),
      'kicker':ParagraphStyle('Kicker',fontName='Bold',fontSize=10,leading=14,textColor=GREEN,spaceAfter=24),
      'title':ParagraphStyle('TitleCover',fontName='Bold',fontSize=37,leading=43,textColor=INK,spaceAfter=24),
      'intro':ParagraphStyle('Intro',fontName='Regular',fontSize=14,leading=21,textColor=INK,spaceAfter=22),
    }
    target=ROOT/'output/pdf/PLANO-CIENTIFICO-JEV-HELENA.pdf'
    target.parent.mkdir(parents=True,exist_ok=True)
    doc=PlanDoc(str(target),pagesize=A4,leftMargin=46,rightMargin=46,topMargin=54,bottomMargin=48,
        title='Jev - Plano científico de testes - Helena',author='Laboratório JEV / análise Helena')
    frame=Frame(doc.leftMargin,doc.bottomMargin,doc.width,doc.height,id='normal')
    doc.addPageTemplates(PageTemplate(id='normal',frames=frame,onPage=footer))
    story=[Spacer(1,47),Paragraph('HELENA  /  PESQUISA APLICADA  /  PLANO v1.0',styles['kicker']),
        Paragraph('Testar todos.<br/>Medir o que importa.',styles['title']),
        Paragraph('Um plano científico para avaliar os 15 sistemas Jev e decidir onde há benefício real no trabalho.',styles['intro'])]
    metrics=[['15 sistemas','96 decisões','US$ 0'],['Rodadas simples e profundas','Histórico recalculado do PDF','Inferência nova nesta etapa']]
    table=Table([[Paragraph(t,styles['sub'] if i==0 else styles['small']) for t in row] for i,row in enumerate(metrics)],colWidths=[doc.width/3]*3)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story += [table,Spacer(1,28),Paragraph('<b>Decisão proposta</b><br/>Reaproveitar a evidência do Hermes, criar casos novos bem rotulados e comparar qualidade, custo e tempo no fluxo completo.',styles['intro']),
      Paragraph('A interface e os documentos estão prontos. Os ensaios dos sistemas, o executor e o bloqueio financeiro continuam como próximos passos do plano.',styles['body']),
      Spacer(1,20),Paragraph('18 de setembro de 2026<br/>Cenário financeiro conservador: US$ 1,997062454 disponíveis dentro do teto total de US$ 5, incluindo o histórico reportado.',styles['small']),PageBreak(),
      Paragraph('Mapa de leitura',ParagraphStyle('ContentsTitle',parent=styles['section']))]
    toc=TableOfContents()
    toc.levelStyles=[ParagraphStyle('TOC',fontName='Regular',fontSize=10,leading=16,textColor=INK,leftIndent=0,spaceBefore=6)]
    story += [toc,Spacer(1,18),Paragraph('Comece pelas seções 1, 3, 7 e 8. A metodologia e o contrato de dados estão nas seções 4 a 6 e 9. As fichas dos 15 sistemas encerram o documento.',styles['small']),PageBreak()]
    lines=markdown.splitlines()
    i=0; section_count=0
    while i<len(lines):
        line=lines[i].strip()
        if not line or line.startswith('# '):
            i+=1;continue
        if line.startswith('## '):
            section_count+=1
            if section_count==13:
                story.append(PageBreak())
            p=Paragraph(markup(line[3:]),styles['section']);p.section_key=section_count
            story.append(p);i+=1;continue
        if line.startswith('### '):
            story.append(Paragraph(markup(line[4:]),styles['sub']));i+=1;continue
        if re.match(r'^(?:- |\d+\. )',line):
            if line.startswith('- '):
                line='• '+line[2:]
            story.append(Paragraph(markup(line),styles['list']));i+=1;continue
        if line.startswith('|'):
            block=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+',c) for c in cells):
                    block.append(cells)
                i+=1
            n=len(block[0])
            if n==2: ratios=[.34,.66]
            elif n==3: ratios=[.25,.37,.38]
            elif n==4: ratios=[.15,.31,.25,.29]
            elif n==5: ratios=[.18,.12,.12,.15,.43]
            else: ratios=[1/n]*n
            data=[[Paragraph(markup(c),styles['tablehead' if idx==0 else 'table']) for c in row] for idx,row in enumerate(block)]
            t=Table(data,colWidths=[doc.width*r for r in ratios],repeatRows=1,hAlign='LEFT',splitByRow=1)
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,LINE),('LINEBELOW',(0,1),(-1,-1),.35,LINE),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            story.extend([t,Spacer(1,11)]);continue
        content=[]
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|')) and not re.match(r'^(?:- |\d+\. )',lines[i]):
            content.append(lines[i].strip());i+=1
        text=' '.join(content)
        if text.startswith('> '):text=text[2:]
        story.append(Paragraph(markup(text),styles['body']))
    doc.multiBuild(story)
    return target


def main():
    plan=json.loads((ROOT/'planning/plan.json').read_text(encoding='utf-8'))
    with (ROOT/'research/hermes/fase2-decisoes-do-pdf.csv').open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    import runpy
    runpy.run_path(str(ROOT/'lab/build_ui.py'),run_name='__main__')
    markdown=(ROOT/'docs/PLANO-CIENTIFICO-JEV-HELENA.md').read_text(encoding='utf-8')
    target=build_pdf(markdown)
    print(json.dumps(dict(pdf=str(target),markdown_words=len(markdown.split()),systems=len(plan['systems']),historical_rows=len(rows)),ensure_ascii=False))


if __name__=='__main__':main()
