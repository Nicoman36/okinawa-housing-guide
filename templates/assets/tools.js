(function(){
  var JA=document.documentElement.lang==='ja';
  var KEY='okhd.short', CK='okhd.check';
  function T(en,ja){ return JA?ja:en; }
  function get(k){ try{ return JSON.parse(localStorage.getItem(k)||'null'); }catch(e){ return null; } }
  function set(k,v){ try{ localStorage.setItem(k,JSON.stringify(v)); }catch(e){} }
  function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  var mem=[]; // fallback if storage is blocked
  function list(){ var v=get(KEY); return Array.isArray(v)?v:mem; }
  function save(a){ mem=a; set(KEY,a); }
  var HEART='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7.5-4.6-9.5-9.2C1.2 8.6 3 5 6.4 5c2 0 3.6 1.1 4.6 2.6h2C14 6.1 15.6 5 17.6 5 21 5 22.8 8.6 21.5 11.8 19.5 16.4 12 21 12 21z"/></svg>';
  var S=JA?{add:'候補に追加',rem:'候補から外す',addw:'♡ 候補に追加',remw:'♥ 候補に入っています',save:'♡ 保存',saved:'♥ 保存済み'}:{add:'Add to shortlist',rem:'Remove from shortlist',addw:'♡ Add to shortlist',remw:'♥ On your shortlist',save:'♡ Save',saved:'♥ Saved'};
  function starHTML(id){ return '<button type="button" class="star-btn" data-id="'+esc(id)+'" aria-pressed="false" aria-label="'+S.add+'" title="'+S.add+'">'+HEART+'</button>'; }
  window.OKTools={starHTML:starHTML};
  function sync(){
    var a=list();
    document.querySelectorAll('.star-btn,.star-btn-wide').forEach(function(b){
      var on=a.indexOf(b.getAttribute('data-id'))>=0; b.setAttribute('aria-pressed',on?'true':'false');
      if(b.classList.contains('star-btn-wide')){ var tx=b.classList.contains('short')?(on?S.saved:S.save):(on?S.remw:S.addw); if(b.textContent!==tx) b.textContent=tx; }
      else { b.setAttribute('aria-label',on?S.rem:S.add); b.title=on?S.rem:S.add; }
    });
    document.querySelectorAll('[data-short-count]').forEach(function(c){ var v=a.length?String(a.length):''; if(c.textContent!==v) c.textContent=v; });
  }
  document.addEventListener('click',function(e){
    var b=e.target.closest&&e.target.closest('.star-btn,.star-btn-wide'); if(!b) return;
    e.preventDefault(); var id=b.getAttribute('data-id'), a=list().slice(), i=a.indexOf(id);
    if(i>=0) a.splice(i,1); else a.push(id);
    save(a); sync(); if(window.OKShortRefresh) window.OKShortRefresh();
  });

  // ---------------- open-now badges (Japan time; listed hours only)
  var DAYS=['sun','mon','tue','wed','thu','fri','sat'];
  var DJA={sun:'日',mon:'月',tue:'火',wed:'水',thu:'木',fri:'金',sat:'土'}, DEN={sun:'Sun',mon:'Mon',tue:'Tue',wed:'Wed',thu:'Thu',fri:'Fri',sat:'Sat'};
  function parseOH(t){ var w={}; DAYS.forEach(function(d){w[d]=[];});
    String(t).split(';').forEach(function(p){ var m=p.trim().match(/^(\w{3})(?:-(\w{3}))? (\d\d):(\d\d)-(\d\d):(\d\d)$/); if(!m) return;
      var a=DAYS.indexOf(m[1]), b=m[2]?DAYS.indexOf(m[2]):a; if(a<0||b<0) return;
      for(var i=a;;i=(i+1)%7){ w[DAYS[i]].push([+m[3]*60+ +m[4], +m[5]*60+ +m[6]]); if(i===b) break; } });
    return w; }
  function jstNow(){ var d=new Date(Date.now()+9*3600e3); return {day:d.getUTCDay(), min:d.getUTCHours()*60+d.getUTCMinutes()}; }
  function hm(m){ return Math.floor(m/60)+':'+('0'+m%60).slice(-2); }
  function openState(t){ var w=parseOH(t), n=jstNow(), today=w[DAYS[n.day]];
    for(var i=0;i<today.length;i++){ if(n.min>=today[i][0]&&n.min<today[i][1]) return {open:true, until:today[i][1]}; }
    for(var k=0;k<8;k++){ var d=(n.day+k)%7, sl=w[DAYS[d]];
      for(var j=0;j<sl.length;j++){ if(k>0||sl[j][0]>n.min) return {open:false, day:k===0?null:DAYS[d], at:sl[j][0]}; } }
    return null; }
  var OHT=T('Based on listed hours, Japan time. Holidays and lunch breaks may differ.','掲載の営業時間（日本時間）に基づく目安です。祝日や昼休みは異なる場合があります。');
  function fillOpen(){
    document.querySelectorAll('.open-badge[data-oh]').forEach(function(b){
      var st=openState(b.getAttribute('data-oh')), txt, cls;
      if(!st){ txt=''; cls='open-badge'; }
      else if(st.open){ txt=T('Open now · until ','営業中・')+hm(st.until)+T('',' まで'); cls='open-badge on'; }
      else { var when=st.day?(JA?DJA[st.day]+'曜 ':DEN[st.day]+' '):''; txt=T('Closed · opens ','営業時間外・')+when+hm(st.at)+T('',' から'); cls='open-badge off'; }
      if(b.textContent!==txt) b.textContent=txt; if(b.className!==cls) b.className=cls; if(b.title!==OHT) b.title=OHT;
    });
  }
  new MutationObserver(function(){ sync(); fillOpen(); }).observe(document.documentElement,{childList:true,subtree:true});
  setInterval(fillOpen,60000);
  sync(); fillOpen();

  function hav(a,b,c,d){ var R=6371,t=Math.PI/180,dl=(c-a)*t,dn=(d-b)*t,h=Math.sin(dl/2)*Math.sin(dl/2)+Math.cos(a*t)*Math.cos(c*t)*Math.sin(dn/2)*Math.sin(dn/2); return 2*R*Math.asin(Math.sqrt(h)); }
  function find(id){ var r=null; if(window.DIR) window.DIR.locations.forEach(function(x){ if(x.id===id) r=x; }); return r; }
  function refPt(id){ var r=null; if(window.DIR) (window.DIR.refs||[]).forEach(function(x){ if(x.id===id) r=x; }); return r; }
  function path(p){ return window.DIR.base+window.DIR.pfx+p; }

  // ---------------- shortlist page
  var sl=document.getElementById('shortlist-app');
  if(sl&&window.DIR){
    var out=document.getElementById('sl-out'), empty=document.getElementById('sl-empty'), cmp=document.getElementById('sl-compare'), refSel=document.getElementById('sl-ref'), msg=document.getElementById('sl-msg');
    var picked=[];
    function render(){
      var ids=list().filter(function(i){return find(i);}); picked=picked.filter(function(i){return ids.indexOf(i)>=0;});
      var rp=refSel.value?refPt(refSel.value):null;
      empty.hidden=ids.length>0;
      out.innerHTML=ids.map(function(id){ var x=find(id), km=(rp&&x.la!=null)?hav(rp.la,rp.lo,x.la,x.lo):null;
        var h='<article class="card v-'+x.v+'"><div class="body"><div class="top"><label class="pick"><input type="checkbox" data-pick="'+esc(id)+'"'+(picked.indexOf(id)>=0?' checked':'')+'> <span class="sr">'+T('Select to compare','比較に選択')+'</span></label><h3><a href="'+path('/l/'+id+'/')+'">'+esc(x.n)+'</a></h3><span class="badge '+x.v+'">'+esc(window.DIR.verif[x.v][0])+'</span><button type="button" class="star-btn" data-id="'+esc(id)+'" aria-pressed="true">'+HEART+'</button></div>';
        if(x.j) h+='<div class="ja">'+esc(x.j)+'</div>';
        h+='<div class="meta">';
        if(km!=null) h+='<span><b>'+km.toFixed(1)+' km</b> '+T('to','から')+' '+esc(rp.n)+'</span>';
        if(x.h) h+='<span><i class="ico clock"></i>'+esc(x.h)+'</span>';
        if(x.p) h+='<a href="tel:'+esc(x.p.replace(/[^0-9+]/g,''))+'"><i class="ico tel"></i>'+esc(x.p)+'</a>';
        if(x.em) h+='<a href="mailto:'+esc(x.em)+'">'+esc(x.em)+'</a>';
        if(x.w) h+='<a href="'+esc(x.w)+'" rel="noopener nofollow"><i class="ico web"></i>'+T('Website','ウェブサイト')+'</a>';
        h+='</div></div></article>'; return h; }).join('');
      cmp.disabled=!(picked.length>=2&&picked.length<=3); sync();
    }
    window.OKShortRefresh=render;
    out.addEventListener('change',function(e){ var c=e.target.getAttribute&&e.target.getAttribute('data-pick'); if(!c) return;
      var i=picked.indexOf(c); if(e.target.checked){ if(picked.length>=3){ e.target.checked=false; msg.textContent=T('Compare up to three at a time.','比較は最大3社までです。'); return; } picked.push(c); } else if(i>=0) picked.splice(i,1);
      msg.textContent=''; cmp.disabled=!(picked.length>=2&&picked.length<=3); });
    refSel.addEventListener('change',render);
    cmp.addEventListener('click',function(){ location.href=path('/compare/')+'?ids='+picked.join(',')+(refSel.value?'&ref='+refSel.value:''); });
    document.getElementById('sl-print').addEventListener('click',function(){ window.print(); });
    document.getElementById('sl-copy').addEventListener('click',function(){
      var rp=refSel.value?refPt(refSel.value):null;
      var t=list().map(find).filter(Boolean).map(function(x){ var l=[x.n+(x.j?' ('+x.j+')':'')];
        if(x.a) l.push(x.a); if(x.p) l.push(T('Tel','電話')+': '+x.p); if(x.em) l.push(x.em); if(x.h) l.push(T('Hours','営業時間')+': '+x.h);
        if(rp&&x.la!=null) l.push(hav(rp.la,rp.lo,x.la,x.lo).toFixed(1)+' km '+T('to','から')+' '+rp.n);
        if(x.w) l.push(x.w); return l.join('\n'); }).join('\n\n');
      function done(ok){ msg.textContent=ok?T('Copied.','コピーしました。'):T('Could not copy. Use Print instead.','コピーできませんでした。印刷をご利用ください。'); }
      if(navigator.clipboard&&navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(function(){done(true);},function(){done(false);}); else done(false);
    });
    var q0=new URLSearchParams(location.search).get('ref'); if(q0) refSel.value=q0;
    render();
  }

  // ---------------- compare page
  var cp=document.getElementById('compare-app');
  if(cp&&window.DIR){
    var qs=new URLSearchParams(location.search), ids=(qs.get('ids')||'').split(',').filter(function(i){return find(i);}).slice(0,3);
    var tbl=document.getElementById('cp-table'), ce=document.getElementById('cp-empty'), rs=document.getElementById('cp-ref');
    if(qs.get('ref')) rs.value=qs.get('ref');
    function cell(v){ return v?esc(v):'<span class="muted">—</span>'; }
    function draw(){
      if(ids.length<2){ ce.hidden=false; tbl.innerHTML=''; return; } ce.hidden=true;
      var rp=rs.value?refPt(rs.value):null, X=ids.map(find), D=window.DIR;
      var rows=[
        [T('Verification','確認状況'),function(x){ return '<span class="badge '+x.v+'">'+esc(D.verif[x.v][0])+'</span>'; }],
        [T('Address','住所'),function(x){ return cell(x.a); }],
        [T('Phone','電話'),function(x){ return x.p?'<a href="tel:'+esc(x.p.replace(/[^0-9+]/g,''))+'">'+esc(x.p)+'</a>':cell(''); }],
        [T('Email','メール'),function(x){ return x.em?'<a href="mailto:'+esc(x.em)+'">'+esc(x.em)+'</a>':cell(''); }],
        [T('Hours','営業時間'),function(x){ return cell(x.h); }],
        [T('English support','英語対応'),function(x){ return cell(x.et); }],
        [T('Military families','米軍関係者対応'),function(x){ return cell(x.mt); }],
        [T('Services','サービス'),function(x){ return cell(x.d.map(function(d){return D.disc[d];}).join(', ')); }],
        [T('Licence no.','免許番号'),function(x){ return cell(x.lic); }]];
      if(rp) rows.splice(2,0,[T('Distance to ','距離：')+rp.n,function(x){ return x.la!=null?'<b>'+hav(rp.la,rp.lo,x.la,x.lo).toFixed(1)+' km</b> '+T('straight line','直線'):cell(''); }]);
      var h='<thead><tr><th></th>'+X.map(function(x){ return '<th><a href="'+path('/l/'+x.id+'/')+'">'+esc(x.n)+'</a>'+(x.j?'<div class="ja">'+esc(x.j)+'</div>':'')+'</th>'; }).join('')+'</tr></thead><tbody>';
      rows.forEach(function(r){ h+='<tr><th scope="row">'+r[0]+'</th>'+X.map(function(x){ return '<td>'+r[1](x)+'</td>'; }).join('')+'</tr>'; });
      tbl.innerHTML=h+'</tbody>';
    }
    rs.addEventListener('change',draw); draw();
  }

  // ---------------- checklist
  var cl=document.getElementById('checklist-app');
  if(cl){
    var boxes=cl.querySelectorAll('input[data-chk]'), st=get(CK)||{}, total=boxes.length;
    function upd(){ var n=0; boxes.forEach(function(b){ if(b.checked) n++; }); document.getElementById('cl-count').textContent=n+' of '+total+' done'; document.getElementById('cl-bar').style.width=Math.round(100*n/total)+'%'; }
    boxes.forEach(function(b){ var k=b.getAttribute('data-chk'); b.checked=!!st[k];
      b.addEventListener('change',function(){ if(b.checked) st[k]=1; else delete st[k]; set(CK,st); upd(); }); });
    document.getElementById('cl-reset').addEventListener('click',function(){ st={}; set(CK,st); boxes.forEach(function(b){b.checked=false;}); upd(); });
    document.getElementById('cl-print').addEventListener('click',function(){ window.print(); });
    upd();
  }

  // ---------------- cost estimator
  var cc=document.getElementById('cost-calc');
  if(cc){
    var f=function(id){ return Math.max(0,parseFloat(document.getElementById(id).value)||0); };
    var yen=function(n){ return '¥'+Math.round(n).toLocaleString('en-US'); };
    function calc(){
      var rent=f('c-rent'), adv=f('c-adv'), dep=f('c-dep'), key=f('c-key'), fee=Math.min(f('c-fee'),1), gua=f('c-gua'), ins=f('c-ins'), kex=f('c-kex'), rate=f('c-rate')||1;
      var L=[['First month(s) rent',rent*adv],['Deposit (shikikin)',rent*dep],['Key money (reikin)',rent*key],['Agency fee incl. 10% tax',rent*fee*1.1],['Guarantor company',rent*gua/100],['Fire insurance',ins],['Key exchange',kex]];
      var t=0; L.forEach(function(r){t+=r[1];});
      var h='<table class="data compact"><tbody>'+L.map(function(r){ return '<tr><td>'+r[0]+'</td><td class="num">'+yen(r[1])+'</td></tr>'; }).join('')+'</tbody></table>';
      h+='<p class="total"><span>Total up front</span><b>'+yen(t)+'</b></p><p class="sub" style="margin:0">≈ $'+Math.round(t/rate).toLocaleString('en-US')+' at ¥'+rate+'/$ · '+(rent?(t/rent).toFixed(1):'0')+' months of rent</p>';
      document.getElementById('c-out').innerHTML=h;
    }
    cc.addEventListener('input',calc); calc();
  }

  // ---------------- experience form
  var xf=document.getElementById('xp-form');
  if(xf){
    var qp=new URLSearchParams(location.search).get('agency'); if(qp) document.getElementById('xp-agency').value=qp;
    xf.addEventListener('submit',function(e){
      e.preventDefault(); var sel=document.getElementById('xp-agency'), name=sel.options[sel.selectedIndex].text;
      var v=function(id){ return document.getElementById(id).value; };
      var data={agency:name,month:v('xp-month'),english:v('xp-english'),fees_clear:v('xp-fees'),cost_matched:v('xp-cost'),housing_office:v('xp-office'),use_again:v('xp-again'),comment:v('xp-comment')};
      var gh=xf.getAttribute('data-gh'), mail=xf.getAttribute('data-mail'), u;
      if(gh&&gh.indexOf('OWNER')<0){
        var p=new URLSearchParams({template:'renter-experience.yml',title:'[Renter report] '+name+' ('+sel.value+')'});
        Object.keys(data).forEach(function(k){ p.set(k,data[k]); }); u='https://github.com/'+gh+'/issues/new?'+p.toString();
      } else {
        var b=['Agency: '+name+' ['+sel.value+']','Month: '+data.month,'English: '+data.english,'Fees explained: '+data.fees_clear,'Cost matched quote: '+data.cost_matched,'Housing office: '+data.housing_office,'Use again: '+data.use_again,'Comment: '+data.comment,'','I confirm this is my own experience and contains no personal details.'].join('\n');
        u='mailto:'+mail+'?subject='+encodeURIComponent('Renter report: '+name)+'&body='+encodeURIComponent(b);
      }
      document.getElementById('xp-msg').textContent=T('Opening your draft…','下書きを開いています…'); location.href=u;
    });
  }

  // ---------------- glossary filter
  var gq=document.getElementById('gloss-q');
  if(gq){
    var items=document.querySelectorAll('.gloss'), none=document.getElementById('gloss-none'), gc=document.getElementById('gloss-count');
    gq.addEventListener('input',function(){ var q=gq.value.normalize('NFKC').toLowerCase().trim(), n=0;
      items.forEach(function(g){ var ok=!q||g.getAttribute('data-t').indexOf(q)>=0; g.hidden=!ok; if(ok) n++; });
      document.querySelectorAll('.gloss-grid').forEach(function(gr){ var any=gr.querySelector('.gloss:not([hidden])'); gr.parentNode.hidden=!any; });
      none.hidden=n>0; gc.textContent=q?n+' found':''; });
  }

  // ---------------- listing mini-map
  var lm=document.getElementById('lmap');
  if(lm){
    (function init(){
      if(!window.L){ return setTimeout(init,200); }
      var la=parseFloat(lm.getAttribute('data-lat')), lo=parseFloat(lm.getAttribute('data-lon')), pts=[];
      try{ pts=JSON.parse(lm.getAttribute('data-pts')||'[]'); }catch(e){}
      var m=L.map(lm,{scrollWheelZoom:false}); L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap contributors'}).addTo(m);
      var b=[[la,lo]];
      L.circleMarker([la,lo],{radius:9,color:'#fff',weight:2,fillColor:'#0f4fe0',fillOpacity:1}).addTo(m).bindPopup('<b>'+esc(lm.getAttribute('data-name'))+'</b>');
      pts.forEach(function(p){ b.push([p.la,p.lo]); L.circleMarker([p.la,p.lo],{radius:6,color:'#fff',weight:1.5,fillColor:p.k==='base'?'#b9770e':'#6b7385',fillOpacity:.95}).addTo(m).bindTooltip(esc(p.n)); L.polyline([[la,lo],[p.la,p.lo]],{color:'#8893a8',weight:1,dashArray:'4 4'}).addTo(m); });
      m.fitBounds(b,{padding:[24,24],maxZoom:14});
    })();
  }
})();
