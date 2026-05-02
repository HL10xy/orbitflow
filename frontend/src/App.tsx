import { Component, type ReactNode } from "react";
import { Dashboard } from "./components/Dashboard";
import "./App.css";

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, color: "#e2e8f0", background: "#0f172a", minHeight: "100vh", fontFamily: "monospace" }}>
          <h1 style={{ color: "#ef4444" }}>Something went wrong</h1>
          <pre style={{ whiteSpace: "pre-wrap", marginTop: 16 }}>{this.state.error?.message}</pre>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{ marginTop: 16, padding: "8px 16px", cursor: "pointer" }}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  return (
    <ErrorBoundary>
      <Dashboard />
    </ErrorBoundary>
  );
}
