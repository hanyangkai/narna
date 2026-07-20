import { useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";

declare global {
  interface Window {
    Paddle?: {
      Initialize: (opts: { token: string; checkout?: { settings?: { displayMode?: string } } }) => void;
      Checkout: { open: (opts: { transactionId?: string; settings?: { successUrl?: string } }) => void };
    };
  }
}

const PADDLE_TOKEN = import.meta.env.VITE_PADDLE_CLIENT_TOKEN || "";
const PADDLE_SCRIPT = "https://cdn.paddle.com/paddle/v2/paddle.js";

function loadPaddleScript(): Promise<void> {
  if (window.Paddle) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${PADDLE_SCRIPT}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve());
      return;
    }
    const script = document.createElement("script");
    script.src = PADDLE_SCRIPT;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Paddle.js"));
    document.head.appendChild(script);
  });
}

/** Required on billing/packages pages — satisfies Paddle default payment link + opens ?_ptxn= checkout. */
export default function PaddleCheckout() {
  const [searchParams] = useSearchParams();
  const opened = useRef(false);

  useEffect(() => {
    const txn =
      searchParams.get("_ptxn") ||
      searchParams.get("txn") ||
      (searchParams.get("paid") === "1" ? searchParams.get("transaction_id") : null);
    if (!txn || !txn.startsWith("txn_")) return;
    if (opened.current) return;
    if (!PADDLE_TOKEN) return;

    opened.current = true;
    loadPaddleScript()
      .then(() => {
        window.Paddle?.Initialize({
          token: PADDLE_TOKEN,
          checkout: { settings: { displayMode: "overlay" } },
        });
        window.Paddle?.Checkout.open({ transactionId: txn });
      })
      .catch(() => {
        opened.current = false;
      });
  }, [searchParams]);

  return null;
}
