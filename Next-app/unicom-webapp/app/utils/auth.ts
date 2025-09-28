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


// // utils/auth.ts - Debug version with detailed logging
// import infra_config from '../../public/infra_config.json';
// // const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
// const API_BASE_URL = `${infra_config.api_url}/api/posts`;

// console.log('🔧 API_URL:', API_BASE_URL); // Debug log

// export interface AuthResponse {
//   message?: string;
//   error?: string;
//   user_id?: string;
//   token?: string;
//   refreshToken?: string;
// }

// // Register user with detailed logging
// export const registerUser = async (email: string, password: string): Promise<AuthResponse> => {
//   const url = `${API_BASE_URL}/register`;
//   console.log('🚀 Making register request to:', url);
//   console.log('📝 Request data:', { email, password: '***' });

//   try {
//     const response = await fetch(url, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify({ email, password }),
//     });

//     console.log('📡 Response status:', response.status);
//     console.log('📡 Response ok:', response.ok);

//     const data = await response.json();
//     console.log('📦 Response data:', data);

//     if (!response.ok) {
//       console.log('❌ Request failed:', data.error);
//       return { error: data.error || 'Registration failed' };
//     }

//     console.log('✅ Registration successful');
//     return { message: data.message };
//   } catch (error) {
//     console.error('🔥 Network error in registerUser:', error);
//     console.error('🔥 Error details:', {
//       name: error?.name,
//       message: error?.message,
//       stack: error?.stack
//     });
//     return { error: 'Network error. Please try again.' };
//   }
// };

// // Verify email with detailed logging
// export const verifyEmail = async (email: string, code: string): Promise<AuthResponse> => {
//   const url = `${API_BASE_URL}/verify`;
//   console.log('🚀 Making verify request to:', url);
//   console.log('📝 Request data:', { email, code });

//   try {
//     const response = await fetch(url, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify({ email, code }),
//     });

//     console.log('📡 Response status:', response.status);
//     console.log('📡 Response ok:', response.ok);

//     const data = await response.json();
//     console.log('📦 Response data:', data);

//     if (!response.ok) {
//       console.log('❌ Request failed:', data.error);
//       return { error: data.error || 'Verification failed' };
//     }

//     console.log('✅ Verification successful');
//     return { message: data.message };
//   } catch (error) {
//     console.error('🔥 Network error in verifyEmail:', error);
//     console.error('🔥 Error details:', {
//       name: error?.name,
//       message: error?.message,
//       stack: error?.stack
//     });
//     return { error: 'Network error. Please try again.' };
//   }
// };

// // Login user with detailed logging
// export const loginUser = async (email: string, password: string): Promise<AuthResponse> => {
//   const url = `${API_BASE_URL}/login`;
//   console.log('🚀 Making login request to:', url);
//   console.log('📝 Request data:', { email, password: '***' });

//   try {
//     const response = await fetch(url, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify({ email, password }),
//     });

//     console.log('📡 Response status:', response.status);
//     console.log('📡 Response ok:', response.ok);

//     const data = await response.json();
//     console.log('📦 Response data:', { ...data, token: data.token ? '***' : undefined, refreshToken: data.refreshToken ? '***' : undefined });

//     if (!response.ok) {
//       console.log('❌ Request failed:', data.error);
//       return { error: data.error || 'Login failed' };
//     }

//     console.log('✅ Login successful');
//     return {
//       message: data.message,
//       user_id: data.user_id,
//       token: data.token,
//       refreshToken: data.refreshToken
//     };
//   } catch (error) {
//     console.error('🔥 Network error in loginUser:', error);
//     console.error('🔥 Error details:', {
//       name: error?.name,
//       message: error?.message,
//       stack: error?.stack
//     });
//     return { error: 'Network error. Please try again.' };
//   }
// };

// // Add a simple connectivity test function
// export const testConnection = async (): Promise<boolean> => {
//   try {
//     console.log('🔍 Testing connection to:', API_BASE_URL);
//     const response = await fetch(API_BASE_URL, { method: 'HEAD' });
//     console.log('🔍 Connection test result:', response.status);
//     return response.status < 500; // Consider anything below 500 as "connected"
//   } catch (error) {
//     console.error('🔍 Connection test failed:', error);
//     return false;
//   }
// };