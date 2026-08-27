/** Subtle HUD grid + colorful scan/radar overlay for dark sections. */
export default function ScanGrid({ className = "" }: { className?: string }) {
  return (
    <div className={`fx-scan-grid ${className}`.trim()} aria-hidden>
      <div className="fx-scan-lines" />
      <div className="fx-scan-radar" />
      <div className="fx-scan-beam" />
    </div>
  );
}
