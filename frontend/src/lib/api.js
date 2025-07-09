// API client configuration for Cybercon Melbourne 2025 Speaker Portal

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000;

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.timeout = API_TIMEOUT;
    this.token = localStorage.getItem('token');
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getToken() {
    return this.token || localStorage.getItem('token');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getToken();

    const config = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      timeout: this.timeout,
      ...options,
    };

    // Add authorization header if token exists
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Handle FormData (for file uploads)
    if (options.body instanceof FormData) {
      delete config.headers['Content-Type'];
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Handle token refresh for 401 responses
      if (response.status === 401 && token) {
        this.setToken(null);
        window.location.href = '/login';
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }

      return response;
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  }

  // Authentication endpoints
  async login(email, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.setToken(null);
    }
  }

  async refreshToken() {
    return this.request('/auth/refresh', { method: 'POST' });
  }

  async verifyEmail(token) {
    return this.request('/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  }

  async resetPassword(email) {
    return this.request('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  // User endpoints
  async getProfile() {
    return this.request('/users/profile');
  }

  async updateProfile(userData) {
    return this.request('/users/profile', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  async changePassword(currentPassword, newPassword) {
    return this.request('/users/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
  }

  // Session endpoints
  async getSessions() {
    return this.request('/sessions');
  }

  async getSession(id) {
    return this.request(`/sessions/${id}`);
  }

  async createSession(sessionData) {
    return this.request('/sessions', {
      method: 'POST',
      body: JSON.stringify(sessionData),
    });
  }

  async updateSession(id, sessionData) {
    return this.request(`/sessions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(sessionData),
    });
  }

  async deleteSession(id) {
    return this.request(`/sessions/${id}`, {
      method: 'DELETE',
    });
  }

  async submitSession(id) {
    return this.request(`/sessions/${id}/submit`, {
      method: 'POST',
    });
  }

  async getSessionTypes() {
    return this.request('/sessions/types');
  }

  // File upload endpoints
  async uploadFile(sessionId, file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const token = this.getToken();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const percentComplete = (event.loaded / event.total) * 100;
          onProgress(percentComplete);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (error) {
            resolve(xhr.responseText);
          }
        } else {
          try {
            const error = JSON.parse(xhr.responseText);
            reject(new Error(error.message || `HTTP ${xhr.status}`));
          } catch {
            reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
          }
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Network error'));
      });

      xhr.addEventListener('timeout', () => {
        reject(new Error('Upload timeout'));
      });

      xhr.open('POST', `${this.baseURL}/files/upload`);
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      xhr.timeout = this.timeout;
      xhr.send(formData);
    });
  }

  async downloadFile(fileId) {
    const response = await this.request(`/files/${fileId}/download`);
    return response;
  }

  async deleteFile(fileId) {
    return this.request(`/files/${fileId}`, {
      method: 'DELETE',
    });
  }

  // Question endpoints
  async getQuestions() {
    return this.request('/sessions/questions');
  }

  async askQuestion(sessionId, question, priority = 'normal') {
    return this.request('/sessions/questions', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        question,
        priority,
      }),
    });
  }

  // Notification endpoints
  async getNotifications() {
    return this.request('/notifications');
  }

  async markNotificationRead(id) {
    return this.request(`/notifications/${id}/read`, {
      method: 'POST',
    });
  }

  async getNotificationPreferences() {
    return this.request('/notifications/preferences');
  }

  async updateNotificationPreferences(preferences) {
    return this.request('/notifications/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }

  // Manager endpoints (for managers and admins)
  async getAssignedSessions() {
    return this.request('/approver/sessions');
  }

  async reviewSession(sessionId, status, comments) {
    return this.request(`/approver/sessions/${sessionId}/review`, {
      method: 'POST',
      body: JSON.stringify({ status, comments }),
    });
  }

  async answerQuestion(questionId, answer) {
    return this.request(`/approver/questions/${questionId}/answer`, {
      method: 'POST',
      body: JSON.stringify({ answer }),
    });
  }

  async scheduleSession(sessionId, scheduleData) {
    return this.request(`/approver/sessions/${sessionId}/schedule`, {
      method: 'POST',
      body: JSON.stringify(scheduleData),
    });
  }

  async getRooms() {
    return this.request('/approver/rooms');
  }

  // Admin endpoints
  async getUsers() {
    return this.request('/admin/users');
  }

  async inviteUser(email, role) {
    return this.request('/admin/users/invite', {
      method: 'POST',
      body: JSON.stringify({ email, role }),
    });
  }

  async updateUserRole(userId, role) {
    return this.request(`/admin/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    });
  }

  async getAllSessions() {
    return this.request('/admin/sessions');
  }

  async assignSession(sessionId, managerId) {
    return this.request(`/admin/sessions/${sessionId}/assign`, {
      method: 'POST',
      body: JSON.stringify({ manager_id: managerId }),
    });
  }

  async getFAQs() {
    return this.request('/admin/faqs');
  }

  async createFAQ(faqData) {
    return this.request('/admin/faqs', {
      method: 'POST',
      body: JSON.stringify(faqData),
    });
  }

  async updateFAQ(id, faqData) {
    return this.request(`/admin/faqs/${id}`, {
      method: 'PUT',
      body: JSON.stringify(faqData),
    });
  }

  async deleteFAQ(id) {
    return this.request(`/admin/faqs/${id}`, {
      method: 'DELETE',
    });
  }

  async sendBroadcast(messageData) {
    return this.request('/admin/broadcast', {
      method: 'POST',
      body: JSON.stringify(messageData),
    });
  }

  async getSystemStats() {
    return this.request('/admin/stats');
  }

  async bulkDownload() {
    const response = await this.request('/admin/bulk-download');
    return response;
  }
}

// Create and export a singleton instance
const apiClient = new ApiClient();
export default apiClient;

