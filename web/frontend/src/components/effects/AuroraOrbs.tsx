/** Floating aurora orbs — colorful high-tech atmosphere. */
export default function AuroraOrbs({ className = "" }: { className?: string }) {
  return (
    <div className={`fx-aurora ${className}`.trim()} aria-hidden>
      <span className="fx-orb fx-orb-cyan" />
      <span className="fx-orb fx-orb-lime" />
      <span className="fx-orb fx-orb-magenta" />
      <span className="fx-orb fx-orb-blue" />
    </div>
  );
}
