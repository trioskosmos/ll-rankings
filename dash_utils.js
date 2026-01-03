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
    let maxDist = 0;
    coords.forEach(p => {
        const d = Math.sqrt(p.x * p.x + p.y * p.y);
        maxDist = Math.max(maxDist, d);
    });

    // 2. Calculate Theoretical Max Radius
    // N = number of songs. 
    const N = data.song_names ? Object.keys(data.song_names).length : 0;
    const theoMax = N > 1 ? Math.sqrt((Math.pow(N, 2) - 1) / 3) : 0;

    // 3. Determine scale (fit both data and theoretical max)
    // If theoMax is generated (N>0), use it as the outer bound.
    // Otherwise fallback to data bounds.
    const outerBound = theoMax > 0 ? theoMax : (maxDist || 1);

    // padding = 30px
    const padding = 30;
    const safeRadius = Math.min(w, h) / 2 - padding;

    // Scale: map outerBound to safeRadius
    const scale = safeRadius / outerBound;

    // --- DRAW ---
    ctx.clearRect(0, 0, w, h);

    // Draw Theoretical Max Boundary
    if (theoMax > 0) {
        ctx.strokeStyle = 'rgba(219, 97, 162, 0.3)'; // Pinkish low opacity
        ctx.setLineDash([5, 5]); // Dashed
        ctx.beginPath();
        ctx.arc(cx, cy, theoMax * scale, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]); // Reset

        // Label for Max Radius
        ctx.fillStyle = 'rgba(219, 97, 162, 0.5)';
        ctx.font = '9px Inter';
        ctx.textAlign = 'center';
        ctx.fillText("Theoretical Limit", cx, cy - (theoMax * scale) - 5);
    }

    // Grid rings (simple) 
    // We can draw intermediate rings based on the max radius now? 
    // Let's keep the fixed pixel rings or make them proportional?
    // Let's make them proportional to 50% of max
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.beginPath(); ctx.arc(cx, cy, (theoMax * scale) * 0.5, 0, Math.PI * 2); ctx.stroke();

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
