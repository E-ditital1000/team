/**
 * JSON Prettify for Django Admin
 * Enhances JSON fields with formatting, syntax highlighting, and validation
 */

(function($) {
    // Wait for the DOM to be ready
    $(document).ready(function() {
        // Initialize JSON prettify on all JSON fields
        initJsonFields();
        
        // Add toolbar for JSON fields
        addJsonToolbar();
    });

    /**
     * Initialize JSON fields found in the form
     */
    function initJsonFields() {
        // Find all textareas with the json-prettify class
        $('textarea.json-prettify').each(function() {
            const textarea = $(this);
            
            // Add event handlers
            textarea.on('change blur', function() {
                validateJsonField(textarea);
            });
            
            // Initial validation
            validateJsonField(textarea);
            
            // Format initial value if not empty
            if (textarea.val().trim()) {
                formatJsonField(textarea);
            }
        });
    }
    
    /**
     * Add toolbar with formatting actions
     */
    function addJsonToolbar() {
        $('textarea.json-prettify').each(function() {
            const textarea = $(this);
            const toolbar = $('<div class="json-toolbar"></div>');
            
            // Format button
            const formatButton = $('<button type="button">Format JSON</button>');
            formatButton.on('click', function(e) {
                e.preventDefault();
                formatJsonField(textarea);
            });
            
            // Minify button
            const minifyButton = $('<button type="button">Minify JSON</button>');
            minifyButton.on('click', function(e) {
                e.preventDefault();
                minifyJsonField(textarea);
            });
            
            // Clear button
            const clearButton = $('<button type="button">Clear</button>');
            clearButton.on('click', function(e) {
                e.preventDefault();
                textarea.val('');
                validateJsonField(textarea);
            });
            
            // Sample JSON button
            const sampleButton = $('<button type="button">Sample</button>');
            sampleButton.on('click', function(e) {
                e.preventDefault();
                insertSampleJson(textarea);
            });
            
            // Add buttons to toolbar
            toolbar.append(formatButton, minifyButton, clearButton, sampleButton);
            
            // Add toolbar before textarea
            textarea.before(toolbar);
            
            // Add help text after textarea
            textarea.after('<span class="json-field-help">Format: Use proper JSON syntax. Arrays should be wrapped in [], objects in {}.</span>');
        });
    }
    
    /**
     * Validates a JSON field and adds validation styling
     * @param {jQuery} textarea - The textarea element to validate
     */
    function validateJsonField(textarea) {
        // Remove existing validation elements
        textarea.removeClass('error valid');
        textarea.next('.json-validation-error').remove();
        
        const value = textarea.val().trim();
        
        // Skip validation for empty fields
        if (!value) {
            textarea.val(''); // Ensure truly empty, not just whitespace
            return;
        }
        
        try {
            // Try to parse as JSON
            JSON.parse(value);
            textarea.addClass('valid');
        } catch (e) {
            // Invalid JSON
            textarea.addClass('error');
            
            // Show error message
            const errorMessage = $('<div class="json-validation-error"></div>')
                .text('Invalid JSON: ' + e.message);
            textarea.after(errorMessage);
        }
    }
    
    /**
     * Formats JSON in a textarea with proper indentation
     * @param {jQuery} textarea - The textarea to format
     */
    function formatJsonField(textarea) {
        const value = textarea.val().trim();
        
        // Skip empty values
        if (!value) return;
        
        try {
            // Parse and re-stringify with indentation
            const parsedJson = JSON.parse(value);
            const formattedJson = JSON.stringify(parsedJson, null, 2);
            textarea.val(formattedJson);
            textarea.removeClass('error').addClass('valid');
            
            // Remove error messages
            textarea.next('.json-validation-error').remove();
        } catch (e) {
            // If invalid JSON, show error but don't change the content
            textarea.addClass('error');
            
            // Show error message if not already present
            if (!textarea.next('.json-validation-error').length) {
                const errorMessage = $('<div class="json-validation-error"></div>')
                    .text('Invalid JSON: ' + e.message);
                textarea.after(errorMessage);
            }
        }
    }
    
    /**
     * Minifies JSON in a textarea (removes all whitespace)
     * @param {jQuery} textarea - The textarea to minify
     */
    function minifyJsonField(textarea) {
        const value = textarea.val().trim();
        
        // Skip empty values
        if (!value) return;
        
        try {
            // Parse and re-stringify without indentation
            const parsedJson = JSON.parse(value);
            const minifiedJson = JSON.stringify(parsedJson);
            textarea.val(minifiedJson);
            textarea.removeClass('error').addClass('valid');
            
            // Remove error messages
            textarea.next('.json-validation-error').remove();
        } catch (e) {
            // If invalid JSON, show error but don't change the content
            textarea.addClass('error');
            
            // Show error message if not already present
            if (!textarea.next('.json-validation-error').length) {
                const errorMessage = $('<div class="json-validation-error"></div>')
                    .text('Invalid JSON: ' + e.message);
                textarea.after(errorMessage);
            }
        }
    }
    
    /**
     * Inserts sample JSON based on field name
     * @param {jQuery} textarea - The textarea to insert sample into
     */
    function insertSampleJson(textarea) {
        let sampleJson = '';
        const fieldName = textarea.attr('name') || '';
        
        // Generate appropriate sample based on field name
        if (fieldName.includes('education')) {
            sampleJson = [
                {
                    "degree": "Bachelor's Degree",
                    "field": "Computer Science",
                    "institution": "Example University",
                    "location": "City, Country",
                    "start_year": 2016,
                    "end_year": 2020,
                    "description": "Studied computer science with focus on web development"
                }
            ];
        } else if (fieldName.includes('skill')) {
            sampleJson = [
                {
                    "name": "Python",
                    "level": "Advanced",
                    "years": 5
                },
                {
                    "name": "JavaScript",
                    "level": "Intermediate",
                    "years": 3
                }
            ];
        } else if (fieldName.includes('project')) {
            sampleJson = [
                {
                    "title": "Project Name",
                    "description": "Brief description of the project",
                    "url": "https://example.com/project",
                    "technologies": ["Python", "Django", "JavaScript"],
                    "start_date": "2022-01",
                    "end_date": "2022-06",
                    "is_ongoing": false
                }
            ];
        } else if (fieldName.includes('work_experience')) {
            sampleJson = [
                {
                    "position": "Software Developer",
                    "company": "Example Company",
                    "location": "City, Country",
                    "start_date": "2020-01",
                    "end_date": "2022-12",
                    "current": false,
                    "responsibilities": [
                        "Developed web applications using Django",
                        "Maintained existing codebase",
                        "Collaborated with team members"
                    ]
                }
            ];
        } else if (fieldName.includes('recommendation')) {
            sampleJson = [
                {
                    "name": "John Doe",
                    "position": "Project Manager",
                    "company": "Example Inc.",
                    "relationship": "Supervisor",
                    "contact": "john@example.com",
                    "text": "Example recommendation text goes here. They did a great job on the project."
                }
            ];
        } else {
            // Generic sample
            sampleJson = {
                "key1": "value1",
                "key2": 123,
                "key3": true,
                "key4": ["item1", "item2"],
                "key5": {
                    "nested_key": "nested_value"
                }
            };
        }
        
        // Insert formatted JSON
        textarea.val(JSON.stringify(sampleJson, null, 2));
        validateJsonField(textarea);
    }

})(django.jQuery);