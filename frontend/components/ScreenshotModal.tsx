"use client";

import { X, ExternalLink } from "lucide-react";

interface ScreenshotModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl: string;
  title?: string;
}

export function ScreenshotModal({ isOpen, onClose, imageUrl, title }: ScreenshotModalProps) {
  if (!isOpen || !imageUrl) return null;

  // Prepend backend host if relative URL
  const fullUrl = imageUrl.startsWith("http") ? imageUrl : `http://localhost:8080${imageUrl}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="relative max-h-[90vh] max-w-5xl w-full overflow-hidden rounded-2xl bg-white border border-slate-200 shadow-2xl flex flex-col">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3.5 bg-slate-50">
          <h3 className="text-sm font-semibold text-slate-800 truncate">{title || "Evidence Screenshot"}</h3>
          <div className="flex items-center gap-2">
            <a
              href={fullUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-200/60 transition-colors"
              title="Open full size"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-200/60 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
        <div className="overflow-auto p-4 flex items-center justify-center bg-slate-100 min-h-[300px]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={fullUrl}
            alt={title || "Screenshot"}
            className="max-h-[75vh] w-auto rounded-lg border border-slate-300 shadow-sm object-contain"
          />
        </div>
      </div>
    </div>
  );
}
