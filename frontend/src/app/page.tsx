"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { supabase } from "@/lib/supabase";

function CallHookLogo() {
  return (
    <svg viewBox="0 0 360 80" className="h-10 w-auto mx-auto" aria-label="CallHook">
      <g transform="translate(4, 8)">
        <path
          d="M2 24 L16 44 L16 12 C16 5 21 0 28 0 C35 0 40 5 40 12"
          stroke="#1B2A4A"
          strokeWidth="5"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M44 8 C48 4 48 -2 44 -4"
          stroke="#E86A2A"
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
          opacity="0.5"
        />
        <path
          d="M48 12 C54 6 54 -4 48 -8"
          stroke="#E86A2A"
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
          opacity="0.3"
        />
      </g>
      <text
        x="64"
        y="50"
        fontFamily="Inter, sans-serif"
        fontWeight="800"
        fontSize="40"
        letterSpacing="-1.5"
      >
        <tspan fill="#1B2A4A">Call</tspan>
        <tspan fill="#E86A2A">Hook</tspan>
      </text>
    </svg>
  );
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Dev mode: skip actual auth
    if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
      router.push("/dashboard");
      return;
    }

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/dashboard`,
        },
      });
      if (error) throw error;
      setSent(true);
    } catch (err: any) {
      setError(err.message || "Failed to send magic link");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-white">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ember" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-warm-white">
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          <CallHookLogo />
          <p className="mt-3 text-slate-light">
            Never lose a job to a missed call.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-card p-4 text-center">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {sent ? (
          <div className="bg-green-50 border border-green-200 rounded-card p-4 text-center">
            <p className="text-green-800">
              Check your email for a login link.
            </p>
          </div>
        ) : (
          <form onSubmit={handleLogin} className="mt-8 space-y-6">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-navy"
              >
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-ember focus:border-ember text-navy"
                placeholder="you@yourbusiness.com"
              />
            </div>
            <button
              type="submit"
              className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-ember hover:bg-ember-dark active:scale-[0.98] transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ember"
            >
              Send Magic Link
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
