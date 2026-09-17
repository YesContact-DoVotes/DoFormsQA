import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "success" | "danger" | "warning" | "info" | "neutral" | "purple";
  size?: "sm" | "md";
  className?: string;
}

export function Badge({ children, variant = "neutral", size = "sm", className = "" }: BadgeProps) {
  const variantStyles = {
    success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    danger: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    warning: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    info: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    purple: "bg-purple-500/10 text-purple-400 border-purple-500/30",
    neutral: "bg-slate-800 text-slate-300 border-slate-700",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-xs font-semibold",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium transition-colors ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  switch (status?.toUpperCase()) {
    case "PASSED":
    case "COMPLETED":
    case "CONFIRMED":
      return <Badge variant="success">{status}</Badge>;
    case "FAILED":
    case "REJECTED":
    case "CRITICAL":
      return <Badge variant="danger">{status}</Badge>;
    case "RUNNING":
    case "PLANNING":
    case "VERIFYING":
      return (
        <Badge variant="info">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse" />
          {status}
        </Badge>
      );
    case "BLOCKED":
    case "HIGH":
      return <Badge variant="warning">{status}</Badge>;
    case "MEDIUM":
      return <Badge variant="purple">{status}</Badge>;
    case "LOW":
    case "PLANNED":
    default:
      return <Badge variant="neutral">{status}</Badge>;
  }
}
