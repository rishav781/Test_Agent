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

    // API file upload functionality
    const apiUploadArea = document.getElementById('apiUploadArea');
    const apiFileInput = document.getElementById('apiFile');
    const apiUploadLink = document.querySelector('.api-upload-link');

    // Click to browse API files
    apiUploadArea.addEventListener('click', function() {
        apiFileInput.click();
    });

    apiUploadLink.addEventListener('click', function(e) {
        e.stopPropagation();
        apiFileInput.click();
    });

    // API file input change
    apiFileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            updateApiUploadArea(file.name);
        }
    });

    // API file drag and drop functionality
    apiUploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        apiUploadArea.classList.add('dragover');
    });

    apiUploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        apiUploadArea.classList.remove('dragover');
    });

    apiUploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        apiUploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.name.toLowerCase().endsWith('.json')) {
                apiFileInput.files = files;
                updateApiUploadArea(file.name);
            } else {
                alert('Please drop a JSON file.');
            }
        }
    });

    function updateApiUploadArea(filename) {
        const uploadContent = apiUploadArea.querySelector('.upload-content');
        uploadContent.innerHTML = `
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 9H16V11H8V9ZM8 13H16V15H8V13ZM10 17H14V19H10V17ZM20 5H4C3.45 5 3 5.45 3 6V18C3 18.55 3.45 19 4 19H20C20.55 19 21 18.55 21 18V6C21 5.45 20.55 5 20 5ZM19 17H5V7H19V17Z" fill="#10b981"/>
            </svg>
            <p><strong>${filename}</strong> selected</p>
            <p class="upload-hint">Click to change file or drag a new one</p>
        `;
    }

    // Generate button functionality
    const generateBtn = document.getElementById('generateBtn');
    // Full-page loading overlay removed; keep only button spinner
    const resultsSection = document.getElementById('results-section');
    const scenariosSection = document.getElementById('scenario-selection-section');
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
        const isUploadTab = activeTab.id === 'upload-tab';
        const isApiTab = activeTab.id === 'api-tab';
        const isWebsiteTab = activeTab.id === 'website-tab';

        let formData = new FormData();
        let apiUrl = `${window.BACKEND_URL}/analyze`;

        if (isDescriptionTab) {
            // Handle description form
            const description = document.getElementById('description').value.trim();
            if (!description) {
                alert('Please enter a functional description.');
                return;
            }
            formData.append('description', description);
        } else if (isUploadTab) {
            // Handle upload form
            const imageFile = document.getElementById('image').files[0];
            if (!imageFile) {
                alert('Please select an image file.');
                return;
            }
            formData.append('image', imageFile);
        } else if (isApiTab) {
            // Handle API document upload
            const apiFile = document.getElementById('apiFile').files[0];
            if (!apiFile) {
                alert('Please select an API document file.');
                return;
            }
            formData.append('api_file', apiFile);
            apiUrl = `${window.BACKEND_URL}/analyze_api`;
        } else if (isWebsiteTab) {
            // Handle website URL
            let websiteUrl = document.getElementById('websiteUrl').value.trim();
            if (!websiteUrl) {
                alert('Please enter a website URL.');
                return;
            }

            // Auto-add https:// if no protocol is specified
            if (!websiteUrl.startsWith('http://') && !websiteUrl.startsWith('https://')) {
                websiteUrl = 'https://' + websiteUrl;
                // Update the input field to show the full URL
                document.getElementById('websiteUrl').value = websiteUrl;
            }

            // Validate URL format
            try {
                new URL(websiteUrl);
            } catch (e) {
                alert('Please enter a valid URL. The URL will automatically be prefixed with https:// if no protocol is specified.');
                return;
            }
            formData.append('url', websiteUrl);
            apiUrl = `${window.BACKEND_URL}/analyze_website`;
        }

    // Show loading state (spinner on button only)
        generateBtn.disabled = true;
        generateBtn.classList.add('loading');

        // Show specific loading message for website analysis
        if (isWebsiteTab) {
            generateBtn.textContent = 'Analyzing website... (this may take up to 60 seconds)';
        } else {
            generateBtn.textContent = 'Analyzing...';
        }
        resultsSection.style.display = 'none';
        scenariosSection.style.display = 'none';

        try {
            // Send request to backend API with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout

            const response = await fetch(apiUrl, {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            const result = await response.json();

            if (response.ok) {
                // Use the new scenario display function for all workflows
                displayScenarios(result);
            } else {
                displayError(result.error || 'An error occurred while analyzing input.');
            }
        } catch (error) {
            let errorMessage = 'Network error: ' + error.message;

            if (error.name === 'AbortError') {
                if (isWebsiteTab) {
                    errorMessage = 'Website analysis timed out. The website may be slow to respond or the analysis is taking longer than expected. Please try a different URL or try again later.';
                } else {
                    errorMessage = 'Request timed out. Please try again.';
                }
            } else if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Cannot connect to the server. Please check that the backend server is running and try again.';
            } else if (isWebsiteTab && error.message.includes('NetworkError')) {
                errorMessage = 'Cannot access the website. Please check the URL and ensure the website is accessible.';
            }

            displayError(errorMessage);
        } finally {
            // Reset button state
            generateBtn.disabled = false;
            generateBtn.classList.remove('loading');
            generateBtn.textContent = 'Analyze'; // Reset to original text
            // No full-page loading overlay
        }
    });

    function updateStepper(activeStep) {
        console.log('Updating stepper to step:', activeStep);
        const steps = document.querySelectorAll('.step');
        steps.forEach((step, index) => {
            const stepNum = index + 1;
            console.log(`Step ${stepNum} before:`, step.className);
            // Remove all state classes first
            step.classList.remove('active', 'inactive', 'completed');

            // Add the appropriate class
            if (stepNum === activeStep) {
                step.classList.add('active');
            } else if (stepNum < activeStep) {
                step.classList.add('completed');
            } else {
                step.classList.add('inactive');
            }
            console.log(`Step ${stepNum} after:`, step.className);
        });
    }

    function displayResults(data) {
        resultsSection.style.display = 'block';
        updateStepper(4);

        if (data.error) {
            displayError(data.error);
            return;
        }

        if (!data.scenarios || data.scenarios.length === 0) {
            displayError('No test scenarios were generated. Please try with a different input.');
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

        // Add website analysis info if available
        if (data.document_type === 'website' && data.website_info) {
            const info = data.website_info;
            html += `
                <div class="website-analysis-info">
                    <h3>Website Analysis Results</h3>
                    <div class="analysis-grid">
                        <div class="analysis-item">
                            <strong>Website:</strong> <a href="${info.url}" target="_blank">${info.title || info.url}</a>
                        </div>
                        <div class="analysis-item">
                            <strong>Overall Rating:</strong> ${info.overall_rating || 0}/5 ⭐
                        </div>
                        <div class="analysis-item">
                            <strong>API Endpoints Found:</strong> ${info.api_endpoints_found || 0}
                        </div>
                        <div class="analysis-item">
                            <strong>Analyzed At:</strong> ${new Date(info.analyzed_at).toLocaleString()}
                        </div>
                    </div>
                    ${info.report ? `<div class="analysis-report"><h4>Analysis Report:</h4><p>${info.report}</p></div>` : ''}
                    ${info.recommendations && info.recommendations.length > 0 ? `
                        <div class="analysis-recommendations">
                            <h4>Recommendations:</h4>
                            <ul>${info.recommendations.filter(rec => rec != null && rec !== '').map(rec => `<li>${rec}</li>`).join('')}</ul>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // Add API analysis info if available
        if ((data.document_type === 'swagger' || data.document_type === 'postman') && data.api_info) {
            const info = data.api_info;
            html += `
                <div class="api-analysis-info">
                    <h3>API Analysis Results</h3>
                    <div class="analysis-grid">
                        <div class="analysis-item">
                            <strong>API:</strong> ${info.title || 'Unknown API'}
                        </div>
                        <div class="analysis-item">
                            <strong>Endpoints:</strong> ${info.endpoints_count || 0}
                        </div>
                        <div class="analysis-item">
                            <strong>Document Type:</strong> ${data.document_type}
                        </div>
                        <div class="analysis-item">
                            <strong>Parsed At:</strong> ${new Date(info.parsed_at).toLocaleString()}
                        </div>
                    </div>
                    ${info.description ? `<div class="api-description"><p>${info.description}</p></div>` : ''}
                </div>
            `;
        }

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
                            ${scenario.preconditions.filter(pre => pre != null && pre !== '').map(pre => `<li>${pre}</li>`).join('')}
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
                                    ${testCase.steps.filter(step => step != null && step !== '').map(step => `<li>${step}</li>`).join('')}
                                </ol>
                            </div>
                        `;
                    }

                    if (testCase.expected_result) {
                        html += `<div class="expected-result"><strong>Expected Result:</strong> ${testCase.expected_result}</div>`;
                    }

                    if (testCase.test_data && Object.keys(testCase.test_data).length > 0) {
                        html += `<div class="test-data"><strong>Test Data:</strong> ${JSON.stringify(testCase.test_data, null, 2)}</div>`;
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
        // Create a new window with error message instead of showing on current page
        const errorWindow = window.open('', '_blank', 'width=600,height=400,scrollbars=yes,resizable=yes');
        if (errorWindow) {
            errorWindow.document.write(`
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Test Case Generation Error</title>
                    <style>
                        body {
                            font-family: 'Inter', system-ui, Avenir, Helvetica, Arial, sans-serif;
                            background: #F8F9FA;
                            margin: 0;
                            padding: 20px;
                            color: #2B2F35;
                        }
                        .error-container {
                            max-width: 500px;
                            margin: 0 auto;
                            background: white;
                            border: 1px solid #DEE2E6;
                            border-radius: 8px;
                            padding: 24px;
                            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                        }
                        .error-title {
                            color: #DC3545;
                            font-size: 18px;
                            font-weight: 600;
                            margin-bottom: 16px;
                        }
                        .error-message {
                            color: #606872;
                            line-height: 1.5;
                            margin-bottom: 20px;
                        }
                        .close-btn {
                            background: #012B38;
                            color: white;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-weight: 500;
                        }
                        .close-btn:hover {
                            background: #011A20;
                        }
                    </style>
                </head>
                <body>
                    <div class="error-container">
                        <h2 class="error-title">❌ Test Case Generation Error</h2>
                        <div class="error-message">${message}</div>
                        <button class="close-btn" onclick="window.close()">Close Window</button>
                    </div>
                </body>
                </html>
            `);
            errorWindow.document.close();
        } else {
            // Fallback if popup is blocked
            alert('Error: ' + message + '\n\nPlease allow popups for this site to see error details in a new window.');
        }
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
        console.log('Results back button clicked');
        resultsSection.style.display = 'none';
        scenarioSection.style.display = 'block';
        const headerBlock2 = document.querySelector('.header-block');
        if (headerBlock2) headerBlock2.style.display = 'none';
        // Keep stepper visible and show selection phase
        stepper.style.display = 'flex';
        updateStepper(3);
    });







    // Scenario Selection Functionality
    const scenarioSection = document.getElementById('scenario-selection-section');
    const scenarioContent = document.getElementById('scenario-content');
    const scenarioBackBtn = document.getElementById('scenarioBackBtn');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const generateTestCasesBtn = document.getElementById('generateTestCasesBtn');
    const scenarioSelectedCount = document.getElementById('scenarioSelectedCount');
    
    let allScenarios = [];
    let scenarioSelections = [];
    let currentApiInfo = null;
    let currentDocumentType = null;

    // Back to input from scenarios
    scenarioBackBtn.addEventListener('click', function() {
        scenarioSection.style.display = 'none';
        inputSection.style.display = 'block';
        updateStepper(1);
        
        // Show header
        const headerBlock = document.querySelector('.header-block');
        if (headerBlock) headerBlock.style.display = 'block';
    });

    // Select all/deselect all scenarios
    selectAllBtn.addEventListener('click', function() {
        if (selectAllBtn.classList.contains('all-selected')) {
            // All are selected, so deselect all
            scenarioSelections = [];
        } else {
            // Not all are selected, so select all
            scenarioSelections = [...allScenarios];
        }
        updateScenarioSelection();
    });

    // Generate test cases for selected scenarios
    generateTestCasesBtn.addEventListener('click', function() {
        if (scenarioSelections.length === 0) {
            alert('Please select at least one scenario');
            return;
        }
        
        generateTestCasesBtn.disabled = true;
        generateTestCasesBtn.innerHTML = 'Generating...';
        
        generateDetailedTestCases();
    });

    function displayScenarios(data) {
        allScenarios = data.scenarios || [];
        scenarioSelections = [];
        currentApiInfo = data.api_info;
        currentDocumentType = data.document_type;
        
        // Hide input section and show scenario selection
        inputSection.style.display = 'none';
        scenarioSection.style.display = 'block';
        updateStepper(3);
        
        // Hide header
        const headerBlock = document.querySelector('.header-block');
        if (headerBlock) headerBlock.style.display = 'none';
        
        // Populate scenarios
        let html = '';
        
        if (allScenarios.length === 0) {
            html = '<div class="no-scenarios">No scenarios generated. Please try again with different input.</div>';
        } else {
            allScenarios.forEach((scenario, index) => {
                const priority = scenario.priority || 'medium';
                const category = scenario.category || 'functional';
                const estimatedCases = scenario.estimated_test_cases || scenario.test_cases?.length || 5;
                
                html += `
                    <div class="scenario-card" data-index="${index}">
                        <div class="scenario-card-header">
                            <div class="scenario-checkbox" data-index="${index}">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: none;">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" stroke="currentColor" stroke-width="2" fill="currentColor"/>
                                </svg>
                            </div>
                            <h4 class="scenario-card-title">${scenario.title || scenario.name || `Scenario ${index + 1}`}</h4>
                        </div>
                        <p class="scenario-card-description">${scenario.description || 'No description available'}</p>
                        <div class="scenario-card-meta">
                            <div class="scenario-meta-item">
                                <span>Priority:</span>
                                <span class="priority-${priority}">${priority.charAt(0).toUpperCase() + priority.slice(1)}</span>
                            </div>
                            <div class="scenario-meta-item">
                                <span>Category:</span>
                                <span>${category.charAt(0).toUpperCase() + category.slice(1)}</span>
                            </div>
                            <div class="scenario-meta-item">
                                <span>Est. Test Cases:</span>
                                <span>${estimatedCases}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
        
        scenarioContent.innerHTML = html;
        
        // Add click handlers for scenario cards and checkboxes
        document.querySelectorAll('.scenario-card').forEach(card => {
            card.addEventListener('click', function(e) {
                if (!e.target.closest('.scenario-checkbox')) {
                    toggleScenarioSelection(parseInt(this.dataset.index));
                }
            });
        });
        
        document.querySelectorAll('.scenario-checkbox').forEach(checkbox => {
            checkbox.addEventListener('click', function(e) {
                e.stopPropagation();
                toggleScenarioSelection(parseInt(this.dataset.index));
            });
        });
        
        updateScenarioSelection();
    }

    function toggleScenarioSelection(index) {
        const scenario = allScenarios[index];
        const existingIndex = scenarioSelections.findIndex(s => 
            (s.id && s.id === scenario.id) || 
            (s.title === scenario.title && s.description === scenario.description)
        );
        
        if (existingIndex >= 0) {
            scenarioSelections.splice(existingIndex, 1);
        } else {
            scenarioSelections.push(scenario);
        }
        
        updateScenarioSelection();
    }

    function updateScenarioSelection() {
        // Update UI
        document.querySelectorAll('.scenario-card').forEach((card, index) => {
            const checkbox = card.querySelector('.scenario-checkbox');
            const checkmark = checkbox.querySelector('svg');
            const scenario = allScenarios[index];
            
            const isSelected = scenarioSelections.some(s => 
                (s.id && s.id === scenario.id) || 
                (s.title === scenario.title && s.description === scenario.description)
            );
            
            if (isSelected) {
                card.classList.add('selected');
                checkbox.classList.add('checked');
                checkmark.style.display = 'block';
            } else {
                card.classList.remove('selected');
                checkbox.classList.remove('checked');
                checkmark.style.display = 'none';
            }
        });
        
        // Update button and counter
        scenarioSelectedCount.textContent = `(${scenarioSelections.length} selected)`;
        generateTestCasesBtn.disabled = scenarioSelections.length === 0;
        
        // Update Select All button visual state
        if (scenarioSelections.length === allScenarios.length && allScenarios.length > 0) {
            selectAllBtn.classList.add('all-selected');
        } else {
            selectAllBtn.classList.remove('all-selected');
        }
    }

    async function generateDetailedTestCases() {
        try {
            let endpoint, requestData;
            
            // Determine which endpoint to use based on current context
            if (currentApiInfo) {
                // API workflow
                endpoint = `${window.BACKEND_URL}/generate_api_test_cases`;
                requestData = {
                    scenarios: scenarioSelections,
                    api_info: currentApiInfo,
                    document_type: currentDocumentType
                };
            } else {
                // Regular workflow (text/image)
                endpoint = `${window.BACKEND_URL}/generate_test_cases`;
                requestData = {
                    scenarios: scenarioSelections
                };
            }
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            // Hide scenario selection and show results
            scenarioSection.style.display = 'none'; 
            displayResults(result);
            
        } catch (error) {
            console.error('Error generating test cases:', error);
            console.error('Error details:', {
                endpoint: endpoint,
                requestData: requestData,
                backendUrl: window.BACKEND_URL
            });
            alert('Error generating test cases: ' + error.message);
        } finally {
            generateTestCasesBtn.disabled = false;
            generateTestCasesBtn.innerHTML = 'Generate Test Cases <span id="scenarioSelectedCount">(0 selected)</span>';
        }
    }

    // Update existing analyze functions to show scenarios instead of results directly
    window.displayScenarios = displayScenarios;
});