// ChequeDB Dashboard — interactions
(function () {
  const shell = document.getElementById('appShell');
  const collapseBtn = document.getElementById('collapseBtn');
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const scrim = document.getElementById('sidebarScrim');
  const themeToggle = document.getElementById('themeToggle');
  const html = document.documentElement;
  const toast = document.getElementById('toast');
  const toastMsg = document.getElementById('toastMsg');

  /* ---------- Sidebar collapse (desktop) ---------- */
  const savedCollapsed = localStorage.getItem('chequedb:collapsed') === '1';
  if (savedCollapsed) shell.classList.add('sidebar-collapsed');

  collapseBtn?.addEventListener('click', () => {
    shell.classList.toggle('sidebar-collapsed');
    localStorage.setItem('chequedb:collapsed', shell.classList.contains('sidebar-collapsed') ? '1' : '0');
  });

  /* ---------- Mobile drawer ---------- */
  mobileMenuBtn?.addEventListener('click', () => shell.classList.add('mobile-open'));
  scrim?.addEventListener('click', () => shell.classList.remove('mobile-open'));

  /* ---------- Theme toggle ---------- */
  const savedTheme = localStorage.getItem('chequedb:theme');
  if (savedTheme) {
    html.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
  }

  themeToggle?.addEventListener('click', () => {
    const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('chequedb:theme', next);
    updateThemeIcon(next);
    showToast(next === 'dark' ? 'Dark mode enabled' : 'Light mode enabled');
  });

  function updateThemeIcon(theme) {
    const icon = themeToggle.querySelector('i');
    icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
  }

  /* ---------- Nav active state ---------- */
  document.querySelectorAll('.nav-item').forEach((item) => {
    item.addEventListener('click', (e) => {
      // Only prevent default if href is "#" (placeholder links)
      const href = item.getAttribute('href');
      if (href === '#') {
        e.preventDefault();
      }
      
      document.querySelectorAll('.nav-item').forEach((n) => n.classList.remove('active'));
      item.classList.add('active');
      shell.classList.remove('mobile-open');
    });
  });

  /* ---------- Filter chips (visual only, table stays illustrative) ---------- */
  document.querySelectorAll('.filter-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      const group = chip.parentElement;
      group.querySelectorAll('.filter-chip').forEach((c) => c.classList.remove('active'));
      chip.classList.add('active');
    });
  });

  /* ---------- Count-up animation for stat values ---------- */
  const counters = document.querySelectorAll('[data-count]');
  const runCounter = (el) => {
    const target = parseInt(el.getAttribute('data-count'), 10);
    const duration = 900;
    const start = performance.now();
    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  };

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          runCounter(entry.target);
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });
    counters.forEach((c) => io.observe(c));
  } else {
    counters.forEach(runCounter);
  }

  /* ---------- Help widget ---------- */
  document.getElementById('helpWidget')?.addEventListener('click', () => {
    showToast('Docs open in a new tab — shortcuts: “/” to search, “g d” for Dashboard');
  });

  /* ---------- Toast helper ---------- */
  let toastTimer;
  function showToast(message) {
    clearTimeout(toastTimer);
    toastMsg.textContent = message;
    toast.classList.add('show');
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
  }

  /* ---------- Demo: upload button feedback ---------- */
  document.querySelector('.btn-primary-brand')?.addEventListener('click', () => {
    showToast('Redirecting to upload…');
  });

  /* ---------- Supabase Realtime updates ---------- */
  const realtimeConfig = window.CHEQUE_REALTIME_CONFIG || {};
  const hasRealtimeConfig = Boolean(realtimeConfig.supabaseUrl && realtimeConfig.supabaseAnonKey);
  let realtimeTimer = null;

  function bindQueueActions() {
    document.querySelectorAll('.delete-form').forEach((form) => {
      if (form.dataset.bound === '1') return;
      form.dataset.bound = '1';
      form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(form);
        if (!formData.has('action')) {
          formData.append('action', event.submitter?.value || 'delete');
        }
        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        try {
          const response = await fetch(form.getAttribute('action') || window.location.href, {
            method: 'POST',
            headers: {
              'X-Requested-With': 'XMLHttpRequest',
              'X-CSRFToken': csrfToken,
            },
            body: formData,
          });
          if (response.ok || response.redirected) {
            showToast('Cheque deleted');
            await refreshRealtimeSnapshot();
            window.location.reload();
          } else {
            showToast('Delete failed');
          }
        } catch (error) {
          console.warn('Delete form failed', error);
          showToast('Delete failed');
        }
      });
    });
  }

  async function refreshRealtimeSnapshot() {
    if (!realtimeConfig.summaryEndpoint) return;

    try {
      const summaryResponse = await fetch(realtimeConfig.summaryEndpoint, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (summaryResponse.ok) {
        const summary = await summaryResponse.json();

        document.querySelectorAll('[data-count]').forEach((el) => {
          const key = el.getAttribute('data-count-key');
          const value = summary[key] ?? summary.total_queue;
          el.textContent = value;
          el.setAttribute('data-count', value);
        });

        const queueBadge = document.querySelector('.nav-badge');
        if (queueBadge) queueBadge.textContent = summary.total_queue;

        const donut = document.querySelector('.donut');
        if (donut) {
          donut.style.setProperty('--p1', summary.approved_percent || 0);
          donut.style.setProperty('--p2', summary.rejected_percent || 0);
          donut.style.setProperty('--p3', summary.pending_percent || 0);
        }

        const donutRows = document.querySelectorAll('.donut-legend-row b');
        if (donutRows.length >= 3) {
          donutRows[0].textContent = summary.total_approved;
          donutRows[1].textContent = summary.total_rejected;
          donutRows[2].textContent = summary.pending_count;
        }
      }
    } catch (error) {
      console.warn('Realtime summary refresh failed', error);
    }

    if (realtimeConfig.page === 'queue' && realtimeConfig.queueEndpoint) {
      try {
        const currentParams = new URLSearchParams(window.location.search);
        const queueParams = new URLSearchParams();
        queueParams.set('status', currentParams.get('status') || 'all');
        const currentSearch = currentParams.get('q') || document.querySelector('.search-box input[name="q"]')?.value || '';
        if (currentSearch) queueParams.set('q', currentSearch);

        const response = await fetch(`${realtimeConfig.queueEndpoint}?${queueParams.toString()}`, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!response.ok) return;

        const payload = await response.json();
        const rows = document.getElementById('queueRows');
        if (rows) {
          if (payload.cheques?.length) {
            const existingIds = Array.from(rows.querySelectorAll('tr[data-cheque-id]')).map((row) => row.getAttribute('data-cheque-id'));
            const incomingIds = payload.cheques?.map((cheque) => cheque.id) || [];
            const shouldHighlightNew = incomingIds.some((id) => !existingIds.includes(id));

            rows.innerHTML = payload.cheques.map((cheque, index) => {
              const isNewRecord = shouldHighlightNew && !existingIds.includes(cheque.id);
              const newClass = isNewRecord ? 'realtime-row new-record' : 'realtime-row';
              const animationDelay = isNewRecord ? `style="animation-delay:${Math.min(index * 0.06, 0.3)}s"` : '';

              return `
                <tr class="${newClass}" data-cheque-id="${cheque.id}" ${animationDelay}>
                  <td class="system-id-cell">${cheque.system_id}</td>
                  <td class="amount-cell">${cheque.amount || '–'}</td>
                  <td class="date-cell">${cheque.date}</td>
                  <td class="beneficiary-cell">${cheque.beneficiary}</td>
                  <td class="action-cell">
                    <a href="/dashboard/cheque/${cheque.id}/" class="action-icon view-icon view-link" title="View details">
                      <i class="bi bi-eye-fill"></i>
                    </a>
                    <form method="post" action="/dashboard/queue/" class="delete-form" style="display:inline;">
                      <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''}" />
                      <input type="hidden" name="cheque_id" value="${cheque.id}" />
                      <input type="hidden" name="action" value="delete" />
                      <button type="submit" class="action-icon delete-icon" title="Delete">
                        <i class="bi bi-trash-fill"></i>
                      </button>
                    </form>
                  </td>
                </tr>`;
            }).join('');
          } else {
            rows.innerHTML = `
              <tr>
                <td colspan="5" style="text-align: center; padding: 2rem; color: var(--ink-faint);">
                  <i class="bi bi-inbox" style="font-size: 2rem; display: block; margin-bottom: .5rem;"></i>
                  No cheques found
                </td>
              </tr>`;
          }
          bindQueueActions();
        }
      } catch (error) {
        console.warn('Realtime queue refresh failed', error);
      }
    }
  }

  function subscribeToSupabase() {
    if (!hasRealtimeConfig || !window.supabase?.createClient) return null;

    const supabase = window.supabase.createClient(realtimeConfig.supabaseUrl, realtimeConfig.supabaseAnonKey);
    const channel = supabase.channel('public-cheques-realtime');
    const handleEvent = () => {
      showToast('Realtime update received');
      refreshRealtimeSnapshot();
    };

    ['cheques', 'processing_queue', 'status_history'].forEach((tableName) => {
      channel.on('postgres_changes', { event: '*', schema: 'public', table: tableName }, handleEvent);
    });

    channel.subscribe((status) => {
      if (status === 'SUBSCRIBED') {
        showToast('Realtime connection active');
      }
    });

    return channel;
  }

  if (hasRealtimeConfig) {
    refreshRealtimeSnapshot();
    if (!subscribeToSupabase()) {
      realtimeTimer = window.setInterval(refreshRealtimeSnapshot, 5000);
    }
  } else {
    refreshRealtimeSnapshot();
    realtimeTimer = window.setInterval(refreshRealtimeSnapshot, 5000);
  }
})();
