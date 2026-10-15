import { useEffect, useState } from "react";
import { AdminView } from "./components/AdminView";
import { ChatView } from "./components/ChatView";
import { ResourcesView } from "./components/ResourcesView";

type View = "chat" | "resources" | "staff";
const VIEWS: { id: View; label: string }[] = [
  { id: "chat", label: "Chat" },
  { id: "resources", label: "Resources" },
  { id: "staff", label: "Staff" },
];

function viewFromHash(): View {
  const h = window.location.hash.replace(/^#\/?/, "");
  return (VIEWS.find((v) => v.id === h)?.id ?? "chat") as View;
}

export function App() {
  const [view, setView] = useState<View>(viewFromHash);

  useEffect(() => {
    const onHash = () => setView(viewFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  return (
    <div className="app">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="app__header">
        <div className="app__brand">
          <h1>RIH Care Insight Assistant</h1>
          <p className="app__tagline">Find campus health and support resources</p>
        </div>
        <nav aria-label="Main">
          <ul className="tabs">
            {VIEWS.map((v) => (
              <li key={v.id}>
                <a href={`#/${v.id}`} className="tab" aria-current={view === v.id ? "page" : undefined}>
                  {v.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <p className="disclaimer" role="note">
        Independent student prototype, not an official UMBC or Retriever Integrated Health service. It shares
        information and does not give medical advice. In an emergency call 911, or call or text 988.
      </p>
      <main id="main" tabIndex={-1}>
        {view === "chat" && <ChatView />}
        {view === "resources" && <ResourcesView />}
        {view === "staff" && <AdminView />}
      </main>
    </div>
  );
}
