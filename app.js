const API = "http://localhost:8000/api/v1";
let activeTab = 'dash', allSubgroups = [];

// Data cache to prevent redundant API calls
let dataCache = { key: '', ranks: null, cont: null, takes: null, spice: null, loaded: false };

// Song metadata cache for year sorting (populated from song-info.json)
let songMetadata = {}; // { songName: { year: 2021, releasedOn: '2021-01-01' } }
let currentLeaderboardRanks = []; // Store current rankings for re-sorting


// Basic/Advanced Mode Toggle
window.advancedMode = false;
function toggleAdvancedMode() {
    window.advancedMode = !window.advancedMode;
    const btn = document.getElementById('mode-toggle');
    if (window.advancedMode) {
        btn.innerHTML = 'Advanced Mode';
        btn.style.background = 'var(--pink)';
        btn.style.color = '#000';
        btn.style.borderColor = 'var(--pink)';
        document.getElementById('btn-oshi').style.display = 'block';
    } else {
        btn.innerHTML = 'Basic Mode';
        btn.style.background = 'transparent';
        btn.style.color = 'var(--muted)';
        btn.style.borderColor = 'var(--border)';
        document.getElementById('btn-oshi').style.display = 'none';
        if (activeTab === 'oshi') tab('dash');
    }
    // Re-render current tab with new limits
    if (dataCache.loaded) {
        renderCurrentTab();
    }
}

// Helper to get list limit based on mode
function getLimit(basic, advanced) {
    return window.advancedMode ? advanced : basic;
}

async function init() {
    await Promise.all([fetchMasterSubgroups(), fetchSongMetadata()]);
    tab('dash'); // Force dashboard view logic on startup
}

// Load song metadata from song-info.json for year sorting
async function fetchSongMetadata() {
    try {
        const res = await fetch('data/song-info.json');
        const songs = await res.json();
        songs.forEach(s => {
            const year = s.releasedOn ? parseInt(s.releasedOn.split('-')[0]) : null;
            songMetadata[s.name] = { year, releasedOn: s.releasedOn || '' };
        });
        console.log(`Loaded metadata for ${Object.keys(songMetadata).length} songs`);
    } catch (e) {
        console.warn('Could not load song metadata:', e);
    }
}

// Apply leaderboard sorting based on dropdown selection
function applyLeaderboardSort() {
    if (!currentLeaderboardRanks.length) return;
    const sortBy = document.getElementById('leaderboard-sort').value;
    let sorted = [...currentLeaderboardRanks];

    switch (sortBy) {
        case 'year-desc':
            sorted.sort((a, b) => {
                const yearA = songMetadata[a.song_name]?.year || 0;
                const yearB = songMetadata[b.song_name]?.year || 0;
                return yearB - yearA || a.song_name.localeCompare(b.song_name);
            });
            break;
        case 'year-asc':
            sorted.sort((a, b) => {
                const yearA = songMetadata[a.song_name]?.year || 9999;
                const yearB = songMetadata[b.song_name]?.year || 9999;
                return yearA - yearB || a.song_name.localeCompare(b.song_name);
            });
            break;
        case 'name':
            sorted.sort((a, b) => a.song_name.localeCompare(b.song_name));
            break;
        case 'rank':
        default:
            // Already in rank order from API
            break;
    }

    renderLeaderboardRows(sorted, sortBy !== 'rank');
}

// Render leaderboard table rows (can show year column)
function renderLeaderboardRows(ranks, showYear = false) {
    const yearCol = showYear ? '<col class="col-metric">' : '';
    const yearHeader = showYear ? '<th>Year</th>' : '';

    document.getElementById('c-leaderboard').innerHTML = `<table><colgroup><col class="col-rank"><col>${yearCol}<col class="col-metric"><col class="col-metric"></colgroup><tr><th>#</th><th>Song Name</th>${yearHeader}<th>Avg</th><th>Pts</th></tr>` +
        ranks.map((s, i) => {
            const year = songMetadata[s.song_name]?.year || '—';
            const yearCell = showYear ? `<td class="col-metric" style="color:var(--muted)">${year}</td>` : '';
            return `<tr onclick="showSongDistribution('${s.song_name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="clickable-row"><td class="col-rank">${i + 1}</td><td>${s.song_name}</td>${yearCell}<td class="col-metric" style="color:var(--pink)">${s.average}</td><td class="col-metric">${s.points}</td></tr>`;
        }).join('') + `</table>`;
}


async function fetchMasterSubgroups() {
    const franchises = ["liella", "aqours", "u's", "nijigasaki", "hasunosora"];
    const results = await Promise.all(franchises.map(f => fetch(`${API}/subgroups?franchise=${f}`).then(r => r.json()).catch(() => [])));
    allSubgroups = results.flat();
    updateSubgroupDropdown();
}

function updateSubgroupDropdown() {
    const f = document.getElementById('view-franchise').value, sel = document.getElementById("view-subgroup");
    const filtered = allSubgroups.filter(sg => sg.franchise === f);
    sel.innerHTML = filtered.map(s => `<option value="${s.name}">${s.name}</option>`).join("");
    if (filtered.some(s => s.name === "All Songs")) sel.value = "All Songs";
    else if (filtered.length > 0) sel.selectedIndex = 0;
}

function changeFranchiseView() {
    dataCache = { key: '', ranks: null, cont: null, takes: null, spice: null, loaded: false }; // Clear cache
    wipeUI();
    updateSubgroupDropdown();
    syncData(true); // Force fetch
}

function changeSubgroupView() {
    dataCache = { key: '', ranks: null, cont: null, takes: null, spice: null, loaded: false }; // Clear cache
    wipeUI();
    syncData(true); // Force fetch
}

function wipeUI() {
    const ids = ['c-leaderboard', 'c-universal', 'c-disputed', 'c-subunits', 'c-controversy', 'c-sleeper', 'c-consistent', 'c-outliers', 'c-matrix', 'c-spice', 'c-dash-top5', 'c-dash-bottom5', 'duel-disputes', 'match-results', 'users-content'];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = "Refreshing..."; });
    ['d-top-song', 'd-cont-song', 'd-spice-user', 'd-sleep-song', 'd-agreed-song', 'd-total-songs'].forEach(id => document.getElementById(id).innerHTML = "...");
    const dr = document.getElementById('duel-results');
    if (dr) dr.classList.add('hidden');
    // Also clear users stats
    const us = document.getElementById('users-stats-container');
    if (us) us.innerHTML = '';
}

function tab(name) {
    activeTab = name;
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    document.getElementById(`btn-${name}`).classList.add('active');
    document.querySelectorAll('main > div').forEach(v => v.classList.add('hidden'));
    document.getElementById(`view-${name}`).classList.remove('hidden');
    syncData(false); // Don't force, use cache if available
}

async function syncData(forceFetch = false) {
    const sub = document.getElementById('view-subgroup').value, f = document.getElementById('view-franchise').value;
    if (!sub) return;

    // Immediately load Users tab data - it has its own API call, no need to wait
    if (activeTab === 'users') {
        loadUsers(); // Fire and forget - don't await
    }

    // Priority fetch for Constellation to ensure immediate refresh
    if (activeTab === 'constellation') {
        try {
            const res = await fetch(`${API}/analysis/divergence?franchise=${encodeURIComponent(f)}&subgroup=${encodeURIComponent(sub)}`);
            const data = await res.json();
            if (data && data.matrix) initConstellation(data);
        } catch (e) { console.error("Constellation load error:", e); }
        // Do not return, let standard data load proceed
    }

    const cacheKey = `${f}|${sub}`;
    let ranks, cont, takes, spice;

    // Check if we have cached data for this franchise/subgroup
    if (!forceFetch && dataCache.loaded && dataCache.key === cacheKey) {
        // Use cached data
        ranks = dataCache.ranks;
        cont = dataCache.cont;
        takes = dataCache.takes;
    } else {
        // Fetch fresh data with timeout
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

            [ranks, cont, takes] = await Promise.all([
                fetch(`${API}/analysis/rankings?franchise=${f}&subgroup=${sub}`, { signal: controller.signal }).then(r => r.ok ? r.json() : null),
                fetch(`${API}/analysis/controversy?franchise=${f}&subgroup=${sub}`, { signal: controller.signal }).then(r => r.ok ? r.json() : null),
                fetch(`${API}/analysis/takes?franchise=${f}&subgroup=${sub}`, { signal: controller.signal }).then(r => r.ok ? r.json() : null)
            ]);

            clearTimeout(timeoutId);

            const oldSpice = dataCache.spice; // Preserve spice if exists
            dataCache = { key: cacheKey, ranks, cont, takes, spice: oldSpice, loaded: true };
        } catch (e) {
            console.error('Fetch error:', e);
            if (e.name === 'AbortError') {
                const ids = ['c-leaderboard', 'c-universal', 'c-disputed', 'c-subunits', 'c-controversy', 'c-sleeper', 'c-consistent', 'c-outliers', 'c-matrix', 'c-spice', 'c-dash-top5', 'c-dash-bottom5'];
                ids.forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = "Request timed out. Please refresh."; });
            }
            return;
        }
    }


    // Render tabs that don't depend on specific subgroup rankings first
    if (activeTab === 'spice' || activeTab === 'dash') fetchSpiceData();
    if (activeTab === 'oshi') fetchUserList();
    // Users already loaded above - no need to call again


    if (!ranks || !ranks.rankings) {
        // If on a rankings-dependent tab, we might want to show a message
        if (['leader', 'more', 'opps'].includes(activeTab)) {
            console.warn("Rankings not available for this subgroup.");
        }
        return;
    }

    // Always update Dashboard Stats (if available) - Spice updated via its own fetch if needed
    updateDashboard(ranks.rankings, cont?.results, takes?.takes, null);

    // Always render full leaderboard data in background (so it's ready)
    renderLeaderboard(ranks.rankings);

    // Conditional rendering for active tabs to save DOM cycles
    if (activeTab === 'more') {
        renderUniversal(ranks.rankings, cont?.results || []); renderDisputed(takes?.takes || []);
        renderSubunitPopularity(ranks.rankings, cont?.results || [], f); renderControversy(cont?.results || []);
        renderConsistent(cont?.results || []); renderSleepers(takes?.takes || []);
        renderHaters(takes?.takes || []);
    }
    if (activeTab === 'opps') renderMatrix(sub, f);
    if (activeTab === 'tiers') renderTierStats(ranks.rankings);
    if (activeTab === 'aff') renderAffinity(ranks.rankings);

    // Render dashboard constellation when on dashboard tab
    if (activeTab === 'dash') {
        try {
            const divRes = await fetch(`${API}/analysis/divergence?franchise=${encodeURIComponent(f)}&subgroup=${encodeURIComponent(sub)}`);
            const divData = await divRes.json();
            if (divData && divData.matrix) initDashboardConstellation(divData);
        } catch (e) { console.warn('Dashboard constellation error:', e); }
    }
}

// Re-render current tab with cached data (used when mode changes)
function renderCurrentTab() {
    if (!dataCache.loaded) return;
    const { ranks, cont, takes } = dataCache;
    const f = document.getElementById('view-franchise').value;
    const sub = document.getElementById('view-subgroup').value;

    if (ranks?.rankings) {
        updateDashboard(ranks.rankings, cont?.results, takes?.takes, null);
        renderLeaderboard(ranks.rankings);
    }
    if (activeTab === 'more' && ranks?.rankings) {
        renderUniversal(ranks.rankings, cont?.results || []);
        renderDisputed(takes?.takes || []);
        renderSubunitPopularity(ranks.rankings, cont?.results || [], f);
        renderControversy(cont?.results || []);
        renderConsistent(cont?.results || []);
        renderSleepers(takes?.takes || []);
        renderHaters(takes?.takes || []);
    }
    if (activeTab === 'opps') renderMatrix(sub, f);
    if (activeTab === 'spice' || activeTab === 'dash') fetchSpiceData();
    if (activeTab === 'constellation' || activeTab === 'oshi') fetchUserList();
    if (activeTab === 'tiers' && ranks?.rankings) renderTierStats(ranks.rankings);
    if (activeTab === 'aff' && ranks?.rankings) renderAffinity(ranks.rankings);
}


function updateDashboard(ranks, cont, takes, spice) {
    // 1. Top Song
    if (ranks.length > 0) {
        const top = ranks[0];
        document.getElementById('d-top-song').innerHTML = `<span onclick="showSongDistribution('${top.song_name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="song-link">${truncate(top.song_name, 22)}</span>`;
        document.getElementById('d-top-score').innerHTML = `${top.average} avg rank`;

        // Total songs count
        document.getElementById('d-total-songs').innerHTML = ranks.length;

        // Render Top 5 and Bottom 5
        renderDashTop5(ranks.slice(0, 5));
        renderDashBottom5(ranks.slice(-5).reverse());
    }

    // 2. Controversial
    if (cont && cont.length > 0) {
        const c = cont[0];
        document.getElementById('d-cont-song').innerHTML = `<span onclick="showSongDistribution('${c.song_name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="song-link">${truncate(c.song_name, 22)}</span>`;
        document.getElementById('d-cont-score').innerHTML = `${c.controversy_score} score`;

        // Most Agreed (lowest controversy)
        const agreed = [...cont].sort((a, b) => a.controversy_score - b.controversy_score)[0];
        if (agreed) {
            document.getElementById('d-agreed-song').innerHTML = `<span onclick="showSongDistribution('${agreed.song_name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="song-link">${truncate(agreed.song_name, 22)}</span>`;
            document.getElementById('d-agreed-score').innerHTML = `${agreed.controversy_score} score`;
        }
    }

    // 3. Spiciest User
    // This will now rely on the dataCache.spice which is fetched by fetchSpiceData
    if (dataCache.spice && dataCache.spice.results && dataCache.spice.results.length > 0) {
        const s = dataCache.spice.results[0];
        const card = document.getElementById('card-spice');
        if (card) {
            card.onclick = () => showSpiceDetail(s.username);
            card.style.cursor = 'pointer';
            card.onmouseover = () => card.style.transform = 'scale(1.02)';
            card.onmouseout = () => card.style.transform = 'scale(1)';
        }
        document.getElementById('d-spice-user').innerText = s.username;
        document.getElementById('d-spice-val').innerHTML = `${s.global_spice} spice`;
    }


    // 4. Sleeper Hit
    if (takes && takes.length > 0) {
        const sleeper = [...takes].sort((a, b) => a.score - b.score)[0];
        if (sleeper && sleeper.score < 0) {
            document.getElementById('d-sleep-song').innerHTML = `<span onclick="showSongDistribution('${sleeper.song_name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="song-link">${truncate(sleeper.song_name, 22)}</span>`;
            document.getElementById('d-sleep-user').innerHTML = `Loved by ${sleeper.username}`;
        }
    }
}

function truncate(str, len) {
    return str.length > len ? str.substring(0, len) + '…' : str;
}

function renderDashTop5(ranks) {
    const el = document.getElementById('c-dash-top5');
    if (!el) return;
    el.innerHTML = `<table>` +
        ranks.map((s, i) => `
                    <tr onclick="showSongDistribution('${s.song_name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="clickable-row">
                        <td class="col-rank" style="color:${i === 0 ? '#ffd700' : i === 1 ? '#c0c0c0' : i === 2 ? '#cd7f32' : 'var(--pink)'}">#${i + 1}</td>
                        <td>${s.song_name}</td>
                        <td class="col-metric" style="color:var(--green)">${s.average}</td>
                    </tr>
                `).join('') + `</table>`;
}

function renderDashBottom5(ranks) {
    const el = document.getElementById('c-dash-bottom5');
    if (!el) return;
    const total = parseInt(document.getElementById('d-total-songs')?.innerHTML) || 100;
    el.innerHTML = `<table>` +
        ranks.map((s, i) => `
                    <tr onclick="showSongDistribution('${s.song_name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="clickable-row">
                        <td class="col-rank">#${total - i}</td>
                        <td>${s.song_name}</td>
                        <td class="col-metric" style="color:var(--red)">${s.average}</td>
                    </tr>
                `).join('') + `</table>`;
}


function renderLeaderboard(ranks) {
    // Store for re-sorting and reset sort dropdown
    currentLeaderboardRanks = ranks;
    const sortDropdown = document.getElementById('leaderboard-sort');
    if (sortDropdown) sortDropdown.value = 'rank';

    // Render with default ranking order
    renderLeaderboardRows(ranks, false);
}


function closeSongModal(event) {
    if (event && event.target.id !== 'song-modal') return;
    document.getElementById('song-modal').classList.add('hidden');
    document.getElementById('song-modal').style.display = 'none';
}

