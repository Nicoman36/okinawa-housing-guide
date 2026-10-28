(function(){
  // Service switcher (dropdown) — navigates to the chosen service's page
  document.querySelectorAll('select[data-nav]').forEach(function(s){
    s.addEventListener('change',function(){ if(s.value) location.href=s.value; });
  });
  // Close the Arts menu when clicking elsewhere
  document.addEventListener('click',function(e){
    document.querySelectorAll('nav.main details[open]').forEach(function(d){ if(!d.contains(e.target)) d.removeAttribute('open'); });
  });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape') document.querySelectorAll('nav.main details[open]').forEach(function(d){d.removeAttribute('open');}); });

  // Home search -> /find/
  var hs=document.getElementById('home-search');
  if(hs){ hs.addEventListener('submit',function(e){ e.preventDefault(); var f=new FormData(hs), p=new URLSearchParams();
      ['q','svc','area'].forEach(function(k){ if(f.get(k)) p.set(k,f.get(k)); });
      location.href=hs.getAttribute('action')+(p.toString()?'?'+p.toString():''); }); }

  // Find page
  var root=document.getElementById('find-app'); if(!root || !window.DIR) return;
  var D=window.DIR, L=D.locations, U=D.ui;
  var norm=function(s){ return (s||'').normalize('NFKC').toLowerCase(); };
  L.forEach(function(x){ x._t=norm([x.n,x.j,x.ne,x.a,x.aj,x.c,x.s,x.al,x.m_en].join(' ')); });
  var el={q:document.getElementById('f-q'),svc:document.getElementById('f-svc'),area:document.getElementById('f-area'),
          ver:document.getElementById('f-ver'),eng:document.getElementById('f-eng'),mil:document.getElementById('f-mil'),org:document.getElementById('f-org'),loc:document.getElementById('f-loc'),
          out:document.getElementById('f-out'),cnt:document.getElementById('f-count'),rst:document.getElementById('f-reset'),
          ref:document.getElementById('f-ref'),rad:document.getElementById('f-rad'),more:document.getElementById('f-more'),near:document.getElementById('f-near'),msg:document.getElementById('f-msg')};
  var qs=new URLSearchParams(location.search);
  ['q','svc','area','ver','ref','rad'].forEach(function(k){ if(qs.get(k)&&el[k]) el[k].value=qs.get(k); });
  if(qs.get('loc')==='1'&&el.loc) el.loc.checked=true;
  var PAGE=40, shown=PAGE, me=null;
  function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function dist(a,b,c,d){ var R=6371,t=Math.PI/180,dl=(c-a)*t,dn=(d-b)*t,h=Math.sin(dl/2)*Math.sin(dl/2)+Math.cos(a*t)*Math.cos(c*t)*Math.sin(dn/2)*Math.sin(dn/2); return 2*R*Math.asin(Math.sqrt(h)); }
  var SKIP={the:1,co:1,ltd:1,inc:1,kk:1,housing:1,okinawa:1,agency:1,corp:1,division:1};
  function mono(x){
    if(x.k!=='agency') return '\u2302';
    if(/[\u3040-\u9fff]/.test(x.n)) return x.n.replace(/^(株式会社|有限会社|（有）|\(有\))/,'').charAt(0);
    var w=(x.n.match(/[A-Za-z0-9]+/g)||[]), f=w.filter(function(t){return !SKIP[t.toLowerCase()];}); if(!f.length) f=w;
    if(f.length>=2) return (f[0][0]+f[1][0]).toUpperCase();
    return f.length? f[0].slice(0,2).toUpperCase() : '?';
  }
  var rp=null;
  function refName(id){ var n=''; (D.refs||[]).forEach(function(r){ if(r.id===id) n=r.n; }); return n; }
  function card(x){
    var h='<article class="card v-'+x.v+'"><span class="mono'+(x.k!=='agency'?' org':'')+'" aria-hidden="true">'+esc(mono(x))+'</span><div class="body"><div class="top"><h3><a href="'+D.base+D.pfx+'/l/'+x.id+'/">'+esc(x.n)+'</a></h3>';
    h+='<span class="badge '+x.v+'" title="'+esc(D.verif[x.v][1])+'">'+esc(D.verif[x.v][0])+'</span>'+(window.OKTools?window.OKTools.starHTML(x.id):'')+'</div>';
    if(x.j) h+='<div class="ja">'+esc(x.j)+'</div>';
    h+='<div class="chips">';
    if(x.k!=='agency') h+='<span class="chip org">'+esc(U.org)+'</span>';
    if(x.g) h+='<span class="chip jp">'+esc(U.jp)+'</span>';
    if(x.e===1) h+='<span class="chip eng">'+esc(U.eng)+'</span>'; else if(x.e===2) h+='<span class="chip eng">'+esc(U.engl)+'</span>';
    if(x.mi===1) h+='<span class="chip mil">'+esc(U.mil)+'</span>'; else if(x.mi===2) h+='<span class="chip mil">'+esc(U.mill)+'</span>';
    if(x.r) h+='<span class="chip"><i class="ico star"></i>'+esc(x.r[0])+' ('+esc(x.r[1])+')</span>';
    x.d.slice(0,3).forEach(function(d){ h+='<span class="chip">'+esc(D.disc[d])+'</span>'; });
    if(x.d.length>3) h+='<span class="chip">+'+(x.d.length-3)+'</span>';
    h+='</div><div class="meta"><span><i class="ico pin"></i>'+esc(x.a||x.m_en||U.noloc)+'</span>';
    if(x._km!=null) h+='<span><b>'+x._km.toFixed(1)+' '+U.km+'</b>'+(rp?' '+esc(refName(el.ref.value)):'')+'</span>';
    if(x.oh) h+='<span class="open-badge" data-oh="'+esc(x.oh)+'"></span>';
    if(x.h) h+='<span><i class="ico clock"></i>'+esc(x.h.length>40?x.h.slice(0,38)+'\u2026':x.h)+'</span>';
    if(x.p) h+='<a href="tel:'+esc(x.p.replace(/[^0-9+]/g,''))+'"><i class="ico tel"></i>'+esc(x.p)+'</a>';
    if(x.w) h+='<a href="'+esc(x.w)+'" rel="noopener nofollow"><i class="ico web"></i>'+U.website.replace(' \u2197','')+'</a>';
    h+='</div></div></article>'; return h;
  }
  function run(reset){
    if(reset) shown=PAGE;
    var q=norm(el.q.value).trim(), svc=el.svc.value, area=el.area.value, ver=el.ver.value, eng=el.eng.checked, mil=el.mil.checked, org=el.org.checked, loc=el.loc?el.loc.checked:false;
    var terms=q?q.split(/\s+/):[];
    var res=L.filter(function(x){
      if(svc && x.d.indexOf(svc)<0) return false;
      if(area && x.m!==area) return false;
      if(ver && ver.indexOf(x.v)<0) return false;
      if(eng && !x.e) return false;
      if(mil && !x.mi) return false;
      if(!org && x.k!=='agency') return false;
      if(!loc && x.g) return false;
      for(var i=0;i<terms.length;i++){ if(x._t.indexOf(terms[i])<0) return false; }
      return true; });
    rp=null; if(el.ref&&el.ref.value){ (D.refs||[]).forEach(function(r){ if(r.id===el.ref.value) rp=[r.la,r.lo]; }); }
    var origin=rp||me, rad=(el.rad&&el.rad.value)?parseFloat(el.rad.value):0;
    res.forEach(function(x){ x._km=(origin&&x.la!=null)? dist(origin[0],origin[1],x.la,x.lo):null; });
    if(rp&&rad) res=res.filter(function(x){ return x._km!=null && x._km<=rad; });
    if(origin) res.sort(function(a,b){ var A=a._km==null?1e9:a._km, B=b._km==null?1e9:b._km; return A-B || a.v.localeCompare(b.v); });
    else res.sort(function(a,b){ return a.v.localeCompare(b.v) || a.n.localeCompare(b.n); });
    el.cnt.textContent=res.length+' '+(res.length===1?U.place:U.places);
    el.out.innerHTML=res.length? res.slice(0,shown).map(card).join('') : '<div class="empty">'+esc(U.none)+'</div>';
    el.more.hidden = res.length<=shown;
    var p=new URLSearchParams(); if(el.q.value)p.set('q',el.q.value); if(el.ref&&el.ref.value)p.set('ref',el.ref.value); if(el.rad&&el.rad.value)p.set('rad',el.rad.value); if(svc)p.set('svc',svc); if(area)p.set('area',area); if(ver)p.set('ver',ver); if(eng)p.set('eng','1'); if(mil)p.set('mil','1');
    try{ history.replaceState(null,'',location.pathname+(p.toString()?'?'+p.toString():'')); }catch(e){}
  }
  ['q','svc','area','ver','ref','rad'].forEach(function(k){ if(el[k]) el[k].addEventListener('input',function(){run(true);}); });
  el.eng.addEventListener('change',function(){run(true);}); el.mil.addEventListener('change',function(){run(true);}); el.org.addEventListener('change',function(){run(true);});
  el.rst.addEventListener('click',function(){ el.q.value='';el.svc.value='';el.area.value='';el.ver.value='';if(el.ref)el.ref.value='';if(el.rad)el.rad.value='';el.eng.checked=false;el.mil.checked=false;el.org.checked=false;me=null;el.msg.textContent='';run(true); });
  el.more.addEventListener('click',function(){ shown+=PAGE; run(false); });
  el.near.addEventListener('click',function(){
    if(!navigator.geolocation){ el.msg.textContent=U.denied; return; }
    el.msg.textContent=U.locating;
    navigator.geolocation.getCurrentPosition(function(p){ me=[p.coords.latitude,p.coords.longitude];
      el.msg.textContent=L.some(function(x){return x.la!=null;})?'':U.nocoord; run(true); },
      function(){ el.msg.textContent=U.denied; }, {timeout:10000});
  });
  if(qs.get('eng')==='1') el.eng.checked=true;
  if(qs.get('mil')==='1') el.mil.checked=true;
  run(true);
})();
