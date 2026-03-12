import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "./app";
import { prepareTelegramWebApp } from "./telegram";
import "./styles.css";

prepareTelegramWebApp();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
