import { useEffect, useState } from "react";
import { fetchPublicBranding } from "../lib/api";
import type { Branding } from "../lib/brandingTypes";

export default function ClientChat() {
  const [branding, setBranding] = useState<Partial<Branding> | null>(null);

  // Load branding on mount
  useEffect(() => {
    fetchPublicBranding()
      .then(setBranding)
      .catch(() => console.warn("Failed to load branding"));
  }, []);

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4">
      <div className="w-full max-w-4xl rounded-2xl shadow-lg bg-white/90 border border-slate-200 backdrop-blur">
        <div className="px-6 py-4 border-b border-slate-200">
          <h1 className="text-xl font-semibold text-slate-900">
            {branding?.companyName ?? "Company Chat"}
          </h1>
          <p className="text-sm text-slate-500">
            {branding?.taglineText ?? "Ask questions about your company documents."}
          </p>
        </div>
        <div className="px-6 py-4">
          <p className="text-sm text-slate-600">
            Enhanced chat with full branding integration, source links, 
            and graceful error handling coming soon.
          </p>
        </div>
      </div>
    </div>
  );
}