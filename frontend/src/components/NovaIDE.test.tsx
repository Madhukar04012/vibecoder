/**
 * NovaIDE - Basic render test
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import NovaIDE from './NovaIDE';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: () => <div data-testid="monaco-editor-mock" />,
  Editor: () => <div data-testid="monaco-editor-mock" />,
}));

describe('NovaIDE', () => {
  it('renders the IDE shell', () => {
    const { container } = render(<NovaIDE />);

    // Should have header
    const header = container.querySelector('header');
    expect(header).toBeTruthy();

    // Should have aside (chat panel)
    const aside = container.querySelector('aside');
    expect(aside).toBeTruthy();
  });

  it('renders the AI assistant header', () => {
    render(<NovaIDE />);
    expect(screen.getByText('AI Assistant')).toBeInTheDocument();
  });

  it('snapshot', () => {
    const { container } = render(<NovaIDE />);
    const header = container.querySelector('header');
    const aside = container.querySelector('aside');
    expect({
      hasHeader: !!header,
      hasAside: !!aside,
    }).toMatchSnapshot();
  });
});
