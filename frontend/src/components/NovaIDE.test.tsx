/**
 * Atoms IDE — snapshot test for empty editor state
 * Prevents accidental UI drift. Update snapshot only when layout intentionally changes.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import NovaIDE from './NovaIDE';

// Monaco Editor loads async; mock to avoid flakiness
vi.mock('@monaco-editor/react', () => ({
  Editor: () => <div data-testid="monaco-editor-mock" />,
}));

describe('NovaIDE', () => {
  it('renders empty editor state with locked layout invariants', () => {
    render(<NovaIDE />);

    // Top bar: project name (New Project when no project), Editor, App view
    expect(screen.getByText('New Project')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Editor' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'App view' })).toBeInTheDocument();

    // Sidebar input
    expect(screen.getByPlaceholderText('Ask the team to bring your idea to life')).toBeInTheDocument();

    // Empty state hint (only text allowed when no file selected)
    expect(screen.getByText('Select a file')).toBeInTheDocument();
  });

  it('uses Atoms layout CSS variables (prevents hardcoding)', () => {
    const { container } = render(<NovaIDE />);

    const header = container.querySelector('header');
    expect(header?.getAttribute('style')).toContain('var(--atoms-charcoal)');

    const root = container.querySelector('[style*="atoms-deep-black"]');
    expect(root).toBeTruthy();
  });

  it('empty editor state snapshot (structure lock)', () => {
    const { container } = render(<NovaIDE />);
    const shell = container.querySelector('[style*="atoms-deep-black"]');
    expect(shell).toBeTruthy();
    // Snapshot: header + sidebar + editor area structure
    const header = container.querySelector('header');
    const aside = container.querySelector('aside');
    expect({
      hasHeader: !!header,
      hasAside: !!aside,
      headerText: header?.textContent?.trim().slice(0, 40),
      emptyHint: container.textContent?.includes('Select a file'),
    }).toMatchSnapshot();
  });
});
