import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { MarkdownSurface } from "../MarkdownSurface";

describe("MarkdownSurface", () => {
  it("renders claim lines with clickable citation markers", () => {
    const { container } = render(
      <MarkdownSurface
        markdown={[
          "### Odpověď podložená Redmine zdroji",
          "1. OAuth callback timeout affects login flow. [1, 2]",
          "2. Rollback steps are documented in runbook. [3]"
        ].join("\n")}
        activeCitationId={2}
        activeClaimIndex={1}
      />
    );

    expect(screen.getByRole("button", { name: "[1]" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "[2]" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "[3]" })).toBeInTheDocument();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("emits selected citation id", async () => {
    const onCitationClick = vi.fn();
    const user = userEvent.setup();

    render(
      <MarkdownSurface
        markdown={"1. OAuth callback timeout affects login flow. [7]"}
        onCitationClick={onCitationClick}
      />
    );

    await user.click(screen.getByRole("button", { name: "[7]" }));

    expect(onCitationClick).toHaveBeenCalledWith(7);
  });
});
