// Main application logic
const App = {
  // Initialize the application
  init() {
    this.setupEventListeners();
    this.checkAuthStatus();
    
    // Set up automatic refresh for deployments tab
    this.setupAutoRefresh();
  },

  // Set up event listeners
  setupEventListeners() {
    // Authentication
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', this.handleLogin.bind(this));
    }

    const registerForm = document.getElementById('register-form');
    if (registerForm) {
      registerForm.addEventListener('submit', this.handleRegister.bind(this));
    }

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', this.handleLogout.bind(this));
    }

    const joinOrgForm = document.getElementById('join-org-form');
    if (joinOrgForm) {
      joinOrgForm.addEventListener('submit', this.handleJoinOrg.bind(this));
    }

    // Organizations
    const createOrgForm = document.getElementById('create-org-form');
    if (createOrgForm) {
      createOrgForm.addEventListener('submit', this.handleCreateOrg.bind(this));
    }

    // Clusters
    const createClusterForm = document.getElementById('create-cluster-form');
    if (createClusterForm) {
      createClusterForm.addEventListener('submit', this.handleCreateCluster.bind(this));
    }

    // Deployments
    const createDeploymentForm = document.getElementById('create-deployment-form');
    if (createDeploymentForm) {
      createDeploymentForm.addEventListener('submit', this.handleCreateDeployment.bind(this));
    }

    // Navigation and tabs
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
    });
  },

  // Check authentication status and update UI
  checkAuthStatus() {
    const authContainer = document.querySelector('.auth-container');
    const appContainer = document.querySelector('.app-container');
    const navUserName = document.getElementById('nav-username');

    if (API.isAuthenticated()) {
      if (authContainer) authContainer.classList.add('hidden');
      if (appContainer) {
        appContainer.classList.remove('hidden');
        this.loadDashboard();
      }
      if (navUserName) navUserName.textContent = API.user.username;
    } else {
      if (authContainer) authContainer.classList.remove('hidden');
      if (appContainer) appContainer.classList.add('hidden');
      this.switchAuthTab('login');
    }
  },

  // Switch between login and registration tabs
  switchAuthTab(tabName) {
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (tabName === 'login') {
      loginTab.classList.add('active');
      registerTab.classList.remove('active');
      loginForm.classList.remove('hidden');
      registerForm.classList.add('hidden');
    } else {
      loginTab.classList.remove('active');
      registerTab.classList.add('active');
      loginForm.classList.add('hidden');
      registerForm.classList.remove('hidden');
    }
  },

  // Switch between dashboard tabs
  switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
      if (tab.dataset.tab === tabName) {
        tab.classList.add('active');
      } else {
        tab.classList.remove('active');
      }
    });

    tabContents.forEach(content => {
      if (content.id === `${tabName}-content`) {
        content.classList.add('active');
        if (tabName === 'organizations') this.loadOrganizations();
        if (tabName === 'clusters') {
          this.loadClusters();
          this.loadOrganizationsForClusterForm();
        }
        if (tabName === 'deployments') {
          this.loadDeployments();
          this.loadClustersForDeploymentForm();
          this.loadDeploymentsForDependencySelect();
          // Immediately do one refresh to ensure we have the latest status
          setTimeout(() => this.refreshDeployments(), 1000);
        }
      } else {
        content.classList.remove('active');
      }
    });
  },

  // Load dashboard data
  async loadDashboard() {
    this.switchTab('organizations');
  },

  // Display an alert message
  showAlert(message, type = 'error') {
    const alertContainer = document.getElementById('alert-container');
    
    // Clear existing alerts
    alertContainer.innerHTML = '';
    
    // Create new alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      alert.remove();
    }, 5000);
  },

  // Handle login form submission
  async handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    try {
      const response = await API.login(username, password);
      
      // Get user details
      API.setAuth(response.access_token, { username });
      
      this.showAlert('Login successful!', 'success');
      this.checkAuthStatus();
    } catch (error) {
      this.showAlert(error.message);
    }
  },

  // Handle registration form submission
  async handleRegister(event) {
    event.preventDefault();
    
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    try {
      await API.register(username, email, password);
      
      this.showAlert('Registration successful! You can now log in.', 'success');
      this.switchAuthTab('login');
    } catch (error) {
      this.showAlert(error.message);
    }
  },

  // Handle logout
  handleLogout() {
    API.clearAuth();
    this.checkAuthStatus();
    this.showAlert('You have been logged out.', 'success');
  },

  // Handle joining an organization
  async handleJoinOrg(event) {
    event.preventDefault();
    
    const inviteCode = document.getElementById('invite-code').value;
    
    try {
      const org = await API.joinOrganization(inviteCode);
      
      this.showAlert(`You have joined the organization "${org.name}"!`, 'success');
      this.loadOrganizations();
    } catch (error) {
      this.showAlert(error.message);
    }
  },

  // Load and display organizations
  async loadOrganizations() {
    const orgList = document.getElementById('org-list');
    const loader = document.createElement('div');
    loader.className = 'loader';
    orgList.innerHTML = '';
    orgList.appendChild(loader);
    
    try {
      const organizations = await API.getOrganizations();
      
      orgList.innerHTML = '';
      
      if (organizations.length === 0) {
        orgList.innerHTML = '<p>You are not a member of any organizations yet.</p>';
        return;
      }
      
      const table = document.createElement('table');
      table.innerHTML = `
        <thead>
          <tr>
            <th>Name</th>
            <th>Invite Code</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody></tbody>
      `;
      
      const tbody = table.querySelector('tbody');
      
      organizations.forEach(org => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${org.name}</td>
          <td>${org.invite_code}</td>
          <td class="actions">
            <button class="regenerate-invite" data-id="${org.id}">New Invite</button>
            <button class="view-clusters" data-id="${org.id}">View Clusters</button>
          </td>
        `;
        tbody.appendChild(tr);
      });
      
      orgList.appendChild(table);
      
      // Add event listeners for organization actions
      document.querySelectorAll('.regenerate-invite').forEach(btn => {
        btn.addEventListener('click', () => this.regenerateInviteCode(btn.dataset.id));
      });
      
      document.querySelectorAll('.view-clusters').forEach(btn => {
        btn.addEventListener('click', () => {
          document.getElementById('create-cluster-org').value = btn.dataset.id;
          this.switchTab('clusters');
        });
      });
    } catch (error) {
      orgList.innerHTML = `<p class="alert alert-error">Error loading organizations: ${error.message}</p>`;
    }
  },

  // Handle creating a new organization
  async handleCreateOrg(event) {
    event.preventDefault();
    
    const name = document.getElementById('org-name').value;
    
    try {
      await API.createOrganization(name);
      
      document.getElementById('org-name').value = '';
      this.showAlert(`Organization "${name}" created successfully!`, 'success');
      this.loadOrganizations();
    } catch (error) {
      this.showAlert(error.message);
    }
  },

  // Regenerate invite code for an organization
  async regenerateInviteCode(orgId) {
    try {
      await API.regenerateInviteCode(orgId);
      
      this.showAlert('Invite code regenerated successfully!', 'success');
      this.loadOrganizations();
    } catch (error) {
      this.showAlert(error.message);
    }
  },

  // New function to load organizations for the cluster form
  async loadOrganizationsForClusterForm() {
    const orgSelect = document.getElementById('create-cluster-org');
    if (!orgSelect) return;
    
    try {
      const organizations = await API.getOrganizations();
      orgSelect.innerHTML = '';
      
      if (organizations.length === 0) {
        const option = document.createElement('option');
        option.textContent = "No organizations available";
        option.disabled = true;
        option.selected = true;
        orgSelect.appendChild(option);
        return;
      }
      
      organizations.forEach(org => {
        const option = document.createElement('option');
        option.value = org.id;
        option.textContent = org.name;
        orgSelect.appendChild(option);
      });
      
      // Select the first organization by default
      if (organizations.length > 0 && !orgSelect.value) {
        orgSelect.value = organizations[0].id;
      }
    } catch (error) {
      this.showAlert('Error loading organizations', 'error');
      
      const option = document.createElement('option');
      option.textContent = "Error loading organizations";
      option.disabled = true;
      option.selected = true;
      orgSelect.appendChild(option);
    }
  },

  // Load and display clusters
  async loadClusters() {
    const clusterList = document.getElementById('cluster-list');
    const loader = document.createElement('div');
    loader.className = 'loader';
    clusterList.innerHTML = '';
    clusterList.appendChild(loader);
    
    try {
      const clusters = await API.getClusters();
      
      clusterList.innerHTML = '';
      
      if (clusters.length === 0) {
        clusterList.innerHTML = '<p>No clusters found.</p>';
        return;
      }
      
      const table = document.createElement('table');
      table.innerHTML = `
        <thead>
          <tr>
            <th>Name</th>
            <th>Total RAM (GB)</th>
            <th>Total CPU (cores)</th>
            <th>Total GPU</th>
            <th>Available RAM (GB)</th>
            <th>Available CPU (cores)</th>
            <th>Available GPU</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody></tbody>
      `;
      
      const tbody = table.querySelector('tbody');
      
      clusters.forEach(cluster => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${cluster.name}</td>
          <td>${cluster.total_ram}</td>
          <td>${cluster.total_cpu}</td>
          <td>${cluster.total_gpu}</td>
          <td>${cluster.available_ram}</td>
          <td>${cluster.available_cpu}</td>
          <td>${cluster.available_gpu}</td>
          <td class="actions">
            <button class="create-deployment" data-id="${cluster.id}">Deploy</button>
          </td>
        `;
        tbody.appendChild(tr);
      });
      
      clusterList.appendChild(table);
      
      // Add event listeners for cluster actions
      document.querySelectorAll('.create-deployment').forEach(btn => {
        btn.addEventListener('click', () => {
          document.getElementById('deployment-cluster').value = btn.dataset.id;
          this.switchTab('deployments');
        });
      });
    } catch (error) {
      clusterList.innerHTML = `<p class="alert alert-error">Error loading clusters: ${error.message}</p>`;
    }
  },

  // Handle creating a new cluster
  async handleCreateCluster(event) {
    event.preventDefault();
    
    const name = document.getElementById('cluster-name').value;
    const totalRam = parseFloat(document.getElementById('cluster-ram').value);
    const totalCpu = parseFloat(document.getElementById('cluster-cpu').value);
    const totalGpu = parseFloat(document.getElementById('cluster-gpu').value);
    const organizationId = parseInt(document.getElementById('create-cluster-org').value);
    
    try {
      await API.createCluster(name, totalRam, totalCpu, totalGpu, organizationId);
      
      document.getElementById('cluster-name').value = '';
      document.getElementById('cluster-ram').value = '';
      document.getElementById('cluster-cpu').value = '';
      document.getElementById('cluster-gpu').value = '';
      
      this.showAlert(`Cluster "${name}" created successfully!`, 'success');
      this.loadClusters();
    } catch (error) {
      this.showAlert(error.message);
    }
  },

  // Load and display deployments
  async loadDeployments() {
    const deploymentList = document.getElementById('deployment-list');
    const loader = document.createElement('div');
    loader.className = 'loader';
    deploymentList.innerHTML = '';
    deploymentList.appendChild(loader);
    
    try {
      const deployments = await API.getDeployments();
      
      deploymentList.innerHTML = '';
      
      if (deployments.length === 0) {
        deploymentList.innerHTML = '<p>No deployments found.</p>';
        return;
      }
      
      const statusIndicator = document.createElement('div');
      statusIndicator.className = 'flex flex-between mb-1';
      statusIndicator.innerHTML = `
        <div></div>
        <div class="flex flex-center">
          <small>Live updates</small>
          <span class="live-indicator"></span>
        </div>
      `;
      deploymentList.appendChild(statusIndicator);
      
      const table = document.createElement('table');
      table.innerHTML = `
        <thead>
          <tr>
            <th>Name</th>
            <th>Docker Image</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Required RAM (GB)</th>
            <th>Required CPU (cores)</th>
            <th>Required GPU</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody></tbody>
      `;
      
      const tbody = table.querySelector('tbody');
      
      deployments.forEach(deployment => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${deployment.name}</td>
          <td>${deployment.docker_image}</td>
          <td><span class="badge badge-${deployment.status.toLowerCase()}">${deployment.status}</span></td>
          <td>${this.getPriorityLabel(deployment.priority)}</td>
          <td>${deployment.required_ram}</td>
          <td>${deployment.required_cpu}</td>
          <td>${deployment.required_gpu}</td>
          <td class="actions">
            ${this.getDeploymentActions(deployment)}
          </td>
        `;
        tbody.appendChild(tr);
      });
      
      deploymentList.appendChild(table);
      
      // Add event listeners for deployment actions
      document.querySelectorAll('.start-deployment').forEach(btn => {
        btn.addEventListener('click', () => this.startDeployment(btn.dataset.id));
      });
      
      document.querySelectorAll('.stop-deployment').forEach(btn => {
        btn.addEventListener('click', () => this.stopDeployment(btn.dataset.id));
      });
      
      document.querySelectorAll('.cancel-deployment').forEach(btn => {
        btn.addEventListener('click', () => this.cancelDeployment(btn.dataset.id));
      });
      
      document.querySelectorAll('.delete-deployment').forEach(btn => {
        btn.addEventListener('click', () => this.deleteDeployment(btn.dataset.id));
      });
    } catch (error) {
      deploymentList.innerHTML = `<p class="alert alert-error">Error loading deployments: ${error.message}</p>`;
    }
    
    // Also update the cluster select
    this.loadClustersForDeploymentForm();
    
    // Add dependency selection for creating deployments
    this.loadDeploymentsForDependencySelect();
  },

  // Load clusters for the deployment form
  async loadClustersForDeploymentForm() {
    const clusterSelect = document.getElementById('deployment-cluster');
    if (!clusterSelect) return;
    
    try {
      const clusters = await API.getClusters();
      clusterSelect.innerHTML = '';
      
      if (clusters.length === 0) {
        const option = document.createElement('option');
        option.textContent = "No clusters available";
        option.disabled = true;
        option.selected = true;
        clusterSelect.appendChild(option);
        return;
      }
      
      clusters.forEach(cluster => {
        const option = document.createElement('option');
        option.value = cluster.id;
        option.textContent = cluster.name;
        clusterSelect.appendChild(option);
      });
      
      // Select the first cluster by default
      if (clusters.length > 0 && !clusterSelect.value) {
        clusterSelect.value = clusters[0].id;
      }
    } catch (error) {
      this.showAlert('Error loading clusters', 'error');
      
      const option = document.createElement('option');
      option.textContent = "Error loading clusters";
      option.disabled = true;
      option.selected = true;
      clusterSelect.appendChild(option);
    }
  },

  // Get deployment action buttons based on status
  getDeploymentActions(deployment) {
    switch (deployment.status) {
      case 'pending':
        return `
          <button class="start-deployment" data-id="${deployment.id}">Start</button>
          <button class="cancel-deployment" data-id="${deployment.id}">Cancel</button>
          <button class="delete-deployment" data-id="${deployment.id}">Delete</button>
        `;
      case 'running':
        return `
          <button class="stop-deployment" data-id="${deployment.id}">Stop</button>
          <button class="delete-deployment" data-id="${deployment.id}">Delete</button>
        `;
      default:
        return `
          <button class="delete-deployment" data-id="${deployment.id}">Delete</button>
        `;
    }
  },

  // Get human-readable priority label
  getPriorityLabel(priority) {
    switch (priority) {
      case 1:
        return 'Low';
      case 2:
        return 'Medium';
      case 3:
        return 'High';
      default:
        return 'Unknown';
    }
  },

  // Handle creating a new deployment
  async handleCreateDeployment(event) {
    event.preventDefault();
    
    const name = document.getElementById('deployment-name').value;
    const dockerImage = document.getElementById('deployment-image').value;
    const requiredRam = parseFloat(document.getElementById('deployment-ram').value);
    const requiredCpu = parseFloat(document.getElementById('deployment-cpu').value);
    const requiredGpu = parseFloat(document.getElementById('deployment-gpu').value);
    const priority = parseInt(document.getElementById('deployment-priority').value);
    const clusterId = parseInt(document.getElementById('deployment-cluster').value);
    
    // Get selected dependencies
    const dependencySelect = document.getElementById('deployment-dependencies');
    const dependencyIds = Array.from(dependencySelect.selectedOptions).map(option => parseInt(option.value));
    
    try {
        await API.createDeployment(
            name, 
            dockerImage, 
            requiredRam, 
            requiredCpu, 
            requiredGpu, 
            priority, 
            clusterId,
            dependencyIds
        );
        
        document.getElementById('deployment-name').value = '';
        document.getElementById('deployment-image').value = '';
        document.getElementById('deployment-ram').value = '';
        document.getElementById('deployment-cpu').value = '';
        document.getElementById('deployment-gpu').value = '';
        
        // Clear dependency selection
        if (dependencySelect.multiple) {
            Array.from(dependencySelect.options).forEach(option => {
                option.selected = false;
            });
        }
        
        this.showAlert(`Deployment "${name}" created successfully!`, 'success');
        this.loadDeployments();
    } catch (error) {
        this.showAlert(error.message);
    }
  },

  // Set up automatic refresh for deployment statuses
  setupAutoRefresh() {
    // Refresh deployments every 5 seconds when on the deployments tab
    setInterval(() => {
      const deploymentsTab = document.getElementById('deployments-content');
      // Only refresh if deployments tab is active and user is logged in
      if (deploymentsTab && deploymentsTab.classList.contains('active') && API.isAuthenticated()) {
        this.refreshDeployments();
      }
    }, 5000);
  },
  
  // Refresh deployments without full page reload
  async refreshDeployments() {
    try {
      const deployments = await API.getDeployments();
      
      // Update status badges for existing deployments in the table
      const rows = document.querySelectorAll('#deployment-list table tbody tr');
      
      rows.forEach(row => {
        const deploymentId = row.querySelector('.actions button').dataset.id;
        const deployment = deployments.find(d => d.id == deploymentId);
        
        if (deployment) {
          // Get current status from DOM
          const statusCell = row.querySelector('td:nth-child(3)');
          if (statusCell) {
            const currentStatus = statusCell.textContent.trim();
            
            // If status has changed, apply highlight effect
            if (currentStatus !== deployment.status) {
              // Remove any existing highlight class
              row.classList.remove('highlight-change');
              
              // Force a DOM reflow to restart the animation
              void row.offsetWidth;
              
              // Add the highlight class
              row.classList.add('highlight-change');
            }
            
            // Update status badge
            statusCell.innerHTML = `<span class="badge badge-${deployment.status.toLowerCase()}">${deployment.status}</span>`;
          }
          
          // Update action buttons based on new status
          const actionsCell = row.querySelector('.actions');
          if (actionsCell) {
            actionsCell.innerHTML = this.getDeploymentActions(deployment);
            
            // Re-attach event listeners for new buttons
            const startBtn = actionsCell.querySelector('.start-deployment');
            if (startBtn) {
              startBtn.addEventListener('click', () => this.startDeployment(startBtn.dataset.id));
            }
            
            const stopBtn = actionsCell.querySelector('.stop-deployment');
            if (stopBtn) {
              stopBtn.addEventListener('click', () => this.stopDeployment(stopBtn.dataset.id));
            }
            
            const cancelBtn = actionsCell.querySelector('.cancel-deployment');
            if (cancelBtn) {
              cancelBtn.addEventListener('click', () => this.cancelDeployment(cancelBtn.dataset.id));
            }
            
            const deleteBtn = actionsCell.querySelector('.delete-deployment');
            if (deleteBtn) {
              deleteBtn.addEventListener('click', () => this.deleteDeployment(deleteBtn.dataset.id));
            }
          }
        }
      });
      
      // If deployment list is empty but we have deployments, or if there are new deployments, do a full reload
      const currentIds = Array.from(rows).map(row => row.querySelector('.actions button').dataset.id);
      const apiIds = deployments.map(d => d.id.toString());
      
      // Check if we need to do a full reload because we have new deployments or missing ones
      const needsFullReload = 
        (rows.length === 0 && deployments.length > 0) || 
        (apiIds.some(id => !currentIds.includes(id))) ||
        (currentIds.some(id => !apiIds.includes(id)));
        
      if (needsFullReload) {
        this.loadDeployments();
      }
    } catch (error) {
      console.error('Error refreshing deployments:', error);
    }
  },

  // Start a deployment
  async startDeployment(deploymentId) {
    try {
      await API.startDeployment(deploymentId);
      
      this.showAlert('Deployment started successfully!', 'success');
      // Immediately refresh the deployment list to show updated status
      this.refreshDeployments();
      // Also refresh clusters to show updated resource availability
      this.loadClusters();
    } catch (error) {
      this.showAlert(error.message);
    }
  },

  // Stop a deployment
  async stopDeployment(deploymentId) {
    try {
      await API.stopDeployment(deploymentId);
      
      this.showAlert('Deployment stopped successfully!', 'success');
      // Immediately refresh the deployment list to show updated status
      this.refreshDeployments();
      // Also refresh clusters to show updated resource availability
      this.loadClusters();
    } catch (error) {
      this.showAlert(error.message);
    }
  },

  // Cancel a deployment
  async cancelDeployment(deploymentId) {
    try {
      await API.cancelDeployment(deploymentId);
      
      this.showAlert('Deployment cancelled successfully!', 'success');
      // Immediately refresh the deployment list to show updated status
      this.refreshDeployments();
    } catch (error) {
      this.showAlert(error.message);
    }
  },

  // Delete a deployment
  async deleteDeployment(deploymentId) {
    if (!confirm('Are you sure you want to delete this deployment?')) {
      return;
    }
    
    try {
      await API.deleteDeployment(deploymentId);
      
      this.showAlert('Deployment deleted successfully!', 'success');
      // Immediately refresh the deployment list to show updated status
      this.refreshDeployments();
      // Also refresh clusters to show updated resource availability
      this.loadClusters();
    } catch (error) {
      this.showAlert(error.message);
    }
  },

  // New function to load deployments for dependency selection
  async loadDeploymentsForDependencySelect() {
    const dependencySelect = document.getElementById('deployment-dependencies');
    if (!dependencySelect) return;
    
    // Get the priority dropdown so we can link the validation
    const prioritySelect = document.getElementById('deployment-priority');
    
    try {
      const deployments = await API.getDeployments();
      dependencySelect.innerHTML = '';
      
      if (deployments.length === 0) {
        return;
      }
      
      // Add option for each deployment
      deployments.forEach(deployment => {
        // Skip any deployments that are FAILED or CANCELLED
        if (deployment.status === 'FAILED' || deployment.status === 'CANCELLED') {
          return;
        }
        
        const option = document.createElement('option');
        option.value = deployment.id;
        option.textContent = `${deployment.name} (${deployment.status} - ${this.getPriorityLabel(deployment.priority)})`;
        option.dataset.status = deployment.status;
        option.dataset.priority = deployment.priority;
        dependencySelect.appendChild(option);
      });
      
      // Add event listener to display warnings for high priority with lower priority pending dependencies
      if (prioritySelect) {
        prioritySelect.addEventListener('change', () => this.validateDependencyPriorities());
        dependencySelect.addEventListener('change', () => this.validateDependencyPriorities());
        
        // Initial validation
        this.validateDependencyPriorities();
      }
      
    } catch (error) {
      console.error('Error loading deployments for dependencies:', error);
    }
  },
  
  // Add validation function for high priority deployments
  validateDependencyPriorities() {
    const prioritySelect = document.getElementById('deployment-priority');
    const dependencySelect = document.getElementById('deployment-dependencies');
    const warningElement = document.getElementById('dependency-priority-warning');
    
    // Remove existing warning if present
    if (warningElement) {
      warningElement.remove();
    }
    
    // Only validate if both selects exist and high priority is selected
    if (!prioritySelect || !dependencySelect || prioritySelect.value !== '3') {
      return;
    }
    
    // Check all selected dependencies
    const selectedOptions = Array.from(dependencySelect.selectedOptions);
    const lowerPriorityPending = selectedOptions.filter(option => 
      option.dataset.status === 'pending' && parseInt(option.dataset.priority) < 3
    );
    
    // Create warning if there are violations
    if (lowerPriorityPending.length > 0) {
      const warning = document.createElement('div');
      warning.id = 'dependency-priority-warning';
      warning.className = 'alert alert-warning';
      warning.textContent = 'Warning: High priority deployments cannot depend on lower priority pending deployments. Some selected dependencies may be rejected.';
      
      // Insert after the dependencies select
      dependencySelect.parentNode.insertBefore(warning, dependencySelect.nextSibling);
    }
  },
};

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  App.init();
}); 