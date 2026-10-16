import { useEffect, useState } from "react";
import { ChatView } from "./components/ChatView";
import { BrandMark, Icon } from "./components/Icon";
import { ResourcesView } from "./components/ResourcesView";
import { StaffView } from "./components/StaffView";

type View = "chat" | "resources" | "staff";
const VIEWS: { id: View; label: string }[] = [
  { id: "chat", label: "Chat" },
  { id: "resources", label: "Resources" },
  { id: "staff", label: "Staff" },
];

type Theme = "light" | "dark";
const THEME_KEY = "rih-theme";

function viewFromHash(): View {
  const h = window.location.hash.replace(/^#\/?/, "");
  return (VIEWS.find((v) => v.id === h)?.id ?? "chat") as View;
}

// An explicit choice is remembered on this device only; otherwise the system setting applies.
function storedTheme(): Theme | null {
  try {
    const t = window.localStorage.getItem(THEME_KEY);
    return t === "light" || t === "dark" ? t : null;
  } catch {
    return null;
  }
}

function systemTheme(): Theme {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function App() {
  const [view, setView] = useState<View>(viewFromHash);
  const [theme, setTheme] = useState<Theme | null>(storedTheme);

  useEffect(() => {
    const onHash = () => setView(viewFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (theme) root.dataset.theme = theme;
    else delete root.dataset.theme;
    try {
      if (theme) window.localStorage.setItem(THEME_KEY, theme);
    } catch {
      // storage unavailable (private mode): the choice lasts for this page only
    }
  }, [theme]);

  const effective = theme ?? systemTheme();
  const next: Theme = effective === "dark" ? "light" : "dark";

  return (
    <div className="app">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="topbar">
        <div className="container topbar__inner">
          <div className="brand">
            <BrandMark />
            <div className="brand__text">
              <h1 className="brand__name">RIH Care Insight Assistant</h1>
              <p className="brand__tagline">Find campus health and support resources</p>
            </div>
          </div>
          <div className="topbar__nav">
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
            <button type="button" className="theme-toggle" onClick={() => setTheme(next)} aria-label={`Use ${next} theme`}
              title={`Use ${next} theme`}>
              <Icon name={next === "dark" ? "moon" : "sun"} />
            </button>
          </div>
        </div>
      </header>
      <div className="container">
        <div className="disclaimer" role="note">
          <Icon name="info" />
          <p>
            Independent student prototype, not an official UMBC or Retriever Integrated Health service. It shares
            information and does not give medical advice. <strong>In an emergency call 911, or call or text 988.</strong>
          </p>
        </div>
        <main id="main" tabIndex={-1} className="page">
          {view === "chat" && <ChatView />}
          {view === "resources" && <ResourcesView />}
          {view === "staff" && <StaffView />}
        </main>
      </div>
      <footer className="footer">
        <div className="container footer__inner">
          <p>Built by Abhinav Varma Vathadi and Devika Rani Sanaboyina. Synthetic demo data only.</p>
          <p>UMBC-inspired colors; not affiliated with or endorsed by UMBC.</p>
        </div>
      </footer>
    </div>
  );
}
