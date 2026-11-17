/* ============================================================
   InsiderEdgePro — Front-End Upgrade Layer (JS)
   Non-invasive enhancers: row entrance animation, ticker chips,
   skeleton loaders, live pulse dots, homepage marquee.
   Exposes window.IEP for page-level hooks.
   ============================================================ */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Ticker chip color (deterministic) ---------- */
  function chipColor(sym) {
    var h = 0;
    for (var i = 0; i < sym.length; i++) h = (h * 31 + sym.charCodeAt(i)) >>> 0;
    var hue = h % 360;
    return { bg: 'hsla(' + hue + ', 60%, 60%, 0.16)', fg: 'hsl(' + hue + ', 75%, 68%)' };
  }

  /* ---------- 1 + 2. Tbody observer: row entrance + ticker chips ---------- */
  function enhanceTbody(tbody) {
    var rows = tbody.querySelectorAll('tr');
    var n = Math.min(rows.length, 24);
    for (var i = 0; i < n; i++) {
      var r = rows[i];
      if (!r.classList.contains('iep-row-in') && !reduced) {
        r.classList.add('iep-row-in');
        r.style.animationDelay = (Math.min(i, 20) * 0.03) + 's';
      }
    }
    // Ticker chips
    var cells = tbody.querySelectorAll('td.td-ticker:not([data-chipped])');
    for (var j = 0; j < cells.length; j++) {
      var td = cells[j];
      td.setAttribute('data-chipped', '1');
      var m = td.textContent.trim().match(/[A-Z][A-Z0-9.\-]{0,9}/);
      if (!m) continue;
      var chip = document.createElement('span');
      chip.className = 'iep-chip';
      chip.textContent = m[0].slice(0, 2);
      var col = chipColor(m[0]);
      chip.style.background = col.bg;
      chip.style.color = col.fg;
      td.insertBefore(chip, td.firstChild);
    }
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
  function fillMarquee(trades) {
    var wrap = document.getElementById('iep-marquee');
    if (!wrap || !trades || !trades.length) return;
    var items = trades.filter(function (t) { return t.ticker; }).slice(0, 24);
    if (!items.length) return;
    var html = items.map(function (t) {
      var val = t.value ? String(t.value) : '';
      return '<span class="iep-mq-item"><span class="mq-t">' + esc(t.ticker) + '</span>' +
        (t.cluster_buy ? '<span class="mq-c">&#9889; CLUSTER</span>' : '') +
        '<span class="mq-v">' + esc(val) + '</span></span>';
    }).join('');
    wrap.innerHTML = html + html; // duplicate for seamless loop
    wrap.parentElement.style.display = '';
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  window.IEP = window.IEP || {};
  window.IEP.fillMarquee = fillMarquee;

  /* ---------- Boot ---------- */
  function boot() {
    wireTbodys();
    wireLiveDots();
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
