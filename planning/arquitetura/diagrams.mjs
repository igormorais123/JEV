// Positions affect presentation only. Labels, branches and meanings come from Markdown.
const layouts = [
  { E:[100,60],S:[345,60],N:[590,60],X:[840,60],V:[840,195],J:[590,195],P:[345,195],R:[590,325],B:[840,325],
    routes:{'N>P':['b','t',[[590,125],[345,125]]],'N>R':['r','t',[[705,60],[705,278],[590,278]]],'V>S':['l','l',[[720,195],[720,268],[220,268],[220,60]]],'B>N':['r','t',[[994,325],[994,6],[590,6]]]} },
  { A:[100,60],B:[345,60],R:[590,60],K:[840,60],Q:[840,195],L:[840,325],C:[590,195],P:[345,195],
    routes:{'C>Q':['b','r',[[590,270],[970,270],[970,195]]]} },
  { A:[100,60],B:[345,60],C:[590,60],D:[840,60],E:[590,195],F:[840,325],J:[345,195],V:[345,325],H:[100,325],
    routes:{'E>F':['r','t',[[840,195]]]} },
  { P:[100,60],B:[345,60],C:[590,60],J:[840,60],S:[840,195],V:[590,195],A:[345,195],R:[590,325],
    routes:{'A>C':['t','b',[[345,125],[590,125]]]} },
  { S:[100,185],D:[345,185],P:[590,55],C:[590,185],T:[590,315],R:[840,315],V:[840,185],F:[100,325],O:[345,325],
    routes:{'D>P':['t','l',[[345,55]]],'D>T':['b','l',[[345,260],[470,260],[470,315]]],'D>R':['t','r',[[345,10],[960,10],[960,315]]],'P>V':['r','t',[[840,55]]],'T>V':['r','l',[[720,315],[720,185]]],'V>S':['r','l',[[994,185],[994,390],[0,390],[0,185]]]},
    labels:{'D>P':[430,45],'D>C':[470,175],'D>T':[400,250],'D>R':[650,0]} },
  { T:[100,60],F:[345,60],Q:[590,60],B:[840,60],P:[840,195],C:[590,195],E:[345,195],V:[100,195],R:[100,325],A:[345,325],
    routes:{'B>C':['l','t',[[715,60],[715,125],[590,125]]],'V>A':['b','t',[[100,268],[345,268]]]},
    labels:{'B>C':[662,115],'V>A':[222,258],'V>R':[125,288]} },
  { S:[100,60],U:[345,60],R:[345,195],C:[590,60],F:[840,60],D:[590,195],P:[840,195],A:[590,325],X:[345,325],K:[100,325],M:[100,195],
    routes:{'R>S':['r','b',[[470,195],[470,120],[100,120]]],'K>S':['b','b',[[100,390],[220,390],[220,120],[100,120]]]},
    labels:{'U>R':[369,148],'K>S':[162,380],'K>M':[125,263]} },
  { E:[100,60],C:[345,60],P:[590,60],F:[840,60],S:[590,195],A:[345,195],O:[100,195],R:[345,325],T:[840,195],X:[840,325],Z:[590,325],
    routes:{'T>Z':['l','t',[[720,195],[720,265],[590,265]]]} },
  { C:[100,185],A:[345,55],B:[345,315],M:[590,185],I:[840,55],D:[840,185],O:[840,315],N:[590,315],R:[590,55],
    routes:{'C>A':['t','l',[[100,55]]],'C>B':['b','l',[[100,315]]],'A>M':['r','l',[[470,55],[470,185]]],'B>M':['r','l',[[470,315],[470,185]]],'M>I':['r','l',[[720,185],[720,55]]],'D>N':['l','r',[[710,185],[710,315]]],'D>R':['r','r',[[995,185],[995,5],[710,5],[710,55]]]},
    labels:{'D>N':[740,258]} },
  { E:[100,60],T:[345,60],O:[590,60],R:[840,60],X:[840,195],V:[590,195],F:[345,195],S:[345,325],B:[100,325],
    routes:{'S>O':['r','l',[[470,325],[470,60]]],'S>X':['r','b',[[840,325]]],'S>V':['r','b',[[590,325]]],'B>T':['t','l',[[100,260],[225,260],[225,60]]]} },
];
const palette={input:['#FFF1DF','#DDB47F','#603E16'],state:['#EDF0FB','#AFB9D9','#252E51'],tool:['#EAF3FA','#9CBED5','#193D5A'],evidence:['#E6F5ED','#9DC7B0','#22513C'],human:['#F9ECF1','#D7ABBE','#68354D'],neutral:['#F4F5F8','#BEC4D1','#434B60'],decision:['#F8F2DC','#D8C88C','#615222']};
const esc=v=>v.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function wrap(label){
  const lines=[];
  for(const part of label.split(/<br\s*\/?>/)){
    let current='';
    for(const word of part.split(' ')){
      if(current && (current+' '+word).length>22){lines.push(current);current=word;}
      else current+=(current?' ':'')+word;
    }
    if(current)lines.push(current);
  }
  return lines;
}
export function renderDiagram(source,index,title){
  const layout=layouts[index];
  if(!layout)throw new Error(`Missing layout ${index}`);
  const nodes=new Map(),edges=[];
  const declarations=/(\w+)(?:\["([^"]*)"\]|\{"([^"]*)"\})/g;
  for(let line of source.split('\n')){
    line=line.trim();
    if(!line||line.startsWith('flowchart')||line.startsWith('%%'))continue;
    line=line.replace(declarations,(_,id,rect,decision)=>{nodes.set(id,{id,label:rect??decision,decision:decision!==undefined});return id;});
    let m;
    if(m=line.match(/^class (\w+(?:,\w+)*) (\w+)$/)){for(const id of m[1].split(',')){if(!nodes.has(id))throw new Error(`Unknown class target ${id}`);nodes.get(id).kind=m[2];}continue;}
    if(m=line.match(/^(\w+) -- (.+?) --> (\w+)$/)){edges.push({a:m[1],b:m[3],label:m[2]});continue;}
    if(m=line.match(/^(\w+) -\. "(.+?)" \.-> (\w+)$/)){edges.push({a:m[1],b:m[3],label:m[2],dashed:true});continue;}
    if(m=line.match(/^(\w+) (-->|---|-\.->) (\w+)$/)){edges.push({a:m[1],b:m[3],dashed:m[2]!=='-->',noArrow:m[2]==='---'});continue;}
    if(!/^\w+$/.test(line))throw new Error(`Unrecognized diagram statement ${line}`);
  }
  for(const node of nodes.values()){
    if(!layout[node.id])throw new Error(`No position for ${node.id}`);
    [node.x,node.y]=layout[node.id];node.lines=wrap(node.label);node.w=node.decision?206:188;node.h=Math.max(64,node.lines.length*21+19);
  }
  const point=(n,side)=>side==='l'?[n.x-n.w/2,n.y]:side==='r'?[n.x+n.w/2,n.y]:side==='t'?[n.x,n.y-n.h/2]:[n.x,n.y+n.h/2];
  let paths='',labels='';
  for(const edge of edges){
    const a=nodes.get(edge.a),b=nodes.get(edge.b);if(!a||!b)throw new Error(`Missing node ${edge.a} ${edge.b}`);
    const spec=layout.routes?.[`${edge.a}>${edge.b}`];let pts;
    if(spec)pts=[point(a,spec[0]),...spec[2],point(b,spec[1])];
    else if(a.y===b.y)pts=[point(a,b.x>a.x?'r':'l'),point(b,b.x>a.x?'l':'r')];
    else if(a.x===b.x)pts=[point(a,b.y>a.y?'b':'t'),point(b,b.y>a.y?'t':'b')];
    else {const p=point(a,b.x>a.x?'r':'l'),q=point(b,b.x>a.x?'l':'r'),x=(p[0]+q[0])/2;pts=[p,[x,p[1]],[x,q[1]],q];}
    const d=pts.map((p,i)=>`${i?'L':'M'} ${p[0]} ${p[1]}`).join(' ');
    paths+=`<path data-edge="${edge.a}-${edge.b}" d="${d}" fill="none" stroke="${edge.dashed?'#a1aabe':'#7a879f'}" stroke-width="1.6" stroke-linejoin="round" ${edge.dashed?'stroke-dasharray="5 4"':''} ${edge.noArrow?'':`marker-end="url(#arrow-${index})"`}/>`;
    if(edge.label){
      const p=pts[0],q=pts[1];let x=(p[0]+q[0])/2,y=(p[1]+q[1])/2-9;
      if(p[0]===q[0]){x+=24;y+=5;}
      if(layout.labels?.[`${edge.a}>${edge.b}`])[x,y]=layout.labels[`${edge.a}>${edge.b}`];
      const w=edge.label.length*8+12;
      labels+=`<rect x="${x-w/2}" y="${y-14}" width="${w}" height="20" fill="#fff" rx="3"/><text x="${x}" y="${y}" text-anchor="middle" font-size="15" fill="#5a657e">${esc(edge.label)}</text>`;
    }
  }
  let shapes='';
  for(const n of nodes.values()){
    const [fill,stroke,color]=palette[n.kind||'state'];
    const x=n.x-n.w/2,y=n.y-n.h/2;
    const shape=n.decision?`<polygon points="${x+15},${y} ${x+n.w-15},${y} ${x+n.w},${n.y} ${x+n.w-15},${y+n.h} ${x+15},${y+n.h} ${x},${n.y}"`:`<rect x="${x}" y="${y}" width="${n.w}" height="${n.h}" rx="7"`;
    shapes+=`<g data-node="${n.id}">${shape} fill="${fill}" stroke="${stroke}" stroke-width="1.2"/>`;
    n.lines.forEach((line,j)=>{shapes+=`<text x="${n.x}" y="${n.y-(n.lines.length-1)*10.5+j*21+5.5}" text-anchor="middle" font-size="17" font-weight="${j===0?'600':'400'}" fill="${color}">${esc(line)}</text>`;});
    shapes+='</g>';
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-10 -20 1040 420" role="img" aria-label="${esc(title)}" style="font-family:'Segoe UI',Arial,sans-serif"><title>${esc(title)}</title><defs><marker id="arrow-${index}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#7a879f"/></marker></defs>${paths}${shapes}${labels}</svg>`;
}
