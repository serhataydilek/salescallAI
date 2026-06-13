"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { deleteCall } from "@/lib/api";

export function DeleteCallButton({
  callId,
  redirectTo,
}: {
  callId: number;
  redirectTo?: string;
}) {
  const router = useRouter();
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState("");

  async function handleDelete() {
    const confirmed = window.confirm("Delete this call and its report?");
    if (!confirmed) return;

    setIsDeleting(true);
    setError("");
    try {
      await deleteCall(callId);
      if (redirectTo) {
        router.push(redirectTo);
      } else {
        router.refresh();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete this call.");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <div className="delete-call-control">
      <button className="secondary danger" disabled={isDeleting} onClick={handleDelete} type="button">
        {isDeleting ? "Deleting..." : "Delete Call"}
      </button>
      {error ? <div className="message error">{error}</div> : null}
    </div>
  );
}
