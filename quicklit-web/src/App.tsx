import { useState } from "react";

function App() {
  const [topic, setTopic] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [maxResults, setMaxResults] = useState(20);
  const [showRaw, setShowRaw] = useState(false);
  const [page, setPage] = useState(1);
  const perPage = 5; // number of papers per page

  // track per-paper summaries
  const [summaries, setSummaries] = useState<Record<string, any>>({});

  const handleSubmit = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    const res = await fetch("http://localhost:3001/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, max_results: maxResults }),
    });
    const data = await res.json();
    setResult(data);
    setLoading(false);
    setShowRaw(false);
    setPage(1);
  };

  const handleGetSummary = async (pdfUrl: string) => {
    if (summaries[pdfUrl]) return; // already fetched
    try {
      const res = await fetch(
        `http://localhost:3001/api/get_summary?url=${encodeURIComponent(pdfUrl)}`
      );
      const data = await res.json();
      setSummaries((prev) => ({ ...prev, [pdfUrl]: data }));
    } catch (err) {
      console.error("Error fetching summary:", err);
      setSummaries((prev) => ({
        ...prev,
        [pdfUrl]: { summary: "⚠️ Failed to fetch summary.", type: "error" },
      }));
    }
  };

  const retrieved = result?.pipeline_output?.retrieved_papers || [];
  const start = (page - 1) * perPage;
  const paginated = retrieved.slice(start, start + perPage);
  const totalPages = Math.ceil(retrieved.length / perPage);

  const [hoveredPaper, setHoveredPaper] = useState<string | null>(null);
  const [clickedPapers, setClickedPapers] = useState<Set<string>>(new Set());

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>QuickLit: Query Pipeline</h1>

      {/* Input row */}
      <div style={{ marginTop: "1rem" }}>
        <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "bold" }}>
          Research Topic
        </label>
        <input
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter research topic..."
          style={{
            width: "400px",
            padding: "0.5rem",
            fontSize: "1rem",
          }}
        />

        <div style={{ display: "inline-block", marginLeft: "1rem" }}>
          <label
            htmlFor="max-results"
            style={{ display: "block", marginBottom: "0.3rem", fontWeight: "bold" }}
          >
            Max Papers
          </label>
          <input
            id="max-results"
            type="number"
            value={maxResults}
            min={1}
            max={100}
            onChange={(e) => setMaxResults(Number(e.target.value))}
            style={{
              width: "80px",
              padding: "0.4rem",
              fontSize: "1rem",
            }}
          />
          <div style={{ fontSize: "0.85rem", color: "#555", marginTop: "0.3rem" }}>
            Number of papers to retrieve (1–100)
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{
            marginLeft: "1.5rem",
            padding: "0.7rem 1.2rem",
            fontSize: "1rem",
            fontWeight: 500,
          }}
        >
          {loading ? "Running..." : "Submit"}
        </button>
      </div>

      {/* Output section */}
      {result && (
        <div style={{ marginTop: "2rem" }}>
          <h3>Retrieved Papers</h3>

          {retrieved.length === 0 ? (
            <p>No papers found.</p>
          ) : (
            <>
                <ul style={{ listStyleType: "none", padding: 0 }}>
                  {paginated.map((p: any, i: number) => {
                    const summaryData = summaries[p.pdf_link];
                    const isHovered = hoveredPaper === p.pdf_link;
                    const isClicked = clickedPapers.has(p.pdf_link);

                    const handleButtonClick = async () => {
                      if (!summaries[p.pdf_link]) {
                        await handleGetSummary(p.pdf_link);
                      }
                      setClickedPapers((prev) => new Set([...prev, p.pdf_link]));
                    };

                    return (
                      <li
                        key={i}
                        style={{
                          background: "#f8f8f8",
                          marginBottom: "0.8rem",
                          padding: "0.7rem 1rem",
                          borderRadius: "8px",
                          boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                        }}
                      >
                        <div>
                          <a
                            href={p.pdf_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              color: "#007bff",
                              textDecoration: "none",
                              fontWeight: 500,
                            }}
                          >
                            {p.title}
                          </a>
                        </div>

                        {/* Summary button with hover popup */}
                        <div
                          style={{ position: "relative", marginLeft: "1rem" }}
                          onMouseEnter={() => setHoveredPaper(p.pdf_link)}
                          onMouseLeave={() => setHoveredPaper(null)}
                        >
                          <button
                            onClick={handleButtonClick}
                            style={{
                              backgroundColor: isClicked ? "#28a745" : "#007bff",
                              color: "white",
                              border: "none",
                              padding: "0.4rem 0.8rem",
                              borderRadius: "6px",
                              cursor: "pointer",
                              fontSize: "0.9rem",
                            }}
                          >
                            {isClicked ? "Display" : "Get Summary"}
                          </button>

                          {/* Hover popup */}
                          {isHovered && summaryData && (
                            <div
                              style={{
                                position: "absolute",
                                top: "2.2rem",
                                right: 0,
                                background: "white",
                                border: "1px solid #ccc",
                                borderRadius: "8px",
                                padding: "0.8rem",
                                width: "350px",
                                boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                                zIndex: 100,
                                whiteSpace: "normal",
                                fontStyle:
                                  summaryData.type === "abstract" ? "italic" : "normal",
                                color: summaryData.type === "abstract" ? "#555" : "#111",
                              }}
                            >
                              <strong>
                                {summaryData.type === "abstract" ? "Abstract" : "Summary"}
                              </strong>
                              <div style={{ marginTop: "0.5rem" }}>
                                {summaryData.summary}
                              </div>
                              {summaryData.warning && (
                                <div
                                  style={{
                                    marginTop: "0.5rem",
                                    color: "#b36b00",
                                    fontSize: "0.85rem",
                                  }}
                                >
                                  ⚠️ {summaryData.warning}
                                </div>
                              )}
                              {summaryData.cached && (
                                <div
                                  style={{
                                    marginTop: "0.3rem",
                                    fontSize: "0.8rem",
                                    color: "#777",
                                  }}
                                >
                                  (Cached)
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </li>
                    );
                  })}
                </ul>

              {/* Pagination controls */}
              {totalPages > 1 && (
                <div style={{ marginTop: "1rem" }}>
                  <button
                    onClick={() => setPage((p) => Math.max(p - 1, 1))}
                    disabled={page === 1}
                    style={{ marginRight: "0.5rem" }}
                  >
                    Prev
                  </button>
                  <span>
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                    disabled={page === totalPages}
                    style={{ marginLeft: "0.5rem" }}
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}

          {/* Toggle raw output */}
          <div style={{ marginTop: "2rem" }}>
            <button
              onClick={() => setShowRaw((s) => !s)}
              style={{ marginBottom: "1rem" }}
            >
              {showRaw ? "Hide complete output" : "Show complete output"}
            </button>

            {showRaw && (
              <pre
                style={{
                  background: "#eee",
                  padding: "1rem",
                  borderRadius: "8px",
                  overflowX: "auto",
                }}
              >
                {JSON.stringify(result.pipeline_output, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;