async function showSongDistribution(songName) {
    const modal = document.getElementById('song-modal');
    const content = document.getElementById('song-modal-content');
    document.getElementById('song-modal-title').textContent = songName;
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    content.innerHTML = 'Loading distribution...';

    try {
        const f = document.getElementById('view-franchise').value;
        const sub = document.getElementById('view-subgroup').value;
        const res = await fetch(`${API}/analysis/divergence?franchise=${f}&subgroup=${sub}`);
        const data = await res.json();

        // Get song rankings from cached data or fetch
        const songId = Object.keys(data.song_names).find(id => data.song_names[id] === songName);
        if (!songId || !data.rankings[songId]) {
            content.innerHTML = 'No ranking data available for this song.';
            return;
        }

        const userRanks = data.rankings[songId];
        const users = Object.keys(userRanks).sort();
        const ranks = users.map(u => userRanks[u]);
        const mean = ranks.reduce((a, b) => a + b, 0) / ranks.length;
        const std = Math.sqrt(ranks.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / ranks.length);
        const minRank = 1;
        const maxRank = Object.keys(data.song_names).length;
        const range = (maxRank - minRank) || 1;

        // Create number line visualization
        content.innerHTML = `
                    <div style="margin-bottom:25px; text-align:center;">
                        <div style="display:inline-flex; gap:40px; font-size:15px;">
                            <div class="stat-item"><span style="color:var(--muted); font-size:11px; display:block; text-transform:uppercase;">Community Mean</span> <span style="font-weight:900; color:var(--pink); font-size:22px;">#${mean.toFixed(1)}</span></div>
                            <div class="stat-item"><span style="color:var(--muted); font-size:11px; display:block; text-transform:uppercase;">Std Deviation</span> <span style="font-weight:900; color:#fff; font-size:22px;">${std.toFixed(2)}</span></div>
                            <div class="stat-item"><span style="color:var(--muted); font-size:11px; display:block; text-transform:uppercase;">Total Voters</span> <span style="font-weight:900; color:#fff; font-size:22px;">${users.length}</span></div>
                        </div>
                    </div>
                    
                    <div style="position:relative; height:120px; border-radius:12px; margin:30px 0; border:1px solid var(--border); background:#0d1117; overflow:hidden;">
                        <!-- Selection Area Coloration (Constrained to Data Range) -->
                         <div style="position:absolute; top:0; bottom:0; left:25px; right:25px; background:linear-gradient(90deg, rgba(63,185,80,0.1) 0%, rgba(219,97,162,0.1) 50%, rgba(248,81,73,0.1) 100%); border-left:1px solid rgba(255,255,255,0.1); border-right:1px solid rgba(255,255,255,0.1);"></div>

                        <!-- Main line (Visual Only, centered in the data range) -->
                        <div style="position:absolute; top:65px; left:25px; right:25px; height:2px; background:rgba(255,255,255,0.1);"></div>
                        
                        <!-- Mean marker -->
                        <div style="position:absolute; top:35px; left:calc(25px + ${(mean - minRank) / range} * (100% - 50px)); transform:translateX(-50%); text-align:center; z-index:5;">
                            <div style="font-size:9px; color:var(--pink); font-weight:900; letter-spacing:1px; margin-bottom:2px;">AVG</div>
                            <div style="width:2px; height:50px; background:var(--pink); margin:0 auto; box-shadow:0 0 10px var(--pink);"></div>
                        </div>

                        <!-- Std dev range box -->
                        <div style="position:absolute; top:60px; height:10px; background:rgba(219,97,162,0.25); border:1px border var(--pink); border-radius:4px; 
                            left:calc(25px + ${Math.max(0, (mean - std - minRank) / range)} * (100% - 50px)); 
                            width:calc(${(2 * std) / range} * (100% - 50px)); z-index:2;"></div>

                        <!-- User dots -->
                        ${users.map((user, i) => {
            const rank = userRanks[user];
            const pct = (rank - minRank) / range;
            const color = rank < (mean - 2) ? 'var(--green)' : rank > (mean + 2) ? 'var(--red)' : 'var(--pink)';
            return `<div title="${user}: #${rank}" 
                                style="position:absolute; top:58px; left:calc(25px + ${pct} * (100% - 50px)); transform:translateX(-50%); 
                                width:16px; height:16px; background:${color}; border-radius:50%; border:2px solid #fff; cursor:pointer; z-index:${10 + i}; transition:all 0.2s;"
                                onmouseover="this.style.transform='translateX(-50%) scale(1.4)'; this.style.zIndex='100';"
                                onmouseout="this.style.transform='translateX(-50%) scale(1)'; this.style.zIndex='${10 + i}';"
                                onclick="event.stopPropagation(); showUserComparison('${user}', '${user}')"></div>`;
        }).join('')}
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:-10px; padding:0 25px;">
                         <div style="font-size:10px; color:var(--green); font-weight:800; text-transform:uppercase;">← High Rank (Love)</div>
                         <div style="font-size:10px; color:var(--red); font-weight:800; text-transform:uppercase;">Low Rank (Hate) →</div>
                    </div>

                    <div style="margin-top:35px;"><h4 style="margin-bottom:15px; font-size:14px; text-transform:uppercase; letter-spacing:1px; color:var(--muted);">Voter Breakdown</h4>
                        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(140px, 1fr)); gap:10px;">
                            ${users.sort((a, b) => userRanks[a] - userRanks[b]).map(u => `
                                <div style="padding:10px 12px; background:var(--card); border:1px solid var(--border); border-radius:8px; display:flex; justify-content:space-between; align-items:center; cursor:pointer;" onclick="showUserComparison('${u}', '${u}')">
                                    <span style="font-size:12px; font-weight:600;">${u.substring(0, 10)}</span>
                                    <span style="font-weight:900; color:var(--pink); font-family:monospace;">#${userRanks[u]}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
    } catch (e) {
        console.error(e);
        content.innerHTML = 'Error loading distribution data.';
    }
}

async function showUserComparison(u1, u2) {
    const modal = document.getElementById('song-modal');
    const content = document.getElementById('song-modal-content');
    document.getElementById('song-modal-title').textContent = u1 === u2 ? 'Self-Reflection' : `${u1} vs ${u2}`;
    modal.classList.remove('hidden');
    modal.style.display = 'flex';

    if (u1 === u2) {
        content.innerHTML = `
                    <div style="text-align:center; padding:40px 20px; font-style:italic;">
                        <p style="font-size:18px; line-height:1.6; color:#fff;">
                            "Now you're tired of fighting (Fighting)<br>
                            Tired of fighting, fighting yourself"
                        </p>
                        <p style="font-size:14px; color:var(--muted); margin-top:15px;">— Matt Bellamy</p>
                    </div>
                `;
        return;
    }

    content.innerHTML = '<div style="padding:20px;">Loading comparison...</div>';

    try {
        const f = document.getElementById('view-franchise').value, sub = document.getElementById('view-subgroup').value;
        const r = await fetch(`${API}/analysis/head-to-head?franchise=${f}&subgroup=${sub}&user_a=${u1}&user_b=${u2}`);
        const data = await r.json();

        const n = data.diffs.length;
        // Calculate Raw RMS
        const rawRms = Math.sqrt(data.diffs.reduce((s, d) => s + Math.pow(d.diff, 2), 0) / n);
        // Normalize: Divide by (N-1) to get approx 0-1 range, then * 100 for percentage
        // Note: For random uniform rankings, expected absolute rank diff is N/3.
        // Standardizing against N-1 is a simple way to make it roughly scale-invariant.
        const rms = ((rawRms / Math.max(1, n - 1)) * 100).toFixed(1);

        window.__compData = { u1, u2, diffs: data.diffs, rms, rawRms: rawRms.toFixed(2), activeTab: 'dis' };
        renderCompModal();

    } catch (e) { console.error(e); content.innerHTML = '<div style="padding:20px;">Error loading comparison.</div>'; }
}

window.switchCompTab = (tab) => {
    if (!window.__compData) return;
    window.__compData.activeTab = tab;
    renderCompModal();
};

function renderCompModal() {
    const { u1, u2, diffs, rms, activeTab } = window.__compData;
    const content = document.getElementById('song-modal-content');

    let tableHtml = "";
    let sortedArr = [...diffs];

    if (activeTab === 'u1') {
        sortedArr.sort((a, b) => a.r1 - b.r1);
    } else if (activeTab === 'dis') {
        sortedArr.sort((a, b) => b.diff - a.diff);
    } else if (activeTab === 'agr') {
        sortedArr.sort((a, b) => a.diff - b.diff);
    }

    if (activeTab === 'math') {
        const sumSq = diffs.reduce((s, d) => s + Math.pow(d.diff, 2), 0);
        const n = diffs.length;
        const varVal = (sumSq / n).toFixed(2);
        const rawRms = Math.sqrt(sumSq / n).toFixed(2);

        tableHtml = `
                    <div style="border-left:3px solid var(--pink); padding-left:15px; margin-bottom:20px;">
                        <h4 style="font-size:13px; margin-bottom:10px; color:var(--pink);">Normalized Divergence Formula</h4>
                        <div style="font-family:'Consolas', monospace; font-size:12px; line-height:1.8; color:var(--muted);">
                            RMS = √(Σ(diff²)/N)<br>
                            <span style="color:#fff; font-weight:bold;">Metric = (RMS / (N-1)) × 100</span>
                        </div>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px; margin-bottom:20px;">
                        <div class="card" style="padding:12px;">
                            <div style="font-size:10px; color:var(--muted); text-transform:uppercase; margin-bottom:5px;">Raw RMS</div>
                            <div style="font-size:20px; font-weight:900; color:#fff;">${rawRms}</div>
                        </div>
                        <div class="card" style="padding:12px;">
                            <div style="font-size:10px; color:var(--muted); text-transform:uppercase; margin-bottom:5px;">Avg Rank Diff</div>
                            <div style="font-size:20px; font-weight:900; color:#fff;">${rawRms}</div>
                        </div>
                        <div class="card" style="padding:12px; grid-column:span 2; background:var(--pink);">
                            <div style="font-size:10px; color:#000; text-transform:uppercase; margin-bottom:5px; opacity:0.7;">Final Normalized Score</div>
                            <div style="font-size:20px; font-weight:900; color:#000;">${rms}%</div>
                        </div>
                    </div>
                    <h4 style="font-size:13px; margin-bottom:10px;">
                        Complete Breakdown 
                        ${window.isAdvancedMode ? '' : '<span style="color:var(--muted); font-weight:400;">(Top 10 - Switch to Advanced for Full List)</span>'}
                    </h4>
                    <table style="margin-top:10px;">
                        <tr><th>Song</th><th>${u1}</th><th>${u2}</th><th>Diff</th><th>Diff²</th></tr>
                        ${diffs.sort((a, b) => b.diff - a.diff).slice(0, window.isAdvancedMode ? diffs.length : 10).map(d => `
                            <tr>
                                <td>${d.name}</td>
                                <td style="color:var(--muted)">#${d.r1}</td>
                                <td style="color:var(--muted)">#${d.r2}</td>
                                <td>${d.diff.toFixed(0)}</td>
                                <td style="color:var(--red)">${(d.diff * d.diff).toFixed(0)}</td>
                            </tr>
                        `).join('')}
                    </table>
                `;
    } else {
        tableHtml = `
                    <table>
                        <colgroup><col><col style="width:70px"><col style="width:70px"><col style="width:60px"></colgroup>
                        <tr><th>Song</th><th>${u1}</th><th>${u2}</th><th>Diff</th></tr>
                        ${sortedArr.map(d => `
                            <tr onclick="showSongDistribution('${d.name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="clickable-row">
                                <td>${d.name}</td>
                                <td style="color:${d.r1 < d.r2 ? 'var(--green)' : 'var(--muted)'}">#${d.r1}</td>
                                <td style="color:${d.r2 < d.r1 ? 'var(--green)' : 'var(--muted)'}">#${d.r2}</td>
                                <td style="font-weight:bold; color:${d.diff > 20 ? 'var(--red)' : d.diff < 5 ? 'var(--green)' : 'var(--pink)'}">${Math.round(d.diff)}</td>
                            </tr>
                        `).join('')}
                    </table>
                `;
    }

    content.innerHTML = `
                <div style="text-align:center; padding:10px 0 20px 0; border-bottom:1px solid var(--border); margin-bottom:15px;">
                    <div style="font-size:32px; font-weight:900; color:var(--pink)">${rms}% <span style="font-size:12px; font-weight:600; color:var(--muted); vertical-align:middle;">DIVERGENCE</span></div>
                    
                    ${(() => {
            let wins = 0, losses = 0, ties = 0;
            diffs.forEach(d => {
                if (d.r1 < d.r2) wins++;
                else if (d.r1 > d.r2) losses++;
                else ties++;
            });
            const total = wins + losses + ties;

            return `
                        <div style="margin-top:15px; background:rgba(0,0,0,0.2); padding:10px; border-radius:8px;">
                            <div style="display:flex; justify-content:space-between; font-size:11px; font-weight:700; text-transform:uppercase; color:var(--muted); margin-bottom:5px;">
                                <span>${u1} Higher (${wins})</span>
                                <span>${u2} Higher (${losses})</span>
                            </div>
                            <div style="height:8px; display:flex; border-radius:4px; overflow:hidden;">
                                <div style="width:${(wins / total) * 100}%; background:var(--green);"></div>
                                <div style="width:${(ties / total) * 100}%; background:var(--muted);"></div>
                                <div style="width:${(losses / total) * 100}%; background:var(--pink);"></div>
                            </div>
                        </div>
                        `;
        })()}
                </div>

                <div class="comp-tabs">
            <div class="comp-tab ${activeTab === 'u1' ? 'active' : ''}" onclick="switchCompTab('u1')">${u1}'s Order</div>
            <div class="comp-tab ${activeTab === 'dis' ? 'active' : ''}" onclick="switchCompTab('dis')">Disagreements</div>
            <div class="comp-tab ${activeTab === 'agr' ? 'active' : ''}" onclick="switchCompTab('agr')">Agreements</div>
            <div class="comp-tab ${activeTab === 'math' ? 'active' : ''}" onclick="switchCompTab('math')">🧮 How It's Calculated</div>
        </div>
                <div style="margin-top:10px;">
                    ${tableHtml}
                </div>
            `;
}

function renderUniversal(ranks, controversy) {
    const limit = getLimit(10, Math.floor(ranks.length / 2));
    const top = ranks.slice(0, limit), btm = ranks.slice(-limit);
    const mapAgreement = (songName) => {
        const c = controversy.find(x => x.song_name === songName);
        return c ? Math.max(0, 100 - ((c.cv * c.avg_rank) * 2.5)).toFixed(1) : "0.0";
    };
    const rows = [...top, ...btm].map((s, i) => `<tr onclick="showSongDistribution('${s.song_name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="clickable-row"><td class="col-rank" style="color:${i < limit ? 'var(--green)' : 'var(--red)'}">${i < limit ? 'TOP' : 'BTM'}</td><td>${s.song_name}</td><td class="col-metric" style="color:var(--pink)">${s.average}</td><td class="col-metric">${mapAgreement(s.song_name)}%</td></tr>`).join('');
    document.getElementById('c-universal').innerHTML = `<table><colgroup><col class="col-rank"><col><col class="col-metric"><col class="col-metric"></colgroup><thead><tr><th>Type</th><th>Song</th><th>Avg</th><th>Agr</th></tr></thead>${rows}</table>` +
        (!window.advancedMode && ranks.length > limit * 2 ? `<div style="padding:10px; text-align:center; font-size:11px; color:var(--muted); background:rgba(0,0,0,0.2); border-top:1px solid rgba(255,255,255,0.05);">Showing top/bottom ${limit} of ${ranks.length} songs. Enable Advanced Mode for full list.</div>` : '');
}

function renderDisputed(takes) {
    const limit = getLimit(10, 50);
    const songGroups = {};
    takes.forEach(t => { if (!songGroups[t.song_name]) songGroups[t.song_name] = []; songGroups[t.song_name].push(t); });
    const res = Object.keys(songGroups).map(name => {
        const g = songGroups[name].sort((a, b) => a.user_rank - b.user_rank);
        return { name, fight: `${g[0].username} vs ${g[g.length - 1].username}`, diff: Math.abs(g[g.length - 1].user_rank - g[0].user_rank) };
    }).sort((a, b) => b.diff - a.diff);

    const displayRes = res.slice(0, limit);

    document.getElementById('c-disputed').innerHTML = `<table><colgroup><col><col class="col-fight"><col class="col-metric"></colgroup>` +
        `<thead><tr><th style="text-align:left; padding-left:10px;">Song</th><th style="padding-left:10px;">Fight</th><th class="col-metric">Diff</th></tr></thead>` +
        displayRes.map(r => `<tr onclick="showSongDistribution('${r.name.replace(/'/g, "\\'")}')" style="cursor:pointer" class="clickable-row"><td style="padding:4px 10px;">${r.name}</td><td class="col-fight" style="padding-left:10px;">${r.fight}</td><td class="col-metric" style="color:var(--pink); font-weight:bold;">${r.diff}</td></tr>`).join('') +
        `</table>` +
        (!window.advancedMode && res.length > limit ? `<div style="padding:10px; text-align:center; font-size:11px; color:var(--muted); background:rgba(0,0,0,0.2); border-top:1px solid rgba(255,255,255,0.05);">Showing top ${limit} of ${res.length} disputes. Enable Advanced Mode for full list.</div>` : '');
}

function showMetricExplanation(type) {
    const modal = document.getElementById('song-modal');
    const content = document.getElementById('song-modal-content');
    const title = document.getElementById('song-modal-title');

    modal.classList.remove('hidden');
    modal.style.display = 'flex';

    const definitions = {
        disputed: {
            title: "Most Disputed",
            math: "Δ = Rank_Max - Rank_Min",
            desc: "Calculates the raw gap between the person who loves the song the most vs. the person who hates it the most.",
            use: "Identifies songs with the most extreme polarization. A high 'Fight' score means two users are essentially at war."
        },
        sleeper: {
            title: "Sleeper Picks",
            math: "Score = User_Rank - Avg_Rank (where < -15)",
            desc: "Identifies songs that a specific user ranks significantly HIGHER (lower number) than the community average.",
            use: "Finds your 'hidden gems'—songs you defend that everyone else ignores."
        },
        haters: {
            title: "Hot Takes",
            math: "Score = User_Rank - Avg_Rank (where > 15)",
            desc: "Identifies songs that a specific user ranks significantly LOWER (higher number) than the community average.",
            use: "Exposes your controversial dislikes. These are the popular songs you just don't get."
        },
        controversy: {
            title: "Controversy Score",
            math: "Score = StdDev * WeightingFactor",
            desc: "A composite metric that measures the overall spread of opinion. <b>Div (Divergence)</b> in the table is the Coefficient of Variation (StdDev / Mean).",
            use: "High Controversy = The community is confused or split. Low Controversy = Everyone agrees."
        },
        consistent: {
            title: "Consistent Tracks",
            math: "Score ≈ 0 (Lowest StdDev)",
            desc: "Songs with the lowest standard deviation in rankings.",
            use: "The 'Safe Bets'. These songs are universally agreed upon, whether they are good or bad. No one fights about them."
        },
        subunits: {
            title: "Subunit Power",
            math: "Avg = Σ(Song_Ranks) / Song_Count",
            desc: "The geometric mean rank of all songs belonging to a specific subunit.",
            use: "Objectively determines which subunit has the strongest overall discography according to the group."
        },
        outliers: {
            title: "Spice Meter",
            math: "Distance = Euclidean_Dist(User_Vector, Consensus_Vector)",
            desc: "Measures how far a user's taste vector deviates from the 'average' taste vector of the group.",
            use: "<b>High Spice</b> = Unique, contrarian taste.<br><b>Low Spice</b> = NPC energy (agrees with the majority)."
        }
    };

    const def = definitions[type];
    if (!def) return;

    title.textContent = def.title;
    content.innerHTML = `
                <div style="padding:10px;">
                    <div class="card" style="margin-bottom:20px; border-left:4px solid var(--pink);">
                        <h4 style="margin:0 0 10px 0; color:var(--pink);">The Math</h4>
                        <div style="font-family:'Consolas', monospace; font-size:14px; background:rgba(0,0,0,0.2); padding:10px; border-radius:6px;">
                            ${def.math}
                        </div>
                    </div>
                    
                    <div style="margin-bottom:20px;">
                        <h4 style="margin-bottom:10px;">What is this?</h4>
                        <p style="line-height:1.6; color:#ccc;">${def.desc}</p>
                    </div>

                    <div>
                        <h4 style="margin-bottom:10px;">Why use it?</h4>
                        <p style="line-height:1.6; color:#ccc;">${def.use}</p>
                    </div>
                </div>
            `;
}

