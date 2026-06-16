// All backend API calls live here.
//
// Local dev: leave VITE_API_URL empty — Vite proxies to localhost:8000 (see vite.config.js)
// Production (Vercel): set VITE_API_URL to your hosted backend, e.g. https://morphy-api.onrender.com

const BASE = import.meta.env.VITE_API_URL ?? "";

export function getApiBase() {
  return BASE || window.location.origin;
}

const THEME_LABELS = {
  missed_fork: "Missed fork",
  missed_pin: "Missed pin",
  missed_skewer: "Missed skewer",
  missed_mate: "Missed mate",
  missed_check: "Missed check",
  missed_discovered_check: "Missed discovered check",
  missed_double_check: "Missed double check",
  missed_hanging_piece: "Missed hanging piece",
  missed_back_rank: "Back rank",
  king_safety: "King safety",
  time_pressure: "Time pressure",
  positional: "Positional",
};

export function themeLabel(theme) {
  return THEME_LABELS[theme] ?? theme.replace(/_/g, " ");
}

function apiUrl(path) {
  return `${BASE}${path}`;
}

async function request(path, options = {}) {
  const url = apiUrl(path);
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      throw new Error(`API error ${res.status} for ${path}`);
    }
    return res.json();
  } catch (err) {
    if (err instanceof TypeError || err.message === "Failed to fetch") {
      throw new Error(
        BASE
          ? `Cannot reach backend at ${BASE}. Check that the server is running and CORS allows this site.`
          : `Cannot reach backend at ${window.location.origin}${path}. Start the API with: cd backend && uvicorn main:app --reload --port 8000`,
      );
    }
    throw err;
  }
}

async function get(path) {
  return request(path);
}

async function post(path, body) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function checkBackendHealth() {
  return get("/health");
}

export function fetchProfile(username) {
  return get(`/profile/${username}`);
}

export async function fetchWeaknessProfile(username) {
  const data = await fetchProfile(username);
  return {
    weaknesses: (data.profile ?? []).map((row) => ({
      theme: row.theme,
      display: themeLabel(row.theme),
      frequency: row.frequency,
      severity: Math.round(row.severity),
      last_seen: row.last_seen,
    })),
    stats: data.stats ?? {},
  };
}

export const fetchTimePressure = (username) => get(`/profile/${username}/time-pressure`);

export const fetchOpeningStats = (username) => get(`/openings/${username}`);

export const fetchStyleGap = (username, gmUsername = "paulmorphy") =>
  get(`/style-gap/${username}?gm=${gmUsername}`);

export const sendCoachMessage = (username, message) =>
  post(`/coach`, { username, message });

export const triggerIngest = (username) => post(`/ingest/${username}`, {});

export const fetchIngestStatus = (jobId) => get(`/jobs/${jobId}`);
