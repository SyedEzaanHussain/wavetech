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
})();
