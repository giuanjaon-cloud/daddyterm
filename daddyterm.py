import sys
import os
import urllib.parse
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Errore: Librerie mancanti.")
    print("Per favore installale eseguendo dal terminale:")
    print("pip install requests beautifulsoup4")
    sys.exit(1)

from datetime import datetime, timedelta
import re
import json

# ================= CONFIGURAZIONE =================
TARGET_URL = "https://dlhd.st/"
PROXY_URL = "https://proxy.alemagno1994alex.workers.dev/?url=" + urllib.parse.quote(TARGET_URL)

OFFSET_HOURS = -1  # Sposta gli orari indietro di 1 ora

# Assicura che il file venga salvato nella STESSA DIRECTORY dello script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILENAME = os.path.join(SCRIPT_DIR, "palinsesto.html")

EXCLUDED_CATEGORIES = [
    "Big Brother 👁️ 28 LIVE CAMERA FEEDS",
    "TV Shows 📺",
    "Upcoming Events",
    "WSOP 2026 ♠️🃏"
]

# ================= TEMPLATE HTML =================
HTML_TEMPLATE = r'''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#070707">
<meta name="referrer" content="no-referrer">
<title>PALINSESTO</title>
<link href="https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-main: #070707;
    --bg-surface: #141414;
    --bg-surface-hover: #1f1f1f;
    --accent: #edff00;
    --text-primary: #ffffff;
    --text-secondary: #a0a0a0;
    --border-color: rgba(255, 255, 255, 0.1);
    --font-head: 'Roboto Condensed', sans-serif;
    --font-body: 'Roboto', sans-serif;
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; margin: 0; padding: 0; }
  body {
    background: var(--bg-main); color: var(--text-primary); font-family: var(--font-body);
    padding: max(20px, env(safe-area-inset-top)) max(20px, env(safe-area-inset-right)) max(30px, env(safe-area-inset-bottom)) max(20px, env(safe-area-inset-left));
    min-height: 100vh; -webkit-font-smoothing: antialiased; overflow-x: hidden;
    background-image: radial-gradient(circle at top right, #111111 0%, #070707 50%);
  }
  .container { max-width: 1400px; margin: 0 auto; }
  .header-wrap { display: flex; flex-direction: column; gap: 20px; margin-bottom: 40px; }
  .logo-area { display: flex; align-items: baseline; flex-wrap: wrap; gap: 15px; }
  .logo-text { font-family: var(--font-head); font-size: clamp(36px, 6vw, 54px); font-weight: 700; color: var(--text-primary); letter-spacing: -1px; text-transform: uppercase; line-height: 1; }
  .update-badge { background: rgba(255,255,255,0.05); border: 1px solid var(--border-color); padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 500; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }
  .update-badge span { color: var(--accent); font-weight: 700; }
  .controls { display: flex; flex-wrap: wrap; gap: 15px; align-items: center; justify-content: space-between; padding-bottom: 25px; border-bottom: 1px solid var(--border-color); }
  .search-wrapper { flex-grow: 2; min-width: 250px; position: relative; display: flex; align-items: center; }
  .search-wrapper input { width: 100%; background: var(--bg-surface); color: var(--text-primary); border: 1px solid var(--border-color); padding: 14px 40px 14px 20px; border-radius: 8px; font-family: var(--font-body); font-size: 16px; outline: none; transition: all 0.3s ease; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2); }
  .search-wrapper input:focus { border-color: var(--accent); background: #1a1a1a; box-shadow: 0 0 0 2px rgba(237, 255, 0, 0.1); }
  .clear-btn { position: absolute; right: 10px; background: transparent; border: none; color: var(--text-secondary); font-size: 22px; font-weight: bold; cursor: pointer; display: none; padding: 0 8px; transition: color 0.2s ease; outline: none; }
  .clear-btn:hover { color: var(--accent); }
  .select-wrapper { flex-grow: 1; min-width: 200px; position: relative; }
  .select-wrapper select { width: 100%; appearance: none; background: var(--bg-surface); color: var(--text-primary); border: 1px solid var(--border-color); padding: 14px 20px; border-radius: 8px; font-family: var(--font-head); font-size: 16px; font-weight: 700; text-transform: uppercase; cursor: pointer; transition: all 0.3s ease; outline: none; }
  .select-wrapper select:focus, .select-wrapper select:hover { border-color: var(--accent); background: #1a1a1a; }
  .select-wrapper::after { content: "▼"; position: absolute; right: 20px; top: 50%; transform: translateY(-50%); color: var(--accent); font-size: 10px; pointer-events: none; }
  .status-text { font-family: var(--font-head); font-size: 16px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; display: flex; align-items: center; gap: 8px; background: var(--bg-surface); padding: 12px 20px; border-radius: 8px; border: 1px solid var(--border-color); }
  .status-text .count { color: var(--text-primary); font-size: 22px; }
  .section-container { margin-top: 40px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; }
  .card { display: flex; flex-direction: column; background: linear-gradient(145deg, var(--bg-surface), #0a0a0a); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; text-decoration: none; color: var(--text-primary); text-align: left; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); cursor: pointer; position: relative; min-height: 150px; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.3); outline: none; }
  .card:hover, .card:focus-visible { transform: translateY(-6px); border-color: var(--accent); box-shadow: 0 12px 24px rgba(0,0,0,0.6), 0 0 0 1px var(--accent); }
  .card-header { padding: 14px 18px; border-bottom: 1px solid rgba(255,255,255,0.03); background: rgba(0,0,0,0.2); display: flex; justify-content: space-between; align-items: center; }
  .sport-label { font-family: var(--font-head); font-size: 14px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
  @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(229, 0, 0, 0.7); } 70% { box-shadow: 0 0 0 6px rgba(229, 0, 0, 0); } 100% { box-shadow: 0 0 0 0 rgba(229, 0, 0, 0); } }
  .time-badge { font-family: var(--font-head); font-size: 13px; font-weight: 700; color: var(--text-primary); background: rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 4px; letter-spacing: 1px; }
  .time-badge.live-active { background: #e50000; animation: pulse 2s infinite; }
  .time-badge.badge-247 { background: transparent; border: 1px solid var(--text-secondary); color: var(--text-secondary); }
  .card-body { padding: 24px 18px; flex-grow: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 12px; }
  .team-logos { display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 5px; }
  .team-logo { width: 45px; height: 45px; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5)); }
  .match-title { font-family: var(--font-head); font-size: 22px; font-weight: 700; line-height: 1.25; text-align: center; }
  .card-footer { padding: 14px 18px; background: rgba(0,0,0,0.5); display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.03); }
  .source-count { font-size: 13px; color: var(--text-secondary); font-weight: 500; display: flex; align-items: center; gap: 5px; }
  .source-count::before { content: "•"; color: var(--accent); font-size: 18px; line-height: 0; }
  .play-btn { font-family: var(--font-head); font-size: 14px; font-weight: 700; color: var(--bg-main); background: var(--text-primary); padding: 8px 20px; border-radius: 6px; transition: all 0.3s ease; text-transform: uppercase; }
  .card:hover .play-btn, .card:focus-visible .play-btn { background: var(--accent); }
  .modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(8px); display: none; align-items: center; justify-content: center; z-index: 1000; padding: 20px; opacity: 0; transition: opacity 0.3s ease; cursor: pointer; }
  .modal-overlay.active { display: flex; opacity: 1; }
  .modal-content { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 16px; width: 100%; max-width: 550px; padding: 30px; display: flex; flex-direction: column; gap: 15px; max-height: 85vh; box-shadow: 0 20px 40px rgba(0,0,0,0.8); transform: translateY(20px); transition: transform 0.3s ease; cursor: default; }
  .modal-overlay.active .modal-content { transform: translateY(0); }
  .modal-title { font-family: var(--font-head); font-size: 26px; font-weight: 700; text-transform: uppercase; color: var(--text-primary); text-align: center; margin-bottom: 5px; border-bottom: 1px solid var(--border-color); padding-bottom: 15px;}
  .modal-search-wrapper { position: relative; width: 100%; display: none; align-items: center; }
  #modal-search { width: 100%; background: #0a0a0a; color: var(--text-primary); border: 1px solid var(--border-color); padding: 14px 40px 14px 16px; border-radius: 8px; font-family: var(--font-body); font-size: 15px; outline: none; transition: all 0.3s; }
  #modal-search:focus { border-color: var(--accent); }
  .sources-list { display: flex; flex-direction: column; gap: 12px; overflow-y: auto; padding-right: 10px; margin-top: 5px; }
  .sources-list::-webkit-scrollbar { width: 6px; }
  .sources-list::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); border-radius: 3px; }
  .sources-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 3px; }
  .sources-list::-webkit-scrollbar-thumb:hover { background: var(--accent); }
  .source-btn { background: #0a0a0a; border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; color: var(--text-primary); font-family: var(--font-body); font-size: 16px; font-weight: 500; text-align: left; cursor: pointer; transition: all 0.2s ease; display: flex; justify-content: space-between; align-items: center; outline: none; }
  .source-btn:hover, .source-btn:focus-visible { border-color: var(--accent); background: #1a1a1a; transform: translateX(4px); }
  .source-btn::after { content: "►"; color: var(--accent); font-size: 14px; opacity: 0; transition: all 0.2s ease; transform: translateX(-10px); }
  .source-btn:hover::after, .source-btn:focus-visible::after { opacity: 1; transform: translateX(0); }
  .close-modal { background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); padding: 14px; border-radius: 8px; cursor: pointer; font-family: var(--font-head); font-weight: 700; font-size: 16px; text-transform: uppercase; transition: all 0.2s; text-align: center; margin-top: 10px; outline: none; }
  .close-modal:hover, .close-modal:focus-visible { background: rgba(255,255,255,0.05); color: var(--text-primary); border-color: var(--text-secondary); }
  #clean-player-container { position: fixed; inset: 0; background: #000; z-index: 9999; display: none; }
  #clean-player-iframe { width: 100%; height: 100%; border: none; }
  .close-player-btn { position: absolute; top: 20px; right: 20px; background: rgba(0,0,0,0.7); border: 2px solid var(--text-secondary); color: var(--text-primary); width: 44px; height: 44px; border-radius: 50%; font-size: 18px; font-weight: bold; cursor: pointer; z-index: 10000; display: flex; align-items: center; justify-content: center; transition: all 0.2s; outline: none; }
  .close-player-btn:hover, .close-player-btn:focus-visible { border-color: var(--accent); color: var(--accent); transform: scale(1.1); }
  @media (max-width: 600px) {
    .logo-area { flex-direction: column; gap: 5px; align-items: flex-start; }
    .controls { flex-direction: column; align-items: stretch; }
    .status-text { justify-content: space-between; }
  }
</style>
</head>
<body>

<div class="container" id="main-ui">
  <div class="header-wrap">
    <div class="logo-area">
        <h1 class="logo-text">PALINSESTO</h1>
        <div class="update-badge">Ultimo aggiornamento il <span id="current-date">__CURRENT_DATE__</span></div>
    </div>
    <div class="controls">
      <div class="search-wrapper">
        <input type="text" id="search-input" placeholder="Cerca evento o competizione...">
        <button id="clear-search" class="clear-btn" title="Cancella">&times;</button>
      </div>
      <div class="select-wrapper">
        <select id="sport-filter">
          <option value="all">TUTTI GLI EVENTI</option>
        </select>
      </div>
      <div class="status-text">
        <span>Eventi totali</span>
        <span class="count" id="total-count">0</span>
      </div>
    </div>
  </div>
  <div id="events-section" class="section-container">
    <main class="grid" id="events-grid"></main>
  </div>
</div>

<div class="modal-overlay" id="source-modal">
  <div class="modal-content">
    <div class="modal-title" id="modal-title">Scegli opzione</div>
    <div class="modal-search-wrapper" id="modal-search-wrapper">
        <input type="text" id="modal-search" placeholder="Filtra canali...">
        <button id="clear-modal-search" class="clear-btn" title="Cancella">&times;</button>
    </div>
    <div class="sources-list" id="sources-list"></div>
    <button class="close-modal" id="close-modal">CHIUDI</button>
  </div>
</div>

<div id="clean-player-container"></div>

<script type="application/json" id="api-data">
__JSON_DATA__
</script>

<script>
(() => {
  const $ = id => document.getElementById(id);
  const escapeHTML = str => String(str || "").replace(/[&<>"']/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[m]);

  let apiData = { events: [], channels: [], sports: [] };
  let lastFocusedElement = null; 
  let lastFocusedModalBtn = null;
  let isHomeModified = false;

  history.replaceState({ view: 'home' }, "", "");

  function pushModifyState() {
      if (!isHomeModified && !$("source-modal").classList.contains("active") && $("clean-player-container").style.display !== "block") {
          history.pushState({ view: 'modified' }, "", "");
          isHomeModified = true;
      }
  }

  window.addEventListener("popstate", (e) => {
      const state = e.state;
      const playerContainer = $("clean-player-container");
      if (playerContainer.style.display === "block") {
          playerContainer.innerHTML = '';
          playerContainer.style.display = "none";
      }
      
      if (!state || state.view === 'home') {
          $("source-modal").classList.remove("active");
          $("main-ui").style.display = "block";
          $("search-input").value = "";
          $("clear-search").style.display = "none";
          $("sport-filter").value = "all";
          isHomeModified = false;
          render();
          if (lastFocusedElement) lastFocusedElement.focus();
      } 
      else if (state.view === 'modified') {
          $("source-modal").classList.remove("active");
          $("main-ui").style.display = "block";
          isHomeModified = true;
          if (lastFocusedElement) lastFocusedElement.focus();
      }
      else if (state.view === 'modal') {
          $("main-ui").style.display = "block";
          $("source-modal").classList.add("active");
          if (lastFocusedModalBtn) lastFocusedModalBtn.focus();
      }
  });

  document.addEventListener("keydown", (e) => {
      const isTVBack = e.key === "Escape" || e.keyCode === 10009 || e.keyCode === 461;
      if (e.key === "Backspace") {
          if (document.activeElement.tagName === "INPUT" && document.activeElement.value !== "") return;
      }
      const isBack = isTVBack || e.key === "Backspace";

      if (isBack) {
          if (isTVBack && document.activeElement.tagName === "INPUT") {
              e.preventDefault();
              document.activeElement.blur(); 
              return;
          }
          if ($("clean-player-container").style.display === "block" || $("source-modal").classList.contains("active") || isHomeModified) {
              e.preventDefault();
              history.back(); 
          }
      }
  });

  window.openStream = function(url, triggerBtn = null) {
      if (!url) return;
      if (triggerBtn) lastFocusedModalBtn = triggerBtn;
      history.pushState({ view: 'player' }, "", "");
      
      const container = $("clean-player-container");
      container.innerHTML = '';
      
      const closeBtn = document.createElement('button');
      closeBtn.className = 'close-player-btn';
      closeBtn.title = 'Chiudi Player';
      closeBtn.innerHTML = '✕';
      closeBtn.onclick = (e) => { e.preventDefault(); history.back(); };
      container.appendChild(closeBtn);
      
      const iframe = document.createElement('iframe');
      iframe.id = 'clean-player-iframe';
      iframe.allowFullscreen = true;
      iframe.allow = "autoplay; fullscreen; encrypted-media";
      if (!url.toLowerCase().includes("matchora")) iframe.setAttribute("sandbox", "allow-scripts allow-same-origin allow-presentation allow-forms");
      iframe.src = url;
      container.appendChild(iframe);
      
      $("source-modal").classList.remove("active");
      $("main-ui").style.display = "none";
      container.style.display = "block";
      closeBtn.focus();
  };

  window.openModal = function(index, triggerCard) {
    const ev = apiData.events[index];
    if (!ev || !ev.links || ev.links.length === 0) return;
    
    lastFocusedElement = triggerCard;
    history.pushState({ view: 'modal' }, "", "");
    
    $("modal-title").textContent = ev.event || "Seleziona Canale";
    $("sources-list").innerHTML = "";

    if (ev.is_channels_group) {
        $("modal-search-wrapper").style.display = "flex";
        $("modal-search").value = $("search-input").value;
        $("clear-modal-search").style.display = $("search-input").value ? "block" : "none";
    } else {
        $("modal-search-wrapper").style.display = "none";
    }

    ev.links.forEach((linkObj, i) => {
      const btn = document.createElement("button");
      btn.className = "source-btn";
      btn.textContent = linkObj.name || `Link ${i + 1}`;
      btn.onclick = function() { openStream(linkObj.url, this); };
      $("sources-list").appendChild(btn);
    });
    
    $("source-modal").classList.add("active");
    
    if (ev.is_channels_group) {
        $("modal-search").focus();
        $("modal-search").dispatchEvent(new Event('input'));
    } else {
        const firstBtn = $("sources-list").querySelector("button");
        if (firstBtn) firstBtn.focus();
    }
  };

  $("close-modal").onclick = (e) => { 
      e.preventDefault(); 
      if ($("source-modal").classList.contains("active")) history.back(); 
  };
  
  $("source-modal").addEventListener("click", function(e) {
      if (e.target === this && this.classList.contains("active")) history.back();
  });

  $("search-input").addEventListener("input", function(e) {
      if (e.target.value !== "") pushModifyState();
      else if (e.target.value === "" && $("sport-filter").value === "all" && isHomeModified) { history.back(); return; }
      $("clear-search").style.display = e.target.value ? "block" : "none";
      render();
  });

  $("clear-search").addEventListener("click", function() {
      if (isHomeModified && $("sport-filter").value === "all") history.back(); 
      else {
          $("search-input").value = "";
          this.style.display = "none";
          $("search-input").focus();
          render();
          if ($("search-input").value === "" && $("sport-filter").value === "all") isHomeModified = false;
      }
  });
  
  $("sport-filter").addEventListener("change", function(e) {
      if (e.target.value !== "all") pushModifyState();
      else if (e.target.value === "all" && $("search-input").value === "" && isHomeModified) { history.back(); return; }
      render();
  });

  $("modal-search").addEventListener("input", function(e) {
      const term = e.target.value.toLowerCase();
      $("clear-modal-search").style.display = term ? "block" : "none";
      const btns = $("sources-list").querySelectorAll(".source-btn");
      btns.forEach(btn => {
          btn.style.display = btn.textContent.toLowerCase().includes(term) ? "flex" : "none";
      });
  });

  $("clear-modal-search").addEventListener("click", function() {
      $("modal-search").value = "";
      this.style.display = "none";
      $("modal-search").focus();
      $("modal-search").dispatchEvent(new Event('input'));
  });

  function render() {
    const searchTerm = $("search-input").value.toLowerCase();
    const selectedSport = $("sport-filter").value;
    let eventsHtml = "", totalDisplayed = 0;

    if (apiData.events) {
        apiData.events.forEach((ev, index) => {
          let matchSearch = false;
          if (ev.is_channels_group) {
              matchSearch = ev.event.toLowerCase().includes(searchTerm) || 
                            ev.links.some(link => (link.name || "").toLowerCase().includes(searchTerm));
          } else {
              matchSearch = (ev.event || "").toLowerCase().includes(searchTerm) || 
                            (ev.sportDisplay || "").toLowerCase().includes(searchTerm);
          }

          const matchSport = selectedSport === "all" || ev.sportId === selectedSport;
          
          if (matchSearch && matchSport) {
            const linkCount = ev.links ? ev.links.length : 0;
            if (linkCount === 0) return;
            
            let isLiveClass = "";
            let displayTime = "";
            let actionBtnText = "GUARDA ORA";

            if (ev.is_channels_group) {
                isLiveClass = "badge-247";
                displayTime = "24/7";
                actionBtnText = "MOSTRA CANALI";
            } else {
                isLiveClass = (ev.displayTime && ev.displayTime.toLowerCase().includes("live")) ? "live-active" : "";
                displayTime = ev.displayTime ? `${escapeHTML(ev.displayTime)}` : "LIVE";
            }

            let logosHtml = "";
            if (ev.home_logo || ev.away_logo) {
                logosHtml = `<div class="team-logos">`;
                if (ev.home_logo) logosHtml += `<img src="${escapeHTML(ev.home_logo)}" alt="Home" class="team-logo" loading="lazy" referrerpolicy="no-referrer">`;
                if (ev.away_logo) logosHtml += `<img src="${escapeHTML(ev.away_logo)}" alt="Away" class="team-logo" loading="lazy" referrerpolicy="no-referrer">`;
                logosHtml += `</div>`;
            }

            const isDirectLink = (linkCount === 1 && !ev.is_channels_group);
            const clickAction = isDirectLink 
                ? `lastFocusedElement=this; openStream('${escapeHTML(ev.links[0].url)}')` 
                : `openModal(${index}, this)`;
            
            eventsHtml += `
              <button class="card" onclick="${clickAction}">
                <div class="card-header">
                  <span class="sport-label">${escapeHTML(ev.sportDisplay)}</span>
                  <span class="time-badge ${isLiveClass}">${displayTime}</span>
                </div>
                <div class="card-body">
                  ${logosHtml}
                  <div class="match-title">${escapeHTML(ev.event)}</div>
                </div>
                <div class="card-footer">
                  <span class="source-count">${linkCount} ${ev.is_channels_group ? 'canali' : 'opzioni'}</span>
                  <span class="play-btn">${actionBtnText}</span>
                </div>
              </button>`;
            totalDisplayed++;
          }
        });
    }

    $("events-grid").innerHTML = eventsHtml || '<div style="color:var(--text-secondary); padding:40px; grid-column:1/-1; text-align:center; font-size:18px; background:var(--bg-surface); border-radius:12px;">Nessun risultato trovato.</div>';
    $("total-count").textContent = totalDisplayed;
  }

  try {
    const raw = JSON.parse($("api-data").textContent);
    const parsedEvents = Array.isArray(raw.data) ? raw.data : [];
    
    const channelEvents = parsedEvents.filter(e => e.league && e.league.toLowerCase().includes("canali"));
    const regularEvents = parsedEvents.filter(e => !(e.league && e.league.toLowerCase().includes("canali")));
    
    apiData.events = regularEvents.map(e => {
        return {
            event: e.title ? e.title.replace(/^[^:]+:\s*/, "") : "",
            sportId: e.league || "altro",
            sportDisplay: (e.league || "Altro").toUpperCase(),
            displayTime: e.time || "LIVE",
            links: e.sources || [],
            home_logo: e.home_logo,
            away_logo: e.away_logo
        };
    });

    if (channelEvents.length > 0) {
        let allChannelLinks = [];
        channelEvents.forEach(ch => {
            if(ch.sources) {
                ch.sources.forEach(s => {
                    allChannelLinks.push({name: s.name, url: s.url});
                });
            }
        });
        const channelsEvent = {
            sportId: "canali_tv",
            sportDisplay: "CANALI TV",
            event: "Canali TV Streaming",
            displayTime: "",
            is_channels_group: true,
            links: allChannelLinks
        };
        apiData.events.unshift(channelsEvent);
    }

    if (apiData.events) {
        let uniqueSportsIds = [...new Set(apiData.events.map(e => e.sportId))];
        const hasCanali = uniqueSportsIds.includes("canali_tv");
        uniqueSportsIds = uniqueSportsIds.filter(id => id !== "canali_tv").sort((a,b) => a.localeCompare(b));
        
        if (hasCanali) $("sport-filter").add(new Option("CANALI TV", "canali_tv"));
        uniqueSportsIds.forEach(id => $("sport-filter").add(new Option(id.toUpperCase(), id)));
    }
  } catch (e) {
    console.error("Errore nel parsing del JSON:", e);
  }

  $("search-input").addEventListener("input", render);
  $("sport-filter").addEventListener("change", render);
  $("clear-search").style.display = $("search-input").value ? "block" : "none";
  
  render();
})();
</script>
</body>
</html>'''

