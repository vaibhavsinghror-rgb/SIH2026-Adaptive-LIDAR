import json
import os

sample_path = 'project/scripts/sample_frame.json'
with open(sample_path, 'r') as f:
    data = json.load(f)

raw_json = json.dumps(data['raw'])
cells_json = json.dumps(data['cells'])

html_content = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    canvas {{ touch-action: none; cursor: grab; }}
    canvas:active {{ cursor: grabbing; }}
  </style>
</head>
<body class="bg-transparent text-[var(--foreground)] antialiased p-2 select-none">
  <div class="bg-[var(--card)] text-[var(--foreground)] border border-[var(--border)] rounded-xl p-3 shadow-md max-w-2xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-[var(--border)] pb-2 mb-2">
      <div>
        <h2 class="font-bold text-sm tracking-wide flex items-center gap-1.5">
          <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
          Adaptive Foveated 2.5D LiDAR Mapping
        </h2>
        <p class="text-xs text-[var(--muted-foreground)]">SIH26053 • KITTI Sequence 00 • Frame 0000</p>
      </div>
      <div class="flex items-center gap-1 text-[11px]">
        <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-semibold border border-emerald-500/20">-43.3% Mem</span>
        <span class="px-2 py-0.5 rounded bg-blue-500/10 text-blue-500 font-semibold border border-blue-500/20">~10.7 FPS</span>
      </div>
    </div>

    <!-- Controls -->
    <div class="flex flex-wrap items-center justify-between gap-2 mb-2 text-xs">
      <div class="flex items-center bg-[var(--background)] border border-[var(--border)] rounded-lg p-0.5">
        <button id="btnFov" class="px-2.5 py-1 rounded-md font-medium bg-emerald-600 text-white shadow-sm transition" onclick="setView('fov')">Foveated 2.5D Grid</button>
        <button id="btnRaw" class="px-2.5 py-1 rounded-md font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition" onclick="setView('raw')">Raw LiDAR Cloud</button>
      </div>
      <div class="flex items-center gap-2 text-[11px]">
        <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-emerald-500"></span> Near (5cm)</span>
        <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-blue-500"></span> Mid (20cm)</span>
        <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-amber-500"></span> Far (50cm)</span>
      </div>
    </div>

    <!-- Canvas Container -->
    <div class="relative bg-[var(--background)] border border-[var(--border)] rounded-lg overflow-hidden flex justify-center items-center h-[260px]">
      <canvas id="lidarCanvas" width="580" height="260" class="w-full h-full"></canvas>
      <div class="absolute bottom-2 left-2 text-[10px] text-[var(--muted-foreground)] bg-[var(--card)]/80 backdrop-blur px-2 py-0.5 rounded border border-[var(--border)]">
        Drag to Pan • Scroll to Zoom
      </div>
      <div class="absolute top-2 right-2 flex flex-col gap-1 text-[10px]">
        <button class="px-2 py-0.5 bg-[var(--card)] border border-[var(--border)] rounded shadow-xs hover:bg-[var(--border)]" onclick="resetView()">Reset View</button>
      </div>
    </div>

    <!-- Stats Bar -->
    <div class="grid grid-cols-4 gap-2 mt-2 pt-2 border-t border-[var(--border)] text-center text-xs">
      <div class="p-1 rounded bg-[var(--background)]/60">
        <span class="text-[10px] text-[var(--muted-foreground)] block">Raw Points</span>
        <span class="font-bold">124,668</span>
      </div>
      <div class="p-1 rounded bg-[var(--background)]/60">
        <span class="text-[10px] text-[var(--muted-foreground)] block">Foveated Cells</span>
        <span class="font-bold text-emerald-500">37,909</span>
      </div>
      <div class="p-1 rounded bg-[var(--background)]/60">
        <span class="text-[10px] text-[var(--muted-foreground)] block">Baseline Cells</span>
        <span class="font-bold text-[var(--muted-foreground)]">66,878</span>
      </div>
      <div class="p-1 rounded bg-[var(--background)]/60">
        <span class="text-[10px] text-[var(--muted-foreground)] block">Memory Saved</span>
        <span class="font-bold text-emerald-500">339.5 KB</span>
      </div>
    </div>
  </div>

  <script>
    const rawData = {raw_json};
    const cellData = {cells_json};

    let currentView = 'fov';
    const canvas = document.getElementById('lidarCanvas');
    const ctx = canvas.getContext('2d');

    let scale = 3.6;
    let offsetX = canvas.width / 2;
    let offsetY = canvas.height * 0.78;
    let isDragging = false;
    let startX = 0, startY = 0;

    function setView(view) {{
      currentView = view;
      document.getElementById('btnFov').className = view === 'fov' 
        ? 'px-2.5 py-1 rounded-md font-medium bg-emerald-600 text-white shadow-sm transition' 
        : 'px-2.5 py-1 rounded-md font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition';
      document.getElementById('btnRaw').className = view === 'raw' 
        ? 'px-2.5 py-1 rounded-md font-medium bg-emerald-600 text-white shadow-sm transition' 
        : 'px-2.5 py-1 rounded-md font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition';
      draw();
    }}

    function resetView() {{
      scale = 3.6;
      offsetX = canvas.width / 2;
      offsetY = canvas.height * 0.78;
      draw();
    }}

    function draw() {{
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Range concentric rings (10m, 30m, 60m)
      const rings = [
        {{ r: 10, label: '10m (5cm)', color: 'rgba(16, 185, 129, 0.35)' }},
        {{ r: 30, label: '30m (20cm)', color: 'rgba(59, 130, 246, 0.3)' }},
        {{ r: 60, label: '60m (50cm)', color: 'rgba(245, 158, 11, 0.25)' }}
      ];

      rings.forEach(ring => {{
        const rad = ring.r * scale;
        ctx.strokeStyle = ring.color;
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.arc(offsetX, offsetY, rad, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = ring.color;
        ctx.font = '9px monospace';
        ctx.fillText(ring.label, offsetX + rad + 4, offsetY);
      }});

      // Draw vehicle origin
      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.arc(offsetX, offsetY, 4, 0, Math.PI * 2);
      ctx.fill();

      if (currentView === 'fov') {{
        cellData.forEach(cell => {{
          const cx = offsetX + cell.y * scale;
          const cy = offsetY - cell.x * scale;

          if (cx < -20 || cx > canvas.width + 20 || cy < -20 || cy > canvas.height + 20) return;

          let color;
          if (cell.res <= 0.08) color = '#10b981';
          else if (cell.res <= 0.25) color = '#3b82f6';
          else color = '#f59e0b';

          if (cell.label === 2) color = '#ef4444';

          const size = Math.max(2, cell.res * scale * 1.5);
          ctx.fillStyle = color;
          ctx.fillRect(cx - size/2, cy - size/2, size, size);
        }});
      }} else {{
        rawData.forEach(pt => {{
          const px = offsetX + pt.y * scale;
          const py = offsetY - pt.x * scale;

          if (px < -10 || px > canvas.width + 10 || py < -10 || py > canvas.height + 10) return;

          let color = '#10b981';
          if (pt.label === 1) color = '#3b82f6';
          else if (pt.label === 2) color = '#ef4444';

          ctx.fillStyle = color;
          ctx.fillRect(px, py, 1.5, 1.5);
        }});
      }}
    }}

    canvas.addEventListener('mousedown', e => {{
      isDragging = true;
      startX = e.clientX - offsetX;
      startY = e.clientY - offsetY;
    }});

    window.addEventListener('mousemove', e => {{
      if (!isDragging) return;
      offsetX = e.clientX - startX;
      offsetY = e.clientY - startY;
      draw();
    }});

    window.addEventListener('mouseup', () => {{ isDragging = false; }});

    canvas.addEventListener('wheel', e => {{
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
      scale = Math.max(1, Math.min(25, scale * zoomFactor));
      draw();
    }}, {{ passive: false }});

    draw();
  </script>
</body>
</html>
'''

out_path = 'C:/Users/abc/.gemini/antigravity/brain/16d615ae-5d5b-4b2f-9b44-bc894d965bac/foveated_viewer.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print('Successfully generated foveated_viewer.html!')
