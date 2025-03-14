/**
 * Django CKEditor 5 Bundle
 * This is a simplified version that initializes CKEditor instances on the page
 * A real implementation would include the actual CKEditor library
 */

// Initialize CKEditor 5 instances when the document is ready
document.addEventListener('DOMContentLoaded', () => {
    initDjangoCKEditor5();
});

/**
 * Initialize all CKEditor 5 instances on the page
 */
function initDjangoCKEditor5() {
    const editorElements = document.querySelectorAll('.django_ckeditor_5');
    
    if (!editorElements.length) {
        return;
    }
    
    console.log(`Initializing ${editorElements.length} CKEditor 5 instances`);
    
    // This is where the actual CKEditor initialization would happen
    // In a real implementation, this would use the CKEditor API to create instances
    
    // For demonstration purposes, let's create simple editor placeholders
    editorElements.forEach((element, index) => {
        // Skip if already initialized
        if (element.classList.contains('ck-editor-initialized')) {
            return;
        }
        
        // In a real implementation, this would be handled by the CKEditor library
        simulateCKEditorInitialization(element, index);
        
        // Mark as initialized
        element.classList.add('ck-editor-initialized');
    });
    
    setupFormSubmitHandlers();
}

/**
 * Simulate CKEditor initialization for demonstration purposes
 * This function would be replaced by actual CKEditor initialization in a real implementation
 */
function simulateCKEditorInitialization(element, index) {
    console.log(`Simulating initialization for CKEditor instance #${index}`);
    
    // This is just a simulation - in a real implementation,
    // this function wouldn't be needed as the actual CKEditor library would handle initialization
    
    // Create a hidden input that will hold the element's ID and a data-editor-status attribute
    const statusInput = document.createElement('input');
    statusInput.type = 'hidden';
    statusInput.name = `editor_status_${index}`;
    statusInput.value = 'ready';
    statusInput.dataset.editorId = element.id;
    element.parentNode.appendChild(statusInput);
    
    // Insert a message into the console
    console.info(`CKEditor 5 instance #${index} (${element.id}) initialized successfully`);
    
    // Dispatch a custom event for other scripts to listen for
    document.dispatchEvent(new CustomEvent('ck-editor-initialized', {
        detail: {
            editorElement: element,
            editorId: element.id,
            editorIndex: index
        }
    }));
}

/**
 * Set up form submit handlers to ensure editor content is saved
 */
function setupFormSubmitHandlers() {
    // Find all forms that contain CKEditor instances
    const formsWithEditors = Array.from(document.querySelectorAll('.django_ckeditor_5'))
        .map(editor => editor.closest('form'))
        .filter(form => form !== null);
    
    // Remove duplicates
    const uniqueForms = [...new Set(formsWithEditors)];
    
    uniqueForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // In a real implementation, this would update the form values with the 
            // current editor content before submission
            console.log('Form with CKEditor is being submitted');
            
            // An actual implementation would use something like:
            // editorInstance.updateSourceElement();
        });
    });
}

/**
 * Add custom event listeners for CKEditor interaction
 */
document.addEventListener('ck-editor-initialized', function(e) {
    const { editorElement, editorId, editorIndex } = e.detail;
    console.log(`CKEditor instance #${editorIndex} (${editorId}) is ready for use`);
    
    // This would be where you might add custom event listeners or configurations
});

/**
 * Handle CSRF token for file uploads
 */
function getDjangoCsrfToken() {
    // Get CSRF token from cookie or from a meta tag
    // Prefer getting it from a meta tag if available
    const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfTokenMeta) {
        return csrfTokenMeta.getAttribute('content');
    }
    
    // Otherwise try to get it from a cookie
    const csrfCookie = document.cookie
        .split(';')
        .map(c => c.trim())
        .find(c => c.startsWith('csrftoken='));
        
    if (csrfCookie) {
        return csrfCookie.split('=')[1];
    }
    
    // If no CSRF token is found, log a warning
    console.warn('CSRF token not found. File uploads may not work correctly.');
    return '';
}

/**
 * Setup upload adapter for CKEditor 5 file uploads
 * This would be used by the actual CKEditor implementation
 */
function setupUploadAdapter(editor) {
    editor.plugins.get('FileRepository').createUploadAdapter = (loader) => {
        return new DjangoUploadAdapter(loader);
    };
}

/**
 * Django upload adapter for CKEditor 5
 * This would handle file uploads to the Django backend
 */
class DjangoUploadAdapter {
    constructor(loader) {
        this.loader = loader;
    }
    
    upload() {
        return this.loader.file.then(file => {
            return new Promise((resolve, reject) => {
                const data = new FormData();
                data.append('upload', file);
                
                // CSRF token for Django
                const csrfToken = getDjangoCsrfToken();
                
                fetch('/ckeditor5/upload/', {
                    method: 'POST',
                    body: data,
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    credentials: 'same-origin'
                })
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        return reject('Upload failed');
                    }
                })
                .then(responseData => {
                    resolve({
                        default: responseData.url
                    });
                })
                .catch(error => {
                    reject(error);
                });
            });
        });
    }
    
    abort() {
        // Abort the upload if needed
    }
}

// Export for modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initDjangoCKEditor5
    };
}