def adjust_time(time_str, offset):
    try:
        h, m = map(int, time_str.split(':'))
        now = datetime.now()
        dt = datetime(now.year, now.month, now.day, h, m)
        dt += timedelta(hours=offset)
        return dt.strftime("%H:%M"), dt
    except:
        return time_str, datetime.now()

def main():
    print(f"Scaricamento dati tramite proxy...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(PROXY_URL, headers=headers)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"Errore durante il download: {e}")
        return

    print("Analisi del palinsesto in corso...")
    soup = BeautifulSoup(html, 'html.parser')
    days = soup.find_all('div', class_='schedule__day')
    
    if not days:
        print("Nessun giorno trovato. Struttura del sito forse cambiata o proxy non raggiungibile.")
        return

    today = datetime.now().date()
    events_data = []
    total_streams = 0
    event_id = 1

    for day in days:
        title_el = day.find(class_='schedule__dayTitle')
        if not title_el:
            continue
            
        day_text = title_el.get_text(strip=True)
        # Parse della data per capire se è oggi (es: Friday 6th November 2026)
        match = re.search(r'(\w+)\s+(\d+)(?:st|nd|rd|th)\s+(\w+)\s+(\d{4})', day_text, re.IGNORECASE)
        is_today = False
        if match:
            day_num = int(match.group(2))
            month_str = match.group(3)[:3].lower()
            year_num = int(match.group(4))
            months_map = {'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6, 
                          'jul':7, 'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12}
            if month_str in months_map:
                try:
                    event_date = datetime(year_num, months_map[month_str], day_num).date()
                    if event_date == today:
                        is_today = True
                except:
                    pass
                    
        # Se non si riesce a parsare e siamo sul primo blocco, assumiamo sia oggi
        if not match and day == days[0]:
            is_today = True
            
        if not is_today:
            continue
            
        categories = day.find_all(class_='schedule__category')
        for cat in categories:
            cat_meta = cat.find(class_='card__meta')
            if not cat_meta: continue
            
            category_name = cat_meta.get_text(strip=True)
            if category_name in EXCLUDED_CATEGORIES:
                continue
                
            events = cat.find_all(class_='schedule__event')
            for ev in events:
                time_el = ev.find(class_='schedule__time')
                title_el = ev.find(class_='schedule__eventTitle')
                links = ev.select('.schedule__channels a')
                
                if not time_el or not title_el or not links:
                    continue
                    
                time_str = time_el.get_text(strip=True)
                title = title_el.get_text(strip=True)
                
                streams = []
                for a in links:
                    href = a.get('href', '')
                    name = a.get('title') or a.get_text(strip=True) or 'Stream'
                    
                    id_match = re.search(r'(\d+)', href)
                    if id_match:
                        final_url = f"https://gomstream.xyz/live/stream-{id_match.group(1)}.php"
                    else:
                        final_url = href
                        
                    streams.append({"name": name, "url": final_url})
                
                if not streams:
                    continue
                    
                adjusted_time, start_dt = adjust_time(time_str, OFFSET_HOURS)
                
                league = category_name
                if '24/7' in league.lower() or 'channel' in league.lower():
                    league = 'Canali on Line'

                events_data.append({
                    "id": event_id,
                    "title": title,
                    "home_team": "",
                    "away_team": "",
                    "league": league,
                    "time": adjusted_time,
                    "home_logo": "",
                    "away_logo": "",
                    "start_time": start_dt.isoformat(),
                    "status": "live",
                    "has_stream": True,
                    "sources": streams
                })
                event_id += 1
                total_streams += len(streams)

    if not events_data:
        print("Nessun evento valido estratto per oggi.")
        return

    json_payload = {"data": events_data}
    
    # Generazione file HTML
    print("Costruzione del file HTML...")
    now_str = datetime.now().strftime("%d/%m/%Y alle %H:%M")
    final_html = HTML_TEMPLATE.replace('__CURRENT_DATE__', now_str)
    final_html = final_html.replace('__JSON_DATA__', json.dumps(json_payload, indent=2))

    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
        f.write(final_html)

    print("\n✅ Operazione Completata!")
    print(f"File salvato come: {OUTPUT_FILENAME}")
    print(f"Eventi trovati: {len(events_data)}")
    print(f"Canali trovati: {total_streams}")

if __name__ == "__main__":
    main()
