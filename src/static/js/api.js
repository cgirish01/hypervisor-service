// API utility functions
const API = {
  token: null,
  user: null,

  // Initialize API with stored token if available
  init() {
    this.token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      this.user = JSON.parse(storedUser);
    }
  },

  // Set authentication token and store it
  setAuth(token, user) {
    this.token = token;
    this.user = user;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },

  // Clear authentication token
  clearAuth() {
    this.token = null;
    this.user = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  // Check if user is authenticated
  isAuthenticated() {
    return !!this.token;
  },

  // Get request headers
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json'
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  },

  // Handle API response
  async handleResponse(response) {
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'An error occurred');
    }
    
    return data;
  },

  // Generic API request method
  async request(endpoint, options = {}) {
    try {
      const response = await fetch(endpoint, {
        ...options,
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  },

  // Authentication methods
  async register(username, email, password) {
    return this.request('/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  },

  async login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch('/token', {
      method: 'POST',
      body: formData,
    });

    return await this.handleResponse(response);
  },

  async joinOrganization(inviteCode) {
    return this.request('/join-organization', {
      method: 'POST',
      body: JSON.stringify({ invite_code: inviteCode }),
    });
  },

  // Organization methods
  async getOrganizations() {
    return this.request('/organizations/');
  },

  async createOrganization(name) {
    return this.request('/organizations/', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  },

  async getOrganization(id) {
    return this.request(`/organizations/${id}`);
  },

  async updateOrganization(id, name) {
    return this.request(`/organizations/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ name }),
    });
  },

  async deleteOrganization(id) {
    return this.request(`/organizations/${id}`, {
      method: 'DELETE',
    });
  },

  async regenerateInviteCode(id) {
    return this.request(`/organizations/${id}/regenerate-invite`, {
      method: 'POST',
    });
  },

  // Cluster methods
  async getClusters() {
    return this.request('/clusters/');
  },

  async createCluster(name, totalRam, totalCpu, totalGpu, organizationId) {
    return this.request('/clusters/', {
      method: 'POST',
      body: JSON.stringify({
        name,
        total_ram: totalRam,
        total_cpu: totalCpu,
        total_gpu: totalGpu,
        organization_id: organizationId,
      }),
    });
  },

  async getCluster(id) {
    return this.request(`/clusters/${id}`);
  },

  async updateCluster(id, data) {
    return this.request(`/clusters/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async deleteCluster(id) {
    return this.request(`/clusters/${id}`, {
      method: 'DELETE',
    });
  },

  // Deployment methods
  async getDeployments() {
    return this.request('/deployments/');
  },

  async createDeployment(name, dockerImage, requiredRam, requiredCpu, requiredGpu, priority, clusterId) {
    return this.request('/deployments/', {
      method: 'POST',
      body: JSON.stringify({
        name,
        docker_image: dockerImage,
        required_ram: requiredRam,
        required_cpu: requiredCpu,
        required_gpu: requiredGpu,
        priority,
        cluster_id: clusterId,
      }),
    });
  },

  async getDeployment(id) {
    return this.request(`/deployments/${id}`);
  },

  async updateDeployment(id, data) {
    return this.request(`/deployments/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async deleteDeployment(id) {
    return this.request(`/deployments/${id}`, {
      method: 'DELETE',
    });
  },

  async startDeployment(id) {
    return this.request(`/deployments/${id}/start`, {
      method: 'POST',
    });
  },

  async stopDeployment(id) {
    return this.request(`/deployments/${id}/stop`, {
      method: 'POST',
    });
  },

  async cancelDeployment(id) {
    return this.request(`/deployments/${id}/cancel`, {
      method: 'POST',
    });
  },
};

// Initialize API on page load
document.addEventListener('DOMContentLoaded', function() {
  API.init();
}); 