// json_editor.js - Helper for JSON fields in profile form
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all JSON input fields
    const jsonInputs = document.querySelectorAll('.json-input');
    
    jsonInputs.forEach(function(textarea) {
        setupJsonEditor(textarea);
    });
    
    /**
     * Setup JSON editor functionality for a textarea
     * @param {HTMLElement} textarea - The textarea to enhance
     */
    function setupJsonEditor(textarea) {
        // Create wrapper and controls
        const wrapper = document.createElement('div');
        wrapper.className = 'json-editor-wrapper';
        
        // Create toolbar with buttons
        const toolbar = document.createElement('div');
        toolbar.className = 'json-editor-toolbar mb-2';
        
        // Add Item button
        const addButton = document.createElement('button');
        addButton.type = 'button';
        addButton.className = 'btn btn-sm btn-outline-primary me-2';
        addButton.innerHTML = '<i class="fas fa-plus-circle me-1"></i> Add Item';
        addButton.addEventListener('click', function() {
            addNewItem(textarea);
        });
        
        // Format button
        const formatButton = document.createElement('button');
        formatButton.type = 'button';
        formatButton.className = 'btn btn-sm btn-outline-secondary me-2';
        formatButton.innerHTML = '<i class="fas fa-code me-1"></i> Format JSON';
        formatButton.addEventListener('click', function() {
            formatJson(textarea);
        });
        
        // View mode toggle button
        const viewModeButton = document.createElement('button');
        viewModeButton.type = 'button';
        viewModeButton.className = 'btn btn-sm btn-outline-info me-2';
        viewModeButton.innerHTML = '<i class="fas fa-table me-1"></i> Table View';
        viewModeButton.dataset.mode = 'json';
        viewModeButton.addEventListener('click', function() {
            toggleViewMode(textarea, viewModeButton);
        });
        
        // Help button
        const helpButton = document.createElement('button');
        helpButton.type = 'button';
        helpButton.className = 'btn btn-sm btn-outline-secondary float-end';
        helpButton.innerHTML = '<i class="fas fa-question-circle"></i>';
        helpButton.title = 'View format example';
        helpButton.addEventListener('click', function() {
            showHelpModal(textarea);
        });
        
        // Add buttons to toolbar
        toolbar.appendChild(addButton);
        toolbar.appendChild(formatButton);
        toolbar.appendChild(viewModeButton);
        toolbar.appendChild(helpButton);
        
        // Error message container
        const errorContainer = document.createElement('div');
        errorContainer.className = 'json-error-message alert alert-danger mt-2 d-none';
        
        // Insert toolbar before textarea
        textarea.parentNode.insertBefore(wrapper, textarea);
        wrapper.appendChild(toolbar);
        wrapper.appendChild(textarea);
        wrapper.appendChild(errorContainer);
        
        // Initial format
        formatJson(textarea);
        
        // Validate on change
        textarea.addEventListener('change', function() {
            validateJson(textarea, errorContainer);
        });
        textarea.addEventListener('blur', function() {
            validateJson(textarea, errorContainer);
        });
    }
    
    /**
     * Format the JSON content for better readability
     * @param {HTMLElement} textarea - The textarea containing JSON
     */
    function formatJson(textarea) {
        try {
            const content = textarea.value.trim();
            if (!content) {
                textarea.value = '[]';
                return;
            }
            
            const jsonObj = JSON.parse(content);
            textarea.value = JSON.stringify(jsonObj, null, 2);
            
            // Clear any error messages
            const errorContainer = textarea.nextElementSibling;
            if (errorContainer && errorContainer.classList.contains('json-error-message')) {
                errorContainer.classList.add('d-none');
            }
        } catch (error) {
            showError(textarea, 'Invalid JSON: ' + error.message);
        }
    }
    
    /**
     * Validate JSON content
     * @param {HTMLElement} textarea - The textarea containing JSON
     * @param {HTMLElement} errorContainer - Element to display error messages
     */
    function validateJson(textarea, errorContainer) {
        try {
            const content = textarea.value.trim();
            if (!content) {
                return;
            }
            
            JSON.parse(content);
            errorContainer.classList.add('d-none');
        } catch (error) {
            errorContainer.textContent = 'Invalid JSON: ' + error.message;
            errorContainer.classList.remove('d-none');
        }
    }
    
    /**
     * Show error message
     * @param {HTMLElement} textarea - The textarea with the error
     * @param {string} message - Error message to display
     */
    function showError(textarea, message) {
        const errorContainer = textarea.nextElementSibling;
        if (errorContainer && errorContainer.classList.contains('json-error-message')) {
            errorContainer.textContent = message;
            errorContainer.classList.remove('d-none');
        }
    }
    
    /**
     * Add a new item to the JSON array
     * @param {HTMLElement} textarea - The textarea containing the JSON array
     */
    function addNewItem(textarea) {
        let template = {};
        const fieldName = textarea.name;
        
        // Determine template based on field name
        if (fieldName.includes('education')) {
            template = {
                "degree": "Bachelor's Degree",
                "institution": "University Name",
                "start_year": 2020,
                "end_year": 2024,
                "description": "Studied Computer Science"
            };
        } else if (fieldName.includes('skills')) {
            template = {
                "name": "Skill Name",
                "level": "Intermediate"
            };
        } else if (fieldName.includes('work_experience')) {
            template = {
                "title": "Job Title",
                "company": "Company Name",
                "start_date": "2020-01",
                "end_date": "Present",
                "description": "Job responsibilities and achievements"
            };
        } else if (fieldName.includes('projects')) {
            template = {
                "title": "Project Name",
                "description": "Project description",
                "url": "https://project-url.com",
                "status": "In progress"
            };
        } else if (fieldName.includes('recommendations')) {
            template = {
                "recommender_name": "John Doe",
                "relationship": "Supervisor",
                "recommendation": "Strong recommendation text here"
            };
        }
        
        try {
            let jsonArray = [];
            if (textarea.value.trim()) {
                jsonArray = JSON.parse(textarea.value);
                if (!Array.isArray(jsonArray)) {
                    jsonArray = [];
                }
            }
            
            jsonArray.push(template);
            textarea.value = JSON.stringify(jsonArray, null, 2);
            
            // Clear any error messages
            const errorContainer = textarea.nextElementSibling;
            if (errorContainer && errorContainer.classList.contains('json-error-message')) {
                errorContainer.classList.add('d-none');
            }
        } catch (error) {
            showError(textarea, 'Error adding item: ' + error.message);
        }
    }
    
    /**
     * Toggle between JSON and Table view
     * @param {HTMLElement} textarea - The textarea containing JSON
     * @param {HTMLElement} button - The toggle button
     */
    function toggleViewMode(textarea, button) {
        const currentMode = button.dataset.mode;
        const wrapper = textarea.closest('.json-editor-wrapper');
        
        if (currentMode === 'json') {
            // Switch to table view
            try {
                const data = JSON.parse(textarea.value);
                if (!Array.isArray(data) || data.length === 0) {
                    alert('No data to display in table view');
                    return;
                }
                
                // Create table view
                const tableView = document.createElement('div');
                tableView.className = 'json-table-view mt-2';
                tableView.innerHTML = createTableFromJson(data);
                
                // Hide textarea, show table
                textarea.style.display = 'none';
                if (wrapper.querySelector('.json-table-view')) {
                    wrapper.removeChild(wrapper.querySelector('.json-table-view'));
                }
                wrapper.appendChild(tableView);
                
                // Update button
                button.innerHTML = '<i class="fas fa-code me-1"></i> JSON View';
                button.dataset.mode = 'table';
            } catch (error) {
                showError(textarea, 'Error creating table view: ' + error.message);
            }
        } else {
            // Switch back to JSON view
            textarea.style.display = '';
            const tableView = wrapper.querySelector('.json-table-view');
            if (tableView) {
                wrapper.removeChild(tableView);
            }
            
            // Update button
            button.innerHTML = '<i class="fas fa-table me-1"></i> Table View';
            button.dataset.mode = 'json';
        }
    }
    
    /**
     * Create HTML table from JSON data
     * @param {Array} data - Array of objects to display in table
     * @return {string} HTML table representation
     */
    function createTableFromJson(data) {
        if (!data || data.length === 0) return '<p>No data available</p>';
        
        // Get all unique keys from all objects
        const keys = new Set();
        data.forEach(item => {
            Object.keys(item).forEach(key => keys.add(key));
        });
        
        // Create table headers
        let html = '<table class="table table-bordered table-striped">';
        html += '<thead><tr>';
        keys.forEach(key => {
            html += `<th>${key}</th>`;
        });
        html += '</tr></thead>';
        
        // Create table body
        html += '<tbody>';
        data.forEach(item => {
            html += '<tr>';
            keys.forEach(key => {
                const value = item[key] !== undefined ? item[key] : '';
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        
        return html;
    }
    
    /**
     * Show help modal with example for the field
     * @param {HTMLElement} textarea - The textarea to show help for
     */
    function showHelpModal(textarea) {
        const fieldName = textarea.name;
        let exampleData = [];
        let title = 'JSON Format Example';
        
        // Determine example data based on field name
        if (fieldName.includes('education')) {
            title = 'Education Format Example';
            exampleData = [
                {
                    "degree": "Bachelor of Science",
                    "institution": "University of Technology",
                    "start_year": 2018,
                    "end_year": 2022,
                    "description": "Computer Science major with focus on AI"
                },
                {
                    "degree": "Master of Business Administration",
                    "institution": "Business School",
                    "start_year": 2022,
                    "end_year": 2023,
                    "description": "Specialized in Technology Management"
                }
            ];
        } else if (fieldName.includes('skills')) {
            title = 'Skills Format Example';
            exampleData = [
                {
                    "name": "Python Programming",
                    "level": "Advanced"
                },
                {
                    "name": "Project Management",
                    "level": "Intermediate"
                },
                {
                    "name": "UI/UX Design",
                    "level": "Beginner"
                }
            ];
        } else if (fieldName.includes('work_experience')) {
            title = 'Work Experience Format Example';
            exampleData = [
                {
                    "title": "Senior Developer",
                    "company": "Tech Solutions Inc.",
                    "start_date": "2020-03",
                    "end_date": "Present",
                    "description": "Lead developer for enterprise applications. Managed team of 5 developers."
                },
                {
                    "title": "Junior Developer",
                    "company": "Startup Co.",
                    "start_date": "2018-06",
                    "end_date": "2020-02",
                    "description": "Full-stack development using React and Node.js"
                }
            ];
        } else if (fieldName.includes('projects')) {
            title = 'Projects Format Example';
            exampleData = [
                {
                    "title": "E-commerce Platform",
                    "description": "Built a complete e-commerce solution with payment processing",
                    "url": "https://github.com/username/project",
                    "status": "Completed"
                },
                {
                    "title": "Mobile App",
                    "description": "Fitness tracking application for iOS and Android",
                    "url": "https://play.google.com/store/apps/example",
                    "status": "In progress"
                }
            ];
        } else if (fieldName.includes('recommendations')) {
            title = 'Recommendations Format Example';
            exampleData = [
                {
                    "recommender_name": "Jane Smith",
                    "relationship": "Former Manager",
                    "recommendation": "An excellent team player with strong technical skills. Always delivers projects on time."
                },
                {
                    "recommender_name": "John Doe",
                    "relationship": "Client",
                    "recommendation": "Provided exceptional service and technical expertise. Highly recommended!"
                }
            ];
        }
        
        // Create and show modal
        const modalHtml = `
        <div class="modal fade" id="helpModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>JSON Format:</h6>
                                <pre class="bg-light p-3 border rounded"><code>${JSON.stringify(exampleData, null, 2)}</code></pre>
                            </div>
                            <div class="col-md-6">
                                <h6>Table View:</h6>
                                ${createTableFromJson(exampleData)}
                            </div>
                        </div>
                        <div class="alert alert-info mt-3">
                            <i class="fas fa-info-circle me-2"></i>
                            Copy and paste the example JSON or use the "Add Item" button to build your own list.
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" id="useExampleBtn">Use This Example</button>
                    </div>
                </div>
            </div>
        </div>
        `;
        
        // Add modal to document if it doesn't exist
        // Add modal to document if it doesn't exist
        if (!document.getElementById('helpModal')) {
            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = modalHtml;
            document.body.appendChild(modalContainer);
            
            // Initialize the modal
            const modal = new bootstrap.Modal(document.getElementById('helpModal'));
            
            // Add event listener for "Use This Example" button
            document.getElementById('useExampleBtn').addEventListener('click', function() {
                textarea.value = JSON.stringify(exampleData, null, 2);
                modal.hide();
            });
            
            // Show the modal
            modal.show();
        } else {
            // Update existing modal content
            const modal = document.getElementById('helpModal');
            modal.querySelector('.modal-title').textContent = title;
            modal.querySelector('pre code').textContent = JSON.stringify(exampleData, null, 2);
            modal.querySelector('.col-md-6:nth-child(2)').innerHTML = `<h6>Table View:</h6>${createTableFromJson(exampleData)}`;
            
            // Update "Use This Example" button event
            const useExampleBtn = document.getElementById('useExampleBtn');
            const oldListener = useExampleBtn.onclick;
            useExampleBtn.onclick = function() {
                textarea.value = JSON.stringify(exampleData, null, 2);
                bootstrap.Modal.getInstance(modal).hide();
            };
            
            // Show the modal
            bootstrap.Modal.getInstance(modal).show();
        }
    }
});