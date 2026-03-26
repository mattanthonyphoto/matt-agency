/**
 * Matt Anthony Photography — Business Command Center
 * Premium dashboard with animated counters, auto-refresh, and Chart.js
 */

const REVENUE_TARGET = 172900;
const AUTO_REFRESH_SECONDS = 60;

let revenueChart = null;
let expenseChart = null;
let refreshTimer = null;
let refreshCountdown = AUTO_REFRESH_SECONDS;

// ── Formatting ──────────────────────────────────────────────────────

function fmt(n) {
    if (n == null || isNaN(n)) return "$0";
    const abs = Math.abs(n);
    const s = abs >= 1000
        ? "$" + abs.toLocaleString("en-CA", { minimumFractionDigits: 0, maximumFractionDigits: 0 })
        : "$" + abs.toLocaleString("en-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return n < 0 ? "-" + s : s;
}

function fmtK(n) {
    if (n == null || isNaN(n)) return "$0";
    const abs = Math.abs(n);
    let s;
    if (abs >= 100000) s = "$" + (abs / 1000).toFixed(0) + "K";
    else if (abs >= 10000) s = "$" + (abs / 1000).toFixed(1) + "K";
    else s = fmt(abs);
    return n < 0 ? "-" + s : s;
}

function fmtPct(n) { return (n == null || isNaN(n)) ? "0%" : n.toFixed(1) + "%"; }
function fmtNum(n) { return (n == null || isNaN(n)) ? "0" : n.toLocaleString("en-CA"); }
function el(id) { return document.getElementById(id); }

function badgeClass(s) {
    switch ((s || "").toLowerCase()) {
        case "paid": return "badge-paid";
        case "sent": case "viewed": return "badge-sent";
        case "overdue": return "badge-overdue";
        default: return "badge-draft";
    }
}

// ── Animated Counter ────────────────────────────────────────────────

function animateValue(element, end, formatter, duration = 800) {
    const start = 0;
    const startTime = performance.now();
    function update(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        const current = start + (end - start) * eased;
        element.textContent = formatter(current);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ── Auto Refresh ────────────────────────────────────────────────────

function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
    refreshCountdown = AUTO_REFRESH_SECONDS;
    refreshTimer = setInterval(() => {
        refreshCountdown--;
        const statusEl = el("autoRefreshStatus");
        if (statusEl) statusEl.textContent = `Auto-refresh in ${refreshCountdown}s`;
        if (refreshCountdown <= 0) {
            loadDashboard();
        }
    }, 1000);
}

// ── Load Dashboard ──────────────────────────────────────────────────

async function loadDashboard() {
    const overlay = el("loadingOverlay");
    const btn = el("refreshBtn");
    overlay.classList.remove("hidden");
    btn.classList.add("loading");

    try {
        const resp = await fetch("/api/all");
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        renderAll(data);
        startAutoRefresh();
    } catch (err) {
        console.error("Dashboard load failed:", err);
        el("lastUpdated").textContent = "Error: " + err.message;
    } finally {
        overlay.classList.add("hidden");
        btn.classList.remove("loading");
    }
}

// ── Render All ──────────────────────────────────────────────────────

function renderAll(data) {
    renderHeader(data);
    renderHeroRing(data.revenue);
    renderKPIs(data);
    renderRevenueChart(data.revenue);
    renderPipeline(data.pipeline);
    renderClients(data.clients);
    renderExpenses(data.financial);
    renderPnL(data.revenue, data.financial);
    renderStats(data.stats, data.pipeline);
    renderInvoices(data.stats);
}

// ── Header ──────────────────────────────────────────────────────────

function renderHeader(data) {
    const now = new Date();
    const startOfYear = new Date(2026, 0, 1);
    const dayOfYear = Math.floor((now - startOfYear) / 86400000) + 1;
    const endOfQ1 = new Date(2026, 2, 31);
    const daysLeftQ1 = Math.max(0, Math.ceil((endOfQ1 - now) / 86400000));

    el("headerDayOfYear").textContent = dayOfYear;
    el("headerDaysLeft").textContent = daysLeftQ1;
    el("lastUpdated").textContent = "Live \u00B7 " + now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    el("footerTime").textContent = now.toLocaleString();
}

// ── Hero Ring ───────────────────────────────────────────────────────

function renderHeroRing(rev) {
    const ytd = rev.ytd || 0;
    const target = rev.target || REVENUE_TARGET;
    const pct = Math.min(100, (ytd / target) * 100);
    const remaining = Math.max(0, target - ytd);

    // Animate ring
    const circumference = 553; // 2 * PI * 88
    const offset = circumference - (circumference * pct / 100);
    const ring = el("ringProgress");
    setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);

    // Animate percentage
    animateValue(el("ringPct"), pct, v => v.toFixed(1) + "%", 1200);

    // Details
    animateValue(el("heroRevenue"), ytd, v => fmt(v), 1000);
    el("heroRemaining").textContent = fmt(remaining);

    // Run rate calculations
    const now = new Date();
    const endOfYear = new Date(2026, 11, 31);
    const daysLeft = Math.max(1, Math.ceil((endOfYear - now) / 86400000));
    const monthsLeft = daysLeft / 30.44;
    const dailyRate = remaining / daysLeft;
    const monthlyRate = remaining / monthsLeft;

    el("heroRunRate").textContent = fmt(dailyRate) + "/day";
    el("heroMonthlyRate").textContent = fmt(monthlyRate) + "/mo";
}

// ── KPI Cards ───────────────────────────────────────────────────────

function renderKPIs(data) {
    const rev = data.revenue;
    const fin = data.financial;
    const pipe = data.pipeline;
    const stats = data.stats;

    // Net Profit
    const profit = fin.net_profit || 0;
    animateValue(el("kpiProfit"), profit, v => fmtK(v));
    el("kpiProfit").className = "kpi-value " + (profit >= 0 ? "accent-green" : "accent-red");
    el("kpiProfitSub").textContent = fmtPct(fin.profit_margin) + " margin";

    // Pipeline
    const pipeVal = pipe.opportunities?.total_value || 0;
    const pipeCount = pipe.opportunities?.count || 0;
    animateValue(el("kpiPipeline"), pipeVal, v => fmtK(v));
    el("kpiPipelineSub").textContent = pipeCount + " active deal" + (pipeCount !== 1 ? "s" : "");

    // Recurring
    const recurring = rev.recurring || 0;
    animateValue(el("kpiRecurring"), recurring, v => fmtK(v));
    const annualized = rev.recurring_monthly_base * 12;
    el("kpiRecurringSub").textContent = fmt(rev.recurring_monthly_base) + "/mo base";

    // Outstanding
    const outstanding = stats.outstanding_invoices || 0;
    const outCount = (stats.outstanding_list || []).length;
    animateValue(el("kpiOutstanding"), outstanding, v => fmtK(v));
    el("kpiOutstandingSub").textContent = outCount + " unpaid invoice" + (outCount !== 1 ? "s" : "");

    // Expenses
    const expenses = fin.ytd_expenses || 0;
    animateValue(el("kpiExpenses"), expenses, v => fmtK(v));
    el("kpiExpensesSub").textContent = fin.expense_breakdown?.length + " categories";
}

// ── Revenue Chart ───────────────────────────────────────────────────

function renderRevenueChart(rev) {
    const ctx = el("revenueChart").getContext("2d");
    if (revenueChart) revenueChart.destroy();

    const months = rev.monthly.map(m => m.month.substring(0, 3));
    const rev2026 = rev.monthly.map(m => m.revenue);
    const exp2026 = rev.monthly.map(m => m.expenses);
    const rev2025 = (rev.monthly_2025 || []).map(m => m.revenue);
    const targetLine = months.map(() => REVENUE_TARGET / 12);

    // Gradient for revenue bars
    const blueGrad = ctx.createLinearGradient(0, 0, 0, 300);
    blueGrad.addColorStop(0, "rgba(59, 125, 237, 0.9)");
    blueGrad.addColorStop(1, "rgba(139, 92, 246, 0.6)");

    revenueChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: months,
            datasets: [
                {
                    label: "2026 Revenue",
                    data: rev2026,
                    backgroundColor: blueGrad,
                    borderRadius: 6,
                    borderSkipped: false,
                    order: 2,
                    barPercentage: 0.7,
                },
                {
                    label: "2026 Expenses",
                    data: exp2026,
                    backgroundColor: "rgba(239, 68, 68, 0.5)",
                    borderRadius: 6,
                    borderSkipped: false,
                    order: 3,
                    barPercentage: 0.7,
                },
                {
                    label: "2025 Revenue",
                    data: rev2025,
                    backgroundColor: "rgba(59, 125, 237, 0.08)",
                    borderColor: "rgba(59, 125, 237, 0.2)",
                    borderWidth: 1,
                    borderRadius: 6,
                    borderSkipped: false,
                    order: 4,
                    barPercentage: 0.7,
                },
                {
                    label: "Target Pace",
                    data: targetLine,
                    type: "line",
                    borderColor: "rgba(139, 92, 246, 0.35)",
                    borderDash: [5, 4],
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    pointHoverBackgroundColor: "#8B5CF6",
                    fill: false,
                    order: 1,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "rgba(13, 15, 20, 0.95)",
                    borderColor: "rgba(255,255,255,0.06)",
                    borderWidth: 1,
                    cornerRadius: 10,
                    padding: 12,
                    titleColor: "#EDEEF1",
                    titleFont: { weight: "700", size: 12 },
                    bodyColor: "#7D849A",
                    bodyFont: { size: 11 },
                    callbacks: {
                        label: ctx => "  " + ctx.dataset.label + ":  " + fmt(ctx.parsed.y),
                    },
                    displayColors: true,
                    boxWidth: 8,
                    boxHeight: 8,
                    boxPadding: 4,
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: "#484E65", font: { size: 11, weight: "500" } },
                    border: { display: false },
                },
                y: {
                    grid: { color: "rgba(255,255,255,0.02)", drawTicks: false },
                    ticks: { color: "#484E65", font: { size: 10 }, callback: v => fmtK(v), padding: 8 },
                    border: { display: false },
                },
            },
        },
    });

    // Custom legend
    el("chartLegend").innerHTML = [
        { color: "#3B7DED", label: "2026 Revenue" },
        { color: "#EF4444", label: "2026 Expenses" },
        { color: "rgba(59,125,237,0.25)", label: "2025 Revenue" },
        { color: "#8B5CF6", label: "Target Pace", dash: true },
    ].map(l => `<span style="display:flex;align-items:center;gap:4px;">
        <span style="width:12px;height:3px;border-radius:2px;background:${l.color};${l.dash ? "background:none;border-top:2px dashed " + l.color : ""}"></span>
        ${l.label}
    </span>`).join("");
}