function renderSubunitPopularity(rankings, controversy, franchise) {
    // Include meaningful categories: Subunits, Solos, Group Songs, and special collections like Liella no Uta
    const categoriesToIndex = ['Solos', 'Group Songs', 'Liella no Uta'];
    const units = allSubgroups.filter(sg =>
        sg.franchise === franchise && (sg.is_subunit || categoriesToIndex.includes(sg.name))
    );

    if (!units.length) { document.getElementById('c-subunits').innerHTML = "No category data."; return; }

    const data = units.map(unit => {
        const rS = rankings.filter(r => unit.songs.includes(r.song_name)), cS = controversy.filter(r => unit.songs.includes(r.song_name));
        return {
            name: unit.name,
            avg: rS.length ? (rS.reduce((a, b) => a + b.average, 0) / rS.length).toFixed(2) : 0,
            div: cS.length ? (cS.reduce((a, b) => a + b.cv, 0) / cS.length).toFixed(4) : 0,
            count: rS.length
        };
    }).filter(d => d.count > 0).sort((a, b) => a.avg - b.avg);

    document.getElementById('c-subunits').innerHTML = `<table><colgroup><col><col class="col-metric"><col class="col-metric"></colgroup><tr><th>Category</th><th class="col-metric">Avg</th><th class="col-metric">Div</th></tr>` + data.map(d => `<tr><td style="font-weight:bold">${d.name}</td><td class="col-metric" style="color:var(--pink)">${d.avg}</td><td class="col-metric">${d.div}</td></tr>`).join('') + `</table>`;
}

function renderControversy(results) {
    const limit = getLimit(10, results.length);
    document.getElementById('c-controversy').innerHTML = `<table><colgroup><col><col class="col-metric"><col class="col-metric"></colgroup><tr><th>Song</th><th class="col-metric">Score</th><th class="col-metric">Div</th></tr>` + results.slice(0, limit).map(s => `<tr onclick="showSongDistribution('${s.song_name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="clickable-row"><td>${s.song_name}</td><td class="col-metric" style="color:var(--pink)">${s.controversy_score}</td><td class="col-metric">${s.cv}</td></tr>`).join('') + `</table>` +
        (!window.advancedMode && results.length > limit ? `<div style="padding:10px; text-align:center; font-size:11px; color:var(--muted); background:rgba(0,0,0,0.2); border-top:1px solid rgba(255,255,255,0.05);">Showing top ${limit} of ${results.length}. Enable Advanced Mode for full list.</div>` : '');
}
function renderConsistent(results) {
    const limit = getLimit(10, results.length);
    const sorted = [...results].sort((a, b) => a.controversy_score - b.controversy_score);
    document.getElementById('c-consistent').innerHTML = `<table><colgroup><col><col class="col-metric"><col class="col-metric"></colgroup><tr><th>Song</th><th class="col-metric">Score</th><th class="col-metric">Avg</th></tr>` + sorted.slice(0, limit).map(s => `<tr onclick="showSongDistribution('${s.song_name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="clickable-row"><td>${s.song_name}</td><td class="col-metric" style="color:var(--pink)">${s.controversy_score}</td><td class="col-metric">${s.avg_rank}</td></tr>`).join('') + `</table>` +
        (!window.advancedMode && sorted.length > limit ? `<div style="padding:10px; text-align:center; font-size:11px; color:var(--muted); background:rgba(0,0,0,0.2); border-top:1px solid rgba(255,255,255,0.05);">Showing top ${limit} of ${sorted.length}. Enable Advanced Mode for full list.</div>` : '');
}
function renderSleepers(takes) {
    const limit = getLimit(10, 50);
    const allSleepers = takes.filter(t => t.score < -15);
    const sleepers = allSleepers.slice(0, limit);
    document.getElementById('c-sleeper').innerHTML = `<table><colgroup><col><col class="col-metric"><col class="col-metric"></colgroup><tr><th>Song</th><th class="col-metric">Lover</th><th class="col-metric">Gap</th></tr>` + sleepers.map(t => `<tr onclick="showSongDistribution('${t.song_name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="clickable-row"><td>${t.song_name}</td><td class="col-metric">${t.username.substring(0, 8)}</td><td class="col-metric" style="color:var(--green)">${Math.abs(t.delta).toFixed(1)}</td></tr>`).join('') + `</table>` +
        (!window.advancedMode && allSleepers.length > limit ? `<div style="padding:10px; text-align:center; font-size:11px; color:var(--muted); background:rgba(0,0,0,0.2); border-top:1px solid rgba(255,255,255,0.05);">Showing top ${limit} of ${allSleepers.length} sleepers. Enable Advanced Mode for full list.</div>` : '');
}
function renderHaters(takes) {
    const limit = getLimit(10, 50);
    const allHaters = takes.filter(t => t.score > 15);
    const displayHaters = allHaters.slice(0, limit);

    document.getElementById('c-haters').innerHTML = `<table><colgroup><col><col class="col-metric"><col class="col-metric"></colgroup>` +
        `<thead><tr><th style="padding-left:10px; text-align:left;">Song</th><th class="col-metric">Hater</th><th class="col-metric">Gap</th></tr></thead>` +
        displayHaters.map(t => `<tr onclick="showSongDistribution('${t.song_name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="clickable-row"><td style="padding:4px 10px;">${t.song_name}</td><td class="col-metric">${t.username.substring(0, 8)}</td><td class="col-metric" style="color:var(--red); font-weight:bold;">${Math.abs(t.delta).toFixed(1)}</td></tr>`).join('') +
        `</table>` +
        (!window.advancedMode && allHaters.length > limit ? `<div style="padding:10px; text-align:center; font-size:11px; color:var(--muted); background:rgba(0,0,0,0.2); border-top:1px solid rgba(255,255,255,0.05);">Showing top ${limit} of ${allHaters.length} haters. Enable Advanced Mode for full list.</div>` : '');
}

async function fetchSpiceData(force = false) {
    const f = document.getElementById('view-franchise').value;
    const sub = document.getElementById('view-subgroup').value;
    const cacheKey = `spice_${f}`;

    // If we have cached data for this franchise, use it unless forced
    if (!force && dataCache.spice && dataCache.spiceKey === cacheKey) {
        renderSpice(dataCache.spice.results);
        return;
    }

    const el = document.getElementById('c-spice');
    if (el) el.innerHTML = '<div style="padding:60px; text-align:center;"><div class="spinner"></div><div style="margin-top:20px; color:var(--muted); letter-spacing:1px; font-size:12px; text-transform:uppercase;">Mixing the spice...</div></div>';

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 12000);

        const res = await fetch(`${API}/analysis/spice?franchise=${f}`, { signal: controller.signal });
        clearTimeout(timeoutId);

        if (!res.ok) throw new Error("API Error");

        const data = await res.json();

        // Update global cache
        dataCache.spice = data;
        dataCache.spiceKey = cacheKey;

        if (activeTab === 'spice') renderSpice(data.results);

        // Also update dashboard card if we are on dashboard
        if (activeTab === 'dash' && data.results.length > 0) {
            const s = data.results[0];
            const card = document.getElementById('card-spice');
            if (card) {
                // Ensure click handler is attached
                card.onclick = () => window.showSpiceDetail(s.username);
                card.title = "View Spice Details";
            }
            const valEl = document.getElementById('d-spice-val');
            if (valEl) valEl.innerHTML = `${s.global_spice.toFixed(2)} spice`;
            const subEl = document.getElementById('d-spice-user');
            if (subEl) subEl.innerHTML = `<span style="font-weight:bold">${s.username}</span>`;
        }

    } catch (e) {
        console.error("Spice fetch error:", e);
        if (el) el.innerHTML = `<div style="padding:40px; text-align:center; color:var(--red);">
                    <div style="font-size:24px; margin-bottom:10px;">⚠️</div>
                    <div>Failed to load spice data.</div>
                    <button onclick="fetchSpiceData(true)" style="margin-top:15px; background:var(--card-bg); border:1px solid var(--border); color:var(--text); padding:8px 16px; border-radius:4px; cursor:pointer;">Retry Request</button>
                </div>`;
    }
}

function renderSpice(results) {
    const el = document.getElementById('c-spice');
    if (!el) return;

    if (!results || !results.length) {
        el.innerHTML = '<div style="padding:40px; color:var(--muted); text-align:center;">No spice data available for this franchise.</div>';
        return;
    }

    const sub = document.getElementById('view-subgroup').value;
    const isAll = sub === 'All Songs';
    const showAdvanced = window.advancedMode;

    // Header with Refresh Button
    const headerHtml = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                    <div>
                        <h3 style="margin:0; font-size:18px; color:var(--pink);">🔥 Spiciest Users <span style="font-size:14px; opacity:0.6; margin-left:10px;">${sub}</span></h3>
                        <div style="font-size:11px; color:var(--muted); margin-top:4px;">Users with the most controversial ${isAll ? 'overall' : 'group'} takes</div>
                    </div>
                    <button onclick="fetchSpiceData(true)" style="background:transparent; border:1px solid var(--border); color:var(--muted); padding:6px 12px; border-radius:4px; cursor:pointer; font-size:12px; transition:all 0.2s;" onmouseover="this.style.color='var(--text)'; this.style.borderColor='var(--text)'" onmouseout="this.style.color='var(--muted)'; this.style.borderColor='var(--border)'">
                        ↻ Refresh
                    </button>
                </div>
            `;

    // Process results based on subgroup
    let filtered = results.map(u => ({
        username: u.username,
        score: isAll ? u.global_spice : (u.group_breakdown ? u.group_breakdown[sub] : null),
        global: u.global_spice, // Keep global for context
        raw: u // Keep raw for advanced
    })).filter(u => u.score !== null && u.score !== undefined);

    if (filtered.length === 0) {
        el.innerHTML = headerHtml + `<div style="padding:40px; color:var(--muted); text-align:center; background:var(--card-bg); border-radius:8px; border:1px solid var(--border);">No spice data found for subgroup "${sub}".</div>`;
        return;
    }

    // Sort by the absolute backend score (already normalized to 0-100)
    filtered.sort((a, b) => b.score - a.score);

    // PODIUM (Top 3)
    const top3 = filtered.slice(0, 3);
    const rest = filtered.slice(3, 23); // Top 20 after top 3

    let podiumHtml = '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:15px; margin-bottom:25px;">';
    const medals = ['🥇', '🥈', '🥉'];

    top3.forEach((u, idx) => {
        podiumHtml += `
                    <div onclick="window.showSpiceDetail('${u.username.replace(/'/g, "\\'")}')" style="background:linear-gradient(135deg, var(--card-bg) 0%, rgba(255,105,180,0.05) 100%); border:1px solid ${idx === 0 ? 'var(--gold)' : 'var(--border)'}; border-radius:12px; padding:20px; text-align:center; cursor:pointer; transition:transform 0.2s;" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
                        <div style="font-size:24px; margin-bottom:10px;">${medals[idx]}</div>
                        <div style="font-weight:bold; font-size:16px; margin-bottom:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${u.username}</div>
                        <div style="font-size:24px; font-weight:900; color:var(--pink);">${u.score.toFixed(1)}</div>
                        <div style="font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">Spice Score</div>
                        <div style="font-size:10px; color:var(--muted);">(out of 100)</div>
                    </div>
                `;
    });
    podiumHtml += '</div>';

    // LIST (The rest) - Use absolute scores for bars (capped at 100 for visual)
    let tableHtml = `<div style="background:var(--card-bg); border:1px solid var(--border); border-radius:8px; overflow:hidden;">
                <table style="width:100%; border-collapse:collapse;">
                <thead style="background:rgba(255,255,255,0.02); border-bottom:1px solid var(--border);">
                    <tr>
                        <th style="padding:12px 15px; text-align:left; font-size:11px; color:var(--muted); text-transform:uppercase;">Rank</th>
                        <th style="padding:12px 15px; text-align:left; font-size:11px; color:var(--muted); text-transform:uppercase;">User</th>
                        <th style="padding:12px 15px; text-align:center; font-size:11px; color:var(--muted); text-transform:uppercase;">Spice</th>
                        ${showAdvanced && !isAll ? `<th style="padding:12px 15px; text-align:center; font-size:11px; color:var(--muted); text-transform:uppercase;">Global</th>` : ''}
                        <th style="padding:12px 15px; width:40%;"></th>
                    </tr>
                </thead><tbody>`;

    tableHtml += rest.map((u, idx) => `
                <tr onclick="window.showSpiceDetail('${u.username.replace(/'/g, "\\'")}')" style="cursor:pointer; border-bottom:1px solid rgba(255,255,255,0.03);" class="clickable-row">
                    <td style="padding:10px 15px; color:var(--muted); font-family:monospace;">#${idx + 4}</td>
                    <td style="padding:10px 15px; font-weight:600;">${u.username}</td>
                    <td style="padding:10px 15px; text-align:center; color:var(--pink); font-weight:bold;">${u.score.toFixed(1)}</td>
                    ${showAdvanced && !isAll ? `<td style="padding:10px 15px; text-align:center; color:var(--muted); font-size:12px;">${u.global.toFixed(1)}</td>` : ''}
                    <td style="padding:10px 15px;"><div class="bar-bg" style="width:100%; height:6px;"><div class="bar-fill" style="width:${Math.min(u.score, 100)}%"></div></div></td>
                </tr>
            `).join('');

    tableHtml += '</tbody></table></div>';

    // Calculate theoretical maximum spice
    // With proper normalization, max spice = 100 (perfectly inverted rankings)
    const songCount = sub === 'All Songs' ? 147 : (allSubgroups.find(s => s.name === sub)?.songs?.length || 20);

    const maxSpiceHtml = `
                <div style="margin-top:30px; padding:20px; background:linear-gradient(135deg, rgba(255,105,180,0.05) 0%, rgba(147,112,219,0.05) 100%); border:1px solid rgba(255,105,180,0.2); border-radius:12px;">
                    <h4 style="margin:0 0 15px; font-size:16px; color:var(--pink); display:flex; align-items:center; gap:10px;">
                        🧮 Theoretical Maximum Spice
                    </h4>
                    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:15px;">
                        <div style="background:rgba(0,0,0,0.2); padding:15px; border-radius:8px; text-align:center;">
                            <div style="font-size:28px; font-weight:900; color:var(--pink);">100</div>
                            <div style="font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:1px; margin-top:5px;">Max Possible Score</div>
                        </div>
                        <div style="background:rgba(0,0,0,0.2); padding:15px; border-radius:8px; text-align:center;">
                            <div style="font-size:28px; font-weight:900; color:var(--text);">${songCount}</div>
                            <div style="font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:1px; margin-top:5px;">Songs in ${sub}</div>
                        </div>
                        <div style="background:rgba(0,0,0,0.2); padding:15px; border-radius:8px; text-align:center;">
                            <div style="font-size:28px; font-weight:900; color:var(--gold);">${filtered.length > 0 ? filtered[0].score.toFixed(0) : 0}%</div>
                            <div style="font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:1px; margin-top:5px;">Top User Score</div>
                        </div>
                    </div>
                    <div style="margin-top:15px; font-size:11px; color:var(--muted); line-height:1.6;">
                        <strong>Formula:</strong> Spice = (RMS / max_RMS) × 100. Perfectly inverted rankings = 100.
                    </div>
                </div>
            `;

    el.innerHTML = headerHtml + podiumHtml + tableHtml + maxSpiceHtml;
}

// Explicitly attach to window to ensure global accessibility
window.showSpiceDetail = async function (username) {
    console.log("Showing spice detail for:", username);
    const modal = document.getElementById('song-modal');
    const content = document.getElementById('song-modal-content');
    if (!modal || !content) return;

    content.innerHTML = '<div style="padding:40px; text-align:center;"><div class="spinner"></div><div style="margin-top:20px; color:var(--muted);">Analyzing spice levels...</div></div>';
    modal.classList.remove('hidden');
    modal.style.display = 'flex';

    try {
        // Fetch fresh spice data for this user
        const f = document.getElementById('view-franchise').value;
        const sub = document.getElementById('view-subgroup').value;

        // Get pre-loaded spice data from cache first to show something immediate
        const cachedUser = dataCache.spice?.results?.find(u => u.username === username);
        let scoreDisplay = 'N/A';

        if (cachedUser) {
            if (sub === 'All Songs') {
                scoreDisplay = cachedUser.global_spice.toFixed(2);
            } else if (cachedUser.group_breakdown && cachedUser.group_breakdown[sub]) {
                scoreDisplay = cachedUser.group_breakdown[sub].toFixed(2);
            }
        }

        const res = await fetch(`${API}/analysis/spice?franchise=${f}&_t=${Date.now()}`);
        const data = await res.json();
        // Update cache with fresh data
        dataCache.spice = data;
        const userResult = data.results.find(u => u.username === username);

        if (!userResult) {
            content.innerHTML = '<div style="padding:20px; text-align:center;">User data not found.</div>';
            return;
        }

        // Filter extreme picks by the CURRENTLY SELECTED SUBGROUP if not "All Songs"
        let allPicks = userResult.extreme_picks || [];

        // Check if we should show global or local picks
        const showGlobal = window.spiceDetailShowGlobal || false;
        let picks = allPicks;

        console.log(`Total picks: ${allPicks.length}, Current subgroup: "${sub}", Show global: ${showGlobal}`);

        if (!showGlobal && sub !== 'All Songs') {
            picks = allPicks.filter(p => p.group === sub);
            console.log(`Filtered to ${picks.length} picks for "${sub}"`);
        }

        // Sort picks by deviation (descending)
        picks.sort((a, b) => b.deviation - a.deviation);

        // Limit to top 5 unless in advanced mode
        if (!window.advancedMode) {
            picks = picks.slice(0, 5);
        }

        const showGroupColumn = showGlobal || sub === 'All Songs';

        // Calculate song count for this group
        const groupSongCount = sub === 'All Songs' ? 147 : (allSubgroups.find(s => s.name === sub)?.songs?.length || allPicks.filter(p => p.group === sub).length || 20);

        // Tab state
        const activeTab = window.spiceModalTab || 'picks';

        content.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:20px;">
                        <div>
                            <h2 style="margin:0; font-size:24px; color:var(--text);">${username}</h2>
                            <div style="color:var(--muted); font-size:14px; margin-top:5px;">Spice Analysis (${sub})</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:32px; font-weight:900; color:var(--pink); line-height:1;">${scoreDisplay}</div>
                            <div style="font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:1px;">Spice Score</div>
                            ${window.advancedMode && sub !== 'All Songs' && cachedUser ?
                `<div style="font-size:12px; color:var(--muted); margin-top:5px;">Global: <span style="color:var(--text);">${cachedUser.global_spice.toFixed(2)}</span></div>`
                : ''}
                        </div>
                    </div>

                    <div style="margin-bottom:15px; display:flex; gap:5px; border-bottom:1px solid var(--border); padding-bottom:10px;">
                        <button onclick="window.spiceModalTab='picks'; window.showSpiceDetail('${username.replace(/'/g, "\\'")}')" 
                            style="padding:8px 16px; font-size:12px; font-weight:600; border:none; border-radius:4px 4px 0 0; cursor:pointer; background:${activeTab === 'picks' ? 'var(--pink)' : 'transparent'}; color:${activeTab === 'picks' ? '#000' : 'var(--muted)'};">
                            🔥 Extreme Picks
                        </button>
                        <button onclick="window.spiceModalTab='math'; window.showSpiceDetail('${username.replace(/'/g, "\\'")}')" 
                            style="padding:8px 16px; font-size:12px; font-weight:600; border:none; border-radius:4px 4px 0 0; cursor:pointer; background:${activeTab === 'math' ? 'var(--pink)' : 'transparent'}; color:${activeTab === 'math' ? '#000' : 'var(--muted)'};">
                            📐 How It's Calculated
                        </button>
                    </div>

                    ${activeTab === 'math' ? `
                    <div style="padding:20px; background:var(--card-bg); border:1px solid var(--border); border-radius:12px;">
                        <h3 style="margin:0 0 15px; color:var(--pink);">Spice Score Formula</h3>
                        
                        <div style="background:rgba(0,0,0,0.3); padding:20px; border-radius:8px; font-family:monospace; margin-bottom:20px;">
                            <div style="font-size:18px; color:var(--text); text-align:center;">
                                Spice = (RMS ÷ Max_RMS) × 100
                            </div>
                        </div>

                        <div style="font-size:13px; color:var(--muted); line-height:1.8;">
                            <p><strong style="color:var(--text);">Where:</strong></p>
                            <ul style="padding-left:20px; margin:10px 0;">
                                <li><strong>RMS</strong> = Root Mean Square of your deviations</li>
                                <li><strong>Max_RMS</strong> = Theoretical max RMS (${groupSongCount}/√3 ≈ ${(groupSongCount / Math.sqrt(3)).toFixed(1)})</li>
                                <li><strong>Deviation</strong> = |Your Rank − Average Rank|</li>
                            </ul>

                            <p style="margin-top:15px;"><strong style="color:var(--text);">Step by Step for ${username}:</strong></p>
                            <ol style="padding-left:20px; margin:10px 0;">
                                <li>For each song, calculate: (Your Rank − Avg Rank)²</li>
                                <li>Sum all squared deviations</li>
                                <li>Divide by number of songs (${groupSongCount}) and take square root → <strong>RMS</strong></li>
                                <li>Calculate <strong>Max_RMS</strong> = ${groupSongCount} ÷ √3 ≈ ${(groupSongCount / Math.sqrt(3)).toFixed(1)}</li>
                                <li>Normalize: (RMS ÷ Max_RMS) × 100 = <strong style="color:var(--pink);">${scoreDisplay}</strong></li>
                            </ol>

                            <div style="margin-top:20px; padding:15px; background:rgba(255,105,180,0.1); border-radius:8px;">
                                <strong style="color:var(--pink);">Maximum Possible:</strong><br>
                                If you ranked every song exactly opposite to the community average, your Spice Score would be exactly <strong>100</strong>.
                            </div>
                        </div>
                    </div>
                    ` : `

                    ${sub !== 'All Songs' && window.advancedMode ? `
                        <div style="margin-bottom:15px; display:flex; align-items:center; gap:10px;">
                            <span style="font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:1px;">Showing:</span>
                            <button 
                                onclick="window.spiceDetailShowGlobal = false; window.showSpiceDetail('${username.replace(/'/g, "\\'")}')" 
                                style="padding:6px 12px; font-size:11px; font-weight:600; border-radius:4px; cursor:pointer; transition:all 0.2s; border:1px solid var(--border); background:${!showGlobal ? 'var(--pink)' : 'transparent'}; color:${!showGlobal ? '#000' : 'var(--text)'};"
                            >
                                ${sub} Only
                            </button>
                            <button 
                                onclick="window.spiceDetailShowGlobal = true; window.showSpiceDetail('${username.replace(/'/g, "\\'")}')" 
                                style="padding:6px 12px; font-size:11px; font-weight:600; border-radius:4px; cursor:pointer; transition:all 0.2s; border:1px solid var(--border); background:${showGlobal ? 'var(--pink)' : 'transparent'}; color:${showGlobal ? '#000' : 'var(--text)'};"
                            >
                                All Groups
                            </button>
                        </div>
                    ` : (sub !== 'All Songs' ? `
                        <div style="margin-bottom:15px; font-size:12px; color:var(--muted);">
                            Showing extreme picks for <span style="color:var(--pink); font-weight:600;">${sub}</span> only
                        </div>
                    ` : '')}

                    <div style="background:var(--card-bg); border:1px solid var(--border); border-radius:12px; overflow:hidden;">
                        <table style="width:100%; border-collapse:collapse;">
                            <thead style="background:rgba(255,255,255,0.03); border-bottom:1px solid var(--border);">
                                <tr>
                                    <th style="padding:12px 15px; text-align:left; font-size:12px; color:var(--muted); text-transform:uppercase;">Song</th>
                                    ${showGroupColumn ? `<th style="padding:12px 15px; text-align:center; font-size:12px; color:var(--muted); text-transform:uppercase;">Group</th>` : ''}
                                    <th style="padding:12px 15px; text-align:center; font-size:12px; color:var(--muted); text-transform:uppercase;">Rank</th>
                                    <th style="padding:12px 15px; text-align:center; font-size:12px; color:var(--muted); text-transform:uppercase;">Avg</th>
                                    <th style="padding:12px 15px; text-align:right; font-size:12px; color:var(--muted); text-transform:uppercase;">Dev</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${picks.map(p => `
                                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                                        <td style="padding:10px 15px; font-weight:500;">${p.song}</td>
                                        ${showGroupColumn ? `<td style="padding:10px 15px; text-align:center; color:var(--muted); font-size:12px;">${p.group}</td>` : ''}
                                        <td style="padding:10px 15px; text-align:center; font-family:monospace; font-weight:bold; color:${p.user_rank < 10 ? 'var(--gold)' : 'var(--text)'}">${p.user_rank}</td>
                                        <td style="padding:10px 15px; text-align:center; font-family:monospace; color:var(--muted);">${p.avg_rank}</td>
                                        <td style="padding:10px 15px; text-align:right; font-family:monospace; font-weight:bold; color:var(--pink);">+${p.deviation}</td>
                                    </tr>
                                `).join('')}
                                ${picks.length === 0 ? `<tr><td colspan="${showGroupColumn ? 5 : 4}" style="padding:30px; text-align:center; color:var(--muted);">No extreme deviations found${!showGlobal && sub !== 'All Songs' ? ` for ${sub}` : ''}.</td></tr>` : ''}
                            </tbody>
                        </table>
                        ${!window.advancedMode && picks.length > 5 ? `<div style="padding:10px; text-align:center; font-size:12px; color:var(--muted); background:rgba(0,0,0,0.2);">Showing top 5 of ${allPicks.filter(p => showGlobal || sub === 'All Songs' || p.group === sub).length} deviations. Enable Advanced Mode for full list.</div>` : ''}
                    </div>

                    ${window.advancedMode ? `
                    <div style="margin-top:20px; padding:15px; background:rgba(255,105,180,0.05); border:1px solid rgba(255,105,180,0.2); border-radius:8px;">
                        <h4 style="margin:0 0 10px; font-size:14px; color:var(--pink);">📊 Theoretical Maximum Spice</h4>
                        <div style="font-size:12px; color:var(--muted); line-height:1.6;">
                            <p style="margin:0 0 8px;">For a group with <strong style="color:var(--text);">${sub === 'All Songs' ? allPicks.length + ' songs' : sub}</strong>:</p>
                            <ul style="margin:5px 0; padding-left:20px;">
                                <li>Max single deviation: <strong style="color:var(--pink);">~${Math.round((sub === 'All Songs' ? 147 : (allPicks.filter(p => p.group === sub).length || 20)) * 0.9)}</strong> (ranking #1 what everyone else has last)</li>
                                <li>Max Spice Score: <strong style="color:var(--pink);">~100</strong> (perfectly inverted rankings)</li>
                                <li>Your current: <strong style="color:var(--text);">${scoreDisplay}</strong> (${(parseFloat(scoreDisplay) || 0) < 30 ? 'relatively mild' : (parseFloat(scoreDisplay) || 0) < 50 ? 'moderately spicy' : 'extremely spicy'})</li>
                            </ul>
                        </div>
                    </div>
                    ` : ''}
                `}
                `;


    } catch (e) {
        console.error("Modal Render Error:", e);
        content.innerHTML = '<div style="padding:20px; color:var(--red); text-align:center;">Failed to load spice details.</div>';
    }
}

