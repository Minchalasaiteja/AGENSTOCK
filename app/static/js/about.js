// Small canvas-based live simulation for About page
document.addEventListener('DOMContentLoaded', function(){
  // Primary canvas (decorative)
  const simCanvas = document.getElementById('about-sim');
  if(simCanvas){
    const ctx = simCanvas.getContext('2d');
    const W = simCanvas.width; const H = simCanvas.height;
    let t = 0;
    const points = [];
    for(let i=0;i<120;i++) points.push( Math.sin(i*0.08) * 10 + (Math.random()-0.5)*6 + 100 );
    function drawSim(){
      t += 0.02;
      ctx.clearRect(0,0,W,H);
      const g = ctx.createLinearGradient(0,0,0,H);
      g.addColorStop(0,'#ffffff'); g.addColorStop(1,'#f7fbff'); ctx.fillStyle = g; ctx.fillRect(0,0,W,H);
      ctx.strokeStyle = 'rgba(10,16,30,0.04)'; ctx.lineWidth=1;
      for(let y=0;y<6;y++){ ctx.beginPath(); ctx.moveTo(0,y*(H/5)); ctx.lineTo(W,y*(H/5)); ctx.stroke(); }
      ctx.beginPath(); for(let i=0;i<points.length;i++){ const x = (i/(points.length-1))*(W-40)+20; const jitter = Math.sin(t + i*0.1)*0.8; const y = H - ((points[i]-80 + jitter)/40)*(H-40) - 20; if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y); }
      ctx.strokeStyle = '#3a86ff'; ctx.lineWidth=2.8; ctx.stroke(); ctx.lineTo(W-20,H-20); ctx.lineTo(20,H-20); ctx.closePath();
      const g2 = ctx.createLinearGradient(0,0,0,H); g2.addColorStop(0,'rgba(58,134,255,0.18)'); g2.addColorStop(1,'rgba(58,134,255,0.02)'); ctx.fillStyle = g2; ctx.fill();
      const lastX = (points.length-1)/(points.length-1)*(W-40)+20; const lastY = H - ((points[points.length-1]-80)/40)*(H-40)-20;
      ctx.beginPath(); ctx.arc(lastX, lastY + Math.sin(t*2)*1.4, 5, 0, Math.PI*2); ctx.fillStyle='#ff6b6b'; ctx.fill();
      ctx.fillStyle='#0b1220'; ctx.font='12px Arial'; ctx.fillText('Live', 12, 18);
      requestAnimationFrame(drawSim);
    }
    drawSim();
  }

  // Live chart canvas wired to cached data (AAPL) with 15s poll
  const liveCanvas = document.getElementById('about-live-chart');
  if(!liveCanvas) return;
  const lctx = liveCanvas.getContext('2d');
  const LW = liveCanvas.width; const LH = liveCanvas.height;
  let livePoints = [];
  const DEFAULT_SYMBOL = 'AAPL';
  const POLL_MS = 15000;

  function renderLive(points){
    lctx.clearRect(0,0,LW,LH);
    if(!points || points.length===0){
      // draw placeholder axes
      lctx.fillStyle='#fff'; lctx.fillRect(0,0,LW,LH);
      lctx.fillStyle='#6b7280'; lctx.font='14px Arial'; lctx.fillText('No live data — falling back to simulation', 12, 22);
      return;
    }
    // normalize
    const vals = points.map(p=>p.close ?? p);
    const min = Math.min(...vals); const max = Math.max(...vals);
    const pad = (max-min)*0.1 || 1;
    const range = (max-min) + pad*2;
    // background
    const g = lctx.createLinearGradient(0,0,0,LH); g.addColorStop(0,'#ffffff'); g.addColorStop(1,'#f8fbff'); lctx.fillStyle = g; lctx.fillRect(0,0,LW,LH);
    // draw line
    lctx.beginPath();
    for(let i=0;i<points.length;i++){
      const v = vals[i];
      const x = 20 + (i/(points.length-1))*(LW-40);
      const y = LH - ((v - min + pad)/range)*(LH-40) - 20;
      if(i===0) lctx.moveTo(x,y); else lctx.lineTo(x,y);
    }
    lctx.strokeStyle = '#3a86ff'; lctx.lineWidth = 2.5; lctx.stroke();
    // latest dot
    const lx = 20 + ((points.length-1)/(points.length-1))*(LW-40); const ly = LH - ((vals[vals.length-1]-min + pad)/range)*(LH-40) - 20;
    lctx.beginPath(); lctx.arc(lx, ly, 5, 0, Math.PI*2); lctx.fillStyle='#06d6a0'; lctx.fill();
  }

  async function pollEnhanced(){
    try{
      // Use the public demo endpoint so About is accessible without login
      const res = await fetch('/api/research/enhanced-public', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ symbol: DEFAULT_SYMBOL, timeframe: '1mo' }) });
      if(!res.ok) throw new Error('no-ok');
      const payload = await res.json();
      // support both payload.research.chart_series and payload.chart_series
      let series = null;
      if (payload) {
        if (payload.research && payload.research.chart_series) series = payload.research.chart_series;
        else if (payload.chart_series) series = payload.chart_series;
        else if (payload.research && payload.research.historical) series = payload.research.historical;
      }
      if(series && series.length>0){
        livePoints = series.slice(-60).map(p=>({date:p.date, close: p.close}));
        renderLive(livePoints);
        return;
      }
    }catch(err){
      // fallback simulation
      const sim = [];
      for(let i=0;i<60;i++) sim.push(100 + Math.sin(i*0.15 + Date.now()*0.0005)*6 + (Math.random()-0.5)*2 );
      renderLive(sim);
    }
  }

  // initial poll and interval
  pollEnhanced();
  setInterval(pollEnhanced, POLL_MS);
});
