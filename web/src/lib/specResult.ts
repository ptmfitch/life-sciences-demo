import type { SpecResult } from "./types";

export function specResultClass(result: SpecResult): string {
  switch (result) {
    case "PASS":
      return "bg-emerald-50 text-healthy border-emerald-100";
    case "FAIL":
      return "bg-rose-50 text-failed border-rose-100";
    default: {
      const unexpected: never = result;
      return unexpected;
    }
  }
}

export function asSpecResult(value: string | undefined): SpecResult | null {
  switch (value) {
    case "PASS":
    case "FAIL":
      return value;
    default:
      return null;
  }
}
