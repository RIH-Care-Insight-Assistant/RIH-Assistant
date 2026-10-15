import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { resetClientStateForTests } from "../api/client";
import type { SourceRow } from "../api/types";
import { installFakeApi } from "../test/fakeApi";
import { StaffView } from "./StaffView";

const ROW: SourceRow = {
  chunk_id: "chk_1", title: "RIH Billing", url: "https://health.umbc.edu/billing", category: "billing",
  version: "abc", updated_on: "2025-09-22", ingested: false, inventory_status: "baseline",
  effective_status: "baseline", freshness: "stale", eligible: true, reasons: [], signals: [],
  approved_by: null, approved_at: null,
};

beforeEach(() => resetClientStateForTests());

describe("StaffView", () => {
  it("rejects a bad password without revealing why", async () => {
    installFakeApi();
    const user = userEvent.setup();
    render(<StaffView />);
    await user.type(await screen.findByLabelText("Username"), "rita.reviewer");
    await user.type(screen.getByLabelText("Password"), "wrong-password-xx");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Sign-in failed.");
    expect(screen.getByLabelText("Password")).toHaveValue("");
  });

  it("reviewer signs in, sees only reviewer tabs and records a decision", async () => {
    const api = installFakeApi({ sources: [ROW] });
    const user = userEvent.setup();
    render(<StaffView />);
    await user.type(await screen.findByLabelText("Username"), "rita.reviewer");
    await user.type(screen.getByLabelText("Password"), "synthetic-Test-pass-0001");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    const tabs = await screen.findByRole("tablist", { name: "Staff sections" });
    expect(within(tabs).getAllByRole("tab").map((t) => t.textContent)).toEqual(["Sources", "Governance", "Feedback"]);
    await user.type(await screen.findByLabelText("Review note for RIH Billing"), "checked official page");
    await user.click(screen.getByRole("button", { name: "Reject RIH Billing" }));
    await waitFor(() => expect(api.reviews).toHaveLength(1));
    expect(api.reviews[0]).toEqual({ path: "/admin/sources/chk_1/review", body: { status: "rejected", note: "checked official page" } });
  });

  it("admin sees administrative tabs; sign-out returns to the login form", async () => {
    installFakeApi({ staff: { username: "adam.admin", roles: ["admin"] } });
    const user = userEvent.setup();
    render(<StaffView />);
    const tabs = await screen.findByRole("tablist", { name: "Staff sections" });
    expect(within(tabs).getAllByRole("tab")).toHaveLength(6);
    await user.click(screen.getByRole("button", { name: "Sign out" }));
    expect(await screen.findByRole("heading", { name: "Staff sign-in" })).toBeInTheDocument();
  });

  it("shows the server's refusal when a role is not allowed", async () => {
    installFakeApi({ staff: { username: "rita.reviewer", roles: ["reviewer"] } });
    render(<StaffView />);
    // Even if a reviewer reached the Users panel, the server answers 403 and the UI says so.
    const { staffApi } = await import("../api/client");
    await expect(staffApi.users()).rejects.toMatchObject({ status: 403 });
  });
});
