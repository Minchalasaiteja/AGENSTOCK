// Chart utilities for AGENSTOCK

class ChartManager {
    constructor() {
        this.charts = new Map();
    }

    createStockChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const defaultOptions = {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: data.label || 'Price',
                    data: data.values || [],
                    borderColor: data.color || '#3a86ff',
                    backgroundColor: this.hexToRgba(data.color || '#3a86ff', 0.1),
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        };

        // Merge custom options
        const mergedOptions = this.deepMerge(defaultOptions, options);
        const chart = new Chart(ctx, mergedOptions);
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    createPortfolioPieChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const colors = this.generateColors(data.length);
        
        const chart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.map(item => item.label),
                datasets: [{
                    data: data.map(item => item.value),
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    createPerformanceChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Performance',
                    data: data.values || [],
                    backgroundColor: data.values.map(value => 
                        value >= 0 ? 'rgba(6, 214, 160, 0.8)' : 'rgba(239, 71, 111, 0.8)'
                    ),
                    borderColor: data.values.map(value => 
                        value >= 0 ? 'rgb(6, 214, 160)' : 'rgb(239, 71, 111)'
                    ),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    updateChart(canvasId, newData) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.data = newData;
            chart.update();
        }
    }

    destroyChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.destroy();
            this.charts.delete(canvasId);
        }
    }

    generateColors(count) {
        const baseColors = [
            '#3a86ff', '#8338ec', '#ff006e', '#fb5607', '#ffbe0b',
            '#06d6a0', '#118ab2', '#ef476f', '#ffd166', '#073b4c'
        ];
        
        const colors = [];
        for (let i = 0; i < count; i++) {
            colors.push(baseColors[i % baseColors.length]);
        }
        return colors;
    }

    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    deepMerge(target, source) {
        const output = Object.assign({}, target);
        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target))
                        Object.assign(output, { [key]: source[key] });
                    else
                        output[key] = this.deepMerge(target[key], source[key]);
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }
        return output;
    }

    isObject(item) {
        return (item && typeof item === 'object' && !Array.isArray(item));
    }

    // Stock chart data utilities
    generateSampleStockData(days = 30, volatility = 0.02) {
        const data = {
            labels: [],
            values: [],
            volumes: []
        };

        let price = 100; // Starting price
        const today = new Date();

        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            
            data.labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
            
            // Generate random price movement
            const change = (Math.random() - 0.5) * 2 * volatility;
            price = price * (1 + change);
            data.values.push(price);
            
            // Generate volume
            data.volumes.push(Math.floor(Math.random() * 1000000) + 100000);
        }

        return data;
    }

    generateComparisonChartData(symbols, days = 30) {
        const datasets = [];
        const colors = this.generateColors(symbols.length);

        symbols.forEach((symbol, index) => {
            const stockData = this.generateSampleStockData(days);
            datasets.push({
                label: symbol,
                data: stockData.values,
                borderColor: colors[index],
                backgroundColor: this.hexToRgba(colors[index], 0.1),
                borderWidth: 2,
                fill: false,
                tension: 0.4
            });
        });

        return {
            labels: this.generateSampleStockData(days).labels,
            datasets: datasets
        };
    }
}

// Global chart manager instance
window.chartManager = new ChartManager();

// Utility functions for stock charts
function formatStockPrice(price) {
    return AGENSTOCK.formatCurrency(price);
}

function calculatePercentageChange(oldPrice, newPrice) {
    return ((newPrice - oldPrice) / oldPrice) * 100;
}

function formatPercentageChange(change) {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
}

// Demo chart initialization
function initializeDemoCharts() {
    // Sample stock chart
    const stockData = chartManager.generateSampleStockData(30);
    chartManager.createStockChart('demoStockChart', {
        labels: stockData.labels,
        values: stockData.values,
        label: 'Stock Price',
        color: '#3a86ff'
    });

    // Sample portfolio allocation
    const portfolioData = [
        { label: 'Technology', value: 45 },
        { label: 'Healthcare', value: 25 },
        { label: 'Finance', value: 15 },
        { label: 'Energy', value: 10 },
        { label: 'Other', value: 5 }
    ];
    chartManager.createPortfolioPieChart('demoPortfolioChart', portfolioData);

    // Sample performance chart
    const performanceData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        values: [5.2, 3.8, -2.1, 7.4, 4.9, 6.3]
    };
    chartManager.createPerformanceChart('demoPerformanceChart', performanceData);
}

// Initialize demo charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('demoStockChart')) {
        initializeDemoCharts();
    }
});