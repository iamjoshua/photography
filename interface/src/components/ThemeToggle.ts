const STORAGE_KEY = 'theme';

export type Theme = 'light' | 'dark';

export function getTheme(): Theme {
  return (document.documentElement.dataset.theme as Theme) ?? 'light';
}

export function setTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem(STORAGE_KEY, theme);
}

export function initThemeToggle(): void {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  btn.addEventListener('click', () => {
    setTheme(getTheme() === 'dark' ? 'light' : 'dark');
  });
}
