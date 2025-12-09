async function postJSON(url, data) {
    const resp = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });
    const json = await resp.json().catch(() => ({}));
    if (!resp.ok) {
        throw json.error || "Request failed";
    }
    return json;
}

async function getJSON(url) {
    const resp = await fetch(url);
    const json = await resp.json().catch(() => ({}));
    if (!resp.ok) {
        throw json.error || "Request failed";
    }
    return json;
}

function setMessage(el, msg, isError) {
    el.textContent = msg;
    el.classList.remove("error", "success");
    el.classList.add(isError ? "error" : "success");
}

document.addEventListener("DOMContentLoaded", () => {
    const entryForm = document.getElementById("entry-form");
    const exitForm = document.getElementById("exit-form");
    const searchForm = document.getElementById("search-form");
    const reportForm = document.getElementById("report-form");
    const refreshActiveBtn = document.getElementById("refresh-active");

    if (entryForm) {
        entryForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const msgEl = document.getElementById("entry-message");
            try {
                const formData = new FormData(entryForm);
                const payload = Object.fromEntries(formData.entries());
                const data = await postJSON("/api/vehicles", payload);
                setMessage(msgEl, data.message, false);
                entryForm.reset();
                loadActiveSessions();
            } catch (err) {
                setMessage(msgEl, err.toString(), true);
            }
        });
    }

    if (exitForm) {
        exitForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const msgEl = document.getElementById("exit-message");
            const summary = document.getElementById("exit-summary");
            try {
                const formData = new FormData(exitForm);
                const payload = Object.fromEntries(formData.entries());
                const data = await postJSON("/api/vehicles/exit", payload);
                setMessage(msgEl, data.message, false);
                document.getElementById("summary-spot").textContent = data.spot_number;
                document.getElementById("summary-exit-time").textContent = data.exit_time;
                document.getElementById("summary-fee").textContent = data.total_fee;
                summary.classList.remove("hidden");
                exitForm.reset();
                loadActiveSessions();
            } catch (err) {
                setMessage(msgEl, err.toString(), true);
            }
        });
    }

    if (refreshActiveBtn) {
        refreshActiveBtn.addEventListener("click", () => {
            loadActiveSessions();
        });
        loadActiveSessions();
    }
    setInterval(() => {
    fetch("/api/stats")
        .then(r => r.json())
        .then(data => {
            document.getElementById("total_spots").textContent = data.total_spots;
            document.getElementById("occupied_spots").textContent = data.occupied_spots;
            document.getElementById("free_spots").textContent = data.free_spots;
            document.getElementById("active_sessions").textContent = data.active_sessions;
        });
}, 3000);


    if (searchForm) {
        searchForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            try {
                const formData = new FormData(searchForm);
                const params = new URLSearchParams(formData);
                const data = await getJSON("/api/sessions/search?" + params.toString());
                const tbody = document.querySelector("#search-table tbody");
                tbody.innerHTML = "";
                data.forEach((row) => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${row.id}</td>
                        <td>${row.license_plate}</td>
                        <td>${row.vehicle_type}</td>
                        <td>${row.entry_time}</td>
                        <td>${row.exit_time || "-"}</td>
                        <td>${row.total_fee ?? "-"}</td>
                        <td>${row.spot_number}</td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (err) {
                alert(err);
            }
        });
    }

    if (reportForm) {
        reportForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            try {
                const formData = new FormData(reportForm);
                const params = new URLSearchParams(formData);
                const data = await getJSON("/api/reports?" + params.toString());
                document.getElementById("report-total").textContent = data.total_earnings || 0;
                const tbody = document.querySelector("#report-table tbody");
                tbody.innerHTML = "";
                data.sessions.forEach((row) => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${row.id}</td>
                        <td>${row.license_plate}</td>
                        <td>${row.vehicle_type}</td>
                        <td>${row.entry_time}</td>
                        <td>${row.exit_time || "-"}</td>
                        <td>${row.total_fee ?? "-"}</td>
                        <td>${row.spot_number}</td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (err) {
                alert(err);
            }
        });
    }
});

async function loadActiveSessions() {
    try {
        const data = await getJSON("/api/sessions/active");
        const tbody = document.querySelector("#active-table tbody");
        if (!tbody) return;
        tbody.innerHTML = "";
        data.forEach((row) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${row.id}</td>
                <td>${row.license_plate}</td>
                <td>${row.vehicle_type}</td>
                <td>${row.entry_time}</td>
                <td>${row.spot_number}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error(err);
    }
}
