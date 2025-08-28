export interface ApiStats {
  status: string;
  timestamp: string;
  service: string;
  version: string;
  description: string;
  endpoints: {
    docs: string;
    redoc: string;
    weeks: string;
    schedules: string;
  };
  git?: {
    commit?: string;
    branch?: string;
  };
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    // Приоритет: параметр > переменная окружения > автоопределение
    this.baseUrl = baseUrl || 
      process.env.API_BASE_URL || 
      (typeof window !== 'undefined' 
        ? 'http://localhost:8080'  // Browser
        : 'http://medusa-backend:8080'  // Server-side rendering in Docker
      );
  }

  async getStats(): Promise<ApiStats> {
    try {
      const response = await fetch(`${this.baseUrl}/stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to fetch API stats:', error);
      // Возвращаем заглушку в случае ошибки
      return {
        status: 'ERROR',
        timestamp: new Date().toISOString(),
        service: 'Medusa Backend API',
        version: '1.0.0',
        description: 'RESTful API for BSU class schedules management',
        endpoints: {
          docs: '/docs',
          redoc: '/redoc',
          weeks: '/weeks',
          schedules: '/groups/{group_id}/schedules',
        },
      };
    }
  }
}

export const apiClient = new ApiClient();