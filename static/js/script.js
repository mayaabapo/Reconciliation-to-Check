document.addEventListener('DOMContentLoaded', function() {

    const select = document.getElementById('top_select');
    const tableBody = document.querySelector('#clientsTable tbody');

    if (!select || !tableBody) return;

    // Read all rows into an array
    const allClients = [];
    tableBody.querySelectorAll('tr').forEach(row => {
        allClients.push({
            code: row.cells[0].innerText,
            name: row.cells[1].innerText,
            count: parseInt(row.cells[2].innerText) || 0,
            breakdown: row.cells[3].innerText
        });
    });

    // Sort by count descending
    allClients.sort((a, b) => b.count - a.count);

    function renderClients(limit) {
        tableBody.innerHTML = '';

        let n = limit === 'all' 
            ? allClients.length 
            : Math.min(parseInt(limit), allClients.length);

        for (let i = 0; i < n; i++) {
            const c = allClients[i];
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${c.code}</td>
                <td>${c.name}</td>
                <td>${c.count}</td>
                <td>${c.breakdown}</td>
            `;
            tableBody.appendChild(tr);
        }
    }

    // Initial render: Top 10
    renderClients('10');

    // Update table on select change
    select.addEventListener('change', function() {
        renderClients(this.value);
    });

    // Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );

    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

});