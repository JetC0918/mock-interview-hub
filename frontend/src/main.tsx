import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

import { OpenAPI } from "./lib/api-client/core/OpenAPI";

// Configure API Client
// Use relative /api path - works with both Vite dev proxy and in production (if served from same origin)
OpenAPI.BASE = "/api";
OpenAPI.WITH_CREDENTIALS = true;

createRoot(document.getElementById("root")!).render(<App />);
