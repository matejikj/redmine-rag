import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TextField } from "../TextField";

describe("TextField", () => {
  it("binds label to input", () => {
    render(<TextField label="Project IDs" name="project_ids" />);

    expect(screen.getByLabelText("Project IDs")).toBeInTheDocument();
  });

  it("exposes error as accessible description", () => {
    render(<TextField label="Top K" name="top_k" error="Must be >= 1" />);

    const input = screen.getByLabelText("Top K");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByText("Must be >= 1")).toBeInTheDocument();
  });
});
