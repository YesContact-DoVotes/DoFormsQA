import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "success" | "danger" | "warning" | "info" | "neutral" | "purple";
  size?: "sm" | "md";
  className?: string;
}

export function Badge({ children, variant = "neutral", size = "sm", className = "" }: BadgeProps) {
  const variantStyles = {
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
    danger: "bg-rose-50 text-rose-700 border-rose-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    info: "bg-blue-50 text-blue-700 border-blue-200",
    purple: "bg-purple-50 text-purple-700 border-purple-200",
    neutral: "bg-slate-100 text-slate-700 border-slate-200",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-xs font-semibold",
  };

  return (
    <span
      className={`inline-flex items-center rounded-md border font-medium ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
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
      return <Badge variant="info">{status}</Badge>;
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
