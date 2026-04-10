document.addEventListener('DOMContentLoaded', () => {
    const projectGrid = document.getElementById('project-grid');
    const refreshBtn = document.getElementById('refresh-projects');
    const detailsSection = document.getElementById('details-section');
    const closeDetailsBtn = document.getElementById('close-details');
    const runEstimateBtn = document.getElementById('run-estimate');
    const projectNameEl = document.getElementById('selected-project-name');
    const configViewer = document.getElementById('config-viewer');
    const estimationResults = document.getElementById('estimation-results');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const toast = document.getElementById('toast');

    let currentProject = null;

    // Fetch and display projects
    async function loadProjects() {
        projectGrid.innerHTML = '<div class="loader-container"><div class="loader"></div></div>';
        try {
            const response = await fetch('/api/projects');
            const projects = await response.json();
            
            projectGrid.innerHTML = '';
            if (projects.length === 0) {
                projectGrid.innerHTML = '<p class="placeholder-text">No projects found. Use CLI to create one!</p>';
                return;
            }

            projects.forEach(project => {
                const card = document.createElement('div');
                card.className = 'project-card';
                card.innerHTML = `
                    <h3>${project.name}</h3>
                    <p class="material-count">ID: ${project.id}</p>
                `;
                card.onclick = () => showProjectDetails(project.id);
                projectGrid.appendChild(card);
            });
        } catch (error) {
            showToast('Error loading projects: ' + error.message, 'error');
        }
    }

    // Show project details
    async function showProjectDetails(projectId) {
        try {
            const response = await fetch(`/api/projects/${projectId}`);
            const project = await response.json();
            currentProject = projectId;
            
            projectNameEl.textContent = project.name || projectId;
            configViewer.textContent = JSON.stringify(project, null, 2);
            estimationResults.innerHTML = '<p class="placeholder-text">Run estimation to see results here.</p>';
            
            detailsSection.classList.remove('hidden');
        } catch (error) {
            showToast('Error loading details: ' + error.message, 'error');
        }
    }

    // Run estimation
    async function runEstimate() {
        if (!currentProject) return;
        
        runEstimateBtn.disabled = true;
        runEstimateBtn.textContent = 'Estimating...';
        
        try {
            const response = await fetch(`/api/projects/${currentProject}/estimate`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to run estimation');
            }
            
            renderEstimationResults(data);
            showToast('Estimation completed successfully!');
        } catch (error) {
            showToast('Error running estimation: ' + error.message, 'error');
            estimationResults.innerHTML = `<p class="placeholder-text error-text">Error: ${error.message}</p>`;
        } finally {
            runEstimateBtn.disabled = false;
            runEstimateBtn.textContent = 'Run Estimation';
        }
    }

    // Render results table
    function renderEstimationResults(data) {
        if (!data || data.length === 0) {
            estimationResults.innerHTML = '<p class="placeholder-text">No data returned from estimator.</p>';
            return;
        }

        const headers = Object.keys(data[0]);
        let tableHtml = '<table><thead><tr>';
        
        headers.forEach(header => {
            tableHtml += `<th>${header}</th>`;
        });
        
        tableHtml += '</tr></thead><tbody>';
        
        data.forEach(row => {
            tableHtml += '<tr>';
            headers.forEach(header => {
                let val = row[header];
                if (typeof val === 'number') val = val.toFixed(3);
                tableHtml += `<td>${val}</td>`;
            });
            tableHtml += '</tr>';
        });
        
        tableHtml += '</tbody></table>';
        estimationResults.innerHTML = tableHtml;
    }

    // UI Helpers
    function showToast(message, type = 'success') {
        toast.textContent = message;
        toast.style.backgroundColor = type === 'error' ? 'var(--error)' : 'var(--secondary)';
        toast.classList.remove('hidden');
        
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 3000);
    }

    // Event Listeners
    refreshBtn.onclick = loadProjects;
    closeDetailsBtn.onclick = () => detailsSection.classList.add('hidden');
    runEstimateBtn.onclick = runEstimate;

    tabBtns.forEach(btn => {
        btn.onclick = () => {
            const tabId = btn.getAttribute('data-tab');
            
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(`tab-${tabId}`).classList.add('active');
        };
    });

    // Init
    loadProjects();
});
