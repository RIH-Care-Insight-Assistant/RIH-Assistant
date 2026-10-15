import { useEffect, useState } from "react";
import { ApiError } from "../api/client";

/**
 * Administrative area foundation. Access is decided by the backend: this view only asks
 * the server and renders what it is allowed to see. Hiding a link is never authorization.
 */
export function AdminView() {
  const [state, setState] = useState<"checking" | "denied" | "error">("checking");

  useEffect(() => {
    const ctrl = new AbortController();
    fetch("/api/v1/admin/status", { credentials: "same-origin", signal: ctrl.signal })
      .then(async (res) => {
        if (res.status === 401 || res.status === 403) setState("denied");
        else if (!res.ok) throw new ApiError(res.status, null);
        else setState("denied"); // no admin features are enabled in this build
      })
      .catch((err: unknown) => {
        if ((err as Error).name !== "AbortError") setState("error");
      });
    return () => ctrl.abort();
  }, []);

  return (
    <section className="admin" aria-labelledby="admin-title">
      <h2 id="admin-title">Staff area</h2>
      {state === "checking" && <p role="status">Checking access…</p>}
      {state === "denied" && (
        <p>
          The staff area requires a signed-in reviewer or administrator account. Access is checked by the server.
        </p>
      )}
      {state === "error" && (
        <p role="alert" className="error-banner">
          The staff area could not be reached.
        </p>
      )}
    </section>
  );
}
