"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../utils/AuthProvider";
import { loginUser } from "../utils/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage("");

    try {
      const res = await loginUser(email, password);
      
      if (res.error) {
        setMessage(res.error);
      } else {
        // Pass refresh token to the auth context login function
        login(res.token, res.user_id, res.refreshToken);
        setMessage("✅ Login successful!");
        
        // Small delay to show success message, then redirect will happen automatically
        setTimeout(() => {
          router.push('/');
        }, 1000);
      }
    } catch (error) {
      console.error('Login error:', error);
      setMessage("An unexpected error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="bg-white shadow-lg rounded-2xl p-8 w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-white font-bold text-xl">UC</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Welcome back</h2>
          <p className="text-gray-600 mt-2">Sign in to your UniCom account</p>
        </div>
        
        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              placeholder="you@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
              required
              disabled={isLoading}
            />
          </div>
          
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
              required
              disabled={isLoading}
            />
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-orange-600 hover:bg-orange-700 disabled:bg-orange-400 text-white py-3 px-4 rounded-lg font-medium transition-colors focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 text-sm"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Signing in...
              </div>
            ) : (
              'Sign in to UniCom'
            )}
          </button>
        </form>
        
        {message && (
          <div className={`mt-4 p-3 rounded-lg text-sm text-center ${
            message.includes('✅') 
              ? 'bg-green-50 text-green-800 border border-green-200' 
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {message}
          </div>
        )}
        
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{' '}
            <Link
              href="/register"
              className="text-orange-600 hover:text-orange-500 font-medium"
            >
              Create account
            </Link>
          </p>
        </div>
        
        <div className="mt-4 text-center">
          <Link
            href="/forgot-password"
            className="text-sm text-orange-600 hover:text-orange-500"
          >
            Forgot your password?
          </Link>
        </div>
      </div>
    </div>
  );
}