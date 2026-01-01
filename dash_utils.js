function initDashboardConstellation(data) {
    // data = { matrix: {...}, rankings: {...}, song_names: {...} }
    const cvs = document.getElementById('dash-taste-canvas');
    if (!cvs || !data.matrix) return;
    const ctx = cvs.getContext('2d');

    // Set canvas size
    const rect = cvs.getBoundingClientRect();
    cvs.width = rect.width; cvs.height = rect.height;
    const w = cvs.width, h = cvs.height;
    const cx = w / 2, cy = h / 2;

    const users = Object.keys(data.matrix);
    if (users.length < 3) {
        ctx.fillStyle = '#666'; ctx.textAlign = 'center'; ctx.fillText("Not enough users", cx, cy); return;
    }

    const distMatrix = users.map(u1 => users.map(u2 => data.matrix[u1][u2]));
    let mdsResult;
    try { mdsResult = MathLib.mds(distMatrix); } catch (e) { return; }

    const coords = mdsResult.coords; // {x,y,z}

    // --- AUTO ZOOM LOGIC ---
    // 1. Find bounding box of all points relative to center 0,0
    let maxX = 0, maxY = 0;
    coords.forEach(p => {
        maxX = Math.max(maxX, Math.abs(p.x));
        maxY = Math.max(maxY, Math.abs(p.y));
    });

    // 2. Calculate scale to fill ~90% of the smallest dimension
    // padding = 20px
    const padding = 30;
    const safeW = (w / 2) - padding;
    const safeH = (h / 2) - padding;

    // If all points are at 0,0 (perfect consensus), default scale 1
    const scaleX = maxX > 0 ? safeW / maxX : 1;
    const scaleY = maxY > 0 ? safeH / maxY : 1;

    // Use the smaller scale to maintain aspect ratio and fit everything
    const scale = Math.min(scaleX, scaleY);

    // --- DRAW ---
    ctx.clearRect(0, 0, w, h);

    // Grid rings (simple)
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.beginPath(); ctx.arc(cx, cy, 50, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath(); ctx.arc(cx, cy, 100, 0, Math.PI * 2); ctx.stroke();

    // Axis lines
    ctx.strokeStyle = 'rgba(255,255,255,0.1)';
    ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(w, cy); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(cx, 0); ctx.lineTo(cx, h); ctx.stroke();

    // Nodes
    const nodes = users.map((u, i) => ({
        id: u,
        x: coords[i].x * scale + cx,
        y: coords[i].y * scale + cy,
        color: `hsl(${280 + ((i * 40) % 80)}, 70%, 60%)`,
        initials: u.substring(0, 2).toUpperCase()
    }));

    // Draw furthest first if we had 3D Z-depth, but for 2D standard draw is fine
    nodes.forEach(n => {
        ctx.fillStyle = n.color;
        ctx.beginPath(); ctx.arc(n.x, n.y, 6, 0, Math.PI * 2); ctx.fill();

        // Initials
        ctx.fillStyle = "#fff";
        ctx.font = "bold 9px Inter";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(n.initials, n.x, n.y + 12);
    });

    // Label
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    ctx.font = '10px Inter';
    ctx.textAlign = 'right';
    ctx.fillText("Zoomed View", w - 10, h - 10);
}
