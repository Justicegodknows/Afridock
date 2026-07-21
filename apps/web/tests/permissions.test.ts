import { describe, expect, it } from "vitest";

import { hasCapability } from "../src/lib/permissions";

describe("hasCapability", () => {
  it("grants admin every capability", () => {
    expect(hasCapability("admin", "members.invite")).toBe(true);
    expect(hasCapability("admin", "billing.view")).toBe(true);
  });

  it("grants user only chat.send", () => {
    expect(hasCapability("user", "chat.send")).toBe(true);
    expect(hasCapability("user", "members.invite")).toBe(false);
  });

  it("grants viewer nothing", () => {
    expect(hasCapability("viewer", "chat.send")).toBe(false);
    expect(hasCapability("viewer", "members.remove")).toBe(false);
  });
});
