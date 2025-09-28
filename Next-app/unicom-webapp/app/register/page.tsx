"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import infraConfig from "../../public/infra_config.json";
export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState<"register" | "verify">("register");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const API_URL = infraConfig.api_url;

  const handleRegister = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (res.ok) {
        setStep("verify");
      } else {
        setError(data.error || "Registration failed");
      }
    } catch {
      setError("Server error");
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code }),
      });
      const data = await res.json();
      if (res.ok) {
        router.push("/login");
      } else {
        setError(data.error || "Verification failed");
      }
    } catch {
      setError("Server error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center h-screen bg-gray-100">
      <div className="bg-white shadow-lg rounded-2xl p-8 w-full max-w-md">
        <h2 className="text-2xl font-bold text-center mb-6">
          {step === "register" ? "Register" : "Verify Email"}
        </h2>

        {error && (
          <div className="bg-red-100 text-red-700 p-2 rounded mb-4">
            {error}
          </div>
        )}

        {step === "register" && (
          <>
            <input
              type="email"
              placeholder="RIT Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border p-2 rounded mb-4"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border p-2 rounded mb-4"
            />
            <button
              onClick={handleRegister}
              disabled={loading}
              className="w-full bg-orange-600 text-white py-2 rounded hover:bg-orange-700"
            >
              {loading ? "Registering..." : "Register"}
            </button>
          </>
        )}

        {step === "verify" && (
          <>
            <p className="text-gray-600 mb-2">
              A verification code has been sent to <b>{email}</b>
            </p>
            <input
              type="text"
              placeholder="Verification Code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full border p-2 rounded mb-4"
            />
            <button
              onClick={handleVerify}
              disabled={loading}
              className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700"
            >
              {loading ? "Verifying..." : "Verify"}
            </button>
          </>
        )}

        <p className="mt-4 text-sm text-center">
          Already have an account?{" "}
          <a href="/login" className="text-orange-600 hover:underline">
            Login
          </a>
        </p>
      </div>
    </div>
  );
}
