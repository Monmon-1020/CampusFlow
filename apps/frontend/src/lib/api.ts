const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseURL: string;
  private accessToken: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.loadTokenFromStorage();
  }

  private loadTokenFromStorage() {
    this.accessToken = localStorage.getItem('access_token');
  }

  setAccessToken(token: string | null) {
    this.accessToken = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  private getAuthHeaders(): Record<string, string> {
    return this.accessToken ? { Authorization: `Bearer ${this.accessToken}` } : {};
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const authHeaders = this.getAuthHeaders();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...authHeaders,
    };
    
    if (options.headers) {
      Object.assign(headers, options.headers);
    }

    const config: RequestInit = {
      headers,
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        if (response.status === 401) {
          // Token expired, try to refresh
          const refreshed = await this.refreshToken();
          if (refreshed) {
            // Retry the original request
            const newAuthHeaders = this.getAuthHeaders();
            const retryHeaders: Record<string, string> = {
              ...headers,
              ...newAuthHeaders,
            };
            const retryConfig = { ...config, headers: retryHeaders };
            const retryResponse = await fetch(url, retryConfig);
            if (retryResponse.ok) {
              return await retryResponse.json();
            }
          }
          // If refresh failed, clear tokens and redirect to login
          this.clearTokens();
          window.location.href = '/login';
          throw new Error('Authentication failed');
        }
        
        const errorData = await response.json().catch(() => ({ 
          detail: `HTTP ${response.status} ${response.statusText}` 
        }));
        throw new Error(errorData.detail || 'Request failed');
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  private async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) return false;

      const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        this.setAccessToken(data.access_token);
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }
    
    return false;
  }

  private clearTokens() {
    this.accessToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  // Auth methods
  async getGoogleAuthUrl() {
    return this.get<{ url: string }>('/api/auth/google/login');
  }

  // Assignment methods
  async getAssignments(params?: {
    mine?: boolean;
    subject?: string;
    due_soon?: boolean;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.mine) searchParams.append('mine', 'true');
    if (params?.subject) searchParams.append('subject', params.subject);
    if (params?.due_soon) searchParams.append('due_soon', 'true');
    
    const queryString = searchParams.toString();
    return this.get(`/api/assignments/${queryString ? `?${queryString}` : ''}`);
  }

  async getAssignment(id: string) {
    return this.get(`/api/assignments/${id}`);
  }

  async createAssignment(data: any) {
    return this.post('/api/assignments/', data);
  }

  async updateAssignment(id: string, data: any) {
    return this.put(`/api/assignments/${id}`, data);
  }

  async deleteAssignment(id: string) {
    return this.delete(`/api/assignments/${id}`);
  }

  // Assignment log methods
  async getAssignmentLogs(assignmentId?: string) {
    const queryString = assignmentId ? `?assignment_id=${assignmentId}` : '';
    return this.get(`/api/assignments/logs/${queryString}`);
  }

  async createAssignmentLog(data: any) {
    return this.post('/api/assignments/logs/', data);
  }

  async updateAssignmentLog(id: string, data: any) {
    return this.put(`/api/assignments/logs/${id}`, data);
  }

  // Event methods
  async getEvents(params?: {
    week?: boolean;
    category?: string;
    start_date?: string;
    end_date?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.week) searchParams.append('week', 'true');
    if (params?.category) searchParams.append('category', params.category);
    if (params?.start_date) searchParams.append('start_date', params.start_date);
    if (params?.end_date) searchParams.append('end_date', params.end_date);
    
    const queryString = searchParams.toString();
    return this.get(`/api/events/${queryString ? `?${queryString}` : ''}`);
  }

  async getEvent(id: string) {
    return this.get(`/api/events/${id}`);
  }

  async createEvent(data: any) {
    return this.post('/api/events/', data);
  }

  async updateEvent(id: string, data: any) {
    return this.put(`/api/events/${id}`, data);
  }

  async deleteEvent(id: string) {
    return this.delete(`/api/events/${id}`);
  }

  async getEventCategories() {
    return this.get<string[]>('/api/events/categories/');
  }
}

export const apiClient = new ApiClient(API_BASE_URL);