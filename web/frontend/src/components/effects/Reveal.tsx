import { motion, useReducedMotion } from "framer-motion";
import type { ElementType, ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
  delay?: number;
  y?: number;
  as?: ElementType;
};

export default function Reveal({ children, className = "", delay = 0, y = 28, as = "div" }: Props) {
  const reduce = useReducedMotion();
  const Tag = motion[as as keyof typeof motion] as typeof motion.div;

  if (reduce) {
    const Static = as;
    return <Static className={className}>{children}</Static>;
  }

  return (
    <Tag
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </Tag>
  );
}

export function RevealStagger({
  children,
  className = "",
  stagger = 0.08,
  as = "div",
}: {
  children: ReactNode;
  className?: string;
  stagger?: number;
  as?: ElementType;
}) {
  const reduce = useReducedMotion();
  if (reduce) {
    const Static = as;
    return <Static className={className}>{children}</Static>;
  }

  const Tag = motion[as as keyof typeof motion] as typeof motion.div;

  return (
    <Tag
      className={className}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-60px" }}
      variants={{
        hidden: {},
        show: { transition: { staggerChildren: stagger } },
      }}
    >
      {children}
    </Tag>
  );
}

export function RevealItem({
  children,
  className = "",
  as = "div",
}: {
  children: ReactNode;
  className?: string;
  as?: ElementType;
}) {
  const reduce = useReducedMotion();
  if (reduce) {
    const Static = as;
    return <Static className={className}>{children}</Static>;
  }

  const Tag = motion[as as keyof typeof motion] as typeof motion.div;

  return (
    <Tag
      className={className}
      variants={{
        hidden: { opacity: 0, y: 22 },
        show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
      }}
    >
      {children}
    </Tag>
  );
}