// ── Pipeline ────────────────────────────────────────────────────────

function renderPipeline(pipe) {
    const funnelEl = el("pipelineFunnel");
    const stages = pipe.opportunities?.stages || {};
    const entries = Object.entries(stages);

    if (entries.length === 0) {
        funnelEl.innerHTML = '<div style="color:var(--text-dim);font-size:0.75rem;padding:1rem 0;">No active pipeline in GHL</div>';
    } else {
        const max = Math.max(...entries.map(([, s]) => s.count), 1);
        funnelEl.innerHTML = entries.map(([name, s]) => {
            const w = Math.max(15, (s.count / max) * 100);
            return `<div class="funnel-item">
                <span class="funnel-label">${name}</span>
                <div class="funnel-bar-wrap">
                    <div class="funnel-bar" style="width:${w}%;background:linear-gradient(90deg, var(--orange), #F97316);">
                        <span class="funnel-count">${s.count} deals \u00B7 ${fmtK(s.value)}</span>
                    </div>
                </div>
            </div>`;
        }).join("");
    }

    // Cold email
    const ce = pipe.cold_email || {};
    const ceEl = el("coldEmailFunnel");
    const total = ce.total_leads || 0;
    const qualified = ce.qualified || 0;
    const emails = ce.emails_found || 0;

    const steps = [
        { label: "Scraped", count: total, color: "var(--blue)", grad: "linear-gradient(90deg, #3B7DED, #60A5FA)" },
        { label: "Qualified", count: qualified, color: "var(--green)", grad: "linear-gradient(90deg, #10B981, #34D399)" },
        { label: "Email Found", count: emails, color: "var(--purple)", grad: "linear-gradient(90deg, #8B5CF6, #A78BFA)" },
    ];
    const maxCe = Math.max(...steps.map(s => s.count), 1);

    ceEl.innerHTML = steps.map(s => {
        const w = Math.max(12, (s.count / maxCe) * 100);
        const convRate = s.count > 0 && total > 0 ? ((s.count / total) * 100).toFixed(0) + "%" : "";
        return `<div class="funnel-item">
            <span class="funnel-label">${s.label}</span>
            <div class="funnel-bar-wrap">
                <div class="funnel-bar" style="width:${w}%;background:${s.grad};">
                    <span class="funnel-count">${fmtNum(s.count)}${convRate ? " \u00B7 " + convRate : ""}</span>
                </div>
            </div>
        </div>`;
    }).join("");

    // Category breakdown tags
    const breakdownEl = el("coldEmailBreakdown");
    if (ce.by_category && Object.keys(ce.by_category).length > 0) {
        breakdownEl.innerHTML = Object.entries(ce.by_category)
            .map(([cat, n]) => `<span class="breakdown-tag">${cat}: ${n}</span>`).join("");
    }
}

