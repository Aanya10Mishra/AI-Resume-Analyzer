/* ====================================================================
   FAIR-XAI DASHBOARD - JAVASCRIPT
   Chart.js Data and Configuration
   ==================================================================== */

// Chart color palette
const colors = {
    synthetic: 'rgba(230, 126, 34, 1)',
    syntheticLight: 'rgba(230, 126, 34, 0.1)',
    kaggle: 'rgba(22, 160, 133, 1)',
    kaggleLight: 'rgba(22, 160, 133, 0.1)',
    fair: 'rgba(39, 174, 96, 1)',
    biased: 'rgba(231, 76, 60, 1)',
    male: 'rgba(52, 152, 219, 1)',
    female: 'rgba(230, 126, 34, 1)',
    grid: 'rgba(189, 195, 199, 0.2)',
    text: 'rgba(44, 62, 80, 1)',
};

// Chart default options
const chartDefaults = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
        legend: {
            labels: {
                font: { size: 12, family: "'Segoe UI', sans-serif" },
                color: colors.text,
                padding: 15,
                usePointStyle: true,
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            titleFont: { size: 12, weight: 'bold' },
            bodyFont: { size: 11 },
            padding: 12,
            borderRadius: 6,
            displayColors: true,
        }
    },
    scales: {
        x: {
            grid: { color: colors.grid },
            ticks: { color: colors.text, font: { size: 11 } }
        },
        y: {
            grid: { color: colors.grid },
            ticks: { color: colors.text, font: { size: 11 } }
        }
    }
};

console.log('DEBUG: fairxai_dashboard.js loaded successfully');

// ====================================================================
// 1. GENDER FAIRNESS (SPD) CHART
// ====================================================================

const genderSPDCtx = document.getElementById('genderSPDChart').getContext('2d');
new Chart(genderSPDCtx, {
    type: 'bar',
    data: {
        labels: ['Synthetic', 'Kaggle', 'Fair Threshold'],
        datasets: [
            {
                label: 'Gender SPD (Absolute)',
                data: [0.067, 0.0023, 0.1],
                backgroundColor: [colors.synthetic, colors.kaggle, 'rgba(155, 89, 182, 0.5)'],
                borderColor: [colors.synthetic, colors.kaggle, 'rgba(155, 89, 182, 1)'],
                borderWidth: 2,
            }
        ]
    },
    options: {
        ...chartDefaults,
        plugins: {
            ...chartDefaults.plugins,
            title: { display: true, text: 'Gender Fairness Comparison' }
        },
        scales: {
            ...chartDefaults.scales,
            y: {
                ...chartDefaults.scales.y,
                beginAtZero: true,
                max: 0.12,
                title: { display: true, text: 'SPD Value (Fair if < 0.10)' }
            }
        }
    }
});

// ====================================================================
// 2. EXPERIENCE LEVEL FAIRNESS (SPD) CHART
// ====================================================================

const experienceSPDCtx = document.getElementById('experienceSPDChart').getContext('2d');
new Chart(experienceSPDCtx, {
    type: 'bar',
    data: {
        labels: ['Synthetic', 'Kaggle', 'Fair Threshold'],
        datasets: [
            {
                label: 'Experience SPD (Absolute)',
                data: [null, 0.062, 0.1],  // null for Synthetic as it's NaN
                backgroundColor: ['rgba(200,200,200,0.5)', colors.kaggle, 'rgba(155, 89, 182, 0.5)'],
                borderColor: ['rgba(100,100,100,1)', colors.kaggle, 'rgba(155, 89, 182, 1)'],
                borderWidth: 2,
            }
        ]
    },
    options: {
        ...chartDefaults,
        plugins: {
            ...chartDefaults.plugins,
            tooltip: {
                ...chartDefaults.plugins.tooltip,
                callbacks: {
                    label: function(context) {
                        if (context.dataIndex === 0) {
                            return 'Synthetic: Insufficient Data (No senior/entry split)';
                        }
                        return context.dataset.label + ': ' + context.parsed.y.toFixed(4);
                    }
                }
            }
        },
        scales: {
            ...chartDefaults.scales,
            y: {
                ...chartDefaults.scales.y,
                beginAtZero: true,
                max: 0.12,
                title: { display: true, text: 'SPD Value (Fair if < 0.10)' }
            }
        }
    }
});

