(() => {
  const storageKey = 'demonstration.theme';
  const modes = ['system', 'light', 'dark'];
  let preference = 'system';
  try {
    const saved = localStorage.getItem(storageKey);
    if (modes.includes(saved)) preference = saved;
  } catch {}

  const applyTheme = () => {
    if (preference === 'system') delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = preference;
    for (const button of document.querySelectorAll('[data-theme-choice]')) {
      button.setAttribute('aria-pressed', String(button.dataset.themeChoice === preference));
    }
  };
  applyTheme();

  document.addEventListener('DOMContentLoaded', () => {
    applyTheme();
    for (const button of document.querySelectorAll('[data-theme-choice]')) {
      button.addEventListener('click', () => {
        preference = button.dataset.themeChoice;
        applyTheme();
        try {
          if (preference === 'system') localStorage.removeItem(storageKey);
          else localStorage.setItem(storageKey, preference);
        } catch {}
      });
    }
  });
})();
