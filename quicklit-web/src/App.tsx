import React, { useState } from "react";
import "./App.css";

// -------------------------
// Types
// -------------------------
type Paper = {
  paper_id: string;
  title: string;
  pdf_url: string;
  abstract: string;
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

  // Utility: show first N words of an abstract
  const firstNWords = (text: string, n: number = 20): string => {
    if (!text) return "";
    const words = text.split(/\s+/);
    return words.slice(0, n).join(" ") + (words.length > n ? " ..." : "");
  };

  const handleQuery = async () => {
    if (!topic.trim()) return;

    setLoading(true);
    setPapers([]);
    setFetchedCount(null);
    setSelectedPaper(null);

    try {
      const res = await fetch("http://localhost:3001/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });

      const data = await res.json();
      setPapers(data.papers || []);
      setFetchedCount(data.num_papers || 0);
    } catch (err) {
      console.error(err);
      alert("Error querying backend");
    }

    setLoading(false);
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* MAIN COLUMN */}
      <div style={{ flex: 1, padding: "20px" }}>
        <h1>QuickLit</h1>

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
        {loading && <p style={{ fontStyle: "italic" }}>Searching… please wait</p>}
        {!loading && fetchedCount !== null && (
          <p>
            <strong>Fetched {fetchedCount} papers</strong>
          </p>
        )}

        {/* Results Table */}
        {papers.length > 0 && (
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
                    <a href={p.pdf_url} target="_blank" rel="noopener noreferrer">
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
    </div>
  );
}

export default App;