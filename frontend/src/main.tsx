import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { router } from "./router";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { SettingsProvider } from "./contexts/SettingsContext";
import "./index.css";

// Log unhandled promise rejections so they are visible (no silent failures)
window.addEventListener("unhandledrejection", (event) => {
  console.error("[Unhandled rejection]", event.reason);
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <SettingsProvider>
        <RouterProvider router={router} />
      </SettingsProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