function renderOutliers(results) {
    const el = document.getElementById('c-outliers');
    if (!el) return;

    if (!results || !results.length) {
        el.innerHTML = '<div style="padding:10px; font-size:12px; color:var(--muted);">No spice data available.</div>';
        return;
    }

    const sub = document.getElementById('view-subgroup').value;
    const isAll = sub === 'All Songs';

    let filtered = results.map(u => ({
        username: u.username,
        score: isAll ? u.global_spice : (u.group_breakdown ? u.group_breakdown[sub] : null)
    })).filter(u => u.score !== null && u.score !== undefined);

    if (filtered.length === 0) {
        el.innerHTML = '<div style="padding:10px; font-size:12px; color:var(--muted);">No spice data for this group.</div>';
        return;
    }

    filtered.sort((a, b) => b.score - a.score);

    const limit = getLimit(10, filtered.length);
    const data = filtered.slice(0, limit);
    const scores = data.map(u => u.score), min = Math.min(...scores), max = Math.max(...scores), r = (max - min) || 1;

    el.innerHTML = `<table><colgroup><col><col class="col-metric"></colgroup><tr><th>User</th><th class="col-metric">Spice</th></tr>` +
        data.map(u => `<tr onclick="window.showSpiceDetail('${u.username.replace(/'/g, "\\'")}')" style="cursor:pointer" class="clickable-row">
                    <td style="font-weight:bold">${u.username}</td>
                    <td class="metric"><div class="bar-bg" style="width:180px"><div class="bar-fill" style="width:${((u.score - min) / r) * 100}%"></div><div style="font-size:10px; margin-top:-14px; margin-left:5px;">${u.score.toFixed(2)}</div></div></td>
                </tr>`).join('') + `</table>`;
}


async function renderMatrix(sub, f) {
    const wrap = document.getElementById("c-matrix"); wrap.innerHTML = "Loading...";
    try {
        const r = await fetch(`${API}/analysis/divergence?franchise=${f}&subgroup=${sub}`);
        const d = await r.json();
        const u = Object.keys(d.matrix).sort();
        const nSongs = Object.keys(d.song_names || {}).length || 1;

        // Max for coloration (cap at 40% for visual contrast, as >40% is extreme)
        const maxVal = 40;

        wrap.style.gridTemplateColumns = `150px repeat(${u.length}, 1fr)`;
        wrap.innerHTML = `<div></div>` + u.map(n => `<div class="m-label">${n}</div>`).join('');

        u.forEach(u1 => {
            wrap.innerHTML += `<div class="m-label" style="text-align:left">${u1}</div>`;
            u.forEach(u2 => {
                const raw = d.matrix[u1][u2];
                const pct = ((raw / Math.max(1, nSongs - 1)) * 100);
                const display = pct.toFixed(0);
                const op = Math.min(1, Math.pow(pct / maxVal, 1.5)); // Color opacity based on %

                wrap.innerHTML += `<div class="cell" onclick="showUserComparison('${u1}', '${u2}')" style="background:rgba(219, 97, 162, ${op}); color:${op > 0.5 ? '#fff' : '#8b949e'}; border-bottom:1px solid #0d1117; cursor:pointer;" title="${u1} vs ${u2}: ${pct.toFixed(1)}%">${display}</div>`;
            });
        });
    } catch (e) { console.error(e); wrap.innerHTML = "Error."; }
}

// Tier calculation method - stored globally for re-render
let tierMethod = 'score'; // 'percentile', 'score', 'stddev'