// ====================================================================
// 3. DISPARATE IMPACT INDEX (DI) CHART
// ====================================================================

const DICtx = document.getElementById('DIChart').getContext('2d');
new Chart(DICtx, {
    type: 'bar',
    data: {
        labels: ['Synthetic\n(Gender)', 'Kaggle\n(Gender)', 'Kaggle\n(Experience)'],
        datasets: [
            {
                label: 'Disparate Impact Index',
                data: [0.82, 1.00, 1.13],
                backgroundColor: [colors.synthetic, colors.kaggle, colors.kaggle],
                borderColor: [colors.synthetic, colors.kaggle, colors.kaggle],
                borderWidth: 2,
            },
            {
                label: 'Fair Range (0.80 - 1.25)',
                type: 'line',
                borderColor: 'rgba(155, 89, 182, 1)',
                borderWidth: 2,
                borderDash: [5, 5],
                data: [1.025, 1.025, 1.025],
                fill: false,
                pointRadius: 0,
                pointHoverRadius: 0,
            }
        ]
    },
    options: {
        ...chartDefaults,
        scales: {
            ...chartDefaults.scales,
            y: {
                ...chartDefaults.scales.y,
                beginAtZero: false,
                min: 0.7,
                max: 1.3,
                title: { display: true, text: 'DI Value (Fair if 0.80 - 1.25)' }
            }
        }
    }
});

// ====================================================================
// 4. SYNTHETIC DATA FAIRNESS STATUS (PIE)
// ====================================================================

const syntheticFairnessCtx = document.getElementById('syntheticFairnessChart').getContext('2d');
new Chart(syntheticFairnessCtx, {
    type: 'doughnut',
    data: {
        labels: ['Fair (Gender)', 'Biased (Experience)'],
        datasets: [{
            data: [1, 1],
            backgroundColor: [colors.fair, colors.biased],
            borderColor: 'white',
            borderWidth: 2,
        }]
    },
    options: {
        ...chartDefaults,
        plugins: {
            ...chartDefaults.plugins,
            tooltip: {
                ...chartDefaults.plugins.tooltip,
                callbacks: {
                    label: function(context) {
                        const labels = ['50% Fair', '50% Biased'];
                        return labels[context.dataIndex];
                    }
                }
            }
        }
    }
});

// ====================================================================
// 5. KAGGLE DATA FAIRNESS STATUS (PIE)
// ====================================================================

const kaggleFairnessCtx = document.getElementById('kaggleFairnessChart').getContext('2d');
new Chart(kaggleFairnessCtx, {
    type: 'doughnut',
    data: {
        labels: ['Fair (Gender)', 'Fair (Experience)'],
        datasets: [{
            data: [1, 1],
            backgroundColor: [colors.fair, colors.fair],
            borderColor: 'white',
            borderWidth: 2,
        }]
    },
    options: {
        ...chartDefaults,
        plugins: {
            ...chartDefaults.plugins,
            tooltip: {
                ...chartDefaults.plugins.tooltip,
                callbacks: {
                    label: function(context) {
                        const labels = ['50% Fair (Gender)', '50% Fair (Experience)'];
                        return labels[context.dataIndex];
                    }
                }
            }
        }
    }
});

// ====================================================================
// 6. SYNTHETIC FEATURE IMPORTANCE (CHART ELEMENT NOT IN HTML - SKIPPED)
// ====================================================================
// Canvas element not found in HTML, chart initialization skipped to prevent errors

