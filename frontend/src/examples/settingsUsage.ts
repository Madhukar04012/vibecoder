/**
 * Example usage of settings in components
 * 
 * This file demonstrates how to use the settings system throughout the application
 */

import { useSettings } from '@/contexts/SettingsContext';
import { getCurrentModel, onModelChange } from '@/utils/settings';

// Example 1: Using settings in a React component
export function ExampleReactComponent() {
  const { language, model, permissions, theme } = useSettings();

  // Use settings in your component logic
  console.log('Current language:', language);
  console.log('Current model:', model);
  console.log('Current permissions:', permissions);
  console.log('Current theme:', theme);

  return null;
}

// Example 2: Using settings in API calls (for AI chat)
export async function sendChatMessage(message: string) {
  const model = getCurrentModel();
  
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      model, // Use the selected model from settings
    }),
  });

  return response.json();
}

// Example 3: Listening to settings changes in non-React code
export function setupModelChangeListener() {
  const unsubscribe = onModelChange((newModel) => {
    console.log('Model changed to:', newModel);
    // Update AI client configuration, reconnect, etc.
  });

  // Call unsubscribe when cleanup is needed
  return unsubscribe;
}

// Example 4: Creating a project with default permissions
export async function createProject(name: string) {
  const { getCurrentPermissions } = await import('@/utils/settings');
  const defaultPermissions = getCurrentPermissions();

  const response = await fetch('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      permissions: defaultPermissions, // Use default from settings
    }),
  });

  return response.json();
}
