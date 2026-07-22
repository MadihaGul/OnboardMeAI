import React, { useState } from "react";

export default function App() {
  const [repo, setRepo] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const ingest = async () => {
    if (!repo) return alert("Enter repo URL");
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repo }),
      });
      let j = {};
      try {
        j = await res.json();
      } catch (e) {
        j = { detail: "invalid json response" };
      }
      if (res.ok) alert("Ingested: " + j.name);
      else alert("Ingest error: " + JSON.stringify(j));
    } catch (err) {
      alert("Network error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const ask = async () => {
    if (!repo || !question) return alert("Repo and question required");
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repo, question }),
      });
      if (!res.ok) {
        let j = {};
        try {
          j = await res.json();
        } catch (e) {
          j = { detail: res.statusText };
        }
        alert("Query error: " + JSON.stringify(j));
        return;
      }
      const j = await res.json();
      setAnswer(j.answer || JSON.stringify(j));
    } catch (err) {
      alert("Network error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: 800,
        margin: "40px auto",
        fontFamily: "system-ui, Arial",
      }}
    >
      <h1>OnboardMeAI — Repo Chat</h1>
      <div style={{ marginBottom: 12 }}>
        <label>Repo URL</label>
        <br />
        <input
          style={{ width: "100%" }}
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
          placeholder="https://github.com/owner/repo"
        />
      </div>
      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        <button onClick={ingest} disabled={loading}>
          Ingest Repo
        </button>
      </div>

      <div style={{ marginBottom: 12 }}>
        <label>Question</label>
        <br />
        <textarea
          style={{ width: "100%", height: 120 }}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={ask} disabled={loading}>
          Ask
        </button>
      </div>

      <div style={{ marginTop: 20 }}>
        <h3>Answer</h3>
        <pre
          style={{ whiteSpace: "pre-wrap", background: "#f5f5f5", padding: 12 }}
        >
          {answer}
        </pre>
      </div>
    </div>
  );
}
