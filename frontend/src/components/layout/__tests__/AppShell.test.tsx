import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AppShell } from "../AppShell";

describe("AppShell", () => {
  it("renders navigation and main content", () => {
    render(
      <MemoryRouter>
        <AppShell>
          <div>Workspace content</div>
        </AppShell>
      </MemoryRouter>
    );

    expect(screen.getByRole("navigation", { name: "Main navigation" })).toBeInTheDocument();
    expect(screen.getByText("Workspace content")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Overview" })).toBeInTheDocument();
  });
});
