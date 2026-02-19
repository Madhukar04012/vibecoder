import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface SettingsContextType {
  language: string;
  setLanguage: (lang: string) => void;
  model: string;
  setModel: (model: string) => void;
  permissions: string;
  setPermissions: (perms: string) => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState("english");
  const [model, setModelState] = useState("auto");
  const [permissions, setPermissionsState] = useState("public");

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedLanguage = localStorage.getItem('app-language');
    const savedModel = localStorage.getItem('app-model');
    const savedPermissions = localStorage.getItem('app-permissions');

    if (savedLanguage) setLanguageState(savedLanguage);
    if (savedModel) setModelState(savedModel);
    if (savedPermissions) setPermissionsState(savedPermissions);
  }, []);

  // Apply and persist language
  const setLanguage = (lang: string) => {
    setLanguageState(lang);
    localStorage.setItem('app-language', lang);
    window.dispatchEvent(new CustomEvent('language-changed', { detail: lang }));
  };

  // Apply and persist model
  const setModel = (modelValue: string) => {
    setModelState(modelValue);
    localStorage.setItem('app-model', modelValue);
    window.dispatchEvent(new CustomEvent('model-changed', { detail: modelValue }));
  };

  // Apply and persist permissions
  const setPermissions = (perms: string) => {
    setPermissionsState(perms);
    localStorage.setItem('app-permissions', perms);
    window.dispatchEvent(new CustomEvent('permissions-changed', { detail: perms }));
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
