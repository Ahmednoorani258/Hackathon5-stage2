"use client";

import SupportForm from "@/components/SupportForm";
import { useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [lookupId, setLookupId] = useState("");
  const [ticketInfo, setTicketInfo] = useState<null | Record<string, unknown>>(
    null
  );
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [lookupLoading, setLookupLoading] = useState(false);

  const handleLookup = async () => {
    if (!lookupId.trim()) return;
    setLookupError(null);
    setTicketInfo(null);
    setLookupLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/support/ticket/${encodeURIComponent(lookupId.trim())}`
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(
          (err as Record<string, string>).detail ?? "Ticket not found"
        );
      }
      const data = await res.json();
      setTicketInfo(data as Record<string, unknown>);
    } catch (err: unknown) {
      setLookupError(
        err instanceof Error ? err.message : "Failed to look up ticket"
      );
    } finally {
      setLookupLoading(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 items-center bg-zinc-50 font-sans dark:bg-black py-12 px-4">
      <header className="w-full max-w-2xl mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-zinc-50">
          FlowSync Support
        </h1>
        <p className="mt-2 text-gray-600 dark:text-zinc-400">
          24/7 AI-powered customer support &mdash; submit a request and our
          assistant will get back to you within minutes.
        </p>
      </header>

      <main className="w-full max-w-2xl space-y-10">
        {/* --- Support Form (reused component) --- */}
        <SupportForm apiEndpoint={`${API_BASE}/api/support/submit`} />

        {/* --- Ticket Lookup Section --- */}
        <section className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Look Up Your Ticket
          </h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={lookupId}
              onChange={(e) => setLookupId(e.target.value)}
              placeholder="Enter your Ticket ID"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={handleLookup}
              disabled={lookupLoading}
              className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400"
            >
              {lookupLoading ? "Looking up..." : "Look Up"}
            </button>
          </div>

          {lookupError && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {lookupError}
            </div>
          )}

          {ticketInfo && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-500">
                  Status
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    (ticketInfo.status as string) === "open"
                      ? "bg-yellow-100 text-yellow-800"
                      : (ticketInfo.status as string) === "escalated"
                        ? "bg-red-100 text-red-800"
                        : (ticketInfo.status as string) === "resolved"
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {(ticketInfo.status as string) ?? "unknown"}
                </span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">
                  Created
                </span>
                <p className="text-sm text-gray-800">
                  {(ticketInfo.created_at as string) ?? "N/A"}
                </p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">
                  Last Updated
                </span>
                <p className="text-sm text-gray-800">
                  {(ticketInfo.last_updated as string) ?? "N/A"}
                </p>
              </div>
              {Array.isArray(ticketInfo.messages) &&
                (ticketInfo.messages as Array<Record<string, string>>).length >
                  0 && (
                  <div>
                    <span className="text-sm font-medium text-gray-500">
                      Messages
                    </span>
                    <ul className="mt-2 space-y-2">
                      {(
                        ticketInfo.messages as Array<Record<string, string>>
                      ).map((msg, i) => (
                        <li
                          key={i}
                          className={`p-3 rounded-lg text-sm ${
                            msg.direction === "inbound"
                              ? "bg-blue-50 text-blue-900"
                              : "bg-green-50 text-green-900"
                          }`}
                        >
                          <div className="flex justify-between text-xs text-gray-500 mb-1">
                            <span>
                              {msg.role} ({msg.direction})
                            </span>
                            <span>{msg.created_at ?? ""}</span>
                          </div>
                          <p>{msg.content}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
            </div>
          )}
        </section>
      </main>

      <footer className="mt-12 text-center text-sm text-gray-400">
        Powered by FlowSync AI Customer Success &middot; Direct async agent
        pipeline (Kafka deferred)
      </footer>
    </div>
  );
}
