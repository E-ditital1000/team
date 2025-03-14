/**
 * Blog Admin Enhanced JavaScript
 * Provides enhanced interactivity for the blog admin interface
 */

(function($) {
    // Wait for the DOM to be ready
    $(document).ready(function() {
        // Initialize functions
        initStatusBadges();
        enhanceFilterDisplay();
        initFeaturedToggle();
        initFormEnhancements();
        initPreviewButtons();
        
        // Add chart initializations if we're on the stats page
        if (document.getElementById('blog-stats-charts')) {
            initBlogStatCharts();
        }
    });

    /**
     * Enhances the appearance of status badges
     */
    function initStatusBadges() {
        // Add proper Bootstrap badge styling
        $('.field-status_badge .badge').each(function() {
            var status = $(this).text().trim().toLowerCase();
            if (status === 'published') {
                $(this).addClass('badge-success');
            } else if (status === 'draft') {
                $(this).addClass('badge-secondary');
            }
        });
    }

    /**
     * Improves the display of filter sidebar
     */
    function enhanceFilterDisplay() {
        // Highlight active filters
        $('#changelist-filter li.selected').addClass('active');
        
        // Add toggle functionality for filter groups
        $('#changelist-filter h3').click(function() {
            $(this).next('ul').slideToggle(200);
            $(this).toggleClass('collapsed');
        });
    }

    /**
     * Enhances the featured checkbox to be more visually apparent
     */
    function initFeaturedToggle() {
        // Replace featured checkboxes with toggle switches or star icons
        $('.field-featured input[type="checkbox"]').each(function() {
            var isChecked = $(this).is(':checked');
            var toggleHtml = '<label class="switch">' +
                '<input type="checkbox" name="' + $(this).attr('name') + '" ' + 
                (isChecked ? 'checked' : '') + '>' +
                '<span class="slider round"></span>' +
                '</label>';
            
            $(this).replaceWith(toggleHtml);
        });
    }

    /**
     * Adds enhancements to the blog post form
     */
    function initFormEnhancements() {
        // Add character counter for title field
        $('#id_title').after('<small class="char-counter">0/200</small>');
        $('#id_title').keyup(function() {
            var count = $(this).val().length;
            $(this).next('.char-counter').text(count + '/200');
            if (count > 180) {
                $(this).next('.char-counter').addClass('text-warning');
            } else {
                $(this).next('.char-counter').removeClass('text-warning');
            }
        });
        
        // Initialize slug generation from title for new posts
        if ($('#id_slug').val() === '') {
            $('#id_title').keyup(function() {
                var title = $(this).val();
                var slug = title.toLowerCase()
                    .replace(/[^\w\s-]/g, '')  // Remove non-word chars
                    .replace(/\s+/g, '-')      // Replace spaces with -
                    .replace(/-+/g, '-')       // Replace multiple - with single -
                    .trim();                    // Trim - from start and end
                
                $('#id_slug').val(slug);
            });
        }
        
        // Add tag input enhancement for the tags field
        if ($('#id_tags').length) {
            enhanceTagInput();
        }
    }

    /**
     * Converts the tags input into an enhanced UI
     */
    function enhanceTagInput() {
        var tagsInput = $('#id_tags');
        var tagsValue = tagsInput.val();
        var tags = tagsValue ? tagsValue.split(',').map(tag => tag.trim()) : [];
        
        // Create container for tags UI
        var tagsContainer = $('<div class="tags-container"></div>');
        var tagsDisplay = $('<div class="tags-display"></div>');
        var tagInput = $('<input type="text" class="tag-input" placeholder="Add a tag and press Enter">');
        
        // Add initial tags
        tags.forEach(function(tag) {
            if (tag) {
                addTagElement(tag, tagsDisplay);
            }
        });
        
        // Add container to the DOM
        tagsContainer.append(tagsDisplay);
        tagsContainer.append(tagInput);
        tagsInput.after(tagsContainer);
        tagsInput.hide();
        
        // Handle adding new tags
        tagInput.keydown(function(e) {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                var value = $(this).val().trim();
                if (value) {
                    // Add the tag
                    tags.push(value);
                    addTagElement(value, tagsDisplay);
                    
                    // Update the original input
                    tagsInput.val(tags.join(', '));
                    
                    // Clear the input
                    $(this).val('');
                }
            }
        });
        
        // Function to add a tag element to the display
        function addTagElement(tag, container) {
            var tagElement = $('<span class="tag"></span>').text(tag);
            var removeButton = $('<span class="remove-tag">×</span>');
            
            removeButton.click(function() {
                // Remove from array
                var index = tags.indexOf(tag);
                if (index !== -1) {
                    tags.splice(index, 1);
                }
                
                // Update the original input
                tagsInput.val(tags.join(', '));
                
                // Remove the element
                tagElement.remove();
            });
            
            tagElement.append(removeButton);
            container.append(tagElement);
        }
    }

    /**
     * Initializes post preview buttons
     */
    function initPreviewButtons() {
        // Add preview button next to the save buttons
        if ($('body').hasClass('change-form') && 
            $('form#blogpost_form').length &&
            $('select#id_status').val() === 'published') {
            
            var postId = window.location.pathname.split('/').filter(Boolean).pop();
            var previewUrl = '/admin/blog/preview/' + postId + '/';
            
            var previewButton = $('<a></a>')
                .attr('href', previewUrl)
                .attr('target', '_blank')
                .addClass('button preview-button')
                .text('Preview');
                
            // Add the button to the submit row
            $('.submit-row').prepend(previewButton);
        }
    }

    /**
     * Initializes charts on the blog statistics page
     * Requires Chart.js to be loaded
     */
    function initBlogStatCharts() {
        // Only run if Chart.js is available
        if (typeof Chart === 'undefined') return;
        
        // Posts by status chart
        var statusCtx = document.getElementById('posts-by-status-chart').getContext('2d');
        var statusChart = new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: ['Published', 'Draft'],
                datasets: [{
                    data: [
                        document.getElementById('published-count').dataset.value,
                        document.getElementById('draft-count').dataset.value
                    ],
                    backgroundColor: ['#28a745', '#6c757d']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: {
                    position: 'bottom'
                }
            }
        });
        
        // Posts by month chart
        var postsMonthlyCtx = document.getElementById('posts-monthly-chart').getContext('2d');
        var postsMonthlyData = JSON.parse(document.getElementById('posts-monthly-chart').dataset.chart);
        
        var postsMonthlyChart = new Chart(postsMonthlyCtx, {
            type: 'bar',
            data: {
                labels: postsMonthlyData.labels,
                datasets: [{
                    label: 'Posts',
                    data: postsMonthlyData.values,
                    backgroundColor: '#007bff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
                            precision: 0
                        }
                    }]
                }
            }
        });
        
        // Post views chart
        var viewsCtx = document.getElementById('views-chart').getContext('2d');
        var viewsData = JSON.parse(document.getElementById('views-chart').dataset.chart);
        
        var viewsChart = new Chart(viewsCtx, {
            type: 'line',
            data: {
                labels: viewsData.labels,
                datasets: [{
                    label: 'Views',
                    data: viewsData.values,
                    borderColor: '#fd7e14',
                    backgroundColor: 'rgba(253, 126, 20, 0.1)',
                    borderWidth: 2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    yAxes: [{
                        ticks: {
                            beginAtZero: true
                        }
                    }]
                }
            }
        });
    }

})(django.jQuery);