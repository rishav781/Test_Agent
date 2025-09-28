document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');

            // Remove active class from all tabs
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Add active class to clicked tab
            this.classList.add('active');
            document.getElementById(tabName + '-tab').classList.add('active');
        });
    });

    // File upload functionality
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('image');
    const uploadLink = document.querySelector('.upload-link');

    // Click to browse files
    uploadArea.addEventListener('click', function() {
        imageInput.click();
    });

    uploadLink.addEventListener('click', function(e) {
        e.stopPropagation();
        imageInput.click();
    });

    // File input change
    imageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            updateUploadArea(file.name);
        }
    });

    // Drag and drop functionality
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.type.startsWith('image/')) {
                imageInput.files = files;
                updateUploadArea(file.name);
            } else {
                alert('Please drop an image file.');
            }
        }
    });

    function updateUploadArea(filename) {
        const uploadContent = uploadArea.querySelector('.upload-content');
        uploadContent.innerHTML = `
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C4.9 2 4.01 2.9 4.01 4L4 20C4 21.1 4.89 22 5.99 22H18C19.1 22 20 21.1 20 20V8L14 2ZM18 20H6V4H13V9H18V20Z" fill="#10b981"/>
            </svg>
            <p><strong>${filename}</strong> selected</p>
            <p class="upload-hint">Click to change file or drag a new one</p>
        `;
    }

    // Generate button functionality
    const generateBtn = document.getElementById('generateBtn');
    // Full-page loading overlay removed; keep only button spinner
    const resultsSection = document.getElementById('results-section');
    const scenariosSection = document.getElementById('scenarios-section');
    const resultsContent = document.getElementById('results-content');

    // Global variables
    let lastGeneratedResults = null;
    let availableScenarios = [];
    // Track accepted test cases across renders (by id or fallback index key)
    let acceptedTestCases = new Set();

    // Get references to main sections
    const inputSection = document.querySelector('.card');
    const stepper = document.querySelector('.stepper');

    generateBtn.addEventListener('click', async function(e) {
        e.preventDefault();

        // Check which tab is active
        const activeTab = document.querySelector('.tab-content.active');
        const isDescriptionTab = activeTab.id === 'description-tab';

        let formData = new FormData();

        if (isDescriptionTab) {
            // Handle description form
            const description = document.getElementById('description').value.trim();
            if (!description) {
                alert('Please enter a functional description.');
                return;
            }
            formData.append('description', description);
        } else {
            // Handle upload form
            const imageFile = document.getElementById('image').files[0];
            if (!imageFile) {
                alert('Please select an image file.');
                return;
            }
            formData.append('image', imageFile);
        }

    // Show loading state (spinner on button only)
        generateBtn.disabled = true;
        generateBtn.classList.add('loading');
        resultsSection.style.display = 'none';
        scenariosSection.style.display = 'none';

        try {
            // Send request to backend API to get scenarios
            const apiUrl = 'http://localhost:5000/analyze';
            const response = await fetch(apiUrl, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                availableScenarios = result.scenarios || [];
                displayScenarios(availableScenarios);
                
                // Hide input section and show scenarios in full body
                inputSection.style.display = 'none';
                // Keep stepper visible to reflect current phase
                stepper.style.display = 'flex';

                // Hide header on scenarios/results; show only on homepage
                const headerBlock = document.querySelector('.header-block');
                if (headerBlock) headerBlock.style.display = 'none';

                // Update stepper to show analysis phase
                updateStepper(2); // Analysis phase
            } else {
                displayError(result.error || 'An error occurred while analyzing input.');
            }
        } catch (error) {
            displayError('Network error: ' + error.message);
        } finally {
            // Reset button state
            generateBtn.disabled = false;
            generateBtn.classList.remove('loading');
            // No full-page loading overlay
        }
    });

    function updateStepper(activeStep) {
        const steps = document.querySelectorAll('.step');
        steps.forEach((step, index) => {
            if (index + 1 === activeStep) {
                step.classList.remove('inactive');
                step.classList.add('active');
            } else if (index + 1 < activeStep) {
                step.classList.remove('inactive', 'active');
                step.classList.add('completed');
            } else {
                step.classList.remove('active', 'completed');
                step.classList.add('inactive');
            }
        });
    }

    function displayResults(data) {
        resultsSection.style.display = 'block';

        if (data.error) {
            resultsContent.innerHTML = `<div class="error-message">${data.error}</div>`;
            return;
        }

        if (!data.scenarios || data.scenarios.length === 0) {
            resultsContent.innerHTML = '<div class="error-message">No test scenarios were generated. Please try with a different input.</div>';
            return;
        }

        // Calculate statistics
        const totalScenarios = data.scenarios.length;
        const totalTestCases = data.scenarios.reduce((total, scenario) => 
            total + (scenario.test_cases ? scenario.test_cases.length : 0), 0);
        
        const priorityCounts = data.scenarios.reduce((counts, scenario) => {
            if (scenario.test_cases) {
                scenario.test_cases.forEach(testCase => {
                    const priority = (testCase.priority || 'medium').toLowerCase();
                    counts[priority] = (counts[priority] || 0) + 1;
                });
            }
            return counts;
        }, {});

        let html = `
            <div class="results-summary">
                <div class="summary-stats">
                    <div class="stat-item">
                        <div class="stat-number">${totalScenarios}</div>
                        <div class="stat-label">Scenarios</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${totalTestCases}</div>
                        <div class="stat-label">Test Cases</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${priorityCounts.high || 0}</div>
                        <div class="stat-label">High Priority</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${priorityCounts.medium || 0}</div>
                        <div class="stat-label">Medium Priority</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${priorityCounts.low || 0}</div>
                        <div class="stat-label">Low Priority</div>
                    </div>
                </div>
                <div class="summary-meta">
                    <span>Generated on ${new Date(data.generated_at || Date.now()).toLocaleString()}</span>
                    <span>•</span>
                    <span>Input type: ${data.input_type || 'unknown'}</span>
                </div>
            </div>
        `;

        data.scenarios.forEach((scenario, sIndex) => {
            const scenarioId = scenario.id || `SC${String(sIndex + 1).padStart(3, '0')}`;
            html += `
                <div class="scenario-card">
                    <div class="scenario-title">${scenario.title || 'Untitled Scenario'} <span class="id-badge">${scenarioId}</span></div>
                    <div class="scenario-description">${scenario.description || 'No description provided'}</div>
            `;

            if (scenario.preconditions && scenario.preconditions.length > 0) {
                html += `
                    <div class="preconditions">
                        <h4>Preconditions:</h4>
                        <ul>
                            ${scenario.preconditions.map(pre => `<li>${pre}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            if (scenario.test_cases && scenario.test_cases.length > 0) {
                html += '<div class="test-cases">';

                scenario.test_cases.forEach((testCase, tcIndex) => {
                    const tcId = testCase.id || `TC${String(tcIndex + 1).padStart(3, '0')}`;
                    const key = testCase.id ? `id:${testCase.id}` : `idx:${sIndex}-${tcIndex}`;
                    const isAccepted = acceptedTestCases.has(key);
                    const priorityClass = (testCase.priority || 'medium').toLowerCase();
                    html += `
                        <div class="test-case-card ${isAccepted ? 'accepted' : ''}" data-key="${key}">
                            <div class="test-case-header">
                                <div class="test-case-title">${testCase.title || 'Untitled Test Case'} <span class="id-badge">${tcId}</span></div>
                                <div class="test-case-actions">
                                    <div class="test-case-priority ${priorityClass}">${testCase.priority || 'Medium'}</div>
                                    <button type="button" class="accept-btn ${isAccepted ? 'accepted' : ''}" data-key="${key}">${isAccepted ? 'Accepted' : 'Accept'}</button>
                                </div>
                            </div>
                            <div class="test-case-description">${testCase.description || 'No description provided'}</div>
                    `;

                    if (testCase.steps && testCase.steps.length > 0) {
                        html += `
                            <div class="test-case-steps">
                                <h5>Steps:</h5>
                                <ol>
                                    ${testCase.steps.map(step => `<li>${step}</li>`).join('')}
                                </ol>
                            </div>
                        `;
                    }

                    if (testCase.expected_result) {
                        html += `<div class="expected-result"><strong>Expected Result:</strong> ${testCase.expected_result}</div>`;
                    }

                    if (testCase.test_data) {
                        html += `<div class="test-data"><strong>Test Data:</strong> ${testCase.test_data}</div>`;
                    }

                    html += '</div>';
                });

                html += '</div>';
            }

            html += '</div>';
        });

        resultsContent.innerHTML = html;

        // Update Export Accepted button enabled state
        const exportAcceptedBtn2 = document.getElementById('exportAcceptedBtn');
        if (exportAcceptedBtn2) {
            exportAcceptedBtn2.disabled = acceptedTestCases.size === 0;
        }

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Accept button toggle via event delegation in results
    resultsContent.addEventListener('click', function(e) {
        const btn = e.target.closest('.accept-btn');
        if (!btn) return;
        const key = btn.getAttribute('data-key');
        if (!key) return;
        const card = btn.closest('.test-case-card');
        if (acceptedTestCases.has(key)) {
            acceptedTestCases.delete(key);
            btn.classList.remove('accepted');
            btn.textContent = 'Accept';
            if (card) card.classList.remove('accepted');
        } else {
            acceptedTestCases.add(key);
            btn.classList.add('accepted');
            btn.textContent = 'Accepted';
            if (card) card.classList.add('accepted');
        }
        // Update Export Accepted button enabled state after toggle
        const exportAcceptedBtn3 = document.getElementById('exportAcceptedBtn');
        if (exportAcceptedBtn3) {
            exportAcceptedBtn3.disabled = acceptedTestCases.size === 0;
        }
    });

    function displayError(message) {
        resultsSection.style.display = 'block';
        resultsContent.innerHTML = `<div class="error-message">${message}</div>`;
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Export functionality
    // Export Accepted button
    const exportAcceptedBtn = document.getElementById('exportAcceptedBtn');
    if (exportAcceptedBtn) {
        exportAcceptedBtn.addEventListener('click', function() {
            if (!lastGeneratedResults) {
                alert('No test cases to export. Please analyze first.');
                return;
            }
            // If no accepted, do nothing
            if (acceptedTestCases.size === 0) {
                alert('No accepted test cases to export.');
                return;
            }
            const filteredScenarios = (lastGeneratedResults.scenarios || []).map((scenario, sIndex) => {
                const test_cases = (scenario.test_cases || []).filter((tc, tcIndex) => {
                    const key = tc.id ? `id:${tc.id}` : `idx:${sIndex}-${tcIndex}`;
                    return acceptedTestCases.has(key);
                });
                return { ...scenario, test_cases };
            }).filter(sc => sc.test_cases && sc.test_cases.length > 0);

            const dataToExport = { ...lastGeneratedResults, scenarios: filteredScenarios };
            const totalScenarios = dataToExport.scenarios ? dataToExport.scenarios.length : 0;
            const totalTestCases = dataToExport.scenarios ? dataToExport.scenarios.reduce((total, scenario) => total + (scenario.test_cases ? scenario.test_cases.length : 0), 0) : 0;
            const exportData = {
                exported_at: new Date().toISOString(),
                total_scenarios: totalScenarios,
                total_test_cases: totalTestCases,
                accepted_only: true,
                accepted_count: acceptedTestCases.size,
                data: dataToExport
            };
            const dataStr = JSON.stringify(exportData, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(dataBlob);
            link.download = `test-cases-accepted-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }

    // Export All button
    document.getElementById('exportBtn').addEventListener('click', function() {
        if (!lastGeneratedResults) {
            alert('No test cases to export. Please analyze first.');
            return;
        }

        const totalScenarios = lastGeneratedResults.scenarios ? lastGeneratedResults.scenarios.length : 0;
        const totalTestCases = lastGeneratedResults.scenarios ? lastGeneratedResults.scenarios.reduce((total, scenario) => total + (scenario.test_cases ? scenario.test_cases.length : 0), 0) : 0;

        const exportData = {
            exported_at: new Date().toISOString(),
            total_scenarios: totalScenarios,
            total_test_cases: totalTestCases,
            accepted_only: false,
            accepted_count: acceptedTestCases.size,
            data: lastGeneratedResults
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});

        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `test-cases-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // Results back button functionality
    const resultsBackBtn = document.getElementById('resultsBackBtn');
    resultsBackBtn.addEventListener('click', function() {
        resultsSection.style.display = 'none';
        scenariosSection.style.display = 'block';
        const headerBlock2 = document.querySelector('.header-block');
        if (headerBlock2) headerBlock2.style.display = 'none';
        // Keep stepper visible and show analysis phase
        stepper.style.display = 'flex';
        updateStepper(2);
    });

    // Scenarios back button functionality (return to input)
    const scenariosBackBtn = document.getElementById('backBtn');
    if (scenariosBackBtn) {
        scenariosBackBtn.addEventListener('click', function() {
            // Hide scenarios and results; show input & stepper
            scenariosSection.style.display = 'none';
            resultsSection.style.display = 'none';
            inputSection.style.display = 'block';
            stepper.style.display = 'flex';

            // Show header on homepage
            const headerBlock3 = document.querySelector('.header-block');
            if (headerBlock3) headerBlock3.style.display = 'flex';

            // Reset selection state
            selectedScenarios.clear();
            // Reset accepted test cases when going back to input
            if (typeof acceptedTestCases !== 'undefined') {
                acceptedTestCases.clear();
            }
            const selectedEls = document.querySelectorAll('.scenario-item.selected');
            selectedEls.forEach(el => el.classList.remove('selected'));
            updateSelectedCount();

            // Stepper back to Input
            updateStepper(1);
        });
    }

    // Scenario selection functionality
    let selectedScenarios = new Set();

    function displayScenarios(scenarios) {
        const scenariosList = document.getElementById('scenarios-list');
        scenariosList.innerHTML = '';

        scenarios.forEach((scenario, index) => {
            const scenarioElement = document.createElement('div');
            scenarioElement.className = 'scenario-item';
            scenarioElement.dataset.id = index;

            const testCaseCount = scenario.test_cases ? scenario.test_cases.length : 0;

            scenarioElement.innerHTML = `
                <div class="scenario-checkbox"></div>
                <div class="scenario-content">
                    <h4 class="scenario-title">${scenario.title}</h4>
                    <p class="scenario-description">${scenario.description}</p>
                    <div class="scenario-meta">
                        <span class="test-case-count">${testCaseCount} test cases</span>
                    </div>
                </div>
            `;

            scenarioElement.addEventListener('click', function() {
                const scenarioId = parseInt(this.dataset.id);
                if (selectedScenarios.has(scenarioId)) {
                    selectedScenarios.delete(scenarioId);
                    this.classList.remove('selected');
                } else {
                    selectedScenarios.add(scenarioId);
                    this.classList.add('selected');
                }
                updateSelectedCount();
            });

            scenariosList.appendChild(scenarioElement);
        });

        scenariosSection.style.display = 'block';
        updateSelectedCount();
    }

    function updateSelectedCount() {
        const selectedCount = document.getElementById('selectedCount');
        const generateSelectedBtn = document.getElementById('generateSelectedBtn');

        selectedCount.textContent = selectedScenarios.size;
        generateSelectedBtn.disabled = selectedScenarios.size === 0;
    }

    // Generate selected scenarios button
    const generateSelectedBtn = document.getElementById('generateSelectedBtn');
    generateSelectedBtn.addEventListener('click', function() {
        const selectedScenarioData = Array.from(selectedScenarios).map(index => availableScenarios[index]);
        generateTestCases(selectedScenarioData);
    });

    // Generate all scenarios button
    const generateAllBtn = document.getElementById('generateAllBtn');
    generateAllBtn.addEventListener('click', function() {
        generateTestCases(availableScenarios);
    });

    function generateTestCases(scenarios) {
        // Since we already have test cases from analyze, just display them
        const resultData = {
            scenarios: scenarios,
            generated_at: new Date().toISOString(),
            input_type: "selected_scenarios"
        };
        // Reset accepted selections on new generation BEFORE rendering
        acceptedTestCases.clear();

        displayResults(resultData);
        lastGeneratedResults = resultData;
        
    // Hide scenarios section
        scenariosSection.style.display = 'none';

    // Hide header on results
    const headerBlock4 = document.querySelector('.header-block');
    if (headerBlock4) headerBlock4.style.display = 'none';
    // Ensure stepper is visible on results and highlight is updated
    stepper.style.display = 'flex';
        
        // Update stepper to show generation phase
        updateStepper(3);
    }
});