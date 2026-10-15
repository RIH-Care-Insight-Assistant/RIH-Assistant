import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { App } from "./App";
import { installFakeApi } from "./test/fakeApi";

describe("App", () => {
  it("shows the non-official disclaimer and navigation", () => {
    installFakeApi();
    render(<App />);
    expect(screen.getByRole("note")).toHaveTextContent(/not an official UMBC/i);
    expect(screen.getByRole("navigation", { name: "Main" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Chat" })).toHaveAttribute("aria-current", "page");
  });

  it("navigates to resources and shows provenance", async () => {
    installFakeApi();
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("link", { name: "Resources" }));
    expect(await screen.findByRole("heading", { name: "Campus resources" })).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "RIH Hours & Location" })).toBeInTheDocument();
    expect(screen.getByText("baseline")).toBeInTheDocument();
  });

  it("staff area defers to the server and shows denial", async () => {
    installFakeApi();
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("link", { name: "Staff" }));
    expect(await screen.findByText(/requires a signed-in reviewer or administrator/i)).toBeInTheDocument();
  });
});
