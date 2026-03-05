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

function goToDashboard() {
    window.location = "/dashboard";
}

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


// ======================================================
// LOGOUT
// ======================================================

async function logout() {
    await fetch("/logout", { credentials: "include" });
    window.location = "/";
}


// ======================================================
// DASHBOARD
// ======================================================

async function loadDashboard() {

    const res = await fetch("/dashboard-data", {
        credentials: "include"
    });

    const data = await res.json();

    document.getElementById("totalValue").innerText =
        "₹ " + Number(data.totalValue).toLocaleString("en-IN");

    document.getElementById("totalDue").innerText =
        "₹ " + Number(data.totalDue).toLocaleString("en-IN");

    document.getElementById("totalInvoices").innerText =
        data.totalInvoices;

    document.getElementById("uniqueCustomers").innerText =
        data.uniqueCustomers;
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

function applyFilters() {

    let data = [...invoiceData];

    const startDate = document.getElementById("startDate").value;
    const endDate = document.getElementById("endDate").value;
    const owner = document.getElementById("ownerFilter").value;

    const dateSort = document.getElementById("dateSort").value;
    const financialSort = document.getElementById("financialSort").value;
    const ageingSort = document.getElementById("ageingSort").value;
    const order = document.getElementById("order").value;


    // ---------- FILTERS ----------

    if (owner)
        data = data.filter(i => i.owner === owner);

    if (startDate) {
        const sd = new Date(startDate);
        data = data.filter(i => parseDate(i.start) >= sd);
    }

    if (endDate) {
        const ed = new Date(endDate);
        data = data.filter(i => parseDate(i.end) <= ed);
    }


    // ---------- SORTING ----------

    let sortField = null;

    if (dateSort) sortField = dateSort;
    else if (financialSort) sortField = financialSort;
    else if (ageingSort) sortField = ageingSort;

    if (sortField) {

        data.sort((a, b) => {

            let A = a[sortField];
            let B = b[sortField];

            if (sortField === "start" || sortField === "end") {
                A = parseDate(A);
                B = parseDate(B);
            } else {
                A = Number(A);
                B = Number(B);
            }

            return order === "asc" ? A - B : B - A;
        });
    }

    renderTable(data);
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

    data.forEach(i => {

        table.innerHTML += `
        <tr>
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

    const table = document.getElementById("customerTable");

    customerCache.forEach(c => {

        table.innerHTML += `
        <tr class="customer-row"
            onmousemove="showPopup(event,'${c.customer}')"
            onmouseleave="hidePopup()">
            <td>${c.customer}</td>
            <td>₹ ${Number(c.total_due).toLocaleString("en-IN")}</td>
            <td>${c.invoices.length}</td>
        </tr>`;
    });
}


// ======================================================
// POPUP
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

    agentCache.forEach(a => {

        table.innerHTML += `
        <tr class="agent-row"
            onmousemove="showAgentPopup(event,'${a.owner}')"
            onmouseleave="hideAgentPopup()">

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