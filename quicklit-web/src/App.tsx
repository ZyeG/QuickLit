// import React from 'react';
// import logo from './logo.svg';
// import './App.css';

// function App() {
//   return (
//     <div className="App">
//       <header className="App-header">
//         <img src={logo} className="App-logo" alt="logo" />
//         <p>
//           Edit <code>src/App.tsx</code> and save to reload.
//         </p>
//         <a
//           className="App-link"
//           href="https://reactjs.org"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           Learn React
//         </a>
//       </header>
//     </div>
//   );
// }

// export default App;

import { useState } from "react";

function App() {
  const [topic, setTopic] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    const res = await fetch("http://localhost:3001/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic }),
    });
    const data = await res.json();
    setResult(data);
    setLoading(false);
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h1>QuickLit: Query Pipeline</h1>
      <input
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        placeholder="Enter research topic..."
        style={{ width: "400px", padding: "0.5rem" }}
      />
      <button onClick={handleSubmit} disabled={loading} style={{ marginLeft: "1rem" }}>
        {loading ? "Running..." : "Submit"}
      </button>

      {result && (
        <div style={{ marginTop: "2rem" }}>
          <h3>Pipeline Output</h3>
          <pre style={{ background: "#eee", padding: "1rem" }}>
            {JSON.stringify(result.pipeline_output, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default App;