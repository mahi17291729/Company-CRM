import sqlite3
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
DB_NAME = "crm.db"


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                industry TEXT NOT NULL,
                location TEXT NOT NULL,
                employees INTEGER NOT NULL,
                linkedin_url TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                title TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE
            )
        """)
        conn.commit()


init_db()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mini CRM - Accounts & Contacts</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen">

    <div class="max-w-7xl mx-auto px-4 py-8">
        <!-- Header -->
        <div class="flex justify-between items-center mb-6 border-b border-slate-700 pb-4">
            <div>
                <h1 class="text-3xl font-bold text-sky-400">Zoho-style Mini CRM</h1>
                <p class="text-slate-400 text-sm">Account & Contact Management Dashboard</p>
            </div>
            <button onclick="openAccountModal()" class="bg-sky-500 hover:bg-sky-600 px-4 py-2 rounded-lg font-medium transition text-white shadow-lg">
                + Add Company Account
            </button>
        </div>

        <!-- Controls Bar: Live Search & Filters -->
        <div class="bg-slate-800 rounded-xl p-4 mb-6 border border-slate-700 shadow-md grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
            <div class="md:col-span-2">
                <label class="block text-xs uppercase text-slate-400 mb-1 font-semibold">Live Search</label>
                <input type="text" id="search-input" oninput="applyFilters()" placeholder="Search by name, industry, or location..." 
                       class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 text-sm">
            </div>
            <div>
                <label class="block text-xs uppercase text-slate-400 mb-1 font-semibold">Filter by Industry</label>
                <select id="industry-filter" onchange="applyFilters()" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500 text-sm">
                    <option value="">All Industries</option>
                </select>
            </div>
            <div>
                <label class="block text-xs uppercase text-slate-400 mb-1 font-semibold">Filter by Location</label>
                <select id="location-filter" onchange="applyFilters()" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500 text-sm">
                    <option value="">All Locations</option>
                </select>
            </div>
        </div>

        <!-- Dashboard Table -->
        <div class="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-xl mb-8">
            <div class="p-4 bg-slate-800/80 border-b border-slate-700 flex justify-between items-center">
                <h2 class="text-lg font-semibold text-slate-200">Accounts Overview</h2>
                <span id="account-count" class="text-xs bg-slate-700 text-slate-300 px-2.5 py-1 rounded-full font-mono">0 Accounts</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm text-slate-300">
                    <thead class="bg-slate-900/50 text-slate-400 uppercase text-xs border-b border-slate-700">
                        <tr>
                            <th class="py-3 px-4">Company Name</th>
                            <th class="py-3 px-4">Industry</th>
                            <th class="py-3 px-4">Location</th>
                            <th class="py-3 px-4">Employees</th>
                            <th class="py-3 px-4">LinkedIn</th>
                            <th class="py-3 px-4 text-center">Contacts</th>
                            <th class="py-3 px-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="accounts-table-body" class="divide-y divide-slate-700">
                        <!-- Dynamic Rows -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Selected Account Contacts Drawer/Section -->
        <div id="contacts-section" class="hidden bg-slate-800 rounded-xl border border-sky-500/30 p-6 shadow-xl">
            <div class="flex justify-between items-center mb-6 border-b border-slate-700 pb-3">
                <div>
                    <h3 class="text-xl font-bold text-white flex items-center gap-2">
                        <span id="selected-company-name"></span>
                        <span class="text-xs font-normal text-sky-400 bg-sky-950/80 px-2 py-0.5 rounded border border-sky-800">Associated Contacts</span>
                    </h3>
                </div>
                <button onclick="openContactModal()" class="bg-emerald-600 hover:bg-emerald-700 px-3 py-1.5 rounded text-sm text-white font-medium transition">
                    + Add Contact
                </button>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm text-slate-300">
                    <thead class="bg-slate-900/40 text-slate-400 uppercase text-xs border-b border-slate-700">
                        <tr>
                            <th class="py-2.5 px-4">Contact Name</th>
                            <th class="py-2.5 px-4">Job Title</th>
                            <th class="py-2.5 px-4">Email</th>
                            <th class="py-2.5 px-4">Phone</th>
                        </tr>
                    </thead>
                    <tbody id="contacts-table-body" class="divide-y divide-slate-700/50">
                        <!-- Dynamic Rows -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Account Modal -->
    <div id="account-modal" class="hidden fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-slate-800 border border-slate-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
            <h3 class="text-xl font-bold mb-4 text-white">Add New Account</h3>
            <form id="account-form" onsubmit="saveAccount(event)" class="space-y-4">
                <div>
                    <label class="block text-xs uppercase text-slate-400 mb-1">Company Name</label>
                    <input type="text" id="acc-name" required class="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-500">
                </div>
                <div>
                    <label class="block text-xs uppercase text-slate-400 mb-1">Industry</label>
                    <input type="text" id="acc-industry" required class="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-500">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs uppercase text-slate-400 mb-1">Location</label>
                        <input type="text" id="acc-location" required class="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-500">
                    </div>
                    <div>
                        <label class="block text-xs uppercase text-slate-400 mb-1">Employees</label>
                        <input type="number" id="acc-employees" required class="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-500">
                    </div>
                </div>
                <div>
                    <label class="block text-xs uppercase text-slate-400 mb-1">LinkedIn Profile URL</label>
                    <input type="url" id="acc-linkedin" placeholder="https://linkedin.com/company/..." class="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-500">
                </div>
                <div class="flex justify-end gap-3 pt-2">
                    <button type="button" onclick="closeAccountModal()" class="px-4 py-2 text-slate-400 hover:text-white">Cancel</button>
                    <button type="submit" class="bg-sky-500 hover:bg-sky-600 text-white px-4 py-2 rounded font-medium">Save Account</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Contact Modal -->
    <div id="contact-modal" class="hidden fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-slate-800 border border-slate-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
            <h3 class="text-xl font-bold mb-4 text-white">Add Contact</h3>
            <form id="contact-form" onsubmit="saveContact(event)" class="space-y-4">
                <div>
                    <label class="block text-xs uppercase text-slate-400 mb-1">Full Name</label>
                    <input type="text" id="con-name" required class="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-500">
                </div>
                <div>
                    <label class="block text-xs uppercase text-slate-400 mb-1">Job Title</label>
                    <input type="text" id="con-title" required class="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-500">
                </div>
                <div>
                    <label class="block text-xs uppercase text-slate-400 mb-1">Email</label>
                    <input type="email" id="con-email" required class="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-500">
                </div>
                <div>
                    <label class="block text-xs uppercase text-slate-400 mb-1">Phone</label>
                    <input type="text" id="con-phone" class="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-500">
                </div>
                <div class="flex justify-end gap-3 pt-2">
                    <button type="button" onclick="closeContactModal()" class="px-4 py-2 text-slate-400 hover:text-white">Cancel</button>
                    <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded font-medium">Add Contact</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let allAccounts = [];
        let currentAccountId = null;

        async function loadAccounts() {
            const res = await fetch('/api/accounts');
            allAccounts = await res.json();
            
            updateFilterDropdowns();
            applyFilters();
        }

        function updateFilterDropdowns() {
            const industrySelect = document.getElementById('industry-filter');
            const locationSelect = document.getElementById('location-filter');

            const currentIndustry = industrySelect.value;
            const currentLocation = locationSelect.value;

            const industries = [...new Set(allAccounts.map(a => a.industry))].sort();
            const locations = [...new Set(allAccounts.map(a => a.location))].sort();

            industrySelect.innerHTML = '<option value="">All Industries</option>' + 
                industries.map(ind => `<option value="${ind}">${ind}</option>`).join('');

            locationSelect.innerHTML = '<option value="">All Locations</option>' + 
                locations.map(loc => `<option value="${loc}">${loc}</option>`).join('');

            industrySelect.value = currentIndustry;
            locationSelect.value = currentLocation;
        }

        function applyFilters() {
            const query = document.getElementById('search-input').value.toLowerCase().trim();
            const selectedIndustry = document.getElementById('industry-filter').value;
            const selectedLocation = document.getElementById('location-filter').value;

            const filtered = allAccounts.filter(acc => {
                const matchesQuery = !query || 
                    acc.company_name.toLowerCase().includes(query) ||
                    acc.industry.toLowerCase().includes(query) ||
                    acc.location.toLowerCase().includes(query);

                const matchesIndustry = !selectedIndustry || acc.industry === selectedIndustry;
                const matchesLocation = !selectedLocation || acc.location === selectedLocation;

                return matchesQuery && matchesIndustry && matchesLocation;
            });

            renderAccountsTable(filtered);
        }

        function renderAccountsTable(accounts) {
            document.getElementById('account-count').innerText = `${accounts.length} of ${allAccounts.length} Accounts`;
            const tbody = document.getElementById('accounts-table-body');
            
            if (accounts.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-slate-500">No matching company accounts found.</td></tr>`;
                return;
            }

            tbody.innerHTML = accounts.map(a => `
                <tr class="hover:bg-slate-700/50 cursor-pointer transition ${currentAccountId === a.id ? 'bg-slate-700/70 border-l-4 border-sky-400' : ''}" onclick="selectAccount(${a.id}, '${a.company_name}')">
                    <td class="py-3 px-4 font-semibold text-white">${a.company_name}</td>
                    <td class="py-3 px-4">${a.industry}</td>
                    <td class="py-3 px-4">${a.location}</td>
                    <td class="py-3 px-4">${a.employees.toLocaleString()}</td>
                    <td class="py-3 px-4" onclick="event.stopPropagation()">
                        ${a.linkedin_url ? `<a href="${a.linkedin_url}" target="_blank" class="text-sky-400 hover:underline">LinkedIn Profile ↗</a>` : '<span class="text-slate-500">N/A</span>'}
                    </td>
                    <td class="py-3 px-4 text-center">
                        <span class="bg-slate-900 px-2 py-1 rounded text-xs text-sky-300 font-mono">${a.contact_count}</span>
                    </td>
                    <td class="py-3 px-4 text-right" onclick="event.stopPropagation()">
                        <button onclick="deleteAccount(${a.id})" class="text-rose-400 hover:text-rose-300 text-xs px-2 py-1 bg-rose-950/40 rounded border border-rose-800">Delete</button>
                    </td>
                </tr>
            `).join('');
        }

        async function selectAccount(id, name) {
            currentAccountId = id;
            document.getElementById('selected-company-name').innerText = name;
            document.getElementById('contacts-section').classList.remove('hidden');
            applyFilters();
            await loadContacts();
        }

        async function loadContacts() {
            if(!currentAccountId) return;
            const res = await fetch(`/api/accounts/${currentAccountId}/contacts`);
            const contacts = await res.json();
            const tbody = document.getElementById('contacts-table-body');

            if(contacts.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-slate-500">No contacts linked to this company yet.</td></tr>`;
                return;
            }

            tbody.innerHTML = contacts.map(c => `
                <tr class="hover:bg-slate-700/30">
                    <td class="py-2.5 px-4 font-medium text-slate-200">${c.name}</td>
                    <td class="py-2.5 px-4">${c.title}</td>
                    <td class="py-2.5 px-4"><a href="mailto:${c.email}" class="text-sky-400 hover:underline">${c.email}</a></td>
                    <td class="py-2.5 px-4">${c.phone || 'N/A'}</td>
                </tr>
            `).join('');
        }

        function openAccountModal() { document.getElementById('account-modal').classList.remove('hidden'); }
        function closeAccountModal() { document.getElementById('account-modal').classList.add('hidden'); }
        function openContactModal() { document.getElementById('contact-modal').classList.remove('hidden'); }
        function closeContactModal() { document.getElementById('contact-modal').classList.add('hidden'); }

        async function saveAccount(e) {
            e.preventDefault();
            const body = {
                company_name: document.getElementById('acc-name').value,
                industry: document.getElementById('acc-industry').value,
                location: document.getElementById('acc-location').value,
                employees: parseInt(document.getElementById('acc-employees').value),
                linkedin_url: document.getElementById('acc-linkedin').value
            };

            await fetch('/api/accounts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            closeAccountModal();
            document.getElementById('account-form').reset();
            loadAccounts();
        }

        async function saveContact(e) {
            e.preventDefault();
            if(!currentAccountId) return;

            const body = {
                account_id: currentAccountId,
                name: document.getElementById('con-name').value,
                title: document.getElementById('con-title').value,
                email: document.getElementById('con-email').value,
                phone: document.getElementById('con-phone').value
            };

            await fetch('/api/contacts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            closeContactModal();
            document.getElementById('contact-form').reset();
            loadContacts();
            loadAccounts();
        }

        async function deleteAccount(id) {
            if(!confirm("Delete this account and all linked contacts?")) return;
            await fetch(`/api/accounts/${id}`, { method: 'DELETE' });
            if(currentAccountId === id) {
                currentAccountId = null;
                document.getElementById('contacts-section').classList.add('hidden');
            }
            loadAccounts();
        }

        loadAccounts();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, COUNT(c.id) as contact_count
            FROM accounts a
            LEFT JOIN contacts c ON a.id = c.account_id
            GROUP BY a.id
            ORDER BY a.id DESC
        """)
        accounts = [dict(row) for row in cursor.fetchall()]
    return jsonify(accounts)


@app.route("/api/accounts", methods=["POST"])
def add_account():
    data = request.json
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO accounts (company_name, industry, location, employees, linkedin_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                data["company_name"],
                data["industry"],
                data["location"],
                data["employees"],
                data.get("linkedin_url", ""),
            ),
        )
        conn.commit()
    return jsonify({"success": True}), 201


@app.route("/api/accounts/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        conn.commit()
    return jsonify({"success": True})


@app.route("/api/accounts/<int:account_id>/contacts", methods=["GET"])
def get_contacts(account_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM contacts WHERE account_id = ?", (account_id,)
        )
        contacts = [dict(row) for row in cursor.fetchall()]
    return jsonify(contacts)


@app.route("/api/contacts", methods=["POST"])
def add_contact():
    data = request.json
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO contacts (account_id, name, email, phone, title)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                data["account_id"],
                data["name"],
                data["email"],
                data.get("phone", ""),
                data["title"],
            ),
        )
        conn.commit()
    return jsonify({"success": True}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
