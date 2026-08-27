import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
  as?: "span" | "strong";
  hover?: boolean;
};

export default function GlitchText({ children, className = "", as = "span", hover = false }: Props) {
  const Tag = as;
  return (
    <Tag
      className={`fx-glitch${hover ? " fx-glitch-hover" : ""} ${className}`.trim()}
      data-text={typeof children === "string" ? children : undefined}
    >
      {children}
    </Tag>
  );
}