// ── Clients ─────────────────────────────────────────────────────────

function renderClients(clients) {
    const ghl = (clients.ghl_clients || []).map(c => ({ name: c.name, revenue: c.amount }));
    const sheet = clients.top_clients || [];
    const list = ghl.length > 0 ? ghl : sheet;

    el("clientCount").textContent = list.length + " client" + (list.length !== 1 ? "s" : "");

    if (list.length === 0) {
        el("clientsTable").innerHTML = '<div style="color:var(--text-dim);font-size:0.75rem;padding:1rem 0;">No client data</div>';
        return;
    }

    const maxRev = list[0]?.revenue || 1;
    let html = `<table><thead><tr>
        <th style="width:30px">#</th><th>Client</th><th class="td-right">Revenue</th><th style="min-width:120px">Share</th>
    </tr></thead><tbody>`;

    list.slice(0, 12).forEach((c, i) => {
        const pct = (c.revenue / maxRev * 100);
        const totalPct = list.reduce((s, x) => s + x.revenue, 0);
        const share = totalPct > 0 ? (c.revenue / totalPct * 100).toFixed(1) : "0";
        html += `<tr>
            <td style="color:var(--text-dim);font-weight:600">${i + 1}</td>
            <td style="color:var(--text-primary);font-weight:500">${c.name}</td>
            <td class="td-right td-amount">${fmt(c.revenue)}</td>
            <td><div class="client-bar-wrap">
                <div class="client-bar" style="width:${pct}%"></div>
                <span class="client-pct">${share}%</span>
            </div></td>
        </tr>`;
    });

    html += "</tbody></table>";
    el("clientsTable").innerHTML = html;
}

