// static/admin/js/json_prettify.js
document.addEventListener('DOMContentLoaded', function() {
    const jsonFields = document.querySelectorAll('textarea[name$="education"], textarea[name$="skills"], textarea[name$="projects"], textarea[name$="recommendations"]');
    
    jsonFields.forEach(field => {
        field.addEventListener('blur', function() {
            try {
                const obj = JSON.parse(this.value);
                this.value = JSON.stringify(obj, null, 2);
            } catch (e) {
                // If JSON is invalid, leave as is
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const jsonInputs = document.querySelectorAll('.json-input');
    
    jsonInputs.forEach(input => {
        // Format on load if there's existing data
        try {
            const value = input.value;
            if (value) {
                const obj = JSON.parse(value);
                input.value = JSON.stringify(obj, null, 2);
            }
        } catch (e) {}

        // Format on blur
        input.addEventListener('blur', function() {
            try {
                const obj = JSON.parse(this.value);
                this.value = JSON.stringify(obj, null, 2);
            } catch (e) {
                // If JSON is invalid, leave as is
            }
        });
    });
});