/**
 * Utility functions to access settings from non-React code
 */

export function getCurrentLanguage(): string {
  return localStorage.getItem('app-language') || 'english';
}

export function getCurrentModel(): string {
  return localStorage.getItem('app-model') || 'auto';
}

export function getCurrentPermissions(): string {
  return localStorage.getItem('app-permissions') || 'public';
}

export function getCurrentTheme(): 'system' | 'light' | 'dark' {
  return (localStorage.getItem('app-theme') as 'system' | 'light' | 'dark') || 'dark';
}

/**
 * Listen to settings changes
 */
export function onLanguageChange(callback: (language: string) => void) {
  const handler = (e: Event) => callback((e as CustomEvent).detail);
  window.addEventListener('language-changed', handler);
  return () => window.removeEventListener('language-changed', handler);
}

export function onModelChange(callback: (model: string) => void) {
  const handler = (e: Event) => callback((e as CustomEvent).detail);
  window.addEventListener('model-changed', handler);
  return () => window.removeEventListener('model-changed', handler);
}

export function onPermissionsChange(callback: (permissions: string) => void) {
  const handler = (e: Event) => callback((e as CustomEvent).detail);
  window.addEventListener('permissions-changed', handler);
  return () => window.removeEventListener('permissions-changed', handler);
}

export function onUserSignOut(callback: () => void) {
  window.addEventListener('user-signed-out', callback);
  return () => window.removeEventListener('user-signed-out', callback);
}

/**
 * Get language display name
 */
export function getLanguageDisplayName(lang: string): string {
  const languages: Record<string, string> = {
    english: 'English',
    spanish: 'Español',
    french: 'Français',
    german: 'Deutsch',
  };
  return languages[lang] || lang;
}

/**
 * Get model display name
 */
export function getModelDisplayName(model: string): string {
  const models: Record<string, string> = {
    auto: 'Auto-Select',
    'minimax-m2.1': 'MiniMax M2.1',
    'gpt-4': 'GPT-4',
    'gpt-3.5': 'GPT-3.5 Turbo',
    claude: 'Claude',
  };
  return models[model] || model;
}
