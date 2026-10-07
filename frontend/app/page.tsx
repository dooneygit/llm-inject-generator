"use client";

import { useEffect, useState } from "react";

type Inject = { minute: number; description: string };

type ScenarioRecord = {
  id: number;
  description: string;
  created_at: string;
  scenario: {
    title: string;
    difficulty: "low" | "medium" | "high";
    objectives: string[];
    injects: Inject[];
  };
};

const DIFFICULTY_STYLES = {
  low: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  medium: "bg-amber-50 text-amber-700 ring-amber-600/20",
  high: "bg-rose-50 text-rose-700 ring-rose-600/20",
};

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    // LLMError returns a string; FastAPI request validation returns a list of {msg}.
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail) && body.detail[0]?.msg) return body.detail[0].msg;
  } catch {}
  return `Request failed (${res.status})`;
}

async function fetchScenarios(): Promise<ScenarioRecord[]> {
  const res = await fetch("/api/scenarios");
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.json();
}

export default function Home() {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioRecord[]>([]);

  useEffect(() => {
    fetchScenarios()
      .then(setScenarios)
      .catch((e: Error) => setError(e.message));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/scenarios", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description }),
      });
      if (!res.ok) throw new Error(await errorMessage(res));
      setDescription("");
      setScenarios(await fetchScenarios());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-12 sm:py-16">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Scenario Generator</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Describe an exercise and get a structured training scenario.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-3">
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g. A wildfire threatening a rural town"
          rows={4}
          maxLength={2000}
          disabled={loading}
          className="block w-full resize-y rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm shadow-sm placeholder:text-neutral-400 focus:border-neutral-900 focus:outline-none focus:ring-1 focus:ring-neutral-900 disabled:bg-neutral-50 disabled:text-neutral-500"
        />
        <div className="flex items-center justify-end gap-3">
          {loading && <span className="text-sm text-neutral-500">Generating… this can take a moment</span>}
          <button
            type="submit"
            disabled={loading || !description.trim()}
            className="inline-flex items-center gap-2 rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-neutral-700 disabled:cursor-not-allowed disabled:bg-neutral-300"
          >
            {loading && (
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
            )}
            {loading ? "Generating" : "Generate"}
          </button>
        </div>
        {error && (
          <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </p>
        )}
      </form>

      <section className="mt-12 space-y-4">
        {scenarios.length === 0 ? (
          <p className="text-center text-sm text-neutral-400">No scenarios yet.</p>
        ) : (
          scenarios.map(({ id, scenario }) => (
            <article key={id} className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <h2 className="text-lg font-semibold leading-snug">{scenario.title}</h2>
                <span
                  className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ring-1 ring-inset ${DIFFICULTY_STYLES[scenario.difficulty]}`}
                >
                  {scenario.difficulty}
                </span>
              </div>

              <h3 className="mt-5 text-xs font-medium uppercase tracking-wide text-neutral-500">Objectives</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-neutral-700">
                {scenario.objectives.map((o, i) => (
                  <li key={i}>{o}</li>
                ))}
              </ul>

              <h3 className="mt-5 text-xs font-medium uppercase tracking-wide text-neutral-500">Injects</h3>
              <ol className="mt-2 space-y-2">
                {scenario.injects.map((inject, i) => (
                  <li key={i} className="flex gap-3 text-sm">
                    <span className="w-14 shrink-0 font-mono text-xs leading-5 text-neutral-500">
                      T+{inject.minute}m
                    </span>
                    <span className="text-neutral-700">{inject.description}</span>
                  </li>
                ))}
              </ol>
            </article>
          ))
        )}
      </section>
    </main>
  );
}
