import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { router } from "./router";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { SettingsProvider } from "./contexts/SettingsContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <SettingsProvider>
        <RouterProvider router={router} />
      </SettingsProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
