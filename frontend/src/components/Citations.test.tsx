import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { safeHttpsUrl } from "../api/client";
import type { Citation } from "../api/types";
import { Citations } from "./Citations";

const base: Citation = {
  source_id: "src_1", chunk_id: "chk_1", title: "Page", url: "https://health.umbc.edu/x", version: "v1",
  approval_status: "approved", approved_at: null, checked_at: null, freshness: "fresh",
};

describe("Citations", () => {
  it("links only HTTPS URLs", () => {
    render(
      <Citations
        citations={[
          base,
          { ...base, chunk_id: "chk_2", title: "Script", url: "javascript:alert(1)" },
          { ...base, chunk_id: "chk_3", title: "Plain", url: "http://example.com" },
        ]}
      />,
    );
    expect(screen.getByRole("link", { name: "Page" })).toHaveAttribute("href", "https://health.umbc.edu/x");
    expect(screen.queryByRole("link", { name: "Script" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Plain" })).toBeNull();
    expect(screen.getByText("Script")).toBeInTheDocument();
  });

  it("renders nothing without citations", () => {
    const { container } = render(<Citations citations={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("safeHttpsUrl rejects credentials and non-https schemes", () => {
    expect(safeHttpsUrl("https://user:pw@health.umbc.edu/")).toBeNull();
    expect(safeHttpsUrl("data:text/html,hi")).toBeNull();
    expect(safeHttpsUrl("not a url")).toBeNull();
    expect(safeHttpsUrl("https://health.umbc.edu/a")).toBe("https://health.umbc.edu/a");
  });
});
