"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import infra_config from '../../public/infra_config.json'; // Adjust path as needed

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: { id: string } | null;
  login: (token: string, userId: string, refreshToken?: string) => void;
  logout: () => void;
  refreshToken: () => Promise<string | null>;
  isTokenExpired: (token?: string) => boolean;
  getValidToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Public routes that don't require authentication
const PUBLIC_ROUTES = ['/login', '/register', '/verify'];

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<{ id: string } | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  // Token utility functions
  const isTokenExpired = useCallback((token?: string): boolean => {
    try {
      const tokenToCheck = token || localStorage.getItem('token');
      if (!tokenToCheck) return true;

      const payload = JSON.parse(atob(tokenToCheck.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      // Add 5 minute buffer to prevent edge cases
      return payload.exp < (currentTime + 300);
    } catch (error) {
      console.error('Error parsing token:', error);
      return true;
    }
  }, []);

  const refreshToken = useCallback(async (): Promise<string | null> => {
    try {
      const storedRefreshToken = localStorage.getItem('refreshToken');
      if (!storedRefreshToken) {
        console.log('No refresh token found');
        return null;
      }

      console.log('Attempting to refresh token...');
      const response = await fetch(`${infra_config.api_url}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refreshToken: storedRefreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Update stored tokens
        localStorage.setItem('token', data.token);
        if (data.refreshToken) {
          localStorage.setItem('refreshToken', data.refreshToken);
        }
        
        console.log('Token refreshed successfully');
        return data.token;
      } else {
        console.error('Token refresh failed with status:', response.status);
        // If refresh fails, clear all tokens and log out
        logout();
        return null;
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      // On network error, don't automatically log out - might be temporary
      return null;
    }
  }, []);

  const getValidToken = useCallback(async (): Promise<string | null> => {
    let token = localStorage.getItem('token');
    
    if (!token) {
      console.log('No token found');
      return null;
    }

    if (isTokenExpired(token)) {
      console.log('Token expired, attempting refresh...');
      const newToken = await refreshToken();
      if (newToken) {
        return newToken;
      } else {
        console.log('Token refresh failed');
        return null;
      }
    }

    return token;
  }, [isTokenExpired, refreshToken]);

  // Check authentication status on mount and route changes
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Handle route protection
  useEffect(() => {
    if (!isLoading) {
      const isPublicRoute = PUBLIC_ROUTES.includes(pathname);
      
      if (!isAuthenticated && !isPublicRoute) {
        // Redirect to login if not authenticated and trying to access protected route
        router.push('/login');
      } else if (isAuthenticated && isPublicRoute) {
        // Redirect to home if authenticated and trying to access auth pages
        router.push('/');
      }
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const userId = localStorage.getItem('user_id');

      if (token && userId) {
        // Check if token is expired
        if (isTokenExpired(token)) {
          console.log('Token expired during auth check, attempting refresh...');
          const newToken = await refreshToken();
          if (newToken) {
            setIsAuthenticated(true);
            setUser({ id: userId });
          } else {
            // Refresh failed, clear auth state
            setIsAuthenticated(false);
            setUser(null);
            localStorage.removeItem('token');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user_id');
          }
        } else {
          // Token is still valid
          setIsAuthenticated(true);
          setUser({ id: userId });
        }
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = (token: string, userId: string, refreshTokenValue?: string) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user_id', userId);
    if (refreshTokenValue) {
      localStorage.setItem('refreshToken', refreshTokenValue);
    }
    setIsAuthenticated(true);
    setUser({ id: userId });
  };

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user_id');
    setIsAuthenticated(false);
    setUser(null);
    router.push('/login');
  }, [router]);

  // Show loading screen while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading...</p>
        </div>
      </div>
    );
  }

  const contextValue: AuthContextType = {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    refreshToken,
    isTokenExpired,
    getValidToken,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}