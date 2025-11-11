import { useState } from "react";

function App() {
  const [topic, setTopic] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [maxResults, setMaxResults] = useState(20);
  const [showRaw, setShowRaw] = useState(false);
  const [page, setPage] = useState(1);
  const perPage = 5; // number of papers per page

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

  const retrieved = result?.pipeline_output?.retrieved_papers || [];
  const start = (page - 1) * perPage;
  const paginated = retrieved.slice(start, start + perPage);
  const totalPages = Math.ceil(retrieved.length / perPage);

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>QuickLit: Query Pipeline</h1>

      {/* Input row */}
      <div style={{ marginTop: "1rem" }}>
        {/* Research topic input */}
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

        {/* Max results input */}
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

        {/* Submit button */}
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
                {paginated.map((p: any, i: number) => (
                  <li
                    key={i}
                    style={{
                      background: "#f8f8f8",
                      marginBottom: "0.8rem",
                      padding: "0.7rem 1rem",
                      borderRadius: "8px",
                      boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
                    }}
                  >
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
                  </li>
                ))}
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