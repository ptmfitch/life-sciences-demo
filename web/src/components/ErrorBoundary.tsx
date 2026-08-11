import { Component, type ReactNode } from "react";

export class ErrorBoundary extends Component<
  { children: ReactNode; title?: string },
  { error: Error | null }
> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-failed">
          <h2 className="font-semibold">{this.props.title || "Something went wrong"}</h2>
          <p className="mt-2 text-sm opacity-80">{this.state.error.message}</p>
          <button
            type="button"
            className="mt-4 rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-sm"
            onClick={() => this.setState({ error: null })}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}