function renderTierStats(rankings) {
    const container = document.getElementById('view-tiers');
    const total = rankings.length;

    if (total === 0) {
        document.getElementById('c-tier-bar').innerHTML = '<div style="padding:10px; color:var(--muted)">No data</div>';
        document.getElementById('c-tier-lists').innerHTML = '';
        return;
    }

    // Sort by average rank
    const sorted = [...rankings].sort((a, b) => a.average - b.average);

    // Calculate stats for stddev method
    const avgRanks = sorted.map(s => s.average);
    const mean = avgRanks.reduce((a, b) => a + b, 0) / total;
    const stddev = Math.sqrt(avgRanks.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / total);

    // In basic mode, use score-based. In advanced mode, use selected method.
    const method = window.advancedMode ? tierMethod : 'score';

    let tiers;
    let labels;

    switch (method) {
        case 'percentile':
            // Equal 20% splits (quintiles)
            const pct20 = Math.ceil(total * 0.2);
            const pct40 = Math.ceil(total * 0.4);
            const pct60 = Math.ceil(total * 0.6);
            const pct80 = Math.ceil(total * 0.8);
            tiers = {
                S: sorted.slice(0, pct20),
                A: sorted.slice(pct20, pct40),
                B: sorted.slice(pct40, pct60),
                C: sorted.slice(pct60, pct80),
                F: sorted.slice(pct80)
            };
            labels = { S: 'S Tier (Top 20%)', A: 'A Tier (20-40%)', B: 'B Tier (40-60%)', C: 'C Tier (60-80%)', F: 'F Tier (Bottom 20%)' };
            break;

        case 'stddev':
            // Standard Normal Distribution z-score bands
            // S: z < -2σ (top ~2.3%)
            // A: -2σ ≤ z < -1σ (next ~13.6%)
            // B: -1σ ≤ z < 1σ (middle ~68.3%)
            // C: 1σ ≤ z < 2σ (next ~13.6%)
            // F: z ≥ 2σ (bottom ~2.3%)
            tiers = { S: [], A: [], B: [], C: [], F: [] };
            sorted.forEach(r => {
                const z = (r.average - mean) / stddev;
                if (z <= -2) tiers.S.push(r);        // Top 2.3%
                else if (z <= -1) tiers.A.push(r);   // Next 13.6%
                else if (z <= 1) tiers.B.push(r);    // Middle 68.3%
                else if (z <= 2) tiers.C.push(r);    // Next 13.6%
                else tiers.F.push(r);                 // Bottom 2.3%
            });
            labels = {
                S: 'S Tier (z < -2σ, ~2%)',
                A: 'A Tier (-2σ to -1σ, ~14%)',
                B: 'B Tier (within ±1σ, ~68%)',
                C: 'C Tier (+1σ to +2σ, ~14%)',
                F: 'F Tier (z > +2σ, ~2%)'
            };
            break;

        case 'score':
        default:
            // Standard grading curve approximating normal distribution
            // Based on common academic bell curve grading:
            // S/A: Top ~7% (exceptional)
            // A/B: Next ~17% (above average) 
            // B/C: Middle ~50% (average)
            // C/D: Next ~17% (below average)
            // D/F: Bottom ~9% (poor)
            const s_cut = Math.ceil(total * 0.07);
            const a_cut = Math.ceil(total * 0.24);  // 7 + 17 = 24
            const b_cut = Math.ceil(total * 0.74);  // 24 + 50 = 74
            const c_cut = Math.ceil(total * 0.91);  // 74 + 17 = 91
            tiers = {
                S: sorted.slice(0, s_cut),
                A: sorted.slice(s_cut, a_cut),
                B: sorted.slice(a_cut, b_cut),
                C: sorted.slice(b_cut, c_cut),
                F: sorted.slice(c_cut)
            };
            labels = {
                S: 'S Tier (Top 7%)',
                A: 'A Tier (7-24%)',
                B: 'B Tier (24-74%)',
                C: 'C Tier (74-91%)',
                F: 'F Tier (Bottom 9%)'
            };
            break;
    }

    const colors = { S: '#e6cc00', A: '#3fb950', B: '#238636', C: '#8b949e', F: '#f85149' };

    // Render method selector (advanced mode only)
    let methodSelector = '';
    if (window.advancedMode) {
        methodSelector = `
            <div style="margin-bottom:15px; display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
                <label style="font-size:12px; color:var(--muted); text-transform:uppercase; white-space:nowrap;">Tier Method:</label>
                <select id="tier-method-select" onchange="changeTierMethod(this.value)" style="padding:8px 12px; font-size:13px; min-width:200px;">
                    <option value="score" ${tierMethod === 'score' ? 'selected' : ''}>Bell Curve</option>
                    <option value="percentile" ${tierMethod === 'percentile' ? 'selected' : ''}>Equal Quintiles</option>
                    <option value="stddev" ${tierMethod === 'stddev' ? 'selected' : ''}>Standard Deviation</option>
                </select>
                <span style="font-size:11px; color:var(--muted);">μ = ${mean.toFixed(1)}, σ = ${stddev.toFixed(1)}</span>
            </div>
        `;
    }

    // Render Bar (Score Density Plot)
    const bar = document.getElementById('c-tier-bar');
    bar.innerHTML = methodSelector;

    const barWrap = document.createElement('div');
    barWrap.style.cssText = 'position:relative; height:50px; border-radius:8px; overflow:hidden; background:#0d1117; border:1px solid var(--border); margin-top:5px;';

    // Add a subtle gradient track
    const track = document.createElement('div');
    track.style.cssText = 'position:absolute; top:20px; left:10px; right:10px; height:2px; background:rgba(255,255,255,0.1); border-radius:2px;';
    barWrap.appendChild(track);

    // Calculate global range for plotting
    const minVal = sorted[0].average;
    const maxVal = sorted[total - 1].average;
    const range = Math.max(0.001, maxVal - minVal);

    const tierOrder = ['S', 'A', 'B', 'C', 'F'];

    // Calculate tier boundaries (start/end percentages)
    const tierBoundaries = {};
    let cumulativePct = 0;
    tierOrder.forEach((k) => {
        const count = tiers[k].length;
        const widthPct = (count / total) * 100;
        tierBoundaries[k] = { start: cumulativePct, width: widthPct, count };
        cumulativePct += widthPct;
    });

    // Draw Tier Background Colors
    tierOrder.forEach((k) => {
        const { start, width, count } = tierBoundaries[k];
        if (count === 0) return;

        const bg = document.createElement('div');
        bg.style.cssText = `
            position:absolute; 
            left:${start}%; 
            width:${width}%; 
            top:0; 
            bottom:0; 
            background:${colors[k]}; 
            opacity:0.35;
        `;
        bg.title = `${labels[k]}: ${count} songs`;
        barWrap.appendChild(bg);

        // Add tier label if wide enough
        if (width > 6) {
            const label = document.createElement('div');
            label.style.cssText = `
                position:absolute; 
                left:${start + width / 2}%; 
                top:4px; 
                transform:translateX(-50%);
                font-size:11px; 
                font-weight:bold; 
                color:${colors[k]}; 
                text-shadow: 0 0 4px #000, 0 0 2px #000;
            `;
            label.textContent = k;
            barWrap.appendChild(label);
        }
    });

    // Create a static info label below the bar (not absolute, stays in flow)
    const infoRow = document.createElement('div');
    infoRow.style.cssText = 'display:flex; justify-content:space-between; align-items:center; margin-top:8px; font-size:11px;';

    const leftLabel = document.createElement('span');
    leftLabel.textContent = '← Best';
    leftLabel.style.cssText = 'color:var(--muted);';

    const hoverInfo = document.createElement('span');
    hoverInfo.id = 'tier-hover-info';
    hoverInfo.textContent = 'Hover over dots to see song details';
    hoverInfo.style.cssText = 'color:var(--muted); font-style:italic; transition: all 0.15s;';

    const rightLabel = document.createElement('span');
    rightLabel.textContent = 'Worst →';
    rightLabel.style.cssText = 'color:var(--muted);';

    infoRow.appendChild(leftLabel);
    infoRow.appendChild(hoverInfo);
    infoRow.appendChild(rightLabel);

    // Draw Song Markers - position WITHIN their tier's region
    // Use global index for unique IDs to avoid collisions
    let globalSongIdx = 0;
    tierOrder.forEach(k => {
        const { start, width, count } = tierBoundaries[k];
        if (count === 0) return;

        tiers[k].forEach((s, idxInTier) => {
            const songIdx = globalSongIdx++;

            // Calculate position within this tier's region
            // For 'percentile' method: Even spacing (rank-based)
            // For 'score'/'stddev': Relative score within the tier (distribution-based)
            let positionInTier;

            if (method === 'percentile') {
                if (count === 1) positionInTier = 0.5;
                else positionInTier = idxInTier / (count - 1);
            } else {
                // Find min/max score for this tier to map relative position
                const tierScores = tiers[k].map(t => t.average);
                const tMin = Math.min(...tierScores);
                const tMax = Math.max(...tierScores);
                const tRange = tMax - tMin;

                if (tRange === 0) positionInTier = 0.5;
                else positionInTier = (s.average - tMin) / tRange;
            }

            const padding = width * 0.05; // 5% padding on each side
            const usableWidth = width - (padding * 2);
            const pct = start + padding + (positionInTier * usableWidth);

            const marker = document.createElement('div');
            marker.id = `mk-${songIdx}`;
            marker.dataset.songIdx = songIdx;
            marker.className = 'tier-marker';
            marker.style.cssText = `
                position:absolute; 
                left:calc(${pct}% - 5px); 
                top:20px; 
                height:10px; 
                width:10px; 
                background:${colors[k]}; 
                opacity:0.9; 
                border-radius:50%; 
                cursor:pointer;
                transition: transform 0.1s, box-shadow 0.1s;
                border: 1px solid rgba(255,255,255,0.4);
                z-index: 10;
            `;

            marker.onmouseenter = () => {
                hoverInfo.textContent = `${s.song_name} — Avg Rank: #${s.average}`;
                hoverInfo.style.color = colors[k];
                hoverInfo.style.fontStyle = 'normal';
                hoverInfo.style.fontWeight = 'bold';
                highlightMarker(songIdx, true);
                highlightListItem(songIdx, true);
            };
            marker.onmouseleave = () => {
                hoverInfo.textContent = 'Hover over dots to see song details';
                hoverInfo.style.color = 'var(--muted)';
                hoverInfo.style.fontStyle = 'italic';
                hoverInfo.style.fontWeight = '';
                highlightMarker(songIdx, false);
                highlightListItem(songIdx, false);
            };
            marker.onclick = () => showSongDistribution(s.song_name);

            barWrap.appendChild(marker);
        });
    });

    bar.appendChild(barWrap);
    bar.appendChild(infoRow);

    // Highlight functions using index-based IDs
    window.highlightMarker = (idx, highlight) => {
        const marker = document.getElementById(`mk-${idx}`);
        if (marker) {
            if (highlight) {
                marker.style.transform = 'scale(2)';
                marker.style.zIndex = '100';
                marker.style.opacity = '1';
                marker.style.boxShadow = '0 0 12px ' + marker.style.backgroundColor;
            } else {
                marker.style.transform = 'scale(1)';
                marker.style.zIndex = '10';
                marker.style.opacity = '0.9';
                marker.style.boxShadow = 'none';
            }
        }
    };

    window.highlightListItem = (idx, highlight) => {
        const listItem = document.getElementById(`li-${idx}`);
        if (listItem) {
            if (highlight) {
                listItem.style.background = 'rgba(219, 97, 162, 0.25)';
                listItem.style.fontWeight = 'bold';
                listItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                listItem.style.background = '';
                listItem.style.fontWeight = '';
            }
        }
    };

    // Helper to get display value based on method
    const getDisplayValue = (r) => {
        switch (method) {
            case 'stddev':
                const z = (r.average - mean) / stddev;
                return `z = ${z.toFixed(2)}σ`;
            case 'percentile':
                const pctile = ((sorted.indexOf(r) + 1) / total * 100).toFixed(0);
                return `${pctile}th %ile`;
            case 'score':
            default:
                return `#${r.average}`;
        }
    };

    // Build song info lookup for list hover
    const songInfoMap = {};
    globalSongIdx = 0;
    tierOrder.forEach(k => {
        tiers[k].forEach((r) => {
            songInfoMap[globalSongIdx] = { name: r.song_name, avg: r.average, tier: k };
            globalSongIdx++;
        });
    });

    // Store reference to hoverInfo for list hover
    window.updateTierHoverInfo = (idx, show) => {
        const hoverInfo = document.getElementById('tier-hover-info');
        if (!hoverInfo) return;
        if (show && songInfoMap[idx]) {
            const info = songInfoMap[idx];
            hoverInfo.textContent = `${info.name} — Avg Rank: #${info.avg}`;
            hoverInfo.style.color = colors[info.tier];
            hoverInfo.style.fontStyle = 'normal';
            hoverInfo.style.fontWeight = 'bold';
        } else {
            hoverInfo.textContent = 'Hover over dots or songs to see details';
            hoverInfo.style.color = 'var(--muted)';
            hoverInfo.style.fontStyle = 'italic';
            hoverInfo.style.fontWeight = '';
        }
    };

    // Tier split descriptions
    const tierDescriptions = {
        'score': { S: 'Top 7%', A: '7–24%', B: '24–74%', C: '74–91%', F: 'Bottom 9%' },
        'percentile': { S: 'Top 20%', A: '20–40%', B: '40–60%', C: '60–80%', F: 'Bottom 20%' },
        'stddev': { S: 'z < -2σ', A: '-2σ to -1σ', B: '±1σ', C: '+1σ to +2σ', F: 'z > +2σ' }
    };
    const descriptions = tierDescriptions[method] || tierDescriptions['score'];

    // Render Lists
    const lists = document.getElementById('c-tier-lists');
    lists.innerHTML = '';

    // Re-iterate with same global index to match
    globalSongIdx = 0;
    tierOrder.forEach(k => {
        const count = tiers[k].length;
        const listContent = count === 0
            ? `<div style="padding:20px; text-align:center; color:var(--muted); font-size:11px;">None</div>`
            : `<div style="max-height:350px; overflow-y:auto;">
                 ${tiers[k].map((r, i) => {
                const idx = globalSongIdx++;
                return `
                     <div 
                         id="li-${idx}"
                         onmouseenter="highlightMarker(${idx}, true); updateTierHoverInfo(${idx}, true);" 
                         onmouseleave="highlightMarker(${idx}, false); updateTierHoverInfo(${idx}, false);"
                         onclick="showSongDistribution('${r.song_name.replace(/'/g, "\\'")}')" 
                         style="padding:8px 10px; border-bottom:1px solid var(--border); font-size:12px; display:flex; justify-content:space-between; cursor:pointer; gap:8px; transition: background 0.1s;" 
                         class="clickable-row">
                         <span style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${i + 1}. ${r.song_name}</span>
                         <span style="color:var(--muted); font-size:10px; white-space:nowrap;">${getDisplayValue(r)}</span>
                     </div>`;
            }).join('')}
               </div>`;

        lists.innerHTML += `
            <div style="background:var(--bg); border:1px solid var(--border); border-radius:8px; overflow:hidden; min-width:0; display:flex; flex-direction:column;">
                <div style="background:${colors[k]}; color:#000; padding:10px; font-weight:bold; text-align:center;">
                    ${k} <span style="font-size:10px; opacity:0.7;">(${count})</span>
                    <div style="font-size:9px; font-weight:normal; opacity:0.8; margin-top:2px;">${descriptions[k]}</div>
                </div>
                ${listContent}
            </div>
        `;
    });
}

// Change tier method (advanced mode)
function changeTierMethod(method) {
    tierMethod = method;
    if (dataCache.loaded && dataCache.ranks?.rankings) {
        renderTierStats(dataCache.ranks.rankings);
    }
}

