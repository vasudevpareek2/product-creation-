const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Batch {
  id: string;
  name: string;
  description?: string;
  client_id: string;
  source_file: string;
  status: 'pending' | 'stage1_completed' | 'stage2_completed' | 'stage3_completed' | 'failed' | 'completed';
  created_at: string;
  updated_at?: string;
  results?: any;
  error_message?: string;
}

export interface PartnerConfig {
  base_url: string;
  client_id: string;
  region_name?: string;
  visibility_scopes: string[];
  open_slots_until?: string;
  required_inclusion_id?: number;
  vendor_names: string[];
  reseller_partner_id?: number;
  inventory_id?: number;
  margin: number;
  currency: string;
  policy_ids: {
    confirmation_policy_id?: number;
    refund_policy_id?: number;
    cancellation_policy_id?: number;
    payment_term_policy_id?: number;
  };
  vendor_payment_term_policy_id?: number;
  default_variant: {
    booking_type: string;
    inventory_type: string;
    min_passenger_count: number;
    transfer_inclusion: string;
    ticket_inclusion: string;
  };
  booking_settings: {
    enable_send_enquiry: boolean;
    enable_online_booking?: boolean;
    is_ticketed: string;
    time_zone: string;
    min_percentage_amount_to_confirm: number;
  };
  seo_template: {
    meta_title: string;
    meta_description: string;
    og_title: string;
    og_description: string;
  };
  existing_product_activity_overrides: Record<string, string>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Request failed' }));
      throw new Error(error.message || error.detail || 'Request failed');
    }

    return response.json();
  }

  // Batch operations
  async getBatches(): Promise<Batch[]> {
    return this.request<Batch[]>('/api/batch');
  }

  async getBatch(batchId: string): Promise<Batch> {
    return this.request<Batch>(`/api/batch/${batchId}`);
  }

  async createBatch(data: {
    name: string;
    description?: string;
    client_id: string;
    source_file: string;
  }): Promise<Batch> {
    return this.request<Batch>('/api/batch', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async executeStage(
    batchId: string,
    stage: number,
    dryRun: boolean = false,
    configOverrides?: Record<string, any>
  ): Promise<any> {
    return this.request<any>(`/api/batch/${batchId}/execute`, {
      method: 'POST',
      body: JSON.stringify({
        stage,
        dry_run: dryRun,
        config_overrides: configOverrides,
      }),
    });
  }

  async deleteBatch(batchId: string): Promise<void> {
    return this.request<void>(`/api/batch/${batchId}`, {
      method: 'DELETE',
    });
  }

  // Config operations
  async getConfig(partnerId: string): Promise<{ partner_id: string; config: PartnerConfig; created_at: string; updated_at: string }> {
    return this.request<any>(`/api/config/${partnerId}`);
  }

  async saveConfig(partnerId: string, config: PartnerConfig): Promise<any> {
    return this.request<any>(`/api/config/${partnerId}`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async deleteConfig(partnerId: string): Promise<void> {
    return this.request<void>(`/api/config/${partnerId}`, {
      method: 'DELETE',
    });
  }

  async listConfigs(): Promise<{ configs: any[] }> {
    return this.request<any>('/api/config');
  }

  // Upload operations
  async uploadCSV(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/upload/csv`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Upload failed' }));
      throw new Error(error.message || error.detail || 'Upload failed');
    }

    return response.json();
  }

  async uploadExcel(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/upload/excel`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Upload failed' }));
      throw new Error(error.message || error.detail || 'Upload failed');
    }

    return response.json();
  }

  async uploadConfig(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/upload/config`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Upload failed' }));
      throw new Error(error.message || error.detail || 'Upload failed');
    }

    return response.json();
  }

  async uploadToken(token: string): Promise<any> {
    return this.request<any>('/api/upload/token', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  }

  async listUploadedFiles(): Promise<{ files: any[] }> {
    return this.request<any>('/api/upload/files');
  }

  async deleteFile(filename: string): Promise<void> {
    return this.request<void>(`/api/upload/${filename}`, {
      method: 'DELETE',
    });
  }

  // AI operations
  async generateProductDescription(data: {
    product_name: string;
    destination: string;
    activity_type: string;
    duration?: string;
    special_features?: string[];
  }): Promise<any> {
    return this.request<any>('/api/ai/generate-content', {
      method: 'POST',
      body: JSON.stringify({
        content_type: 'product_description',
        input_data: data,
      }),
    });
  }

  async generateVariantName(data: {
    product_name: string;
    variant_details: Record<string, any>;
  }): Promise<any> {
    return this.request<any>('/api/ai/generate-content', {
      method: 'POST',
      body: JSON.stringify({
        content_type: 'variant_name',
        input_data: data,
      }),
    });
  }

  async generateSEOContent(data: {
    product_name: string;
    destination: string;
    activity_type: string;
  }): Promise<any> {
    return this.request<any>('/api/ai/generate-content', {
      method: 'POST',
      body: JSON.stringify({
        content_type: 'seo_meta',
        input_data: data,
      }),
    });
  }

  async suggestProduct(data: {
    destination: string;
    activity_type: string;
    target_audience?: string;
  }): Promise<any> {
    return this.request<any>('/api/ai/suggest-product', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getAIStatus(): Promise<{ available: boolean; configured: boolean; model: string }> {
    return this.request<any>('/api/ai/status');
  }

  // Token capture operations
  async captureTokenInteractive(adminUrl?: string, clientId?: string): Promise<any> {
    const params = new URLSearchParams();
    if (adminUrl) params.append('admin_url', adminUrl);
    if (clientId) params.append('client_id', clientId);

    const response = await fetch(`${this.baseUrl}/api/token/capture-interactive?${params}`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Token capture failed' }));
      throw new Error(error.message || error.detail || 'Token capture failed');
    }

    return response.json();
  }

  async captureTokenFromStorage(cookies: any[], localStorage: Record<string, string>, adminUrl?: string, clientId?: string): Promise<any> {
    const params = new URLSearchParams();
    if (adminUrl) params.append('admin_url', adminUrl);
    if (clientId) params.append('client_id', clientId);

    const response = await fetch(`${this.baseUrl}/api/token/capture-from-storage?${params}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ cookies, localStorage }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Token capture failed' }));
      throw new Error(error.message || error.detail || 'Token capture failed');
    }

    return response.json();
  }

  async validateToken(token: string, adminUrl?: string): Promise<any> {
    const params = new URLSearchParams();
    if (adminUrl) params.append('admin_url', adminUrl);

    const response = await fetch(`${this.baseUrl}/api/token/validate?${params}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Validation failed' }));
      throw new Error(error.message || error.detail || 'Validation failed');
    }

    return response.json();
  }

  async getTokenStatus(): Promise<any> {
    return this.request<any>('/api/token/status');
  }

  // Health check
  async healthCheck(): Promise<any> {
    return this.request<any>('/health');
  }
}

export const apiClient = new ApiClient();