import '@testing-library/jest-dom';

// jsdom lacks ResizeObserver — required by react-resizable-panels
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

// jsdom lacks scrollIntoView or it's not callable — polyfill for tests
Element.prototype.scrollIntoView = () => {};
