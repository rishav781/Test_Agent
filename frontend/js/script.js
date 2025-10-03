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
    if (uploadArea && imageInput) {
        uploadArea.addEventListener('click', function() {
            imageInput.click();
        });
    }

    if (uploadLink && imageInput) {
        uploadLink.addEventListener('click', function(e) {
            e.stopPropagation();
            imageInput.click();
        });
    }

    // File input change
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                updateUploadArea(file.name);
            }
        });
    }

    // Drag and drop functionality
    if (uploadArea) {
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
    }

    function updateUploadArea(filename) {
        if (!uploadArea) return;
        const uploadContent = uploadArea.querySelector('.upload-content');
        if (!uploadContent) return;
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
    if (apiUploadArea && apiFileInput) {
        apiUploadArea.addEventListener('click', function() {
            apiFileInput.click();
        });
    }

    if (apiUploadLink && apiFileInput) {
        apiUploadLink.addEventListener('click', function(e) {
            e.stopPropagation();
            apiFileInput.click();
        });
    }

    // API file input change
    if (apiFileInput) {
        apiFileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                updateApiUploadArea(file.name);
            }
        });
    }

    // API file drag and drop functionality
    if (apiUploadArea) {
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
    }

    function updateApiUploadArea(filename) {
        if (!apiUploadArea) return;
        const uploadContent = apiUploadArea.querySelector('.upload-content');
        if (!uploadContent) return;
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

    // Global state variables
    let allScenarios = [];
    let scenarioSelections = [];
    let currentApiInfo = null;
    let currentDocumentType = null;
    let lastAnalysisResult = null; // Cache the last result

    // Get references to main sections
    const inputSection = document.querySelector('.card');
    const stepper = document.querySelector('.stepper');

    // State management for browser history
    window.addEventListener('popstate', function(event) {
        if (event.state) {
            restoreState(event.state);
        } else {
            // This handles the case where the user navigates back to the initial page
            showInputPage(true); // Force a full reset
        }
    });

    function saveState(state) {
        // Don't push the same state twice
        if (history.state && history.state.page === state.page) {
            history.replaceState(state, '', `#${state.page}`);
        } else {
            history.pushState(state, '', `#${state.page}`);
        }
    }

    function restoreState(state) {
        if (state.page === 'scenarios') {
            // Restore data from state and re-render the scenario page
            allScenarios = state.data.scenarios || [];
            scenarioSelections = state.selections || [];
            currentApiInfo = state.data.api_info;
            currentDocumentType = state.data.document_type;
            lastAnalysisResult = state.data;
            
            showScenarioPage(false, true); // Don't save state again, but indicate this is a restore
            
        } else if (state.page === 'results') {
            // Restore data and display the results page
            displayResults(state.data, false);

        } else {
            // Default to the input page
            showInputPage(true);
        }
    }

    function showInputPage(forceReset = false) {
        if (scenariosSection) scenariosSection.style.display = 'none';
        if (resultsSection) resultsSection.style.display = 'none';
        if (inputSection) inputSection.style.display = 'block';
        
        const headerBlock = document.querySelector('.header-block');
        if (headerBlock) headerBlock.style.display = 'block';
        
        updateStepper(1);

        if (forceReset) {
            // Reset all input fields to provide a "fresh" experience
            const descriptionInput = document.getElementById('description');
            if (descriptionInput) descriptionInput.value = '';
            
            const imageInput = document.getElementById('image');
            if (imageInput) imageInput.value = '';
            
            const apiFileInput = document.getElementById('apiFile');
            if (apiFileInput) apiFileInput.value = '';

            const websiteUrlInput = document.getElementById('websiteUrl');
            if (websiteUrlInput) websiteUrlInput.value = '';

            // Reset upload area UI
            const uploadContent = document.querySelector('#uploadArea .upload-content');
            if (uploadContent) {
                uploadContent.innerHTML = `
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4C9.11 4 6.6 5.64 5.35 8.04C2.34 8.36 0 10.91 0 14C0 17.31 2.69 20 6 20H19C21.76 20 24 17.76 24 15C24 12.36 21.95 10.22 19.35 10.04ZM19 18H6C3.79 18 2 16.21 2 14C2 11.95 3.53 10.24 5.56 10.03L6.63 9.92L7.13 8.97C8.08 7.14 9.94 6 12 6C14.76 6 17 8.24 17 11H19C20.66 11 22 12.34 22 14C22 15.66 20.66 17 19 17V18Z" fill="#4a5568"/>
                        <path d="M8 13H10.55V17H13.45V13H16L12 9L8 13Z" fill="#4a5568"/>
                    </svg>
                    <p><strong>Drag & drop an image</strong> or <span class="upload-link">browse</span></p>
                    <p class="upload-hint">Supports: PNG, JPG, GIF, WebP</p>
                `;
            }
            const apiUploadContent = document.querySelector('#apiUploadArea .upload-content');
             if (apiUploadContent) {
                apiUploadContent.innerHTML = `
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                         <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4C9.11 4 6.6 5.64 5.35 8.04C2.34 8.36 0 10.91 0 14C0 17.31 2.69 20 6 20H19C21.76 20 24 17.76 24 15C24 12.36 21.95 10.22 19.35 10.04ZM19 18H6C3.79 18 2 16.21 2 14C2 11.95 3.53 10.24 5.56 10.03L6.63 9.92L7.13 8.97C8.08 7.14 9.94 6 12 6C14.76 6 17 8.24 17 11H19C20.66 11 22 12.34 22 14C22 15.66 20.66 17 19 17V18Z" fill="#4a5568"/>
                        <path d="M8 13H10.55V17H13.45V13H16L12 9L8 13Z" fill="#4a5568"/>
                    </svg>
                    <p><strong>Drag & drop a JSON file</strong> or <span class="api-upload-link">browse</span></p>
                    <p class="upload-hint">Supports: Swagger, Postman (JSON)</p>
                `;
            }
        }
    }

    if (generateBtn) {
        generateBtn.addEventListener('click', async function(e) {
            e.preventDefault();

        // Check which tab is active
        const activeTab = document.querySelector('.tab-content.active');
        const isDescriptionTab = activeTab.id === 'description-tab';
        const isUploadTab = activeTab.id === 'upload-tab';
        const isApiTab = activeTab.id === 'api-tab';
        const isWebsiteTab = activeTab.id === 'website-tab';

        let formData = new FormData();
        let apiUrl;

        if (isDescriptionTab) {
            // Handle description form
            const description = document.getElementById('description').value.trim();
            if (!description) {
                alert('Please enter a functional description.');
                return;
            }
            formData.append('description', description);
            apiUrl = `${window.BACKEND_URL}/api/analyze`;
        } else if (isUploadTab) {
            // Handle upload form
            const imageFile = document.getElementById('image').files[0];
            if (!imageFile) {
                alert('Please select an image file.');
                return;
            }
            formData.append('image', imageFile);
            apiUrl = `${window.BACKEND_URL}/api/analyze`;
        } else if (isApiTab) {
            // Handle API document upload
            const apiFile = document.getElementById('apiFile').files[0];
            if (!apiFile) {
                alert('Please select an API document file.');
                return;
            }
            formData.append('api_file', apiFile);
            apiUrl = `${window.BACKEND_URL}/api/analyze_api`;
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
            apiUrl = `${window.BACKEND_URL}/api/analyze_website`;
        }

        // Show loading state (spinner on button only)
        generateBtn.disabled = true;
        generateBtn.classList.add('loading');

        // Update stepper to show analyzing state
        updateStepper(2);

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

            if (!response.ok) {
                const errorText = await response.text();
                try {
                    const errorJson = JSON.parse(errorText);
                    throw new Error(errorJson.error || `Server error: ${response.status}`);
                } catch (e) {
                    throw new Error(`Received non-JSON response from server (status: ${response.status}). Check Nginx logs.`);
                }
            }

            const result = await response.json();
            lastAnalysisResult = result; // Cache the result

            if (response.ok) {
                // Set global state from the result
                allScenarios = result.scenarios || [];
                scenarioSelections = []; // Always start with a fresh selection
                currentApiInfo = result.api_info;
                currentDocumentType = result.document_type;

                // Transition to the scenario page
                showScenarioPage();
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
    }

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

    function displayResults(data, shouldSaveState = true) {
        if (resultsSection) {
            resultsSection.style.display = 'block';
        }
        if (scenarioSection) {
            scenarioSection.style.display = 'none';
        }
        updateStepper(4);

        if (shouldSaveState) {
            saveState({ page: 'results', data: data });
        }

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

        if (resultsContent) {
            resultsContent.innerHTML = html;
        }

        // Update Export Accepted button enabled state
        const exportAcceptedBtn2 = document.getElementById('exportAcceptedBtn');
        if (exportAcceptedBtn2) {
            exportAcceptedBtn2.disabled = acceptedTestCases.size === 0;
        }

        // Scroll to results
        if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
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
        history.back();
    });

    // Scenario Selection Functionality
    const scenarioSection = document.getElementById('scenario-selection-section');
    const scenarioContent = document.getElementById('scenario-content');
    const scenarioBackBtn = document.getElementById('scenarioBackBtn');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const generateTestCasesBtn = document.getElementById('generateTestCasesBtn');
    const scenarioSelectedCount = document.getElementById('scenarioSelectedCount');
    
    // Back to input from scenarios
    if (scenarioBackBtn) {
        scenarioBackBtn.addEventListener('click', function() {
            // Use browser history to navigate back, which will trigger popstate
            history.back();
        });
    }

    // Select all/deselect all scenarios
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            // Check actual selection state, not just the CSS class
            const allSelected = scenarioSelections.length === allScenarios.length && allScenarios.length > 0;
            
            console.log('Select All clicked. Currently selected:', scenarioSelections.length, 'Total:', allScenarios.length, 'All selected:', allSelected);
            
            if (allSelected) {
                // All are selected, so deselect all
                console.log('Deselecting all scenarios');
                scenarioSelections = [];
            } else {
                // Not all are selected, so select all
                console.log('Selecting all scenarios');
                scenarioSelections = [...allScenarios];
            }
            updateScenarioSelection();
        });
    }

    // Generate test cases for selected scenarios
    if (generateTestCasesBtn) {
        generateTestCasesBtn.addEventListener('click', function() {
            if (scenarioSelections.length === 0) {
                alert('Please select at least one scenario');
                return;
            }
            
            generateTestCasesBtn.disabled = true;
            generateTestCasesBtn.innerHTML = 'Generating...';
            
            generateDetailedTestCases();
        });
    }

    async function generateDetailedTestCases() {
        try {
            let endpoint, requestData;
            
            // Determine which endpoint to use based on current context
            if (currentApiInfo) {
                // API workflow
                endpoint = `${window.BACKEND_URL}/api/generate_api_test_cases`;
                requestData = {
                    scenarios: scenarioSelections,
                    api_info: currentApiInfo,
                    document_type: currentDocumentType
                };
            } else {
                // Regular workflow (text/image)
                endpoint = `${window.BACKEND_URL}/api/generate_test_cases`;
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

            if (!response.ok) {
                // Attempt to read response as text, as it might be HTML from nginx
                const errorText = await response.text();
                try {
                    // See if it's valid JSON
                    const errorJson = JSON.parse(errorText);
                    throw new Error(errorJson.error || 'An unknown error occurred.');
                } catch (e) {
                    // If not JSON, it's likely an HTML error page
                    throw new Error(`Server returned an error page (status: ${response.status}). Check Nginx configuration.`);
                }
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            // Hide scenario selection and show results
            if (scenarioSection) scenarioSection.style.display = 'none'; 
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
            if (generateTestCasesBtn) {
                generateTestCasesBtn.disabled = false;
                // Re-enable the button and update the count
                updateScenarioSelection();
            }
        }
    }

    function showScenarioPage(shouldSaveState = true, isRestore = false) {
        // Hide other sections and show the scenario section
        if (inputSection) inputSection.style.display = 'none';
        if (resultsSection) resultsSection.style.display = 'none';
        if (scenarioSection) scenarioSection.style.display = 'block';

        // Update stepper based on context
        if (isRestore) {
            // When restoring from history, show step 3 (Selection)
            updateStepper(3);
        }
        // Otherwise keep at step 2 (Analysis) until user interacts

        // Hide header
        const headerBlock = document.querySelector('.header-block');
        if (headerBlock) headerBlock.style.display = 'none';

        // Save the current state to browser history
        if (shouldSaveState) {
            saveState({
                page: 'scenarios',
                data: lastAnalysisResult,
                selections: scenarioSelections
            });
        }

        // Populate the list of scenarios and update all UI elements
        populateScenarioList();
        updateScenarioSelection();

        // Reattach event listeners for buttons that might have lost them during navigation
        attachScenarioButtonListeners();
        updateScenarioSelection(); // Update button states after attaching listeners
    }    function attachScenarioButtonListeners() {
        // Reattach Select All button listener
        const selectAllBtn = document.getElementById('selectAllBtn');
        if (selectAllBtn) {
            // Store current classes and text before cloning
            const currentClasses = selectAllBtn.className;
            const currentText = selectAllBtn.textContent;

            // Remove existing listeners to avoid duplicates
            selectAllBtn.replaceWith(selectAllBtn.cloneNode(true));
            const newSelectAllBtn = document.getElementById('selectAllBtn');

            // Restore classes and text
            newSelectAllBtn.className = currentClasses;
            newSelectAllBtn.textContent = currentText;

            newSelectAllBtn.addEventListener('click', function() {
                // Update stepper to step 3 (Selection) on first interaction
                updateStepper(3);

                // Check actual selection state, not just the CSS class
                const allSelected = scenarioSelections.length === allScenarios.length && allScenarios.length > 0;

                console.log('Select All clicked. Currently selected:', scenarioSelections.length, 'Total:', allScenarios.length, 'All selected:', allSelected);

                if (allSelected) {
                    // All are selected, so deselect all
                    console.log('Deselecting all scenarios');
                    scenarioSelections = [];
                } else {
                    // Not all are selected, so select all
                    console.log('Selecting all scenarios');
                    scenarioSelections = [...allScenarios];
                }
                updateScenarioSelection();
            });
        }

        // Reattach Generate Test Cases button listener
        const generateTestCasesBtn = document.getElementById('generateTestCasesBtn');
        if (generateTestCasesBtn) {
            // Store current classes and HTML before cloning
            const currentClasses = generateTestCasesBtn.className;
            const currentHTML = generateTestCasesBtn.innerHTML;

            // Remove existing listeners to avoid duplicates
            generateTestCasesBtn.replaceWith(generateTestCasesBtn.cloneNode(true));
            const newGenerateBtn = document.getElementById('generateTestCasesBtn');

            // Restore classes and HTML
            newGenerateBtn.className = currentClasses;
            newGenerateBtn.innerHTML = currentHTML;

            newGenerateBtn.addEventListener('click', function() {
                // Update stepper to step 3 (Selection) on first interaction
                updateStepper(3);

                if (scenarioSelections.length === 0) {
                    alert('Please select at least one scenario');
                    return;
                }

                // Update stepper to step 4 (Generation) when starting test case generation
                updateStepper(4);

                // Disable button and show loading state
                newGenerateBtn.disabled = true;
                newGenerateBtn.innerHTML = 'Generating...';

                // Generate test cases for selected scenarios
                generateTestCasesForScenarios(scenarioSelections);
            });
        }
    }

    function populateScenarioList() {
        let html = '';
        if (!allScenarios || allScenarios.length === 0) {
            html = '<div class="no-scenarios">No scenarios generated. Please try again with different input.</div>';
        } else {
            allScenarios.forEach((scenario, index) => {
                const priority = scenario.priority || 'medium';
                const category = scenario.category || 'functional';
                const estimatedCases = scenario.estimated_test_cases || scenario.test_cases?.length || 5;
                
                // Determine if the current scenario is selected
                const isSelected = scenarioSelections.some(s => 
                    (s.id && scenario.id && s.id === scenario.id) || 
                    (s.title === scenario.title && s.description === scenario.description)
                );

                html += `
                    <div class="scenario-card ${isSelected ? 'selected' : ''}" data-index="${index}">
                        <div class="scenario-card-header">
                            <div class="scenario-checkbox ${isSelected ? 'checked' : ''}" data-index="${index}">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: ${isSelected ? 'block' : 'none'};">
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
        
        if (scenarioContent) {
            scenarioContent.innerHTML = html;
        }
        
        // Re-add click handlers for the newly created scenario cards and checkboxes
        document.querySelectorAll('.scenario-card').forEach(card => {
            card.addEventListener('click', function(e) {
                // Prevent selection when clicking on links or buttons inside the card
                if (e.target.tagName.toLowerCase() === 'a' || e.target.closest('button')) {
                    return;
                }
                toggleScenarioSelection(parseInt(this.dataset.index, 10));
            });
        });
    }

    function toggleScenarioSelection(index) {
        // Update stepper to step 3 (Selection) on first interaction
        updateStepper(3);

        const scenario = allScenarios[index];
        if (!scenario) return;

        const existingIndex = scenarioSelections.findIndex(s => 
            (s.id && scenario.id && s.id === scenario.id) || 
            (s.title === scenario.title && s.description === scenario.description)
        );
        
        if (existingIndex >= 0) {
            // Deselect
            scenarioSelections.splice(existingIndex, 1);
        } else {
            // Select
            scenarioSelections.push(scenario);
        }
        
        // Update the UI and save the new selection state
        updateScenarioSelection();
        saveState({ 
            page: 'scenarios', 
            data: lastAnalysisResult,
            selections: scenarioSelections 
        });
    }

    function updateScenarioSelection() {
        if (!allScenarios) return;
        
        // Update card and checkbox visuals
        document.querySelectorAll('.scenario-card').forEach((card, index) => {
            const checkbox = card.querySelector('.scenario-checkbox');
            const checkmark = checkbox ? checkbox.querySelector('svg') : null;
            const scenario = allScenarios[index];
            
            if (!scenario || !checkbox || !checkmark) return;

            const isSelected = scenarioSelections.some(s => 
                (s.id && scenario.id && s.id === scenario.id) || 
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
        
        // Update button text and state
        const currentCountEl = document.getElementById('scenarioSelectedCount');
        if (currentCountEl) {
            currentCountEl.textContent = `(${scenarioSelections.length} selected)`;
        }
        
        const currentGenerateBtn = document.getElementById('generateTestCasesBtn');
        if (currentGenerateBtn) {
            currentGenerateBtn.disabled = scenarioSelections.length === 0;
            // Ensure button text is correct if not generating
            if (!currentGenerateBtn.classList.contains('loading')) {
                 currentGenerateBtn.innerHTML = `Generate Test Cases <span id="scenarioSelectedCount">(${scenarioSelections.length} selected)</span>`;
            }
        }
        
        // Update "Select All" button
        const currentSelectAllBtn = document.getElementById('selectAllBtn');
        if (currentSelectAllBtn) {
            const allAreSelected = scenarioSelections.length === allScenarios.length && allScenarios.length > 0;
            if (allAreSelected) {
                currentSelectAllBtn.classList.add('all-selected');
                currentSelectAllBtn.textContent = 'Deselect All';
            } else {
                currentSelectAllBtn.classList.remove('all-selected');
                currentSelectAllBtn.textContent = 'Select All';
            }
        }
    }
});