import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Theme = 'system' | 'light' | 'dark';

interface SettingsContextType {
  language: string;
  setLanguage: (lang: string) => void;
  model: string;
  setModel: (model: string) => void;
  permissions: string;
  setPermissions: (perms: string) => void;
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState("english");
  const [model, setModelState] = useState("auto");
  const [permissions, setPermissionsState] = useState("public");
  const [theme, setThemeState] = useState<Theme>('dark');

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedLanguage = localStorage.getItem('app-language');
    const savedModel = localStorage.getItem('app-model');
    const savedPermissions = localStorage.getItem('app-permissions');
    const savedTheme = localStorage.getItem('app-theme');
    
    if (savedLanguage) setLanguageState(savedLanguage);
    if (savedModel) setModelState(savedModel);
    if (savedPermissions) setPermissionsState(savedPermissions);
    if (savedTheme) setThemeState(savedTheme as Theme);
  }, []);

  // Apply and persist language
  const setLanguage = (lang: string) => {
    setLanguageState(lang);
    localStorage.setItem('app-language', lang);
    // Dispatch event for other components to react to language change
    window.dispatchEvent(new CustomEvent('language-changed', { detail: lang }));
  };

  // Apply and persist model
  const setModel = (modelValue: string) => {
    setModelState(modelValue);
    localStorage.setItem('app-model', modelValue);
    // Dispatch event for AI components to update
    window.dispatchEvent(new CustomEvent('model-changed', { detail: modelValue }));
  };

  // Apply and persist permissions
  const setPermissions = (perms: string) => {
    setPermissionsState(perms);
    localStorage.setItem('app-permissions', perms);
    // Dispatch event for project components
    window.dispatchEvent(new CustomEvent('permissions-changed', { detail: perms }));
  };

  // Apply and persist theme
  const setTheme = (themeValue: Theme) => {
    setThemeState(themeValue);
    localStorage.setItem('app-theme', themeValue);
    applyTheme(themeValue);
  };

  // Apply theme to document
  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const applyTheme = (themeValue: Theme) => {
    const root = document.documentElement;
    
    if (themeValue === 'light') {
      root.classList.remove('dark');
      root.classList.add('light');
      root.style.setProperty('--background', '255 255 255');
      root.style.setProperty('--foreground', '0 0 0');
    } else if (themeValue === 'dark') {
      root.classList.remove('light');
      root.classList.add('dark');
      root.style.setProperty('--background', '10 10 10');
      root.style.setProperty('--foreground', '255 255 255');
    } else {
      // System theme
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.remove('light', 'dark');
      root.classList.add(prefersDark ? 'dark' : 'light');
      
      if (prefersDark) {
        root.style.setProperty('--background', '10 10 10');
        root.style.setProperty('--foreground', '255 255 255');
      } else {
        root.style.setProperty('--background', '255 255 255');
        root.style.setProperty('--foreground', '0 0 0');
      }
    }
  };

  return (
    <SettingsContext.Provider
      value={{
        language,
        setLanguage,
        model,
        setModel,
        permissions,
        setPermissions,
        theme,
        setTheme,
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}
