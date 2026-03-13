// ======================================================
// GLOBAL STORAGE
// ======================================================

let invoiceData = [];
let customerCache = [];

// ======================================================
// INITIALIZATION
// ======================================================

document.addEventListener("DOMContentLoaded", () => {
    const dateDisplay = document.getElementById("todayDateDisplay");
    if (dateDisplay) {
        const today = new Date();
        const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
        dateDisplay.innerText = today.toLocaleDateString('en-IN', options);
    }
});


// ======================================================
// NAVIGATION
// ======================================================

function goToInvoices() {
    window.location = "/invoices-page";
}

function goToCustomers() {
    window.location = "/customers-page";
}


// ======================================================
// LOGIN
// ======================================================

async function login() {

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const error = document.getElementById("error");

    const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password })
    });

    if (res.ok)
        window.location = "/upload-page";
    else
        error.innerText = "Invalid Credentials";
}

function togglePasswordVisibility() {
    const passwordInput = document.getElementById("password");
    const eyeIcon = document.getElementById("eye-icon");
    if (!passwordInput) return;
    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        // Switch to "eye-off" (slash through)
        eyeIcon.innerHTML = `
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"></path>
            <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"></path>
            <line x1="1" y1="1" x2="23" y2="23"></line>`;
    } else {
        passwordInput.type = "password";
        // Switch back to "eye" (normal)
        eyeIcon.innerHTML = `
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>`;
    }
}


// ======================================================
// LOGOUT
// ======================================================

async function logout() {
    await fetch("/logout", { credentials: "include" });
    window.location = "/";
}


// ======================================================
// LOAD INVOICES PAGE
// ======================================================

async function loadInvoices() {

    const res = await fetch("/invoices", {
        credentials: "include"
    });

    invoiceData = await res.json();

    populateOwnerDropdown(invoiceData);
    renderTable(invoiceData);
}


// ======================================================
// OWNER DROPDOWN
// ======================================================

function populateOwnerDropdown(data) {

    const owners = [...new Set(data.map(i => i.owner).filter(Boolean))];

    const dropdown = document.getElementById("ownerFilter");

    dropdown.innerHTML = `<option value="">All Owners</option>`;

    owners.forEach(o => {
        dropdown.innerHTML += `<option value="${o}">${o}</option>`;
    });
}


// ======================================================
// DATE PARSER
// ======================================================

function parseDate(str) {
    if (!str) return null;

    const p = str.split("/");
    return new Date(p[2], p[1] - 1, p[0]);
}


// ======================================================
// APPLY FILTERS  
// ======================================================

function applyDailyFilters() {

    let filtered = [...invoiceData];

    const cust = document.getElementById('custFilter').value.toLowerCase();
    const status = document.getElementById('statusFilter').value;
    const ageing = document.getElementById('ageingFilter').value;
    const owner = document.getElementById('ownerFilter').value;

    const startDate = document.getElementById('startDateFilter').value;
    const endDate = document.getElementById('endDateFilter').value;

    const sortField = document.getElementById('sortField').value;
    const dateSortField = document.getElementById('dateSortField').value;
    const sortOrder = document.getElementById('sortOrder').value;

    // SEARCH FILTER
    if (cust) {
        filtered = filtered.filter(i =>
            (i.customer || "").toLowerCase().includes(cust) ||
            (i.invoice || "").toLowerCase().includes(cust) ||
            (i.owner || "").toLowerCase().includes(cust)
        );
    }

    // STATUS FILTER
    if (status) {
        filtered = filtered.filter(i => i.status === status);
    }

    // OWNER FILTER
    if (owner) {
        filtered = filtered.filter(i => i.owner === owner);
    }

    // AGEING FILTER
    if (ageing) {

        filtered = filtered.filter(i => {

            const age = Number(i.age) || 0;

            if (ageing === "gt45") return age > 45;
            if (ageing === "31_45") return age >= 31 && age <= 45;
            if (ageing === "16_30") return age >= 16 && age <= 30;
            if (ageing === "1_15") return age >= 1 && age <= 15;
            if (ageing === "current") return age <= 0;

            return true;
        });

    }

    // DATE FILTER
    if (startDate || endDate) {

        filtered = filtered.filter(i => {

            const start = i.start ? new Date(i.start) : null;
            const end = i.end ? new Date(i.end) : null;

            if (startDate) {
                const filterStart = new Date(startDate);
                if (start && start < filterStart) return false;
            }

            if (endDate) {
                const filterEnd = new Date(endDate);
                if (end && end > filterEnd) return false;
            }

            return true;

        });

    }

    // SORTING
    filtered.sort((a, b) => {

        let valA;
        let valB;

        // DATE SORT
        if (sortField === "date") {

            valA = new Date(a[dateSortField] || "1900-01-01");
            valB = new Date(b[dateSortField] || "1900-01-01");

        }

        // NUMBER SORT
        else if (['amount', 'due', 'age'].includes(sortField)) {

            valA = Number(a[sortField]) || 0;
            valB = Number(b[sortField]) || 0;

        }

        // TEXT SORT
        else {

            valA = (a[sortField] || "").toString().toLowerCase();
            valB = (b[sortField] || "").toString().toLowerCase();

        }

        if (sortOrder === "asc") return valA > valB ? 1 : -1;
        else return valA < valB ? 1 : -1;

    });

    renderTable(filtered);
}


