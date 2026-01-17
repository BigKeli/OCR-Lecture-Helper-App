import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { Injectable } from '@angular/core';

//setup authTokens not neccessary though

@Injectable({
  providedIn: 'root'
})
export class AxiosConfigService {
  private axiosInstance: AxiosInstance;

  constructor() {
    this.axiosInstance = this.createAxiosInstance();
    this.setupInterceptors();
  }

  private createAxiosInstance(): AxiosInstance {
    return axios.create({
      baseURL: 'http://localhost:3000/api',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'X-App-Version': '1.0.0'
      }
    });
  }

  private setupInterceptors(): void {
    // Request Interceptor - Updated types
    this.axiosInstance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Add auth token
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add timestamp for cache busting
        if (config.method === 'get') {
          config.params = { ...config.params, _t: Date.now() };
        }

        console.log(`🚀 ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error: AxiosError) => {
        console.error('Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response Interceptor
    this.axiosInstance.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
        return response;
      },
      (error: AxiosError) => {
        console.error(`❌ ${error.config?.method?.toUpperCase()} ${error.config?.url} - ${error.response?.status}`);
        
        // Handle specific error cases
        this.handleErrorResponse(error);
        
        return Promise.reject(error);
      }
    );
  }

  private handleErrorResponse(error: AxiosError): void {
    switch (error.response?.status) {
      case 401:
        localStorage.removeItem('authToken');
        window.location.href = '/login';
        break;
      case 403:
        console.error('Access denied');
        break;
      case 404:
        console.error('Resource not found');
        break;
      case 413:
        console.error('File too large');
        break;
      case 500:
        console.error('Server error');
        break;
      default:
        console.error('Unknown error:', error.message);
    }
  }

  // Get the configured axios instance
  getInstance(): AxiosInstance {
    return this.axiosInstance;
  }

  // Helper methods for different request types
  async get<T = any>(url: string, config?: InternalAxiosRequestConfig): Promise<T> {
    try {
      const response = await this.axiosInstance.get<T>(url, config);
      return response.data;
    } catch (error) {
      throw this.formatError(error);
    }
  }

  async post<T = any>(url: string, data?: any, config?: InternalAxiosRequestConfig): Promise<T> {
    try {
      const response = await this.axiosInstance.post<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw this.formatError(error);
    }
  }

  async put<T = any>(url: string, data?: any, config?: InternalAxiosRequestConfig): Promise<T> {
    try {
      const response = await this.axiosInstance.put<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw this.formatError(error);
    }
  }

  async patch<T = any>(url: string, data?: any, config?: InternalAxiosRequestConfig): Promise<T> {
    try {
      const response = await this.axiosInstance.patch<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw this.formatError(error);
    }
  }

  async delete<T = any>(url: string, config?: InternalAxiosRequestConfig): Promise<T> {
    try {
      const response = await this.axiosInstance.delete<T>(url, config);
      return response.data;
    } catch (error) {
      throw this.formatError(error);
    }
  }

  // Upload with progress tracking
  async uploadWithProgress<T = any>(
    url: string, 
    data: FormData, 
    onProgress?: (progress: number) => void
  ): Promise<T> {
    try {
      const response = await this.axiosInstance.post<T>(url, data, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        }
      });
      return response.data;
    } catch (error) {
      throw this.formatError(error);
    }
  }

  // Download file
  async downloadFile(url: string, filename?: string): Promise<Blob> {
    try {
      const response = await this.axiosInstance.get(url, {
        responseType: 'blob'
      });

      // Create download link if filename provided
      if (filename) {
        const blob = new Blob([response.data]);
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
      }
      
      return response.data;
    } catch (error) {
      throw this.formatError(error);
    }
  }

  // Format error for consistent error handling
  private formatError(error: any): Error {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.message || error.message || 'Unknown error occurred';
      return new Error(message);
    }
    return error;
  }

  // Set auth token
  setAuthToken(token: string): void {
    localStorage.setItem('authToken', token);
    this.axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  // Remove auth token
  removeAuthToken(): void {
    localStorage.removeItem('authToken');
    delete this.axiosInstance.defaults.headers.common['Authorization'];
  }

  // Update base URL
  setBaseURL(baseURL: string): void {
    this.axiosInstance.defaults.baseURL = baseURL;
  }
}