// Chart.js Configuration for Exam Allocation Dashboard

document.addEventListener('DOMContentLoaded', function() {
    if (typeof statsData === 'undefined') return;

    // 1. Department Distribution Chart (Doughnut)
    const deptCtx = document.getElementById('deptChart');
    if (deptCtx) {
        const deptLabels = statsData.dept_dist.map(d => d.code);
        const deptCounts = statsData.dept_dist.map(d => d.count);

        new Chart(deptCtx, {
            type: 'doughnut',
            data: {
                labels: deptLabels,
                datasets: [{
                    data: deptCounts,
                    backgroundColor: [
                        '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe',
                        '#0284c7', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    // 2. Hall Utilization Chart (Stacked Bar)
    const hallCtx = document.getElementById('hallChart');
    if (hallCtx) {
        const hallNames = statsData.hall_util.map(h => h.name);
        const usedSeats = statsData.hall_util.map(h => h.used);
        const emptySeats = statsData.hall_util.map(h => h.empty);

        new Chart(hallCtx, {
            type: 'bar',
            data: {
                labels: hallNames,
                datasets: [
                    {
                        label: 'Allocated / Used Seats',
                        data: usedSeats,
                        backgroundColor: '#2563eb'
                    },
                    {
                        label: 'Empty Seats',
                        data: emptySeats,
                        backgroundColor: '#e2e8f0'
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, beginAtZero: true }
                },
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    // 3. Subject Stats Chart (Bar)
    const subjCtx = document.getElementById('subjChart');
    if (subjCtx) {
        const subjLabels = statsData.subject_stats.map(s => s.code);
        const subjCounts = statsData.subject_stats.map(s => s.count);

        new Chart(subjCtx, {
            type: 'bar',
            data: {
                labels: subjLabels,
                datasets: [{
                    label: 'Allocated Students',
                    data: subjCounts,
                    backgroundColor: '#10b981'
                }]
            },
            options: {
                responsive: true,
                scales: { y: { beginAtZero: true } },
                plugins: { legend: { display: false } }
            }
        });
    }
});
