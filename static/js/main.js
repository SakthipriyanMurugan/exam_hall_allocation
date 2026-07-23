// Main JavaScript for Exam System UI Interactions

document.addEventListener('DOMContentLoaded', function() {
    // Sidebar toggle for mobile & compact view
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');

    if (sidebarCollapse && sidebar) {
        sidebarCollapse.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }

    // Dynamic Live Search in Tables
    const searchInputs = document.querySelectorAll('.table-search');
    searchInputs.forEach(input => {
        input.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const tableId = this.getAttribute('data-table');
            const table = document.getElementById(tableId);
            if (!table) return;

            const rows = table.getElementsByTagName('tr');
            for (let i = 1; i < rows.length; i++) {
                const text = rows[i].textContent.toLowerCase();
                if (text.includes(filter)) {
                    rows[i].style.display = '';
                } else {
                    rows[i].style.display = 'none';
                }
            }
        });
    });
});
