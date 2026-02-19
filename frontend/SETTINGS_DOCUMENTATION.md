# Settings System Documentation

## Overview

The application includes a comprehensive settings system that allows users to customize their experience. All settings are persisted to localStorage and synchronized across the application in real-time.

## Available Settings

### 1. Language
- **Purpose**: Sets the UI language for the application
- **Options**: English, Spanish, French, German
- **Default**: English
- **Storage Key**: `app-language`

### 2. AI Model
- **Purpose**: Selects the default AI model for code generation and chat responses
- **Options**: Auto, GPT-4, GPT-3.5, Claude
- **Default**: Auto
- **Storage Key**: `app-model`
- **Usage**: Components making AI requests should use this to determine which model to call

### 3. Permissions
- **Purpose**: Sets default visibility for newly created projects
- **Options**: Public (anyone can view), Private (only you can view)
- **Default**: Public
- **Storage Key**: `app-permissions`
- **Usage**: When creating a new project, use this as the default permission level

### 4. Theme
- **Purpose**: Controls the visual appearance of the application
- **Options**: System (follows OS preference), Light, Dark
- **Default**: Dark
- **Storage Key**: `app-theme`
- **Implementation**: Automatically applies CSS classes and CSS variables to document root

## Usage in Components

### React Components

Use the `useSettings` hook in any functional component:

```tsx
import { useSettings } from '@/contexts/SettingsContext';

function MyComponent() {
  const { language, model, permissions, theme, setLanguage, setModel } = useSettings();

  // Read settings
  console.log('Current language:', language);

  // Update settings
  const changeLanguage = () => {
    setLanguage('spanish');
  };

  return <div>Current model: {model}</div>;
}
```

### Non-React Code

Use the utility functions for accessing settings outside React components:

```ts
import { getCurrentModel, getCurrentLanguage, onModelChange } from '@/utils/settings';

// Get current values
const model = getCurrentModel();
const language = getCurrentLanguage();

// Listen to changes
const unsubscribe = onModelChange((newModel) => {
  console.log('Model changed to:', newModel);
  // Update your configuration
});

// Cleanup when done
unsubscribe();
```

## Implementation Details

### Settings Context

The settings are managed by a React Context (`SettingsContext`) that wraps the entire application. This ensures:

1. **Single source of truth**: All components access the same settings
2. **Automatic persistence**: Changes are immediately saved to localStorage
3. **Real-time synchronization**: All components update when settings change
4. **Event system**: Non-React code can listen to settings changes

### Event System

The settings system dispatches custom events when values change:

- `language-changed`: Fired when language changes
- `model-changed`: Fired when AI model changes
- `permissions-changed`: Fired when default permissions change
- `user-signed-out`: Fired when user signs out (clears all settings)

### Theme Application

The theme setting automatically:

1. Adds/removes CSS classes (`light` or `dark`) to `document.documentElement`
2. Sets CSS custom properties (`--background`, `--foreground`)
3. Respects system preferences when "System" is selected
4. Persists user's choice across sessions

## Sign Out Functionality

The sign out button in the Profile settings:

1. Clears all saved settings from localStorage
2. Resets settings to defaults
3. Dispatches the `user-signed-out` event
4. Can be extended to clear authentication tokens, redirect users, etc.

## Integration Examples

### AI Chat Component

```tsx
import { useSettings } from '@/contexts/SettingsContext';

function ChatComponent() {
  const { model } = useSettings();

  const sendMessage = async (message: string) => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message, model }), // Use selected model
    });
    return response.json();
  };

  return <div>Using model: {model}</div>;
}
```

### Project Creation

```tsx
import { useSettings } from '@/contexts/SettingsContext';

function CreateProjectButton() {
  const { permissions } = useSettings();

  const createProject = async (name: string) => {
    const response = await fetch('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ 
        name, 
        permissions // Use default from settings
      }),
    });
    return response.json();
  };

  return <button onClick={() => createProject('My Project')}>Create</button>;
}
```

## Future Enhancements

Potential improvements to consider:

1. **i18n Integration**: Connect language setting to a proper internationalization library
2. **Model Validation**: Verify selected model is available before making requests
3. **User Profiles**: Store settings on server for multi-device sync
4. **Advanced Settings**: Add more granular controls (font size, code theme, etc.)
5. **Settings Import/Export**: Allow users to backup and restore their settings
