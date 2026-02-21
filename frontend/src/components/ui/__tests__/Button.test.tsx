import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Button } from "../Button";

describe("Button", () => {
  it("renders provided label", () => {
    render(<Button>Run sync</Button>);

    expect(screen.getByRole("button", { name: "Run sync" })).toBeInTheDocument();
  });

  it("calls click handler", async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();

    render(<Button onClick={onClick}>Ask</Button>);
    await user.click(screen.getByRole("button", { name: "Ask" }));

    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
