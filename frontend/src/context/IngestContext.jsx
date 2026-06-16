import { createContext, useCallback, useContext, useState } from "react";

import { fetchIngestStatus, triggerIngest } from "../api/client.js";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function pollJob(jobId, onUpdate) {
  while (true) {
    const job = await fetchIngestStatus(jobId);
    onUpdate(job);
    if (job.status === "completed" || job.status === "failed") {
      return job;
    }
    await sleep(2000);
  }
}

const IngestContext = createContext(null);

export function IngestProvider({ children }) {
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");
  const [isRunning, setIsRunning] = useState(false);

  const startIngest = useCallback(async (username) => {
    setError("");
    setIsRunning(true);
    try {
      const created = await triggerIngest(username);
      setJob(created);
      const finalJob = await pollJob(created.job_id, setJob);
      if (finalJob.status === "failed") {
        setError(finalJob.error ?? "Analysis failed");
      }
      return finalJob;
    } catch (err) {
      setError(err.message ?? "Could not reach the backend");
      throw err;
    } finally {
      setIsRunning(false);
    }
  }, []);

  const clearJob = useCallback(() => {
    setJob(null);
    setError("");
  }, []);

  const value = { job, error, isRunning, startIngest, clearJob };

  return <IngestContext.Provider value={value}>{children}</IngestContext.Provider>;
}

export function useIngest() {
  const ctx = useContext(IngestContext);
  if (!ctx) throw new Error("useIngest must be used within IngestProvider");
  return ctx;
}
