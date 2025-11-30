import React, { useEffect, useState } from "react";
import "./App.css";
import MyChatBot from "./components/chatbot";

type Paper = {
  paper_id: string;
  title: string;
  pdf_url: string;
  abstract: string;
};

type Session = {
  id: string;
  topic: string;
  papers: Paper[];
  fetchedCount: number;
  createdAt: string;
};

const STORAGE_KEY = "quicklitSessions";
const SUMMARY_CACHE_KEY = "quicklitSummaryCache";

const readSessionsFromStorage = (): Session[] => {
  if (typeof window === "undefined") return [];
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    if (!value) return [];
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? (parsed as Session[]) : [];
  } catch (err) {
    console.error("Unable to read sessions from storage", err);
    return [];
  }
};

const writeSessionsToStorage = (sessions: Session[]) => {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
};

const readSummaryFromStorage = (paperId: string): string | null => {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(SUMMARY_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && paperId in parsed) {
      return parsed[paperId];
    }
  } catch (err) {
    console.error("Unable to read summary cache", err);
  }
  return null;
};

const writeSummaryToStorage = (paperId: string, summary: string) => {
  if (typeof window === "undefined") return;
  try {
    const raw = window.localStorage.getItem(SUMMARY_CACHE_KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    const next = { ...(parsed || {}), [paperId]: summary };
    window.localStorage.setItem(SUMMARY_CACHE_KEY, JSON.stringify(next));
  } catch (err) {
    console.error("Unable to write summary cache", err);
  }
};

const buildSessionId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `session-${Date.now()}`;
};