// ======================================================
// TABLE RENDER
// ======================================================

function renderTable(data) {

    const table = document.getElementById("invoiceTableBody");
    const msg = document.getElementById("noDataMessage");

    table.innerHTML = "";

    if (!data.length) {
        msg.classList.remove("hidden");
        return;
    }

    msg.classList.add("hidden");

    data.forEach((i, idx) => {
        table.innerHTML += `
        <tr>
            <td style="color:#666; font-size:11px;">${idx + 1}</td>
            <td>${i.invoice}</td>
            <td>${i.type}</td>
            <td>${i.customer}</td>
            <td>₹ ${Number(i.amount).toLocaleString("en-IN")}</td>
            <td>₹ ${Number(i.due).toLocaleString("en-IN")}</td>
            <td>${i.start}</td>
            <td>${i.end}</td>
            <td>${i.ageing}</td>
            <td>${i.owner}</td>
            <td>${i.status}</td>
        </tr>`;
    });
}


// ======================================================
// CUSTOMERS PAGE
// ======================================================

async function loadCustomersPage() {

    const res = await fetch("/customers-data", {
        credentials: "include"
    });

    customerCache = await res.json();
    renderCustomers(customerCache);
}

function renderCustomers(data) {
    const table = document.getElementById("customerTable");
    if (!table) return;
    table.innerHTML = "";

    data.forEach((c, idx) => {
        table.innerHTML += `
        <tr class="customer-row"
            onmousemove="showPopup(event,'${c.customer}')"
            onmouseleave="hidePopup()">
            <td style="color:#666; font-size:11px;">${idx + 1}</td>
            <td>${c.customer}</td>
            <td>₹ ${Number(c.total_due).toLocaleString("en-IN")}</td>
            <td>${c.invoices.length}</td>
        </tr>`;
    });
}

function sortCustomers() {
    const sortVal = document.getElementById("dueSort").value;
    let sortedData = [...customerCache];

    if (sortVal === "high") {
        sortedData.sort((a, b) => (Number(b.total_due) || 0) - (Number(a.total_due) || 0));
    } else if (sortVal === "low") {
        sortedData.sort((a, b) => (Number(a.total_due) || 0) - (Number(b.total_due) || 0));
    }
    // "none" uses the default order from cache

    renderCustomers(sortedData);
}


// ======================================================
// CUSTOMER POPUP
// ======================================================

function showPopup(event, name) {

    const popup = document.getElementById("invoicePopup");

    const customer = customerCache.find(c => c.customer === name);

    let html = `<h4>${customer.customer}</h4>`;
    html += `<p><b>Total Due:</b> ₹ ${customer.total_due.toLocaleString("en-IN")}</p><hr>`;

    customer.invoices.forEach(inv => {
        html += `<div>${inv.invoice} | ₹${inv.due.toLocaleString("en-IN")} | ${inv.status}</div>`;
    });

    popup.innerHTML = html;
    popup.style.top = event.pageY + 15 + "px";
    popup.style.left = event.pageX + 15 + "px";
    popup.classList.remove("hidden");
}

function hidePopup() {
    document.getElementById("invoicePopup").classList.add("hidden");
}


// ================= AGENT PAGE NAVIGATION =================

function goToAgentPage() {
    window.location = "/agent-page";
}


// ================= LOAD AGENT PAGE =================

let agentCache = [];

async function loadAgentPage() {

    const res = await fetch("/agent-data", {
        credentials: "include"
    });

    agentCache = await res.json();

    const table = document.getElementById("agentTable");

    agentCache.forEach((a, idx) => {
        table.innerHTML += `
        <tr class="agent-row"
            onmousemove="showAgentPopup(event,'${a.owner}')"
            onmouseleave="hideAgentPopup()">
            <td style="color:#666; font-size:11px;">${idx + 1}</td>
            <td>${a.owner}</td>
            <td>₹ ${Number(a.total_amount).toLocaleString("en-IN")}</td>
            <td>₹ ${Number(a.total_due).toLocaleString("en-IN")}</td>
            <td>${a.invoice_count}</td>
        </tr>`;
    });
}


// ================= AGENT POPUP =================

function showAgentPopup(event, name) {

    const popup = document.getElementById("agentPopup");

    const agent = agentCache.find(a => a.owner === name);

    let html = `<h4>${agent.owner}</h4>`;
    html += `<p><b>Total Amount:</b> ₹ ${agent.total_amount.toLocaleString("en-IN")}</p>`;
    html += `<p><b>Total Due:</b> ₹ ${agent.total_due.toLocaleString("en-IN")}</p><hr>`;

    agent.invoices.forEach(inv => {
        html += `<div>${inv.invoice} | ${inv.customer} | ₹${inv.due.toLocaleString("en-IN")}</div>`;
    });

    popup.innerHTML = html;
    popup.style.top = event.pageY + 15 + "px";
    popup.style.left = event.pageX + 15 + "px";
    popup.classList.remove("hidden");
}

function hideAgentPopup() {
    document.getElementById("agentPopup").classList.add("hidden");
}