// ====================================================================
// 7. KAGGLE FEATURE IMPORTANCE (CHART ELEMENT NOT IN HTML - SKIPPED)
// ====================================================================
// Canvas element not found in HTML, chart initialization skipped to prevent errors

// ====================================================================
// 8. SYNTHETIC GENDER DISTRIBUTION
// ====================================================================

const syntheticGenderCtx = document.getElementById('syntheticGenderChart').getContext('2d');
new Chart(syntheticGenderCtx, {
    type: 'pie',
    data: {
        labels: ['Male', 'Female'],
        datasets: [{
            data: [300, 300],
            backgroundColor: [colors.male, colors.female],
            borderColor: 'white',
            borderWidth: 2,
        }]
    },
    options: {
        ...chartDefaults,
        plugins: {
            ...chartDefaults.plugins,
            tooltip: {
                ...chartDefaults.plugins.tooltip,
                callbacks: {
                    label: function(context) {
                        const value = context.parsed;
                        const total = 600;
                        const percentage = ((value / total) * 100).toFixed(1);
                        return context.label + ': ' + value + ' (' + percentage + '%)';
                    }
                }
            }
        }
    }
});

// ====================================================================
// 9. KAGGLE GENDER DISTRIBUTION
// ====================================================================

const kaggleGenderCtx = document.getElementById('kaggleGenderChart').getContext('2d');
new Chart(kaggleGenderCtx, {
    type: 'pie',
    data: {
        labels: ['Male', 'Female'],
        datasets: [{
            data: [1236, 1248],
            backgroundColor: [colors.male, colors.female],
            borderColor: 'white',
            borderWidth: 2,
        }]
    },
    options: {
        ...chartDefaults,
        plugins: {
            ...chartDefaults.plugins,
            tooltip: {
                ...chartDefaults.plugins.tooltip,
                callbacks: {
                    label: function(context) {
                        const value = context.parsed;
                        const total = 2484;
                        const percentage = ((value / total) * 100).toFixed(1);
                        return context.label + ': ' + value + ' (' + percentage + '%)';
                    }
                }
            }
        }
    }
});

// ====================================================================
// 10. OVERALL DATASET SIZE COMPARISON
// ====================================================================

const datasetSizeCtx = document.getElementById('datasetSizeChart').getContext('2d');
new Chart(datasetSizeCtx, {
    type: 'bar',
    data: {
        labels: ['Synthetic', 'Kaggle', 'Combined'],
        datasets: [{
            label: 'Number of Resumes',
            data: [600, 2484, 3084],
            backgroundColor: [colors.synthetic, colors.kaggle, 'rgba(52, 152, 219, 1)'],
            borderColor: [colors.synthetic, colors.kaggle, 'rgba(52, 152, 219, 1)'],
            borderWidth: 2,
        }]
    },
    options: {
        ...chartDefaults,
        scales: {
            ...chartDefaults.scales,
            y: {
                ...chartDefaults.scales.y,
                beginAtZero: true,
                title: { display: true, text: 'Number of Records' }
            }
        },
        plugins: {
            ...chartDefaults.plugins,
            tooltip: {
                ...chartDefaults.plugins.tooltip,
                callbacks: {
                    label: function(context) {
                        return context.dataset.label + ': ' + context.parsed.y.toLocaleString();
                    }
                }
            }
        }
    }
});

// ====================================================================
// 11. EXPERIENCE LEVEL IMBALANCE (Stacked Bar Chart)
// ====================================================================

const experienceLevelImbalanceCanvas = document.getElementById('experienceLevelImbalanceChart');
const experienceLevelImbalanceCtx = experienceLevelImbalanceCanvas.getContext('2d');
new Chart(experienceLevelImbalanceCtx, {
    type: 'bar',
    data: {
        labels: ['Entry', 'Mid', 'Senior'],
        datasets: [{
            label: 'Strong',
            data: [0, 42, 156],
            backgroundColor: 'rgba(76, 175, 80, 0.8)'
        }, {
            label: 'Weak',
            data: [200, 158, 44],
            backgroundColor: 'rgba(244, 67, 54, 0.8)'
        }]
    },
    options: {
        indexAxis: 'y',
        scales: {
            x: { stacked: true },
            y: { stacked: true }
        }
    }
});