function App() {
  const [topic, setTopic] = useState<string>("");
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [summaryPanelPaperId, setSummaryPanelPaperId] = useState<string | null>(
    null
  );
  const [summaryByPaperId, setSummaryByPaperId] = useState<
    Record<string, string>
  >({});
  const [summaryLoadingId, setSummaryLoadingId] = useState<string | null>(null);
  const [summaryErrorByPaperId, setSummaryErrorByPaperId] = useState<
    Record<string, string>
  >({});
  const [fetchedCount, setFetchedCount] = useState<number | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [isAbstractOpen, setIsAbstractOpen] = useState<boolean>(false);
  const [syncingSessionId, setSyncingSessionId] = useState<string | null>(null);

  const firstNWords = (text: string, n: number = 20): string => {
    if (!text) return "";
    const words = text.split(/\s+/);
    return words.slice(0, n).join(" ") + (words.length > n ? " ..." : "");
  };

  useEffect(() => {
    const storedSessions = readSessionsFromStorage();
    if (storedSessions.length === 0) return;
    setSessions(storedSessions);
    const latestSession = storedSessions[0];
    setActiveSessionId(latestSession.id);
    setTopic(latestSession.topic);
    setPapers(latestSession.papers);
    setFetchedCount(latestSession.fetchedCount);
    setSelectedPaper(null);
  }, []);

  const asyncPersistSession = async (session: Session) => {
    try {
      await fetch("http://localhost:3001/api/collections/papers/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session,
        }),
      }).then(() => {
        setSessions((prev: Session[]) => {
          const updated = [session, ...prev.filter((s) => s.id !== session.id)];
          writeSessionsToStorage(updated);
          return updated;
        });
        setActiveSessionId(session.id);
      });
    } catch (err) {
      console.error("Error persisting session to backend", err);
    } finally {
      setIsSyncing(false);
      setSyncingSessionId(null);
    }
  };

  const handleSessionSelect = (sessionId: string) => {
    const session = sessions.find((s) => s.id === sessionId);
    if (!session) return;
    setActiveSessionId(sessionId);
    setTopic(session.topic);
    setPapers(session.papers);
    setFetchedCount(session.fetchedCount);
    setSelectedPaper(null);
    setIsAbstractOpen(false);
    setSummaryPanelPaperId(null);
    setSummaryByPaperId({});
    setSummaryErrorByPaperId({});
    setSummaryLoadingId(null);
  };

  const handleQuery = async () => {
    if (!topic.trim()) return;
    const newSessionId = buildSessionId();

    setLoading(true);
    setIsSyncing(true);
    setSyncingSessionId(newSessionId);
    setActiveSessionId(newSessionId);
    setPapers([]);
    setFetchedCount(null);
    setSelectedPaper(null);
    setIsAbstractOpen(false);
    setSummaryPanelPaperId(null);
    setSummaryByPaperId({});
    setSummaryErrorByPaperId({});
    setSummaryLoadingId(null);

    // If this topic was queried before, reuse the stored session instead of refetching
    const normalizedTopic = topic.trim().toLowerCase();
    const existing = sessions.find(
      (s) => s.topic.trim().toLowerCase() === normalizedTopic
    );
    if (existing) {
      setPapers(existing.papers);
      setFetchedCount(existing.fetchedCount);
      setLoading(false);
      setIsSyncing(false);
      setActiveSessionId(existing.id);
      return;
    }

    await fetch("http://localhost:3001/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic }),
    })
      .then(async (res) => {
        const data = await res.json();
        const nextPapers: Paper[] = data.papers || [];
        const total =
          typeof data.num_papers === "number"
            ? data.num_papers
            : nextPapers.length;
        setPapers(nextPapers);
        setFetchedCount(total);
        const newSession: Session = {
          id: newSessionId,
          topic: topic.trim(),
          papers: nextPapers,
          fetchedCount: total,
          createdAt: new Date().toISOString(),
        };
        setLoading(false);
        await asyncPersistSession(newSession);
      })
      .catch((err) => {
        console.error(err);
        alert("Error querying backend");
        setIsSyncing(false);
        setSyncingSessionId(null);
        setLoading(false);
      });
  };

  const statusLabel = () => {
    if (loading && papers.length === 0) return "Searching for relevant papers";
    if (isSyncing && papers.length > 0)
      return "Syncing results, please wait...";
    if (!loading && fetchedCount !== null)
      return `Fetched ${fetchedCount} papers`;
    if (!loading && fetchedCount === 0) return "No papers found for this topic";
    return "";
  };

  const openAbstractModal = (paper: Paper) => {
    setSelectedPaper(paper);
    setIsAbstractOpen(true);
  };

  const handleSummaryBySection = async (paper: Paper) => {
    if (loading || isSyncing) {
      return;
    }
    setSelectedPaper(paper);
    setSummaryPanelPaperId(paper.paper_id);
    setSummaryErrorByPaperId((prev) => {
      const next = { ...prev };
      delete next[paper.paper_id];
      return next;
    });

    if (summaryByPaperId[paper.paper_id]) {
      return;
    }

    const cachedSummary = readSummaryFromStorage(paper.paper_id);
    if (cachedSummary) {
      setSummaryByPaperId((prev) => ({
        ...prev,
        [paper.paper_id]: cachedSummary,
      }));
      return;
    }

    setSummaryLoadingId(paper.paper_id);
    try {
      const res = await fetch("http://localhost:3001/api/summary/by-id", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ arxiv_id: paper.paper_id }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || "Failed to fetch summary");
      }
      if (!data?.summary) {
        throw new Error("No summary returned");
      }

      setSummaryByPaperId((prev) => ({
        ...prev,
        [paper.paper_id]: data.summary as string,
      }));
      writeSummaryToStorage(paper.paper_id, data.summary as string);
    } catch (err) {
      console.error("Error fetching summary", err);
      setSummaryErrorByPaperId((prev) => ({
        ...prev,
        [paper.paper_id]: "Unable to fetch summary. Please try again.",
      }));
    } finally {
      setSummaryLoadingId(null);
    }
  };

  const closeAbstractModal = () => {
    setIsAbstractOpen(false);
    setSelectedPaper(null);
    setSummaryPanelPaperId(null);
  };

  return (
    <div className="ql-page">
      <div className="ql-surface-glow" />
      <div className="ql-app-shell">
        <header className="ql-topbar">
          <div className="ql-brand">
            <div className="ql-logo">QL</div>
            <div>
              <div className="ql-brand-title">QuickLit</div>
              <div className="ql-brand-sub">Research-ready in seconds</div>
            </div>
          </div>
        </header>

        <div className="ql-layout">
          <main className="ql-main">
            <section className="ql-hero">
              <p className="ql-eyebrow">AI-powered literature scout</p>
              <h1 className="ql-heading">
                Discover focused papers, summarized fast.
              </h1>
              <p className="ql-subheading">
                Search, scan abstracts, and pin a paper without leaving your
                flow.
              </p>

              <div className="ql-search-card">
                <label className="ql-label" htmlFor="topic">
                  Research topic
                </label>
                <div className="ql-input-row">
                  <input
                    id="topic"
                    type="text"
                    className="ql-input"
                    placeholder="e.g. Multimodal transformers for medical imaging triage"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                  />
                  <button
                    className="ql-btn-primary"
                    onClick={handleQuery}
                    disabled={loading}
                  >
                    {loading ? "Searching..." : "Search"}
                  </button>
                </div>
                <p className="ql-hint">
                  Keep it concise (around 8-12 words) for the cleanest results.
                </p>
              </div>

              {sessions.length > 0 && (
                <div className="ql-session-panel">
                  <div className="ql-session-header">
                    <span>Recent sessions</span>
                    <span className="ql-session-count">{sessions.length}</span>
                  </div>
                  <div className="ql-session-chips">
                    {sessions.map((session) => (
                      <button
                        key={session.id}
                        onClick={() => handleSessionSelect(session.id)}
                        className={`ql-chip ${
                          activeSessionId === session.id ? "active" : ""
                        }`}
                      >
                        <span className="ql-chip-title">
                          {session.topic || "Untitled"}
                        </span>
                        <span className="ql-chip-date">
                          {new Date(session.createdAt).toLocaleDateString(
                            undefined,
                            {
                              month: "short",
                              day: "numeric",
                            }
                          )}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </section>

            <section className="ql-status-row">
              <div className="ql-status-dot" />
              <span className="ql-status-text">{statusLabel()}</span>
            </section>

            <section className="ql-results-card">
              <div className="ql-results-header">
                <div>
                  <p className="ql-eyebrow">Results</p>
                  <h3 className="ql-section-title">
                    {fetchedCount !== null
                      ? `${fetchedCount} papers`
                      : "Waiting for a query"}
                  </h3>
                </div>
              </div>

              {loading && papers.length === 0 && (
                <div className="ql-empty">
                  <div className="ql-loader" />
                  <p>Gathering papers tailored to your topic...</p>
                </div>
              )}

              {!loading && papers.length === 0 && fetchedCount === null && (
                <div className="ql-empty">
                  <p>Start with a topic to see focused literature.</p>
                </div>
              )}

              {!loading && fetchedCount === 0 && (
                <div className="ql-empty">
                  <p>No papers found. Refine the query and try again.</p>
                </div>
              )}

              {!loading && papers.length > 0 && (
                <div className="ql-paper-grid">
                  {papers.map((paper) => (
                    <article
                      key={paper.paper_id}
                      className="ql-paper-card"
                      onClick={() => {
                        openAbstractModal(paper);
                        setSelectedPaper(paper);
                        setSummaryPanelPaperId(null);
                      }}
                    >
                      <div className="ql-paper-id">{paper.paper_id}</div>
                      <h4 className="ql-paper-title">{paper.title}</h4>
                      <p className="ql-paper-abstract">
                        {firstNWords(paper.abstract, 28)}
                      </p>
                      <div className="ql-paper-actions">
                        <a
                          className="ql-link"
                          href={paper.pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          Open PDF
                        </a>
                        <button
                          className="ql-ghost-btn"
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            openAbstractModal(paper);
                            setSelectedPaper(paper);
                            setSummaryPanelPaperId(null);
                          }}
                        >
                          Preview
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </main>
        </div>
      </div>

      {isAbstractOpen && selectedPaper && (
        <div className="ql-modal-overlay" onClick={closeAbstractModal}>
          <div className="ql-modal" onClick={(e) => e.stopPropagation()}>
            <div className="ql-sidebar-card">
              <div className="ql-sidebar-header">
                <p className="ql-eyebrow">Abstract</p>
                <button className="ql-close-btn" onClick={closeAbstractModal}>
                  Close
                </button>
              </div>
              <h3 className="ql-sidebar-title">{selectedPaper.title}</h3>
              <p className="ql-sidebar-abstract">{selectedPaper.abstract}</p>
              <a
                className="ql-btn-secondary"
                href={selectedPaper.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Open PDF
              </a>
              <button
                className="ql-btn-secondary"
                onClick={() => handleSummaryBySection(selectedPaper)}
                disabled={
                  summaryLoadingId === selectedPaper.paper_id ||
                  loading ||
                  isSyncing
                }
              >
                {summaryLoadingId === selectedPaper.paper_id
                  ? "Fetching summary..."
                  : isSyncing || loading
                  ? "Waiting for syncing to complete before fetching summary enablement..."
                  : "Get summary by section"}
              </button>

              {summaryPanelPaperId &&
                summaryPanelPaperId === selectedPaper.paper_id && (
                  <div className="ql-summary-panel">
                    <div className="ql-sidebar-header">
                      <p className="ql-eyebrow">Summary by section</p>
                    </div>
                    <p className="ql-summary-meta">
                      {summaryLoadingId === summaryPanelPaperId
                        ? "Working on it..."
                        : `Paper ${summaryPanelPaperId}`}
                    </p>
                    {summaryLoadingId === summaryPanelPaperId && (
                      <div className="ql-summary-loading">
                        <div className="ql-loader small" />
                        <span>Generating concise section summaries...</span>
                      </div>
                    )}
                    {summaryErrorByPaperId[summaryPanelPaperId] && (
                      <p className="ql-summary-error">
                        {summaryErrorByPaperId[summaryPanelPaperId]}
                      </p>
                    )}
                    {summaryByPaperId[summaryPanelPaperId] && (
                      <pre className="ql-summary-text">
                        {summaryByPaperId[summaryPanelPaperId]}
                      </pre>
                    )}
                    {!summaryByPaperId[summaryPanelPaperId] &&
                      !summaryErrorByPaperId[summaryPanelPaperId] &&
                      summaryLoadingId !== summaryPanelPaperId && (
                        <p className="ql-summary-hint">
                          Tap "Get summary by section" to fetch notes.
                        </p>
                      )}
                  </div>
                )}
            </div>
          </div>
        </div>
      )}

      <div className="ql-chat-dock">
        <MyChatBot
          collection_name={activeSessionId ? activeSessionId : ""}
          disabled={isSyncing && syncingSessionId === activeSessionId}
        />
      </div>
    </div>
  );
}
export default App;
