/* ============================================================
   InsiderEdgePro — Front-End Upgrade Layer (JS)
   Non-invasive enhancers: row entrance animation, ticker chips,
   skeleton loaders, live pulse dots, homepage marquee.
   Exposes window.IEP for page-level hooks.
   ============================================================ */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1 + 2. Tbody observer: row entrance + live trade flash ---------- */
  var lastInteraction = 0;
  ['pointerdown', 'keydown', 'touchstart'].forEach(function (ev) {
    document.addEventListener(ev, function () { lastInteraction = Date.now(); }, { passive: true, capture: true });
  });

  function rowKey(row) {
    var cells = row.querySelectorAll('td');
    var parts = [];
    for (var i = 0; i < Math.min(cells.length, 3); i++) parts.push(cells[i].textContent.trim());
    return parts.join('|');
  }
  function isSkelRow(row) {
    return row.querySelector('.iep-skel, .skeleton-cell, .skeleton, .skeleton-row') !== null;
  }
  function flashRow(row) {
    if (reduced) return;
    var cls = row.className || '';
    var kind = /row-buy|buy/i.test(cls) ? 'buy' : /row-sell|sell/i.test(cls) ? 'sell' : null;
    if (!kind) {
      var txt = row.textContent;
      kind = /\bBUY\b/i.test(txt) ? 'buy' : /\bSELL\b/i.test(txt) ? 'sell' : null;
    }
    if (!kind) return;
    var flashCls = kind === 'buy' ? 'iep-flash-buy' : 'iep-flash-sell';
    row.classList.add(flashCls);
    row.addEventListener('animationend', function h() {
      row.classList.remove(flashCls);
      row.removeEventListener('animationend', h);
    });
  }

  function enhanceTbody(tbody) {
    var allRows = tbody.querySelectorAll('tr');
    var rows = [];
    for (var i = 0; i < allRows.length; i++) {
      if (!isSkelRow(allRows[i])) rows.push(allRows[i]);
    }

    // entrance animation (first 24 rows)
    var n = Math.min(rows.length, 24);
    for (var j = 0; j < n; j++) {
      var r = rows[j];
      if (!r.classList.contains('iep-row-in') && !reduced) {
        r.classList.add('iep-row-in');
        r.style.animationDelay = (Math.min(j, 20) * 0.03) + 's';
      }
    }

    // live trade flash: only for auto-refresh renders, never user-driven ones
    if (!rows.length) { tbody.__iepPrevHead = null; return; }
    var headKey = rowKey(rows[0]);
    var canFlash = tbody.__iepPrevHead &&
      tbody.__iepPrevHead !== headKey &&
      (Date.now() - lastInteraction > 2500) &&
      document.visibilityState === 'visible';
    if (canFlash) {
      var seen = tbody.__iepSeen || {};
      var flashed = 0;
      for (var k = 0; k < Math.min(rows.length, 10) && flashed < 6; k++) {
        var key = rowKey(rows[k]);
        if (key === tbody.__iepPrevHead) break;      // reached old head: rows above are new
        if (!seen[key]) { flashRow(rows[k]); flashed++; }
      }
    }
    // refresh seen-set (recreate to stay bounded)
    var ns = {};
    for (var m = 0; m < Math.min(rows.length, 300); m++) ns[rowKey(rows[m])] = 1;
    tbody.__iepSeen = ns;
    tbody.__iepPrevHead = headKey;
  }

  function wireTbodys() {
    var tbodys = document.querySelectorAll('tbody');
    tbodys.forEach(function (tb) {
      if (tb.__iepWired) return;
      tb.__iepWired = true;

      // 3. Skeleton placeholders while empty
      if (!tb.children.length && !reduced) {
        var cols = (tb.closest('table') || { querySelectorAll: function () { return []; } })
          .querySelectorAll('thead th').length || 6;
        var html = '';
        for (var r = 0; r < 8; r++) {
          html += '<tr class="iep-skel-row">';
          for (var c = 0; c < cols; c++) {
            var w = 40 + ((r * 37 + c * 53) % 50);
            html += '<td><span class="iep-skel" style="width:' + w + '%"></span></td>';
          }
          html += '</tr>';
        }
        tb.innerHTML = html;
      }

      var obs = new MutationObserver(function () { enhanceTbody(tb); });
      obs.observe(tb, { childList: true });
      if (tb.children.length) enhanceTbody(tb);
    });
  }

  /* ---------- 4. Live pulse dots ---------- */
  function wireLiveDots() {
    var sels = ['#last-updated', '#refresh-label', '.last-updated'];
    sels.forEach(function (sel) {
      document.querySelectorAll(sel).forEach(function (el) {
        if (el.querySelector('.iep-live-dot')) return;
        var dot = document.createElement('span');
        dot.className = 'iep-live-dot';
        el.insertBefore(dot, el.firstChild);
      });
    });
  }

  /* ---------- 5. Homepage marquee ---------- */
  function fmtVal(v) {
    var n = parseFloat(String(v == null ? '' : v).replace(/[^0-9.-]/g, ''));
    if (isNaN(n) || !n) return '';
    if (n >= 1e9) return '$' + (n / 1e9).toFixed(1) + 'B';
    if (n >= 1e6) return '$' + (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return '$' + (n / 1e3).toFixed(0) + 'K';
    return '$' + n.toFixed(0);
  }
  function fillMarquee(trades) {
    var wrap = document.getElementById('iep-marquee');
    if (!wrap || !trades || !trades.length) return;
    var items = trades.filter(function (t) { return t.ticker; }).slice(0, 24);
    if (!items.length) return;
    var html = items.map(function (t) {
      var val = fmtVal(t.value);
      return '<span class="iep-mq-item"><span class="mq-t">' + esc(t.ticker) + '</span>' +
        (t.cluster_buy ? '<span class="mq-c">&#9889; CLUSTER</span>' : '') +
        (val ? '<span class="mq-v">' + esc(val) + '</span>' : '') + '</span>';
    }).join('');
    wrap.innerHTML = html + html; // duplicate for seamless loop
    wrap.parentElement.style.display = '';
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* ---------- 6. Ambient mesh background ---------- */
  function wireAmbient() {
    if (reduced || document.getElementById('iep-ambient')) return;
    var a = document.createElement('div');
    a.id = 'iep-ambient';
    a.setAttribute('aria-hidden', 'true');
    document.body.appendChild(a);
  }

  /* ---------- 7. Cursor glow (desktop only) ---------- */
  function wireCursorGlow() {
    if (reduced || document.getElementById('iep-cursor')) return;
    if (!window.matchMedia('(pointer: fine)').matches) return;
    if (window.innerWidth < 900) return;
    var c = document.createElement('div');
    c.id = 'iep-cursor';
    c.setAttribute('aria-hidden', 'true');
    document.body.appendChild(c);
    var tx = window.innerWidth / 2, ty = window.innerHeight / 3;
    var x = tx, y = ty, shown = false;
    document.addEventListener('mousemove', function (e) {
      tx = e.clientX; ty = e.clientY;
      if (!shown) { shown = true; c.style.opacity = '1'; }
    }, { passive: true });
    (function loop() {
      x += (tx - x) * 0.12;
      y += (ty - y) * 0.12;
      c.style.transform = 'translate3d(' + x + 'px,' + y + 'px,0)';
      requestAnimationFrame(loop);
    })();
  }

  window.IEP = window.IEP || {};
  window.IEP.fillMarquee = fillMarquee;

  /* ---------- Boot ---------- */
  function boot() {
    wireTbodys();
    wireLiveDots();
    wireAmbient();
    wireCursorGlow();
    // late-added tables
    new MutationObserver(function () { wireTbodys(); wireLiveDots(); })
      .observe(document.body, { childList: true, subtree: true });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