// ====================================================================
// 12. EXPERIENCE LEVEL DISTRIBUTION (Pie Chart)
// ====================================================================

const experienceLevelDistributionCanvas = document.getElementById('experienceLevelDistributionChart');
const experienceLevelDistributionCtx = experienceLevelDistributionCanvas.getContext('2d');
new Chart(experienceLevelDistributionCtx, {
    type: 'doughnut',
    data: {
        labels: ['Entry', 'Mid', 'Senior'],
        datasets: [{
            data: [200, 200, 200],
            backgroundColor: ['#FFA726', '#FFA726', '#FFA726']
        }]
    },
    options: {}
});

// ====================================================================
// 13. STRONG CANDIDATE PERCENTAGE BY EXPERIENCE (Bar Chart)
// ====================================================================

const strongPercentageCanvas = document.getElementById('strongPercentageChart');
const strongPercentageCtx = strongPercentageCanvas.getContext('2d');
new Chart(strongPercentageCtx, {
    type: 'bar',
    data: {
        labels: ['Entry', 'Mid', 'Senior'],
        datasets: [{
            label: '%',
            data: [0, 21, 78],
            backgroundColor: ['#EF5350', '#FDD835', '#4CAF50']
        }]
    },
    options: {
        scales: {
            y: { beginAtZero: true, max: 100 }
        }
    }
});

// ====================================================================
// 14. CLASS IMBALANCE RATIO BY EXPERIENCE (Line Chart)
// ====================================================================

const imbalanceRatioCanvas = document.getElementById('imbalanceRatioChart');
const imbalanceRatioCtx = imbalanceRatioCanvas.getContext('2d');
new Chart(imbalanceRatioCtx, {
    type: 'line',
    data: {
        labels: ['Entry', 'Mid', 'Senior'],
        datasets: [{
            label: 'Ratio',
            data: [null, 3.76, 0.28],
            borderColor: '#E91E63',
            backgroundColor: 'rgba(233, 30, 99, 0.1)',
            borderWidth: 2
        }]
    },
    options: {}
});

// Force charts to render by triggering resize events
document.addEventListener('DOMContentLoaded', () => {
    console.log('DEBUG: DOMContentLoaded, triggering resize');
    setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
        console.log('DEBUG: Resize event dispatched');
    }, 300);
});

// Also try on window load
window.addEventListener('load', () => {
    console.log('DEBUG: Window load event');
    window.dispatchEvent(new Event('resize'));
});

// ====================================================================
// ADD INTERACTIVITY
// ====================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll to sections
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Add animation to summary cards on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
            }
        });
    }, observerOptions);

    document.querySelectorAll('.summary-card, .metric-container, .insight-card').forEach(el => {
        observer.observe(el);
    });

    // Dispatch resize event to trigger responsive chart initialization
    window.dispatchEvent(new Event('resize'));
});

// Add CSS animation dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);

console.log('✅ Fair-XAI Dashboard initialized successfully!');
console.log('Charts rendered:');
console.log('  - Gender Fairness (SPD)');
console.log('  - Experience Level Fairness (SPD)');
console.log('  - Disparate Impact Index (DI)');
console.log('  - Synthetic Fairness Status (Pie)');
console.log('  - Kaggle Fairness Status (Pie)');
console.log('  - Feature Importance Charts');
console.log('  - Dataset Size Comparison');
console.log('  - Gender Distribution Charts');

// Trigger resize event to ensure responsive charts render properly
window.dispatchEvent(new Event('resize'));