async function renderAffinity(subData) {
    const wrapAff = document.getElementById('c-affinity');
    const wrapUnq = document.getElementById('c-unique-favs');

    const currentSub = document.getElementById('view-subgroup').value;
    const f = document.getElementById('view-franchise').value;

    if (currentSub.toLowerCase().includes('all') || currentSub === '') {
        wrapAff.innerHTML = '<div style="padding:20px; text-align:center; color:var(--muted);">Select a specific Subgroup to see affinities vs the Global Average.</div>';
        wrapUnq.innerHTML = '';
        return;
    }

    try {
        // Fetch Global Data
        const res = await fetch(`${API}/analysis/rankings?franchise=${f}&subgroup=All%20Songs`);
        if (!res.ok) throw new Error("Could not fetch global data");
        const globalData = await res.json();

        // Map Global Ranks (Indices + 1)
        // Note: The globalData might not be sorted by average, so let's sort it first to get true rank.
        globalData.rankings.sort((a, b) => a.average - b.average);

        const globalInfo = {};
        globalData.rankings.forEach((r, i) => {
            globalInfo[r.song_name] = { average: r.average, rank: i + 1 };
        });

        const globalTotal = globalData.rankings.length || 1;
        const subTotal = subData.length || 1;

        // Calculate Deltas based on PERCENTILE
        // Global Pct = Rank / Total (0.0 = Top, 1.0 = Bottom)
        // Group Pct = Rank / Total
        // Bias = Global_Pct - Group_Pct 
        // (Positive Bias = Group ranks it "higher" (lower pct) than Global).

        // Example: G Rank 100/200 (0.5), Group Rank 5/20 (0.25). Bias = 0.5 - 0.25 = 0.25 (+25%)

        const affinity = subData.sort((a, b) => a.average - b.average).map((r, i) => {
            const g = globalInfo[r.song_name];
            if (!g) return null;

            const groupRank = i + 1; // Current index in sorted subData
            const globalRank = g.rank;

            const groupPct = groupRank / subTotal;
            const globalPct = globalRank / globalTotal;

            const bias = globalPct - groupPct;

            return {
                ...r,
                groupRank: groupRank,
                globalRank: globalRank,
                groupPct: groupPct,
                globalPct: globalPct,
                bias: bias
            };
        }).filter(x => x).sort((a, b) => b.bias - a.bias);

        // Affinity List (Top 15 Bias)
        const topAff = affinity.slice(0, 15);
        wrapAff.innerHTML = `<table style="width:100%; font-size:13px;">
                    <tr style="text-align:left; color:var(--muted);"><th>Song</th><th>Group %</th><th>Global %</th><th>Bias</th></tr>
                    ${topAff.map(s => `
                        <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                            <td style="padding:8px;">${s.song_name}</td>
                            <td style="color:var(--green);">Top ${(s.groupPct * 100).toFixed(0)}% <span style="font-size:10px; opacity:0.6;">(#${s.groupRank})</span></td>
                            <td style="color:var(--muted);">Top ${(s.globalPct * 100).toFixed(0)}% <span style="font-size:10px; opacity:0.6;">(#${s.globalRank})</span></td>
                            <td style="color:var(--pink); font-weight:bold;">+${(s.bias * 100).toFixed(1)}%</td>
                        </tr>
                    `).join('')}
                </table>`;

        // Top Unique Favorites 
        // Logic: Songs in Global Bottom 50% (Pct > 0.5) but Group Top 20% (Pct < 0.2)
        const uniqueFavs = affinity.filter(s => s.globalPct > 0.5 && s.groupPct <= 0.20);

        if (uniqueFavs.length === 0) {
            wrapUnq.innerHTML = '<div style="padding:20px; color:var(--muted); font-size:12px;">No specific "Hidden Gems" found (Global Bottom 50% vs Group Top 20%).</div>';
        } else {
            wrapUnq.innerHTML = `<div style="display:flex; flex-wrap:wrap; gap:8px;">
                        ${uniqueFavs.map(s => `
                            <div style="background:rgba(63, 185, 80, 0.1); border:1px solid var(--green); padding:4px 10px; border-radius:12px; font-size:12px; color:var(--green);">
                                <b>${s.song_name}</b> <span style="opacity:0.7; font-size:10px;">(+${(s.bias * 100).toFixed(0)}%)</span>
                            </div>
                        `).join('')}
                    </div>`;
        }

    } catch (e) {
        console.warn(e);
        wrapAff.innerHTML = '<div style="padding:20px; text-align:center; color:var(--red);">Could not load global comparison data.</div>';
    }
}

/* --- RIVALS LOGIC --- */
let allUsers = [];

async function fetchUserList() {
    const f = document.getElementById('view-franchise').value, sub = document.getElementById('view-subgroup').value;
    try {
        // Use divergence endpoint to get reliable user list
        const r = await fetch(`${API}/analysis/divergence?franchise=${f}&subgroup=${sub}`);
        const d = await r.json();
        allUsers = Object.keys(d.matrix).sort();

        // Update dynamic dimensionality text
        const dimCount = Object.keys(d.song_names || {}).length || "?";
        const descEl = document.getElementById('constellation-desc');
        if (descEl) {
            descEl.childNodes[0].nodeValue = `Visualizing ${dimCount}-dimensional taste differences in 2D space. `;
        }


        // Init Graph with full data (for loading calculations)
        setTimeout(() => typeof initConstellation === 'function' && initConstellation(d), 500);

        const opts = allUsers.map(u => `<option value="${u}">${u}</option>`).join('');
        ['duel-user-a', 'duel-user-b', 'match-finder-user', 'bias-user'].forEach(id => {
            const el = document.getElementById(id);
            if (el && !el.innerHTML) {  // Only populate if empty to preserve selection
                const old = el.value;
                el.innerHTML = '<option value="">Select User</option>' + opts;
                if (old && allUsers.includes(old)) el.value = old;
            } else if (el && el.innerHTML === "") {
                el.innerHTML = '<option value="">Select User</option>' + opts;
            }
        });
    } catch (e) { }
}

function switchRivalTab(tab) {
    // Update button styles
    const buttons = {
        constellation: document.getElementById('rtab-constellation'),
        duel: document.getElementById('rtab-duel'),
        oshi: document.getElementById('rtab-oshi')
    };
    Object.keys(buttons).forEach(key => {
        const btn = buttons[key];
        if (key === tab) {
            btn.style.background = 'var(--pink)';
            btn.style.color = '#000';
            btn.style.borderColor = 'transparent';
        } else {
            btn.style.background = 'var(--card)';
            btn.style.color = 'var(--text)';
            btn.style.borderColor = 'var(--border)';
        }
    });
    // Update views
    document.getElementById('rview-constellation').classList.toggle('hidden', tab !== 'constellation');
    document.getElementById('rview-duel').classList.toggle('hidden', tab !== 'duel');
    document.getElementById('rview-oshi').classList.toggle('hidden', tab !== 'oshi');
}

function switchMatchTab(tab) {
    // Update button styles
    const buttons = { duel: document.getElementById('mtab-duel'), match: document.getElementById('mtab-match'), oshi: document.getElementById('mtab-oshi') };
    Object.keys(buttons).forEach(key => {
        const btn = buttons[key];
        if (key === tab) {
            btn.style.background = 'var(--pink)';
            btn.style.color = '#000';
            btn.style.borderColor = 'transparent';
        } else {
            btn.style.background = 'var(--card)';
            btn.style.color = 'var(--text)';
            btn.style.borderColor = 'var(--border)';
        }
    });
    // Update views
    document.getElementById('mview-duel').classList.toggle('hidden', tab !== 'duel');
    document.getElementById('mview-match').classList.toggle('hidden', tab !== 'match');
    document.getElementById('mview-oshi').classList.toggle('hidden', tab !== 'oshi');
}



async function runDuel() {
    const u1 = document.getElementById('duel-user-a').value;
    const u2 = document.getElementById('duel-user-b').value;
    if (!u1 || !u2 || u1 === u2) {
        document.getElementById('duel-results').classList.add('hidden');
        return;
    }

    const f = document.getElementById('view-franchise').value, sub = document.getElementById('view-subgroup').value;
    document.getElementById('duel-score').innerHTML = "...";
    document.getElementById('duel-results').classList.remove('hidden');

    try {
        const res = await fetch(`${API}/analysis/head-to-head?franchise=${f}&subgroup=${sub}&user_a=${u1}&user_b=${u2}`);
        const data = await res.json();

        // Render Score
        const sc = data.score;
        document.getElementById('duel-score').innerHTML = `${sc}%`;
        document.getElementById('duel-score').style.color = sc > 75 ? 'var(--green)' : sc < 40 ? 'var(--red)' : '#fff';
        document.getElementById('duel-msg').innerHTML = sc > 85 ? "BEST FRIENDS FOREVER 💖" : sc > 60 ? "Solid Compatibility 👍" : sc < 30 ? "MORTAL ENEMIES 💀" : "It's Complicated 🤷";

        // Render Disputes
        const limit = getLimit(10, data.diffs.length);
        const disputes = data.diffs.slice(0, limit);
        document.getElementById('duel-disputes').innerHTML = `<table>
                    <colgroup><col><col style="width:80px"><col style="width:80px"><col style="width:60px"></colgroup>
                    <tr><th>Song</th><th>${u1}</th><th>${u2}</th><th>Diff</th></tr>` +
            disputes.map(d => `
                        <tr onclick="showSongDistribution('${d.name.replace(/'/g, "\\'")}')" style="cursor:pointer;" class="clickable-row">
                            <td>${d.name}</td>
                            <td style="color:${d.r1 < d.r2 ? 'var(--green)' : 'var(--muted)'}">#${d.r1}</td>
                            <td style="color:${d.r2 < d.r1 ? 'var(--green)' : 'var(--muted)'}">#${d.r2}</td>
                            <td style="font-weight:bold; color:var(--red)">${Math.round(d.diff)}</td>
                        </tr>`).join('') + `</table>`;

    } catch (e) { console.error(e); document.getElementById('duel-score').innerHTML = "Err"; }
}

async function findMatches() {
    const u = document.getElementById('match-finder-user').value;
    if (!u) return;
    const f = document.getElementById('view-franchise').value, sub = document.getElementById('view-subgroup').value;
    const res = document.getElementById('match-results');
    res.innerHTML = "Scanning database...";

    try {
        const r = await fetch(`${API}/analysis/user-match?franchise=${f}&subgroup=${sub}&user=${u}`);
        const data = await r.json();

        const renderCard = (title, list, color) => `
                    <div class="card" style="border-color:${color}">
                        <h3 style="color:${color}; border-color:${color}; margin-bottom:10px;">${title}</h3>
                        ${list.map(x => `<div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05)">
                            <span style="font-weight:600">${x.user}</span>
                            <span style="font-family:Consolas; opacity:0.7">Div: ${x.div.toFixed(2)}</span>
                        </div>`).join('')}
                    </div>
                `;

        res.innerHTML = renderCard("❤️ Soulmates", data.soulmates, "var(--green)") +
            renderCard("💀 Nemeses", data.nemeses, "var(--red)");
    } catch (e) {
        console.error('Match finding error:', e);
        res.innerHTML = `<div class="card" style="border-color:var(--red); text-align:center; padding:30px;">
                    <div style="font-size:48px; margin-bottom:10px;">⚠️</div>
                    <div style="color:var(--red); font-weight:600; margin-bottom:10px;">Error Finding Matches</div>
                    <div style="font-size:12px; color:var(--muted);">The API endpoint may not be available. Please check the backend service.</div>
                </div>`;
    }
}

async function fetchUserList() {
    const f = document.getElementById('view-franchise').value;
    const sub = document.getElementById('view-subgroup').value;
    const sel = document.getElementById('bias-user');
    if (!sel) return;

    try {
        const res = await fetch(`${API}/users/rankings?franchise=${f}&subgroup=${encodeURIComponent(sub)}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.users && data.users.length > 0) {
            const current = sel.value;
            sel.innerHTML = data.users.map(u => `<option value="${u.username}">${u.username}</option>`).join('');
            if (current && data.users.some(u => u.username === current)) sel.value = current;
        }
    } catch (e) { console.error("Error fetching users:", e); }
}

window.lastBiasData = [];
async function analyzeBias() {
    const u = document.getElementById('bias-user').value;
    if (!u) return;
    const f = document.getElementById('view-franchise').value;
    const res = document.getElementById('bias-results');
    res.innerHTML = "Computing bias...";

    try {
        const r = await fetch(`${API}/analysis/oshi-bias?franchise=${f}&user=${u}`);
        const d = await r.json();

        if (d.error) { res.innerHTML = d.error; return; }

        window.lastBiasData = d.biases;
        window.lastBiasGlobalAvg = d.global_avg;
        const displayList = window.advancedMode ? d.biases : d.biases.slice(0, 5);

        let html = '';
        displayList.forEach((b, i) => {
            const isTop = i === 0;
            const biasColor = b.bias > 0 ? (isTop ? 'var(--pink)' : 'var(--green)') : 'var(--red)';

            html += `
                     <div class="stat-card" 
                          onclick="showMemberBiasDetail(${i})"
                          style="padding:15px; border-color:${isTop ? 'var(--pink)' : 'var(--border)'}; cursor:pointer; transition:all 0.2s;"
                          onmouseover="this.style.transform='translateY(-3px)'; this.style.borderColor='var(--pink)'; this.style.boxShadow='0 4px 12px rgba(219,97,162,0.2)'"
                          onmouseout="this.style.transform='translateY(0)'; this.style.borderColor='${isTop ? 'var(--pink)' : 'var(--border)'}'; this.style.boxShadow='none'">
                        <div style="font-size:10px; opacity:0.7; text-transform:uppercase; letter-spacing:1px;">${isTop ? '🏆 OSHI' : 'Favored Member'}</div>
                        <div style="font-size:16px; font-weight:bold; color:#fff; margin:5px 0;">${b.name}</div>
                        <div style="font-size:24px; font-weight:900; color:${biasColor}">
                            ${b.bias > 0 ? '+' : ''}${b.bias}
                        </div>
                        <div style="font-size:11px; opacity:0.5; margin-top:5px;">Avg Rank #${b.avg_rank} (${b.count} songs)</div>
                        <div style="font-size:9px; color:var(--pink); margin-top:8px; opacity:0; transition:0.2s;" class="click-hint">Click for song list →</div>
                     </div>`;
        });

        // Add a hover style via CSS to show the hint
        const styleId = 'bias-hover-style';
        if (!document.getElementById(styleId)) {
            const style = document.createElement('style');
            style.id = styleId;
            style.innerHTML = `.stat-card:hover .click-hint { opacity: 0.8 !important; }`;
            document.head.appendChild(style);
        }

        res.innerHTML = html || "No significant bias found (You love everyone equally?).";
    } catch (e) { console.error(e); res.innerHTML = "Error."; }
}

window.showMemberBiasDetail = function (index) {
    const data = window.lastBiasData[index];
    if (!data) return;

    const modal = document.getElementById('song-modal');
    const content = document.getElementById('song-modal-content');
    const title = document.getElementById('song-modal-title');

    title.textContent = `${data.name} Analysis`;
    modal.classList.remove('hidden');
    modal.style.display = 'flex';

    content.innerHTML = `
                <div style="margin-bottom:20px; display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                    <div class="card" style="padding:12px; text-align:center; border-color:var(--pink);">
                        <div style="font-size:10px; color:var(--muted); text-transform:uppercase; margin-bottom:4px;">Bias Intensity</div>
                        <div style="font-size:20px; font-weight:900; color:var(--pink)">${data.bias > 0 ? '+' : ''}${data.bias}</div>
                    </div>
                    <div class="card" style="padding:12px; text-align:center;">
                        <div style="font-size:10px; color:var(--muted); text-transform:uppercase; margin-bottom:4px;">Average Rank</div>
                        <div style="font-size:20px; font-weight:900;">#${data.avg_rank}</div>
                    </div>
                </div>

                <div style="margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="font-size:14px; color:var(--pink);">Songs Involving ${data.name}</h4>
                    <span style="font-size:11px; color:var(--muted);">${data.count} songs ranked</span>
                </div>

                <div style="max-height:350px; overflow-y:auto; border:1px solid var(--border); border-radius:8px; background:rgba(0,0,0,0.2);">
                    <table style="width:100%; font-size:12px; border-collapse:collapse;">
                        <thead>
                            <tr style="background:rgba(255,255,255,0.05); text-align:left;">
                                <th style="padding:10px; border-bottom:1px solid var(--border);">Song Title</th>
                                <th style="padding:10px; border-bottom:1px solid var(--border); text-align:center;">Rank</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.songs.map(s => `
                                <tr hover-style="background:rgba(255,255,255,0.02)">
                                    <td style="padding:8px 10px; border-bottom:1px solid rgba(255,255,255,0.03);">${s.name}</td>
                                    <td style="padding:8px 10px; border-bottom:1px solid rgba(255,255,255,0.03); text-align:center; font-weight:bold; color:${s.rank <= 10 ? 'var(--green)' : (s.rank > 50 ? 'var(--red)' : '#fff')}">#${s.rank}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                
                <div style="margin-top:15px; padding:10px; background:rgba(255,255,255,0.03); border-radius:6px; font-size:11px; color:var(--muted); line-height:1.4;">
                    <strong>About Bias:</strong> A positive score means you rank songs involving this member <strong>better</strong> than your global average rank of <strong>${window.lastBiasGlobalAvg || '??'}</strong>.
                </div>
            `;
};


/* --- CONSTELLATION GRAPH --- */
let graphCtx = null, graphNodes = [], graphEdges = [], graphAnimParams = { w: 0, h: 0 };
let graphHover = null, graphDrag = null, graphMouse = { x: 0, y: 0 };

// --- Math Helpers for MDS ---
const MathLib = {
    mean: (arr) => arr.reduce((a, b) => a + b, 0) / arr.length,
    pearson: (x, y) => {
        const n = x.length;
        if (n !== y.length || n === 0) return 0;
        const mx = MathLib.mean(x), my = MathLib.mean(y);
        let num = 0, dx2 = 0, dy2 = 0;
        for (let i = 0; i < n; i++) {
            const dx = x[i] - mx, dy = y[i] - my;
            num += dx * dy;
            dx2 += dx * dx;
            dy2 += dy * dy;
        }
        return (dx2 === 0 || dy2 === 0) ? 0 : num / Math.sqrt(dx2 * dy2);
    },
    jacobi: (A, tol = 1e-8, maxIter = 100) => {
        const n = A.length;
        let V = Array(n).fill(0).map((_, i) => Array(n).fill(0).map((_, j) => i === j ? 1 : 0));
        let D = A.map(row => [...row]);
        for (let iter = 0; iter < maxIter; iter++) {
            let maxVal = 0, p = 0, q = 0;
            for (let i = 0; i < n - 1; i++) for (let j = i + 1; j < n; j++) if (Math.abs(D[i][j]) > maxVal) { maxVal = Math.abs(D[i][j]); p = i; q = j; }
            if (maxVal < tol) break;
            const phi = 0.5 * Math.atan2(2 * D[p][q], D[q][q] - D[p][p]);
            const c = Math.cos(phi), s = Math.sin(phi);
            for (let i = 0; i < n; i++) {
                let t = D[i][p]; D[i][p] = c * t - s * D[i][q]; D[i][q] = s * t + c * D[i][q];
                t = V[i][p]; V[i][p] = c * t - s * V[i][q]; V[i][q] = s * t + c * V[i][q];
            }
            for (let i = 0; i < n; i++) {
                D[p][i] = D[i][p]; D[q][i] = D[i][q];
            }
            D[p][p] = c * D[p][p] * c - 2 * s * D[p][q] * c + s * D[q][q] * s;
            D[q][q] = s * D[p][p] * s + 2 * s * D[p][q] * c + c * D[q][q] * c;
            D[p][q] = D[q][p] = 0;
        }
        const eig = D.map((r, i) => ({ val: r[i], vec: V.map(row => row[i]) }));
        return eig.sort((a, b) => b.val - a.val);
    },
    mds: (distMatrix) => {
        const n = distMatrix.length;
        const D2 = distMatrix.map(row => row.map(v => v * v));
        const rowMeans = D2.map(r => MathLib.mean(r));
        const colMeans = Array(n).fill(0).map((_, i) => MathLib.mean(D2.map(r => r[i])));
        const matrixMean = MathLib.mean(rowMeans);
        const B = Array(n).fill(0).map((_, i) => Array(n).fill(0).map((_, j) =>
            -0.5 * (D2[i][j] - rowMeans[i] - colMeans[j] + matrixMean)
        ));
        const eig = MathLib.jacobi(B);

        // Calculate variance explained by top 2 dimensions
        const positiveEigs = eig.filter(e => e.val > 0).map(e => e.val);
        const totalVar = positiveEigs.reduce((a, b) => a + b, 0);
        const explainedVar = (positiveEigs.length >= 2 && totalVar > 0)
            ? ((positiveEigs[0] + positiveEigs[1]) / totalVar) * 100
            : 100;

        const X = eig[0].val > 0 ? eig[0].vec.map(v => v * Math.sqrt(eig[0].val)) : Array(n).fill(0);
        const Y = eig[1].val > 0 ? eig[1].vec.map(v => v * Math.sqrt(eig[1].val)) : Array(n).fill(0);
        const Z = (eig[2] && eig[2].val > 0) ? eig[2].vec.map(v => v * Math.sqrt(eig[2].val)) : Array(n).fill(0);

        return {
            coords: X.map((x, i) => ({ x, y: Y[i], z: Z[i] })),
            varianceExplained: Math.round(explainedVar)
        };
    }
};

let graphVarianceExplained = 0; // Store for legend
let graphPC1Songs = []; // Top 3 songs defining X-axis
let graphPC2Songs = []; // Top 3 songs defining Y-axis

function initConstellation(data) {
    // data = { matrix: {...}, rankings: {...}, song_names: {...} }
    const matrixData = data.matrix;
    const songRankings = data.rankings || {};
    const songNames = data.song_names || {};
    const cvs = document.getElementById('taste-canvas');

    if (!cvs || !matrixData) return;

    // Set canvas dimensions from CSS layout (critical for proper scaling!)
    const rect = cvs.getBoundingClientRect();
    cvs.width = rect.width;
    cvs.height = rect.height;

    // Initialize the global graphCtx for drawGraph() to use
    graphCtx = cvs.getContext('2d');

    // Compute users and distance matrix from matrixData
    const users = Object.keys(matrixData);
    const distMatrix = users.map(u1 => users.map(u2 => matrixData[u1][u2]));

    let mdsResult;
    try { mdsResult = MathLib.mds(distMatrix); } catch (e) { console.error("MDS Failed", e); return; }

    const coords = mdsResult.coords;
    graphVarianceExplained = mdsResult.varianceExplained;

    let maxX = 0;
    let maxY = 0;
    coords.forEach(p => {
        if (Math.abs(p.x) > maxX) maxX = Math.abs(p.x);
        if (Math.abs(p.y) > maxY) maxY = Math.abs(p.y);
    });

    const padding = 40; // Reduced padding for tighter fit
    const w = cvs.width, h = cvs.height;

    // Scale to fit the furthest point within the canvas (keeping origin at center)
    const scaleX = (w / 2 - padding) / (maxX || 1);
    const scaleY = (h / 2 - padding) / (maxY || 1);
    const fitScale = Math.min(scaleX, scaleY);

    // Use Uniform Scaling to preserve Aspect Ratio (Distance = Divergence)
    // Engineers expect Euclidean space to be consistent.
    const scale = fitScale;

    graphNodes = users.map((u, i) => ({
        id: u,
        x: coords[i].x * scale + w / 2,
        y: coords[i].y * scale + h / 2,

        // 3D Real World Coords (Centered)
        realX: coords[i].x * scale,
        realY: coords[i].y * scale,
        realZ: coords[i].z * scale,

        color: `hsl(${280 + ((i * 40) % 80)}, 70%, 60%)`,
        initials: u.substring(0, 2).toUpperCase(),
        pc1: coords[i].x, // Store raw PC coords for loading calc
        pc2: coords[i].y,
        pc3: coords[i].z
    }));

    // Compute Song Loadings (Pearson correlation of song ranks with PC scores)
    const pc1Coords = graphNodes.map(n => n.pc1);
    const pc2Coords = graphNodes.map(n => n.pc2);
    const pc3Coords = graphNodes.map(n => n.pc3);

    const songLoadings = [];
    for (const [songId, userRanks] of Object.entries(songRankings)) {
        // Build rank vector aligned with users array
        const rankVec = users.map(u => userRanks[u] ?? 0);

        // Pearson correlation with PC scores
        const r1 = MathLib.pearson(rankVec, pc1Coords);
        const r2 = MathLib.pearson(rankVec, pc2Coords);
        const r3 = MathLib.pearson(rankVec, pc3Coords);

        songLoadings.push({
            id: songId,
            name: songNames[songId] || songId.substring(0, 8),
            pc1: r1,
            pc2: r2,
            pc3: r3
        });
    }

    // Helper to generate "Vs" labels
    const getAxisLabel = (loadings, axisName) => {
        const sorted = [...loadings].sort((a, b) => Math.abs(b[axisName]) - Math.abs(a[axisName]));
        if (sorted.length < 1) return `${axisName.toUpperCase()}: Variance`;
        const s1 = sorted[0];
        const s2 = sorted[1];

        // If only 1 song or 2nd is weak, just show top
        if (!s2 || Math.abs(s2[axisName]) < 0.3) {
            return `${axisName.toUpperCase()}: Polarized by "${s1.name}"`;
        }
        // If signs oppose, it's a VS
        if (Math.sign(s1[axisName]) !== Math.sign(s2[axisName])) {
            return `${axisName.toUpperCase()}: "${s1.name}" vs "${s2.name}"`;
        } else {
            return `${axisName.toUpperCase()}: Driven by "${s1.name}" & "${s2.name}"`;
        }
    };

    window.graphAxisLabels = {
        x: getAxisLabel(songLoadings, 'pc1'),
        y: getAxisLabel(songLoadings, 'pc2'),
        z: getAxisLabel(songLoadings, 'pc3')
    };

    // Store full data for drill-down
    window.graphAxisData = {
        pc1: [...songLoadings].sort((a, b) => Math.abs(b.pc1) - Math.abs(a.pc1)),
        pc2: [...songLoadings].sort((a, b) => Math.abs(b.pc2) - Math.abs(a.pc2)),
        pc3: [...songLoadings].sort((a, b) => Math.abs(b.pc3) - Math.abs(a.pc3))
    };

    // Store rankings and song names for position analysis
    window.graphRankingsData = songRankings;
    window.graphSongNames = songNames;
    window.graphUsers = users;

    // Global helper for showing details (now uses MODAL instead of alert)
    window.showAxisDetails = (title, data, key) => {
        const modal = document.getElementById('song-modal');
        const content = document.getElementById('song-modal-content');
        document.getElementById('song-modal-title').textContent = title + " Drivers";
        modal.classList.remove('hidden');
        modal.style.display = 'flex';

        const limit = getLimit(10, data.length);
        const topSongs = data.slice(0, limit);

        content.innerHTML = `
                    <div style="font-size:12px; color:var(--muted); margin-bottom:15px; text-align:center;">
                        High magnitude Pearson correlation indicates a strong driver of this axis. Click any song for distribution.
                    </div>
                    <div style="max-height:60vh; overflow-y:auto; padding-right:5px;">
                        ${topSongs.map((s, i) => `
                            <div class="axis-item" onclick="showSongDistribution('${s.name.replace(/'/g, "\\'")}')">
                                <div style="display:flex; align-items:center; gap:12px;">
                                    <span style="font-family:monospace; color:var(--muted); font-size:11px;">${(i + 1).toString().padStart(2, '0')}</span>
                                    <span style="font-weight:600;">${s.name}</span>
                                </div>
                                <div style="font-weight:900; color:${s[key] > 0 ? 'var(--green)' : 'var(--red)'}; font-family:monospace;">
                                    ${s[key] > 0 ? '+' : ''}${s[key].toFixed(3)}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
    };

    // Click Handler for Drill-Down
    cvs.onclick = e => {
        const r = cvs.getBoundingClientRect();
        const x = e.clientX - r.left, y = e.clientY - r.top;
        const w = cvs.width, h = cvs.height;
        const cx = w / 2, cy = h / 2;

        // Click X-Axis Label (Right area) - REDUCED hitbox
        if (x > w - 120 && Math.abs(y - cy) < 25) {
            window.showAxisDetails('X-Axis', window.graphAxisData.pc1, 'pc1');
            return;
        }
        // Click Y-Axis Label (Top center area) - REDUCED hitbox
        if (Math.abs(x - cx) < 100 && y < 35) {
            window.showAxisDetails('Y-Axis', window.graphAxisData.pc2, 'pc2');
            return;
        }

        // Check for node clicks (with 15px radius for easier clicking)
        const clickRadius = 15;
        const clickedNodes = graphNodes.filter(n => Math.hypot(n.x - x, n.y - y) < clickRadius);

        if (clickedNodes.length === 0) return;

        // If multiple nodes overlap, show picker
        if (clickedNodes.length > 1) {
            showNodePicker(clickedNodes, x, y);
        } else {
            showUserPositionMath(clickedNodes[0]);
        }
    };

    // Show user's position math
    window.showUserPositionMath = function (node) {
        const modal = document.getElementById('song-modal');
        const content = document.getElementById('song-modal-content');
        const title = document.getElementById('song-modal-title');

        title.textContent = `${node.id}'s Position Analysis`;
        modal.classList.remove('hidden');
        modal.style.display = 'flex';

        // Calculate distance from origin (community consensus)
        const distance = Math.sqrt(node.pc1 * node.pc1 + node.pc2 * node.pc2 + node.pc3 * node.pc3).toFixed(2);
        const distance2D = Math.sqrt(node.pc1 * node.pc1 + node.pc2 * node.pc2).toFixed(2);

        // Advanced Mode: Calculate per-song contributions
        let songContributionHTML = '';

        // Debug checks
        const hasRanks = window.graphRankingsData && Object.keys(window.graphRankingsData).length > 0;

        if (window.advancedMode && hasRanks && window.graphAxisData) {
            const songContributions = [];

            // Calculate mean ranks for normalization
            const meanRanks = {};
            for (const [songId, userRanks] of Object.entries(window.graphRankingsData)) {
                const ranks = Object.values(userRanks);
                meanRanks[songId] = ranks.reduce((a, b) => a + b, 0) / ranks.length;
            }

            // For each song, calculate its contribution
            for (const songData of window.graphAxisData.pc1) {
                const songId = songData.id;
                const userRank = window.graphRankingsData[songId]?.[node.id];

                if (userRank !== undefined) {
                    const deviation = userRank - meanRanks[songId];
                    const pc2Data = window.graphAxisData.pc2.find(s => s.id === songId);
                    const pc3Data = window.graphAxisData.pc3.find(s => s.id === songId);

                    songContributions.push({
                        name: songData.name,
                        rank: userRank,
                        mean: meanRanks[songId].toFixed(1),
                        deviation: deviation.toFixed(1),
                        pc1Contrib: (songData.pc1 * deviation).toFixed(3),
                        pc2Contrib: ((pc2Data?.pc2 || 0) * deviation).toFixed(3),
                        pc3Contrib: ((pc3Data?.pc3 || 0) * deviation).toFixed(3)
                    });
                }
            }

            // Sort by absolute total contribution
            songContributions.sort((a, b) => {
                const totA = Math.abs(parseFloat(a.pc1Contrib)) + Math.abs(parseFloat(a.pc2Contrib));
                const totB = Math.abs(parseFloat(b.pc1Contrib)) + Math.abs(parseFloat(b.pc2Contrib));
                return totB - totA;
            });

            if (songContributions.length > 0) {
                songContributionHTML = `
                            <div style="margin-top:25px; border-top:2px solid var(--pink); padding-top:20px;">
                                <h4 style="font-size:14px; color:var(--pink); margin-bottom:10px;">
                                    Per-Song Contribution Analysis
                                    <span style="font-size:10px; color:var(--muted); font-weight:400; margin-left:8px;">(Advanced Mode)</span>
                                </h4>
                                <div style="font-size:11px; color:var(--muted); margin-bottom:12px; line-height:1.5;">
                                    Shows how ${node.id}'s rank on each song contributes to their position. Contribution = Song Loading × (User Rank - Mean Rank)
                                </div>
                                <div style="max-height:400px; overflow-y:auto;">
                                    <table style="width:100%; font-size:11px;">
                                        <thead>
                                            <tr style="position:sticky; top:0; background:var(--bg); border-bottom:2px solid var(--border);">
                                                <th style="text-align:left; padding:8px 4px;">Song</th>
                                                <th style="text-align:center; padding:8px 4px;">Rank</th>
                                                <th style="text-align:center; padding:8px 4px;">Dev</th>
                                                <th style="text-align:center; padding:8px 4px;">→PC1</th>
                                                <th style="text-align:center; padding:8px 4px;">→PC2</th>
                                                <th style="text-align:center; padding:8px 4px;">→PC3</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${songContributions.map(s => `
                                                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                                                    <td style="padding:6px 4px; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${s.name}</td>
                                                    <td style="text-align:center; padding:6px 4px; color:var(--muted);">#${s.rank}</td>
                                                    <td style="text-align:center; padding:6px 4px; color:${parseFloat(s.deviation) > 0 ? 'var(--red)' : 'var(--green)'}; font-weight:600;">
                                                        ${parseFloat(s.deviation) > 0 ? '+' : ''}${s.deviation}
                                                    </td>
                                                    <td style="text-align:center; padding:6px 4px; color:${Math.abs(parseFloat(s.pc1Contrib)) > 0.1 ? 'var(--pink)' : 'var(--muted)'}; font-family:monospace;">
                                                        ${parseFloat(s.pc1Contrib) > 0 ? '+' : ''}${s.pc1Contrib}
                                                    </td>
                                                    <td style="text-align:center; padding:6px 4px; color:${Math.abs(parseFloat(s.pc2Contrib)) > 0.1 ? 'var(--pink)' : 'var(--muted)'}; font-family:monospace;">
                                                        ${parseFloat(s.pc2Contrib) > 0 ? '+' : ''}${s.pc2Contrib}
                                                    </td>
                                                    <td style="text-align:center; padding:6px 4px; color:${Math.abs(parseFloat(s.pc3Contrib)) > 0.1 ? 'var(--pink)' : 'var(--muted)'}; font-family:monospace;">
                                                        ${parseFloat(s.pc3Contrib) > 0 ? '+' : ''}${s.pc3Contrib}
                                                    </td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                                <div style="margin-top:10px; padding:10px; background:rgba(255,255,255,0.03); border-radius:6px; font-size:10px; color:var(--muted); line-height:1.5;">
                                    <b>Reading the table:</b><br>
                                    • <b>Rank</b>: ${node.id}'s ranking for this song<br>
                                    • <b>Dev</b>: Deviation from average (Red = ranked lower/worse, Green = ranked higher/better)<br>
                                    • <b>→PC1/PC2/PC3</b>: Contribution to each coordinate (larger absolute values = stronger influence)
                                </div>
                            </div>
                        `;
            } else {
                songContributionHTML = `<div style="padding:20px; text-align:center; color:var(--muted);">No rank data available for this user to calculate contributions.</div>`;
            }
        } else if (window.advancedMode) {
            songContributionHTML = `<div style="padding:20px; text-align:center; color:var(--red); font-size:12px;">Data missing for advanced analysis.<br>Ranks: ${!!hasRanks}, Axis: ${!!window.graphAxisData}<br>Please refresh the page.</div>`;
        }

        content.innerHTML = `
                    <div style="margin-bottom:20px;">
                        <h4 style="font-size:14px; color:var(--pink); margin-bottom:10px;">Coordinates in Taste Space</h4>
                        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px;">
                            <div class="card" style="padding:12px; text-align:center;">
                                <div style="font-size:10px; color:var(--muted); margin-bottom:5px;">PC1 (X-Axis)</div>
                                <div style="font-size:18px; font-weight:900; color:${node.pc1 > 0 ? 'var(--green)' : 'var(--red)'}">
                                    ${node.pc1 > 0 ? '+' : ''}${node.pc1.toFixed(3)}
                                </div>
                            </div>
                            <div class="card" style="padding:12px; text-align:center;">
                                <div style="font-size:10px; color:var(--muted); margin-bottom:5px;">PC2 (Y-Axis)</div>
                                <div style="font-size:18px; font-weight:900; color:${node.pc2 > 0 ? 'var(--green)' : 'var(--red)'}">
                                    ${node.pc2 > 0 ? '+' : ''}${node.pc2.toFixed(3)}
                                </div>
                            </div>
                            <div class="card" style="padding:12px; text-align:center;">
                                <div style="font-size:10px; color:var(--muted); margin-bottom:5px;">PC3 (Z-Depth)</div>
                                <div style="font-size:18px; font-weight:900; color:${node.pc3 > 0 ? 'var(--green)' : 'var(--red)'}">
                                    ${node.pc3 > 0 ? '+' : ''}${node.pc3.toFixed(3)}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div style="margin-bottom:20px;">
                        <h4 style="font-size:14px; color:var(--pink); margin-bottom:10px;">Distance from Consensus</h4>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                            <div class="card" style="padding:12px; background:rgba(219,97,162,0.1); border-color:var(--pink);">
                                <div style="font-size:10px; color:var(--muted); margin-bottom:5px;">2D Distance (Visible)</div>
                                <div style="font-size:22px; font-weight:900; color:var(--pink)">${distance2D}</div>
                                <div style="font-size:9px; color:var(--muted); margin-top:3px;">Euclidean distance in 2D projection</div>
                            </div>
                            <div class="card" style="padding:12px;">
                                <div style="font-size:10px; color:var(--muted); margin-bottom:5px;">3D Distance (True)</div>
                                <div style="font-size:22px; font-weight:900;">${distance}</div>
                                <div style="font-size:9px; color:var(--muted); margin-top:3px;">Full dimensional distance</div>
                            </div>
                        </div>
                    </div>

                    <div>
                        <h4 style="font-size:14px; color:var(--pink); margin-bottom:10px;">Interpretation</h4>
                        <div style="font-size:12px; color:var(--muted); line-height:1.6; padding:12px; background:rgba(255,255,255,0.03); border-radius:6px;">
                            <p style="margin:0 0 8px 0;">The <b>coordinates</b> show where <b>${node.id}</b> sits in the multi-dimensional taste space.</p>
                            <ul style="margin:0; padding-left:20px;">
                                <li><b>PC1 (${node.pc1 > 0 ? 'Positive' : 'Negative'})</b>: Aligns with ${node.pc1 > 0 ? 'right' : 'left'} side of the X-axis spectrum</li>
                                <li><b>PC2 (${node.pc2 > 0 ? 'Positive' : 'Negative'})</b>: Aligns with ${node.pc2 > 0 ? 'top' : 'bottom'} side of the Y-axis spectrum</li>
                                <li><b>Distance</b>: ${distance2D > 0.5 ? 'High divergence - unique taste profile' : 'Low divergence - mainstream taste'}</li>
                            </ul>
                            <p style="margin:12px 0 0 0; padding-top:12px; border-top:1px solid var(--border);">
                                Click the <b>X-Axis</b> or <b>Y-Axis</b> labels to see which specific songs drive each dimension.
                                ${!window.advancedMode ? '<br><b>Enable Advanced Mode</b> to see per-song contribution analysis.' : ''}
                            </p>
                        </div>
                    </div>
                    
                    ${songContributionHTML}
                `;
    }

    // Show picker when nodes overlap
    window.showNodePicker = function (nodes, x, y) {
        const modal = document.getElementById('song-modal');
        const content = document.getElementById('song-modal-content');
        const title = document.getElementById('song-modal-title');

        title.textContent = 'Select User';
        modal.classList.remove('hidden');
        modal.style.display = 'flex';

        // Store nodes globally for onclick access
        window.tempOverlapNodes = nodes;

        content.innerHTML = `
                    <div style="font-size:12px; color:var(--muted); margin-bottom:15px; text-align:center;">
                        Multiple users are in this area. Select one to view position details:
                    </div>
                    <div style="display:grid; gap:10px;">
                        ${nodes.map((n, idx) => `
                            <div onclick="showUserPositionMath(window.tempOverlapNodes[${idx}]);"  
                                 style="padding:15px; background:var(--card); border:1px solid var(--border); border-radius:8px; cursor:pointer; transition:all 0.2s;"
                                 onmouseover="this.style.borderColor='var(--pink)'; this.style.background='rgba(219,97,162,0.1)'"
                                 onmouseout="this.style.borderColor='var(--border)'; this.style.background='var(--card)'">
                                <div style="display:flex; align-items:center; gap:12px;">
                                    <div style="width:32px; height:32px; border-radius:50%; background:${n.color}; display:flex; align-items:center; justify-content:center; font-weight:bold; color:#000; font-size:14px;">
                                        ${n.initials}
                                    </div>
                                    <div style="font-weight:600; font-size:16px;">${n.id}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
    }


    // Find top polarizing songs for each axis (keep for reference)
    graphPC1Songs = window.graphAxisData.pc1.slice(0, 3).map(s => s.name);
    graphPC2Songs = window.graphAxisData.pc2.slice(0, 3).map(s => s.name);

    // No edges needed (user requested removal)

    // Events
    // Drag State
    window.graphIsDragging = false;
    window.graphLastMouseX = 0;
    window.graphAutoRotate = true;

    cvs.onmousedown = e => {
        if (window.graphIs3D) {
            window.graphIsDragging = true;
            window.graphLastMouseX = e.clientX;
            window.graphAutoRotate = false;
            cvs.style.cursor = 'grabbing';
        }
    };
    cvs.onmouseup = e => {
        window.graphIsDragging = false;
        if (window.graphIs3D) cvs.style.cursor = 'grab';
    };
    cvs.onmouseleave = cvs.onmouseup;

    // Events
    cvs.onmousemove = e => {
        const r = cvs.getBoundingClientRect();
        const mx = e.clientX - r.left, my = e.clientY - r.top;

        // 3D Logic
        if (window.graphIs3D) {
            if (window.graphIsDragging) {
                const delta = e.clientX - window.graphLastMouseX;
                window.graphRotation += delta * 0.005;
                window.graphLastMouseX = e.clientX;
            } else {
                cvs.style.cursor = 'grab';
            }
            return; // Skip 2D hover logic
        }

        // Node Hover
        graphHover = graphNodes.find(n => Math.hypot(n.x - mx, n.y - my) < 12);

        // Axis Hover (REDUCED to match click areas)
        const w = cvs.width, h = cvs.height, cx = w / 2, cy = h / 2;
        window.graphHoverLabel = null;
        if (mx > w - 120 && Math.abs(my - cy) < 25) window.graphHoverLabel = 'x';
        else if (Math.abs(mx - cx) < 100 && my < 35) window.graphHoverLabel = 'y';

        // Cursor
        cvs.style.cursor = (graphHover || window.graphHoverLabel) ? 'pointer' : 'default';

        if (typeof drawGraph === 'function') drawGraph();
    };

    if (typeof drawGraph === 'function') drawGraph();
}

// Dashboard Constellation (simplified 2D version)
function initDashboardConstellation(data) {
    const matrixData = data.matrix;
    const cvs = document.getElementById('dash-taste-canvas');
    if (!cvs || !matrixData) return;

    const rect = cvs.getBoundingClientRect();
    cvs.width = rect.width;
    cvs.height = rect.height;
    const ctx = cvs.getContext('2d');
    const w = cvs.width, h = cvs.height;
    const cx = w / 2, cy = h / 2;

    const users = Object.keys(matrixData);

    // Need at least 3 users for meaningful constellation
    if (users.length < 3) {
        ctx.fillStyle = '#666';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('Need at least 3 users', cx, cy);
        return;
    }

    const distMatrix = users.map(u1 => users.map(u2 => matrixData[u1][u2]));

    let mdsResult;
    try {
        mdsResult = MathLib.mds(distMatrix);
    } catch (e) {
        console.error('MDS failed:', e);
        ctx.fillStyle = '#666';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('Calculation error', cx, cy);
        return;
    }

    const coords = mdsResult.coords;

    // Calculate actual coordinate spread for auto-scaling
    let maxX = 0, maxY = 0;
    coords.forEach(p => {
        maxX = Math.max(maxX, Math.abs(p.x));
        maxY = Math.max(maxY, Math.abs(p.y));
    });

    // If all coordinates are zero (perfect consensus), show message
    if (maxX === 0 && maxY === 0) {
        ctx.fillStyle = '#666';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('Perfect consensus!', cx, cy);
        return;
    }

    // Calculate scale to fit nodes within 85% of canvas (with padding)
    const padding = 40;
    const safeW = (w / 2) - padding;
    const safeH = (h / 2) - padding;
    const scaleX = maxX > 0 ? safeW / maxX : 1;
    const scaleY = maxY > 0 ? safeH / maxY : 1;
    const scale = Math.min(scaleX, scaleY);

    // Clear and draw background
    ctx.clearRect(0, 0, w, h);

    // Draw subtle grid circles
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    [50, 100].forEach(r => {
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.stroke();
    });

    // Draw axis lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.beginPath();
    ctx.moveTo(0, cy);
    ctx.lineTo(w, cy);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(cx, 0);
    ctx.lineTo(cx, h);
    ctx.stroke();

    // Create nodes with scaled positions
    const nodes = users.map((u, i) => ({
        id: u,
        x: coords[i].x * scale + cx,
        y: coords[i].y * scale + cy,
        color: `hsl(${280 + ((i * 40) % 80)}, 70%, 60%)`,
        initials: u.substring(0, 2).toUpperCase()
    }));

    // Draw nodes
    nodes.forEach(n => {
        // Outer glow
        ctx.shadowColor = n.color;
        ctx.shadowBlur = 8;

        // Node circle
        ctx.fillStyle = n.color;
        ctx.beginPath();
        ctx.arc(n.x, n.y, 8, 0, Math.PI * 2);
        ctx.fill();

        ctx.shadowBlur = 0;

        // Username label
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 9px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(n.id, n.x, n.y + 12);
    });

    // Draw legend
    ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
    ctx.font = '9px Inter';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    ctx.fillText(`${users.length} users • Distance = Disagreement`, 10, h - 8);
}

function drawGraph() {
    if (!graphCtx || window.graphIs3D) return;
    const cvs = document.getElementById('taste-canvas');
    const w = cvs.width, h = cvs.height;

    graphCtx.clearRect(0, 0, w, h);

    // Background Structure (to make it look less random)
    const cx = w / 2, cy = h / 2;

    graphCtx.save();
    graphCtx.strokeStyle = 'rgba(219, 97, 162, 0.1)'; // Theme pink, very faint
    graphCtx.lineWidth = 1;
    graphCtx.fillStyle = 'rgba(255, 255, 255, 0.2)';
    graphCtx.font = '9px Inter, monospace';
    graphCtx.textAlign = 'center';
    graphCtx.textBaseline = 'middle';

    // Find the global max distance for grid scaling (from graphNodes)
    // graphNodes are already centered at cx, cy
    let maxNodeDist = 0;
    graphNodes.forEach(n => {
        maxNodeDist = Math.max(maxNodeDist, Math.abs(n.x - cx), Math.abs(n.y - cy));
    });
    // Round up to nearest 100 for nice grid
    const gridStep = 100;
    const maxGrid = Math.ceil(maxNodeDist / gridStep) * gridStep + gridStep;

    // Concentric circles (Radar style) with labels
    for (let r = gridStep; r <= maxGrid; r += gridStep) {
        graphCtx.beginPath();
        graphCtx.arc(cx, cy, r, 0, Math.PI * 2);
        graphCtx.stroke();
        // Axis labels
        graphCtx.fillText(r, cx + r, cy);
        graphCtx.fillText(-r, cx - r, cy);
    }

    // Crosshairs with Labels
    graphCtx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    graphCtx.beginPath(); graphCtx.moveTo(0, cy); graphCtx.lineTo(w, cy); graphCtx.stroke();
    graphCtx.beginPath(); graphCtx.moveTo(cx, 0); graphCtx.lineTo(cx, h); graphCtx.stroke();

    // Axis Labels (with Defining Songs)
    // Axis Labels (with Defining Songs)
    graphCtx.font = 'italic 10px Inter, sans-serif';

    // X-Axis
    graphCtx.textAlign = 'right';
    const pc1Label = window.graphAxisLabels ? window.graphAxisLabels.x : (graphPC1Songs.length ? `X: Polarized by "${graphPC1Songs[0]}"` : "X: Primary Variance");
    graphCtx.fillStyle = (window.graphHoverLabel === 'x') ? '#fff' : 'rgba(255, 255, 255, 0.4)';
    graphCtx.fillText(pc1Label, w - 10, cy - 6);
    if (window.graphHoverLabel === 'x') {
        const m = graphCtx.measureText(pc1Label);
        graphCtx.fillRect(w - 10 - m.width, cy - 4, m.width, 1);
    }

    // Y-Axis
    graphCtx.textAlign = 'center';
    const pc2Label = window.graphAxisLabels ? window.graphAxisLabels.y : (graphPC2Songs.length ? `Y: Polarized by "${graphPC2Songs[0]}"` : "Y: Secondary Variance");
    graphCtx.fillStyle = (window.graphHoverLabel === 'y') ? '#fff' : 'rgba(255, 255, 255, 0.4)';
    graphCtx.fillText(pc2Label, cx, 20);
    if (window.graphHoverLabel === 'y') {
        const m = graphCtx.measureText(pc2Label);
        graphCtx.fillRect(cx - m.width / 2, 22, m.width, 1);
    }

    // Origin Label
    graphCtx.textAlign = 'center';
    graphCtx.fillText("0", cx + 5, cy + 10);

    // Legend / Explanation
    graphCtx.fillStyle = 'rgba(255, 255, 255, 0.5)';
    graphCtx.font = 'bold 12px Inter, sans-serif';
    graphCtx.textAlign = 'left'; graphCtx.textBaseline = 'bottom';
    graphCtx.fillText("TASTE CONSTELLATION (Multidimensional Scaling)", 20, h - 75);

    graphCtx.font = '10px Inter, sans-serif'; graphCtx.fillStyle = 'rgba(255, 255, 255, 0.4)';
    graphCtx.fillText("• Center (0,0): Community Consensus (Average Taste)", 20, h - 55);
    graphCtx.fillText("• Distance: RMS Taste Divergence (Length of difference vector)", 20, h - 40);
    graphCtx.fillText("• Projection: Top 2 Principal Components (PC1 & PC2) of variance", 20, h - 25);
    graphCtx.fillText(`• 2D Accuracy: ${graphVarianceExplained}% (captures nearly all structure)`, 20, h - 10);

    // Interaction instruction
    if (window.constellationSelectedUser) {
        graphCtx.fillStyle = 'rgba(219, 97, 162, 0.8)';
        graphCtx.font = 'bold 11px Inter';
        graphCtx.fillText(`✓ ${window.constellationSelectedUser} selected - Click another user to compare`, 20, 20);
    } else {
        graphCtx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        graphCtx.font = '10px Inter';
        graphCtx.fillText("Click any user to select, then click another to compare divergence", 20, 20);
    }

    graphCtx.restore();

    // No Edges (removed per user feedback)

    // Nodes (smaller for less overlap)
    graphNodes.forEach(n => {
        graphCtx.shadowBlur = 0;

        // Border
        graphCtx.fillStyle = '#161b22';
        graphCtx.beginPath(); graphCtx.arc(n.x, n.y, 12, 0, Math.PI * 2); graphCtx.fill();
        // Color
        graphCtx.fillStyle = n.color;
        graphCtx.beginPath(); graphCtx.arc(n.x, n.y, 10, 0, Math.PI * 2); graphCtx.fill();

        // Label (Full Name) - draw below the node
        graphCtx.fillStyle = "rgba(255, 255, 255, 0.8)";
        graphCtx.font = "bold 9px Inter, sans-serif";
        graphCtx.textAlign = "center"; graphCtx.textBaseline = "top";
        graphCtx.fillText(n.id, n.x, n.y + 14);

        // Hover glow
        if (graphHover === n) {
            graphCtx.shadowBlur = 15; graphCtx.shadowColor = n.color;
        }
    });
}

// 3D Visualizer Logic
window.graphIs3D = false;
window.graphRotation = 0;
let graphAnimFrame = null;

window.toggle3D = () => {
    window.graphIs3D = !window.graphIs3D;
    const btn = document.getElementById('toggle-3d');
    const cvs = document.getElementById('taste-canvas');
    if (window.graphIs3D) {
        btn.innerHTML = "SWITCH TO 2D";
        btn.style.background = "var(--pink)";
        btn.style.color = "#000";
        // Start Loop
        window.graphRotation = 0;
        if (graphAnimFrame) cancelAnimationFrame(graphAnimFrame);
        animate3D();
    } else {
        btn.innerHTML = "SWITCH TO 3D";
        btn.style.background = "transparent";
        btn.style.color = "var(--pink)";
        if (graphAnimFrame) cancelAnimationFrame(graphAnimFrame);
        drawGraph(); // Draw 2D
        cvs.style.cursor = 'default';
    }
};

function animate3D() {
    if (!window.graphIs3D) return;
    if (window.graphAutoRotate) {
        window.graphRotation += 0.005;
    }
    drawGraph3D();
    graphAnimFrame = requestAnimationFrame(animate3D);
}

window.drawGraph3D = () => {
    if (!graphCtx) return;
    const cvs = document.getElementById('taste-canvas');
    const w = cvs.width, h = cvs.height;
    const cx = w / 2, cy = h / 2;

    graphCtx.clearRect(0, 0, w, h);

    // 3D Config
    const fov = 500;
    const cameraZ = 600;
    const cos = Math.cos(window.graphRotation);
    const sin = Math.sin(window.graphRotation);

    // Project Helper
    const project = (x, y, z) => {
        const x3 = x * cos - z * sin;
        const y3 = y;
        const z3 = x * sin + z * cos;
        const depth = z3;
        const dist = cameraZ - depth;
        if (dist <= 0) return null;
        const scale = fov / dist;
        return { x: x3 * scale + cx, y: y3 * scale + cy, scale, depth };
    };

    // Draw Title
    graphCtx.fillStyle = 'rgba(255,255,255,0.5)';
    graphCtx.font = '12px Inter';
    graphCtx.textAlign = 'left'; graphCtx.textBaseline = 'top';
    const title = window.graphAutoRotate ? "3D Mode - Auto-Rotating" : "3D Mode - Drag to Rotate";
    graphCtx.fillText(title, 20, 20);

    // Draw Axes
    const axisLen = 300;
    const axes = [
        { s: [-axisLen, 0, 0], e: [axisLen, 0, 0], c: '#ff4444', l: 'X' },
        { s: [0, -axisLen, 0], e: [0, axisLen, 0], c: '#44ff44', l: 'Y' },
        { s: [0, 0, -axisLen], e: [0, 0, axisLen], c: '#4488ff', l: 'Z' }
    ];

    axes.forEach(ax => {
        const p1 = project(...ax.s);
        const p2 = project(...ax.e);
        if (p1 && p2) {
            graphCtx.beginPath();
            graphCtx.strokeStyle = ax.c;
            graphCtx.lineWidth = 1; graphCtx.globalAlpha = 0.5;
            graphCtx.moveTo(p1.x, p1.y);
            graphCtx.lineTo(p2.x, p2.y);
            graphCtx.stroke();
            graphCtx.globalAlpha = 1;
            // Short Label
            graphCtx.fillStyle = ax.c;
            graphCtx.font = 'bold 12px Inter';
            graphCtx.textAlign = 'center';
            graphCtx.fillText(ax.l, p2.x, p2.y);

            // Full Label (Song Drivers)
            if (window.graphAxisLabels) {
                const labelKey = ax.l.toLowerCase();
                const fullLabel = window.graphAxisLabels[labelKey];
                if (fullLabel) {
                    graphCtx.font = '10px Inter';
                    graphCtx.fillStyle = 'rgba(255,255,255,0.7)';
                    graphCtx.fillText(fullLabel, p2.x, p2.y + 15);
                }
            }
        }
    });

    // Draw Nodes
    const projected = graphNodes.map(n => {
        const p = project(n.realX, n.realY, n.realZ);
        return p ? { ...n, x2d: p.x, y2d: p.y, scale: p.scale, depth: p.depth } : { ...n, scale: 0 };
    });

    // Sort: draw furthest first
    projected.sort((a, b) => a.scale - b.scale);

    projected.forEach(n => {
        if (n.scale <= 0) return;

        const size = Math.max(1, 8 * n.scale);
        graphCtx.beginPath();
        graphCtx.fillStyle = n.color;
        // Fade distant nodes
        graphCtx.globalAlpha = Math.min(1, Math.max(0.1, n.scale));
        graphCtx.arc(n.x2d, n.y2d, size, 0, Math.PI * 2);
        graphCtx.fill();

        // Text for closer nodes
        if (n.scale > 0.8) {
            graphCtx.fillStyle = '#fff';
            graphCtx.font = `bold ${Math.max(9, 12 * n.scale)}px Inter`;
            graphCtx.textAlign = 'center';
            graphCtx.fillText(n.initials, n.x2d, n.y2d + size + 5);
        }
        graphCtx.globalAlpha = 1;
    });
};


function toggleSubmission(show) { document.getElementById('submission-overlay').style.display = show ? 'flex' : 'none'; }

// UPDATED SUBMISSION LOGIC
async function postSubmission() {
    const log = document.getElementById('submit-log');
    const user = document.getElementById('in-user').value.trim();
    const list = document.getElementById('in-list').value.trim();
    const f = document.getElementById('sub-franchise').value;
    const btn = document.getElementById('submit-btn-real');

    // Validation: Ensure fields are non-empty
    if (!user || !list) {
        log.innerHTML = `<span style="color:var(--red)">Username and list are required.</span>`;
        return;
    }

    btn.disabled = true;
    log.innerHTML = "POSTING DATA...";

    try {
        const r = await fetch(`${API}/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: user,
                franchise: f,
                subgroup_name: "All Songs",
                ranking_list: list
            })
        });
        const d = await r.json();
        if (d.status === "VALID") {
            log.innerHTML = `<span style="color:var(--green)">SUCCESSFULLY SUBMITTED!</span>`;
            setTimeout(() => {
                toggleSubmission(false);
                btn.disabled = false;
            }, 1500);
        } else {
            let firstErr = Object.values(d.conflicts)[0];
            log.innerHTML = `<span style="color:var(--red)">VALIDATION ERROR: Line ${firstErr.line_num} (${firstErr.reason})</span>`;
            btn.disabled = false;
        }
    } catch (e) {
        log.innerHTML = `<span style="color:var(--red)">CONNECTION ERROR.</span>`;
        btn.disabled = false;
    }
}

async function loadUsers() {
    const franchise = document.getElementById('view-franchise').value;
    const subgroup = document.getElementById('view-subgroup').value;
    const content = document.getElementById('users-content');
    const statsContainer = document.getElementById('users-stats-container');

    content.innerHTML = '<div style="text-align: center; padding: 80px 20px; font-size: 18px; color: var(--muted);">Loading rankings...</div>';
    statsContainer.innerHTML = '';

    try {
        // Fetch rankings first - don't wait for spice
        const rankingsRes = await fetch(`${API}/users/rankings?franchise=${franchise}&subgroup=${encodeURIComponent(subgroup)}`);

        if (!rankingsRes.ok) throw new Error(`API returned ${rankingsRes.status}`);

        const data = await rankingsRes.json();

        // Render immediately with placeholder spice values
        renderUsersData(data, {}, subgroup);

        // Fetch spice in background and update when ready
        fetch(`${API}/analysis/spice?franchise=${franchise}`)
            .then(r => r.ok ? r.json() : { results: [] })
            .then(spiceData => {
                const spiceMap = {};
                (spiceData.results || []).forEach(u => spiceMap[u.username] = u.global_spice);
                // Update spice values in the already-rendered cards
                updateSpiceValues(spiceMap);
            })
            .catch(e => console.warn('Spice fetch error:', e));

    } catch (error) {
        console.error('Error loading rankings:', error);
        content.innerHTML = `<div style="background: rgba(248, 81, 73, 0.15); border: 1px solid var(--red); color: var(--red); padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center; font-weight: 600;">Failed to load rankings: ${error.message}</div>`;
    }
}

// Update spice values after they load
function updateSpiceValues(spiceMap) {
    document.querySelectorAll('.user-card').forEach(card => {
        const username = card.querySelector('.user-name')?.textContent;
        const spiceEl = card.querySelector('.spice-value');
        if (username && spiceEl && spiceMap[username] !== undefined) {
            spiceEl.textContent = spiceMap[username];
            spiceEl.classList.remove('loading');
        }
    });
}

// Render users data (extracted for reuse)
function renderUsersData(data, spiceMap, subgroup) {
    const content = document.getElementById('users-content');
    const statsContainer = document.getElementById('users-stats-container');

    // Calculate aggregate stats
    const avgSongsRanked = data.users.length > 0
        ? Math.round(data.users.reduce((a, u) => a + u.total_songs, 0) / data.users.length)
        : 0;

    // Stats Bar
    statsContainer.innerHTML = `
                    <div class="dashboard-grid" style="margin-bottom: 25px;">
                        <div class="stat-card">
                            <div class="stat-label">Total Users</div>
                            <div class="stat-value">${data.total_users}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Franchise</div>
                            <div class="stat-value">${capitalize(data.franchise)}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Avg. Songs Ranked</div>
                            <div class="stat-value">${avgSongsRanked}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Subgroup</div>
                            <div class="stat-value" style="font-size:18px">${subgroup}</div>
                        </div>
                    </div>
                `;

    if (data.users.length === 0) {
        content.innerHTML = '<div style="text-align: center; padding: 60px 20px; color: var(--muted);"><p>No rankings found for this selection.</p></div>';
        return;
    }

    const grid = document.createElement('div');
    grid.className = 'user-grid';

    data.users.forEach(user => {
        const card = document.createElement('div');
        card.className = 'user-card';

        // Find user's #1 pick
        const topPick = user.rankings.length > 0 ? user.rankings[0].song_name : 'N/A';

        // User spice level - show loading initially, will be updated async
        const spice = spiceMap[user.username] !== undefined ? spiceMap[user.username] : '...';
        const spiceClass = spiceMap[user.username] !== undefined ? '' : 'loading';

        const rankingsList = user.rankings.map((r, i) => {
            let rankClass = '';
            let itemClass = '';
            if (i === 0) { rankClass = 'gold'; itemClass = 'top-3'; }
            else if (i === 1) { rankClass = 'silver'; itemClass = 'top-3'; }
            else if (i === 2) { rankClass = 'bronze'; itemClass = 'top-3'; }

            const escapedName = r.song_name.replace(/'/g, "\\'");
            return `
                            <div class="rank-item ${itemClass}" onclick="showSongDistribution('${escapedName}')" style="cursor:pointer;">
                                <div class="rank-number ${rankClass}">#${r.rank}</div>
                                <div class="song-name">${r.song_name}</div>
                            </div>
                        `;
        }).join('');

        card.innerHTML = `
                        <div class="user-header">
                            <div class="user-name">${user.username}</div>
                            <div class="song-count">${user.total_songs} songs</div>
                        </div>
                        <div class="user-insights">
                            <div class="insight-item">
                                <div class="insight-label">Top Pick</div>
                                <div class="insight-value green">${truncate(topPick, 20)}</div>
                            </div>
                            <div class="insight-item">
                                <div class="insight-label">Spice Level</div>
                                <div class="insight-value yellow spice-value ${spiceClass}">${spice}</div>
                            </div>
                        </div>
                        <div class="rankings-list">
                            ${rankingsList}
                        </div>
                    `;

        grid.appendChild(card);
    });

    content.innerHTML = '';
    content.appendChild(grid);
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

async function recompute() {
    document.getElementById('engine-log').innerText = "CALCULATING...";
    await fetch(`${API}/analysis/trigger`, { method: 'POST' });
    setTimeout(() => { syncData(); document.getElementById('engine-log').innerText = "READY"; }, 3000);
}

init();