// ── Expense Chart ───────────────────────────────────────────────────

function renderExpenses(fin) {
    const ctx = el("expenseChart").getContext("2d");
    if (expenseChart) expenseChart.destroy();

    const breakdown = fin.expense_breakdown || [];
    if (breakdown.length === 0) { expenseChart = null; return; }

    const colors = [
        "#3B7DED", "#10B981", "#EF4444", "#F59E0B", "#8B5CF6",
        "#06B6D4", "#EC4899", "#84CC16", "#F97316", "#6366F1",
        "#14B8A6", "#E879F9", "#A3E635", "#FB923C", "#64748B",
    ];

    expenseChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: breakdown.map(e => e.category),
            datasets: [{
                data: breakdown.map(e => e.amount),
                backgroundColor: colors.slice(0, breakdown.length),
                borderWidth: 0,
                hoverOffset: 8,
                spacing: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "70%",
            plugins: {
                legend: {
                    position: "right",
                    labels: {
                        color: "#7D849A",
                        font: { family: "'Inter'", size: 10, weight: "500" },
                        boxWidth: 8, boxHeight: 8, padding: 8,
                        usePointStyle: true, pointStyle: "circle",
                        generateLabels: chart => {
                            return chart.data.labels.map((label, i) => ({
                                text: (label.length > 18 ? label.substring(0, 18) + "\u2026" : label) + "  " + fmt(chart.data.datasets[0].data[i]),
                                fillStyle: chart.data.datasets[0].backgroundColor[i],
                                hidden: false, index: i, pointStyle: "circle",
                            }));
                        },
                    },
                },
                tooltip: {
                    backgroundColor: "rgba(13, 15, 20, 0.95)",
                    borderColor: "rgba(255,255,255,0.06)",
                    borderWidth: 1,
                    cornerRadius: 10,
                    padding: 10,
                    titleColor: "#EDEEF1",
                    bodyColor: "#7D849A",
                    callbacks: { label: ctx => " " + ctx.label + ": " + fmt(ctx.parsed) },
                },
            },
        },
    });
}

