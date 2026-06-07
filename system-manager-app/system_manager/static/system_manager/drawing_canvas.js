(function(){
  const canvas = document.getElementById('maintenance-drawing-canvas');
  const input = document.querySelector('[data-drawing-canvas-data="1"]');
  if(!canvas || !input) return;
  const ctx = canvas.getContext('2d');
  let drawing=false, erase=false, last=null;
  function drawGrid(){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle='#ffffff'; ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.strokeStyle='#dfe7e5'; ctx.lineWidth=1;
    for(let x=0;x<canvas.width;x+=18){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,canvas.height);ctx.stroke();}
    for(let y=0;y<canvas.height;y+=18){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(canvas.width,y);ctx.stroke();}
  }
  drawGrid();
  function pos(e){
    const r=canvas.getBoundingClientRect();
    const p=e.touches ? e.touches[0] : e;
    return {x:(p.clientX-r.left)*canvas.width/r.width, y:(p.clientY-r.top)*canvas.height/r.height};
  }
  function start(e){drawing=true;last=pos(e);e.preventDefault();}
  function move(e){
    if(!drawing) return; const p=pos(e); ctx.beginPath(); ctx.moveTo(last.x,last.y); ctx.lineTo(p.x,p.y); ctx.lineCap='round'; ctx.lineJoin='round'; ctx.lineWidth=erase?18:3; ctx.strokeStyle=erase?'#ffffff':'#111111'; ctx.stroke(); last=p; input.value=canvas.toDataURL('image/png'); e.preventDefault();
  }
  function end(){drawing=false; input.value=canvas.toDataURL('image/png');}
  canvas.addEventListener('mousedown',start); canvas.addEventListener('mousemove',move); window.addEventListener('mouseup',end);
  canvas.addEventListener('touchstart',start,{passive:false}); canvas.addEventListener('touchmove',move,{passive:false}); canvas.addEventListener('touchend',end);
  document.querySelectorAll('[data-draw-tool]').forEach(btn=>btn.addEventListener('click',()=>{const t=btn.dataset.drawTool;if(t==='erase') erase=true;if(t==='pen') erase=false;if(t==='clear'){drawGrid(); input.value='';}}));
})();
