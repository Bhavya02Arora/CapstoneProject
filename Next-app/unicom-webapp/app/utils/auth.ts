// utils/auth.ts
import infra_config from '../../public/infra_config.json';

const API_URL: string = infra_config.api_url;

// Authentication functions
export async function registerUser(email: string, password: string) {
  try {
    const res = await fetch(`${API_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      return { error: data.error || `Registration failed: ${res.status}` };
    }
    
    return data;
  } catch (error) {
    console.error('Register error:', error);
    return { error: 'Network error during registration' };
  }
}

export async function verifyUser(email: string, code: string) {
  try {
    const res = await fetch(`${API_URL}/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code }),
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      return { error: data.error || `Verification failed: ${res.status}` };
    }
    
    return data;
  } catch (error) {
    console.error('Verify error:', error);
    return { error: 'Network error during verification' };
  }
}

export async function loginUser(email: string, password: string) {
  try {
    console.log('Attempting login with:', { email, api_url: API_URL });
    
    const res = await fetch(`${API_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    
    console.log('Login response status:', res.status);
    
    const data = await res.json();
    console.log('Login response data:', data);
    
    if (!res.ok) {
      return { error: data.error || `Login failed: ${res.status}` };
    }
    
    // Ensure we have the required fields
    if (!data.token) {
      console.error('No token in response:', data);
      return { error: 'Invalid response from server - no token received' };
    }
    
    return {
      token: data.token,
      user_id: data.user_id,
      message: data.message
    };
  } catch (error) {
    console.error('Login network error:', error);
    return { error: 'Network error during login' };
  }
}

// Authentication state management
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

export function getUserId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('user_id');
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

export function setAuthData(token: string, userId: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('token', token);
  localStorage.setItem('user_id', userId);
}

export function clearAuthData(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('token');
  localStorage.removeItem('user_id');
}

// Protected route function
export function redirectToLoginIfNotAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  
  if (!isAuthenticated()) {
    window.location.href = '/login';
    return true;
  }
  return false;
}

// API request helper with authentication
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken();
  
  if (!token) {
    throw new Error('No authentication token found');
  }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  // Handle 401 responses globally
  if (response.status === 401) {
    clearAuthData();
    window.location.href = '/login';
    throw new Error('Authentication expired');
  }

  return response;
}
