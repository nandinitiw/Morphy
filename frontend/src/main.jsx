import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App.jsx";
import { IngestProvider } from "./context/IngestContext.jsx";
import { UsernameProvider } from "./context/UsernameContext.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <UsernameProvider>
      <IngestProvider>
        <App />
      </IngestProvider>
    </UsernameProvider>
  </StrictMode>,
);