// ── P&L ─────────────────────────────────────────────────────────────

function renderPnL(rev, fin) {
    el("pnlSummary").innerHTML = `
        <div class="pnl-row">
            <span class="pnl-label">Revenue</span>
            <span class="pnl-value blue">${fmt(rev.ytd)}</span>
        </div>
        <div class="pnl-row indent">
            <span class="pnl-label">Recurring</span>
            <span class="pnl-value muted">${fmt(rev.recurring)}</span>
        </div>
        <div class="pnl-row indent">
            <span class="pnl-label">Project</span>
            <span class="pnl-value muted">${fmt(rev.project)}</span>
        </div>
        <div class="pnl-row">
            <span class="pnl-label">Expenses</span>
            <span class="pnl-value negative">${fmt(fin.ytd_expenses)}</span>
        </div>
        <div class="pnl-row total">
            <span class="pnl-label" style="font-weight:700">Net Profit</span>
            <span class="pnl-value ${fin.net_profit >= 0 ? 'positive' : 'negative'}" style="font-size:1rem">${fmt(fin.net_profit)}</span>
        </div>
        <div class="pnl-row">
            <span class="pnl-label">Margin</span>
            <span class="pnl-value muted">${fmtPct(fin.profit_margin)}</span>
        </div>`;
}

// ── Stats ───────────────────────────────────────────────────────────

function renderStats(stats, pipeline) {
    animateValue(el("statMileage"), stats.mileage_km, v => fmtNum(Math.round(v)) + " km");
    el("statMileageSub").textContent = stats.mileage_trips + " trips logged";

    const gst = stats.gst_owing || 0;
    animateValue(el("statGST"), gst, v => fmt(v));
    el("statGSTSub").textContent = fmt(stats.gst_collected) + " collected";

    animateValue(el("statCCA"), stats.total_cca, v => fmt(v));

    const leads = pipeline.cold_email?.emails_found || 0;
    animateValue(el("statColdLeads"), leads, v => fmtNum(Math.round(v)));
    el("statColdLeadsSub").textContent = "with verified email";

    animateValue(el("statContacts"), pipeline.contacts_total || 0, v => fmtNum(Math.round(v)));
}

// ── Invoices ────────────────────────────────────────────────────────

function renderInvoices(stats) {
    const invoices = stats.recent_invoices || [];
    el("invoiceCount").textContent = invoices.length + " recent";

    if (invoices.length === 0) {
        el("invoicesTable").innerHTML = '<div style="color:var(--text-dim);font-size:0.75rem;padding:1rem 0;">No invoice data</div>';
        return;
    }

    let html = `<table><thead><tr>
        <th>Invoice</th><th>Client</th><th>Date</th><th class="td-right">Amount</th><th>Status</th>
    </tr></thead><tbody>`;

    invoices.forEach(inv => {
        html += `<tr>
            <td style="color:var(--text-primary);font-weight:600">${inv.number || "\u2014"}</td>
            <td>${inv.client}</td>
            <td style="font-variant-numeric:tabular-nums">${inv.date}</td>
            <td class="td-right td-amount">${fmt(inv.amount)}</td>
            <td><span class="badge ${badgeClass(inv.status)}">${inv.status}</span></td>
        </tr>`;
    });

    html += "</tbody></table>";
    el("invoicesTable").innerHTML = html;
}

// ── Init ─────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", loadDashboard);
