"use client";

/* eslint-disable no-restricted-syntax -- tokens.css is not loaded here, so palette colors are inlined */

/** Last resort: the root layout itself crashed. No fonts or components, just HTML. */
export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  return (
    <html lang="uk">
      <body style={{ fontFamily: "system-ui, sans-serif", background: "#f7f5f0", color: "#252522", padding: 32 }}>
        <h1>Сайт тимчасово недоступний</h1>
        <p>Спробуйте оновити сторінку за хвилину.</p>
        <button type="button" onClick={reset} style={{ padding: "12px 24px", background: "#292925", color: "#f7f5f0", border: 0 }}>
          Оновити
        </button>
      </body>
    </html>
  );
}
