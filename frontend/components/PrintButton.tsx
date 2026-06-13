"use client";

export function PrintButton() {
  return (
    <button className="secondary" onClick={() => window.print()} type="button">
      Print Report
    </button>
  );
}
