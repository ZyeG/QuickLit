import React, { useEffect, useState } from "react";
import "./App.css";
import MyChatBot from "./components/chatbot";

// -------------------------
// Types
// -------------------------
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

const buildSessionId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `session-${Date.now()}`;
};

// -------------------------
// Component
// -------------------------
function App() {
  const [topic, setTopic] = useState<string>("");
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [fetchedCount, setFetchedCount] = useState<number | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  // Utility: show first N words of an abstract
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
    // Persist to backend
    await fetch("http://localhost:3001/api/collections/papers/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session,
      }),
    })
      .then(() => {
        // Update local storage
        setSessions((prev: any[]) => {
          const updated = [session, ...prev.filter((s) => s.id !== session.id)];
          writeSessionsToStorage(updated);
          return updated;
        });
        setActiveSessionId(session.id);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error persisting session to backend", err);
      });
  };

  const handleSessionSelect = (sessionId: string) => {
    const session = sessions.find((s) => s.id === sessionId);
    if (!session) return;
    setActiveSessionId(sessionId);
    setTopic(session.topic);
    setPapers(session.papers);
    setFetchedCount(session.fetchedCount);
    setSelectedPaper(null);
  };

  const handleQuery = async () => {
    if (!topic.trim()) return;

    setLoading(true);
    setPapers([]);
    setFetchedCount(null);
    setSelectedPaper(null);

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
          id: buildSessionId(),
          topic: topic.trim(),
          papers: nextPapers,
          fetchedCount: total,
          createdAt: new Date().toISOString(),
        };
        await asyncPersistSession(newSession);
      })
      .catch((err) => {
        console.error(err);
        alert("Error querying backend");
      });
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* MAIN COLUMN */}
      <div style={{ flex: 1, padding: "20px" }}>
        <h1>QuickLit</h1>

        {sessions.length > 0 && (
          <div style={{ margin: "10px 0" }}>
            <div style={{ fontWeight: "bold", marginBottom: "6px" }}>
              Sessions
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => handleSessionSelect(session.id)}
                  style={{
                    padding: "6px 10px",
                    borderRadius: "6px",
                    border:
                      activeSessionId === session.id
                        ? "2px solid #0077cc"
                        : "1px solid #ccc",
                    background:
                      activeSessionId === session.id ? "#e6f2fb" : "#fff",
                    cursor: "pointer",
                  }}
                >
                  {session.topic || "Untitled"} (
                  {new Date(session.createdAt).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                  })}
                  )
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Topic Input */}
        <input
          type="text"
          placeholder="Enter a research topic (~10 words)..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          style={{
            width: "70%",
            padding: "10px",
            fontSize: "16px",
            marginRight: "10px",
          }}
        />

        <button
          onClick={handleQuery}
          disabled={loading}
          style={{
            padding: "10px 20px",
            fontSize: "16px",
            cursor: "pointer",
          }}
        >
          {loading ? "Searching..." : "Search"}
        </button>

        <hr style={{ margin: "20px 0" }} />

        {/* Status text */}
        {loading && papers.length === 0 && (
          <p style={{ fontStyle: "italic" }}>Searching… please wait</p>
        )}
        {loading && papers.length > 0 && (
          <p style={{ fontStyle: "italic" }}>Syncing results… please wait</p>
        )}
        {!loading && fetchedCount !== null && (
          <p>
            <strong>Fetched {fetchedCount} papers</strong>
          </p>
        )}

        {/* Results Table */}
        {!loading && papers.length > 0 && (
          <table
            border={1}
            cellPadding={8}
            style={{ width: "100%", borderCollapse: "collapse" }}
          >
            <thead>
              <tr style={{ background: "#eee" }}>
                <th>arXiv ID</th>
                <th>Title</th>
                <th>PDF</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {papers.map((p, idx) => (
                <tr key={idx}>
                  <td>{p.paper_id}</td>
                  <td>{p.title}</td>
                  <td>
                    <a
                      href={p.pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      PDF
                    </a>
                  </td>
                  <td>
                    <span
                      style={{
                        textDecoration: "underline",
                        cursor: "pointer",
                        color: "#0077cc",
                      }}
                      onClick={() => setSelectedPaper(p)}
                    >
                      {firstNWords(p.abstract, 20)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {!loading && fetchedCount === 0 && papers.length === 0 && (
          <p>No papers found for this topic.</p>
        )}
      </div>

      {/* SIDEBAR – Full Abstract */}
      {selectedPaper && (
        <div
          style={{
            width: "350px",
            borderLeft: "1px solid #ccc",
            padding: "20px",
            background: "#fafafa",
            overflowY: "auto",
          }}
        >
          <button
            onClick={() => setSelectedPaper(null)}
            style={{
              float: "right",
              padding: "5px 10px",
              cursor: "pointer",
            }}
          >
            ✕
          </button>

          <h2 style={{ marginTop: 0 }}>{selectedPaper.title}</h2>

          <p style={{ fontSize: "14px", lineHeight: "1.5" }}>
            {selectedPaper.abstract}
          </p>

          <a
            href={selectedPaper.pdf_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            Open PDF
          </a>
        </div>
      )}
      <MyChatBot collection_name={activeSessionId ? activeSessionId : ""} />
    </div>
  );
}

export default App;
