(function () {
  const cfg = window.LPDISPLAY;
  const state = {
    manifest: null,
    timers: {},
    indexes: {},
    frozen: false,
    freezeTimer: null
  };

  function status(msg) {
    const el = document.getElementById('lpdisplay-status');
    if (el) el.textContent = msg;
  }

  async function postJson(url, data) {
    try {
      await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data || {})
      });
    } catch (e) {
      console.warn('POST failed', url, e);
    }
  }

  async function loadManifest() {
    const res = await fetch(cfg.manifestUrl, {cache: 'no-store'});
    if (!res.ok) throw new Error('manifest failed');
    state.manifest = await res.json();
    applyLayout(state.manifest);
    startAllZones();
    status('manifest ' + new Date().toLocaleTimeString());
  }

  function applyLayout(manifest) {
    const root = document.getElementById('lpdisplay-root');
    if (!manifest.layout) return;
    root.classList.remove('left', 'right');
    root.classList.add(manifest.layout.column_position || 'right');
  }

  function zoneElement(zoneName) {
    return document.getElementById('zone-' + zoneName);
  }

  function renderItem(zoneName, item) {
    const zone = zoneElement(zoneName);
    if (!zone) return;
    zone.innerHTML = '';
    if (!item) {
      const empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = zoneName;
      zone.appendChild(empty);
      return;
    }
    if (item.type === 'image') {
      const img = document.createElement('img');
      img.src = item.url;
      img.alt = item.name || '';
      zone.appendChild(img);
    } else if (item.type === 'web') {
      const iframe = document.createElement('iframe');
      iframe.src = item.url;
      iframe.referrerPolicy = 'no-referrer-when-downgrade';
      zone.appendChild(iframe);
    } else {
      const empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = 'Type non supporté : ' + item.type;
      zone.appendChild(empty);
    }
  }

  function startZone(zoneName) {
    clearTimeout(state.timers[zoneName]);
    const items = (state.manifest && state.manifest.zones && state.manifest.zones[zoneName]) || [];
    if (!items.length) {
      renderItem(zoneName, null);
      return;
    }
    if (state.indexes[zoneName] === undefined) state.indexes[zoneName] = 0;
    const item = items[state.indexes[zoneName] % items.length];
    renderItem(zoneName, item);
    state.indexes[zoneName] = (state.indexes[zoneName] + 1) % items.length;
    if (!state.frozen) {
      state.timers[zoneName] = setTimeout(() => startZone(zoneName), Math.max(1, item.duration || 15) * 1000);
    }
  }

  function startAllZones() {
    ['main', 'thumb1', 'thumb2', 'thumb3'].forEach(startZone);
  }

  function stopAllZones() {
    Object.keys(state.timers).forEach(k => clearTimeout(state.timers[k]));
    state.timers = {};
  }

  function freeze(duration) {
    state.frozen = true;
    stopAllZones();
    clearTimeout(state.freezeTimer);
    if (duration && duration > 0) {
      state.freezeTimer = setTimeout(resume, duration * 1000);
    }
    status('freeze ' + duration + 's');
  }

  function resume() {
    state.frozen = false;
    clearTimeout(state.freezeTimer);
    startAllZones();
    status('resume');
  }

  async function pollCommands() {
    try {
      const res = await fetch(cfg.commandsUrl, {cache: 'no-store'});
      const data = await res.json();
      for (const cmd of data.commands || []) {
        let ok = true;
        let result = 'ok';
        try {
          if (cmd.action === 'freeze') freeze((cmd.payload && cmd.payload.duration) || 60);
          else if (cmd.action === 'resume') resume();
          else if (cmd.action === 'reload') location.reload();
          else result = 'unknown action';
        } catch (e) {
          ok = false;
          result = String(e);
        }
        await postJson(cfg.commandResultBase + cmd.id + '/result/', {ok, result});
      }
    } catch (e) {
      console.warn('commands failed', e);
    }
  }

  function heartbeat() {
    postJson(cfg.heartbeatUrl, {agent_version: 'kiosk-js-v0.1'});
  }

  loadManifest().catch(e => status('manifest error: ' + e));
  setInterval(heartbeat, 30000);
  setInterval(pollCommands, 3000);
  setInterval(() => {
    if (!state.frozen) loadManifest().catch(e => console.warn(e));
  }, 60000);
  heartbeat();
  pollCommands();
})();
