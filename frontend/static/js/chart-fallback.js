// Fallback Chart implementation when Chart.js is not available
// This provides basic functionality to display data without charts

if (typeof Chart === 'undefined') {
    console.warn('Chart.js not loaded, using fallback display');
    
    window.Chart = function(ctx, config) {
        // Store the canvas and config
        this.ctx = ctx;
        this.canvas = ctx.canvas;
        this.config = config;
        this.data = config.data;
        
        // Create a simple data display instead of a chart
        this._createFallbackDisplay();
    };
    
    Chart.prototype._createFallbackDisplay = function() {
        const container = this.canvas.parentElement;
        
        // Create a div to show data summary
        const fallback = document.createElement('div');
        fallback.className = 'chart-fallback';
        fallback.style.cssText = 'padding: 20px; background: #f0f0f0; border-radius: 8px; margin: 10px 0;';
        
        // Get latest values from datasets
        const datasets = this.config.data.datasets;
        if (datasets && datasets.length > 0) {
            let html = '<div style="font-size: 14px;">';
            html += '<strong>Latest Values:</strong><br>';
            
            datasets.forEach(dataset => {
                if (dataset.data && dataset.data.length > 0 && !dataset.hidden) {
                    const latestValue = dataset.data[dataset.data.length - 1];
                    if (latestValue !== null && latestValue !== undefined) {
                        html += `<div style="margin: 5px 0;">
                            <span style="color: ${dataset.borderColor || '#000'};">●</span>
                            <strong>${dataset.label}:</strong> ${typeof latestValue === 'number' ? latestValue.toFixed(2) : latestValue}
                        </div>`;
                    }
                }
            });
            
            html += '</div>';
            fallback.innerHTML = html;
        } else {
            fallback.innerHTML = '<em>Chart data available but Chart.js library is not loaded.</em>';
        }
        
        // Hide the canvas and show fallback
        this.canvas.style.display = 'none';
        container.insertBefore(fallback, this.canvas);
    };
    
    Chart.prototype.destroy = function() {
        // Clean up fallback display
        const container = this.canvas.parentElement;
        const fallback = container.querySelector('.chart-fallback');
        if (fallback) {
            fallback.remove();
        }
        this.canvas.style.display = 'block';
    };
    
    Chart.prototype.update = function() {
        // For fallback, we just recreate the display
        this.destroy();
        this._createFallbackDisplay();
    };
}
