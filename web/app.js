document.addEventListener('DOMContentLoaded', () => {
    const projectGrid = document.getElementById('project-grid');
    const refreshBtn = document.getElementById('refresh-projects');
    const detailsSection = document.getElementById('details-section');
    const closeDetailsBtn = document.getElementById('close-details');
    const runEstimateBtn = document.getElementById('run-estimate');
    const projectNameEl = document.getElementById('selected-project-name');
    const configViewer = document.getElementById('config-viewer');
    const estimationResults = document.getElementById('estimation-results');
    const downloadControls = document.getElementById('download-controls');
    const downloadBtn = document.getElementById('download-reports');
    const newProjectBtn = document.getElementById('open-new-project');
    const newProjectModal = document.getElementById('new-project-modal');
    const closeNewProjectBtn = document.getElementById('close-new-project');
    const newProjectForm = document.getElementById('new-project-form');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const toast = document.getElementById('toast');

    // File Upload Elements
    const uploadPartsInput = document.getElementById('upload-parts-input');
    const uploadInventoryInput = document.getElementById('upload-inventory-input');
    const btnUploadParts = document.getElementById('btn-upload-parts');
    const btnUploadInventory = document.getElementById('btn-upload-inventory');

    // Confirm Modal Elements
    const confirmModal = document.getElementById('confirm-modal');
    const confirmTitle = document.getElementById('confirm-title');
    const confirmMessage = document.getElementById('confirm-message');
    const confirmProceedBtn = document.getElementById('confirm-proceed');
    const confirmCancelBtn = document.getElementById('confirm-cancel');
    const closeConfirmBtn = document.getElementById('close-confirm');

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
                    <div class="project-card-header">
                        <h3>${project.name}</h3>
                        <button class="btn-archive" title="Archive Project">📦</button>
                    </div>
                    <p class="material-count">ID: ${project.id}</p>
                `;
                card.onclick = () => showProjectDetails(project.id);
                
                const archiveBtn = card.querySelector('.btn-archive');
                archiveBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    archiveProject(project.id);
                });
                
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
            
            // Try to load existing estimation results
            try {
                const estResponse = await fetch(`/api/projects/${projectId}/estimation`);
                if (estResponse.ok) {
                    const estData = await estResponse.json();
                    renderEstimationResults(estData);
                    downloadControls.classList.remove('hidden');
                } else {
                    // Not estimated yet or error
                    estimationResults.innerHTML = '<p class="placeholder-text">Run estimation to see results here.</p>';
                    downloadControls.classList.add('hidden');
                }
            } catch (e) {
                console.error('Error fetching existing estimation:', e);
                estimationResults.innerHTML = '<p class="placeholder-text">Run estimation to see results here.</p>';
                downloadControls.classList.add('hidden');
            }
            
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
            downloadControls.classList.remove('hidden');
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

    // Download logic
    function downloadReports() {
        const types = [
            { id: 'dl-color', type: 'color' },
            { id: 'dl-grayscale', type: 'grayscale' },
            { id: 'dl-buy', type: 'buy' },
            { id: 'dl-inventory', type: 'inventory' }
        ];

        const selected = types.filter(t => document.getElementById(t.id).checked);

        if (selected.length === 0) {
            showToast('Please select at least one report to download.', 'error');
            return;
        }

        selected.forEach((s, index) => {
            // Use a slight delay between downloads to ensure the browser handles multiple files
            setTimeout(() => {
                const link = document.createElement('a');
                link.href = `/api/projects/${currentProject}/download/${s.type}`;
                link.download = ''; // Let the server headers decide the filename
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }, index * 500);
        });
    }

    // Custom Confirmation Modal Helper
    function showConfirmModal(options) {
        return new Promise((resolve) => {
            const { title, message, confirmText, isDanger } = options;
            
            confirmTitle.textContent = title || 'Confirm Action';
            confirmMessage.textContent = message || 'Are you sure?';
            confirmProceedBtn.textContent = confirmText || 'Confirm';
            
            if (isDanger) {
                confirmProceedBtn.classList.add('btn-danger');
            } else {
                confirmProceedBtn.classList.remove('btn-danger');
            }
            
            confirmModal.classList.remove('hidden');
            
            const cleanup = () => {
                confirmModal.classList.add('hidden');
                confirmProceedBtn.onclick = null;
                confirmCancelBtn.onclick = null;
                closeConfirmBtn.onclick = null;
                confirmModal.onclick = null;
            };
            
            confirmProceedBtn.onclick = () => {
                cleanup();
                resolve(true);
            };
            
            const cancel = () => {
                cleanup();
                resolve(false);
            };
            
            confirmCancelBtn.onclick = cancel;
            closeConfirmBtn.onclick = cancel;
            confirmModal.onclick = (e) => {
                if (e.target === confirmModal) cancel();
            };
        });
    }

    // Archive Project
    async function archiveProject(projectId) {
        const confirmed = await showConfirmModal({
            title: 'Archive Project',
            message: `Are you sure you want to archive project "${projectId}"? This will compress the project and remove it from the active list.`,
            confirmText: 'Archive Project',
            isDanger: true
        });

        if (!confirmed) return;

        try {
            const response = await fetch(`/api/projects/${projectId}/archive`, {
                method: 'POST'
            });
            
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'Failed to archive project');
            }

            showToast('Project archived successfully!');
            loadProjects();
            
            // Close details if the archived project was open
            if (currentProject === projectId) {
                detailsSection.classList.add('hidden');
                downloadControls.classList.add('hidden');
                currentProject = null;
            }
        } catch (error) {
            showToast('Error archiving project: ' + error.message, 'error');
        }
    }

    // Upload Files
    async function uploadProjectFile(file, type) {
        if (!currentProject || !file) return;

        const formData = new FormData();
        formData.append(`${type}_file`, file);

        const btn = type === 'parts' ? btnUploadParts : btnUploadInventory;
        const originalText = btn.textContent;
        btn.disabled = true;
        btn.textContent = 'Uploading...';

        try {
            const response = await fetch(`/api/projects/${currentProject}/upload`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'Upload failed');
            }

            showToast(`${type.charAt(0).toUpperCase() + type.slice(1)} updated successfully!`);
            
            // Refresh config viewer
            showProjectDetails(currentProject);
            
            // Clear estimation results since files changed
            estimationResults.innerHTML = '<p class="placeholder-text text-muted">Files updated. Run estimation to see new results.</p>';
            downloadControls.classList.add('hidden');
            
        } catch (error) {
            showToast('Upload error: ' + error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
            // Reset inputs to allow uploading the same file again if needed
            uploadPartsInput.value = '';
            uploadInventoryInput.value = '';
        }
    }

    // New Project Logic
    async function submitNewProject(e) {
        e.preventDefault();
        const submitBtn = newProjectForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';
        
        try {
            const formData = new FormData(newProjectForm);
            const response = await fetch('/api/projects', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.detail || 'Failed to create project');
            }
            
            showToast('Project created successfully!');
            newProjectModal.classList.add('hidden');
            newProjectForm.reset();
            loadProjects();
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
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
    closeDetailsBtn.onclick = () => {
        detailsSection.classList.add('hidden');
        downloadControls.classList.add('hidden');
    };
    runEstimateBtn.onclick = runEstimate;
    downloadBtn.onclick = downloadReports;
    newProjectBtn.onclick = () => newProjectModal.classList.remove('hidden');
    closeNewProjectBtn.onclick = () => {
        newProjectModal.classList.add('hidden');
        newProjectForm.reset();
    };
    newProjectForm.onsubmit = submitNewProject;

    // File Upload Handlers
    btnUploadParts.onclick = () => uploadPartsInput.click();
    btnUploadInventory.onclick = () => uploadInventoryInput.click();

    uploadPartsInput.onchange = (e) => {
        if (e.target.files.length > 0) {
            uploadProjectFile(e.target.files[0], 'parts');
        }
    };

    uploadInventoryInput.onchange = (e) => {
        if (e.target.files.length > 0) {
            uploadProjectFile(e.target.files[0], 'inventory');
        }
    };

    // Close modal on outside click
    window.onclick = (event) => {
        if (event.target === newProjectModal) {
            newProjectModal.classList.add('hidden');
            newProjectForm.reset();
        }
    };
    // Tab Switching Logic
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
