const VERSION = new URLSearchParams(window.location.search).get("v");
const DATA_URL = VERSION
  ? `./data/dashboard-data.json?v=${encodeURIComponent(VERSION)}`
  : "./data/dashboard-data.json";

const state = {
  data: null,
  filters: {
    type: new Set(),
    status: new Set(),
  },
};
const { formatResetHint } = window.shadowDashboardRenderUtils;

function normalizeClass(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function formatCountMap(countMap) {
  return Object.entries(countMap)
    .map(([key, value]) => {
      const span = document.createElement("span");
      span.className = `pill type-${normalizeClass(key)}`;
      span.textContent = `${key} ${value}`;
      return span;
    });
}

function updateSummary(summary, generatedAt) {
  document.getElementById("total-items").textContent = String(summary.total_items);
  document.getElementById("latest-date").textContent = summary.latest_created_at || "-";
  document.getElementById("generated-at").textContent = generatedAt.replace("T", " ");

  const legend = document.getElementById("type-legend");
  legend.replaceChildren(...formatCountMap(summary.type_counts));
}

function uniqueSorted(values) {
  return [...new Set(values)].sort((a, b) => a.localeCompare(b));
}

function getAllItems() {
  return state.data?.all_items || [];
}

function isItemVisible(item) {
  const typeSelected = state.filters.type.size === 0 || state.filters.type.has(item.type);
  const statusSelected = state.filters.status.size === 0 || state.filters.status.has(item.status);
  return typeSelected && statusSelected;
}

function buildFilterChip(kind, value, count) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "filter-chip";
  button.dataset.kind = kind;
  button.dataset.value = value;
  button.setAttribute("aria-pressed", "true");
  button.textContent = `${value} ${count}`;
  button.addEventListener("click", () => {
    const set = state.filters[kind];
    if (set.has(value)) {
      set.delete(value);
    } else {
      set.add(value);
    }
    updateFilterUI();
    renderDashboard();
  });
  return button;
}

function updateFilterUI() {
  const allItems = getAllItems();
  const typeCounts = new Map();
  const statusCounts = new Map();

  for (const item of allItems) {
    typeCounts.set(item.type, (typeCounts.get(item.type) || 0) + 1);
    statusCounts.set(item.status, (statusCounts.get(item.status) || 0) + 1);
  }

  const typeContainer = document.getElementById("type-filters");
  const statusContainer = document.getElementById("status-filters");
  typeContainer.replaceChildren(
    ...uniqueSorted([...typeCounts.keys()]).map((value) =>
      buildFilterChip("type", value, typeCounts.get(value) || 0)
    )
  );
  statusContainer.replaceChildren(
    ...uniqueSorted([...statusCounts.keys()]).map((value) =>
      buildFilterChip("status", value, statusCounts.get(value) || 0)
    )
  );

  for (const button of document.querySelectorAll(".filter-chip")) {
    const kind = button.dataset.kind;
    const value = button.dataset.value;
    const selected = state.filters[kind].size === 0 || state.filters[kind].has(value);
    button.setAttribute("aria-pressed", String(selected));
  }

  document.getElementById("reset-filters").disabled =
    state.filters.type.size === 0 && state.filters.status.size === 0;
}

function buildRow(item) {
  const template = document.getElementById("row-template");
  const row = template.content.firstElementChild.cloneNode(true);

  row.querySelector(".target-text").textContent = item.title;
  const collocationNode = row.querySelector(".collocation-text");
  if (item.collocation) {
    collocationNode.hidden = false;
    collocationNode.textContent = item.collocation;
  }
  const resetHint = formatResetHint(item);
  const resetHintNode = row.querySelector(".reset-hint");
  if (resetHint) {
    resetHintNode.hidden = false;
    resetHintNode.textContent = resetHint;
    resetHintNode.title = "Previously learned item re-added through a later capture";
  }

  const typePill = row.querySelector(".type-pill");
  typePill.textContent = item.type;
  typePill.classList.add(`type-${normalizeClass(item.type)}`);

  const statusPill = row.querySelector(".status-pill");
  statusPill.textContent = item.status;
  statusPill.classList.add(`status-${normalizeClass(item.status)}`);

  row.querySelector(".english-cell").textContent = item.english || "—";
  row.querySelector(".example-cell").textContent = item.example_sentence || "—";

  return row;
}

function renderRecent(items) {
  const tbody = document.querySelector("#recent-table tbody");
  tbody.replaceChildren(...items.map(buildRow));
}

function renderWeekly(groups) {
  const container = document.getElementById("weekly-groups");
  const fragments = groups.map((group) => {
    const details = document.createElement("details");
    details.className = "week-card";

    const summary = document.createElement("summary");

    const title = document.createElement("div");
    title.className = "week-title";
    const strong = document.createElement("strong");
    strong.textContent = group.week;
    const meta = document.createElement("span");
    meta.className = "week-meta";
    meta.textContent = `${group.items[0]?.created_at || ""} and earlier`;
    title.append(strong, meta);

    const count = document.createElement("span");
    count.className = "week-count";
    count.textContent = `${group.count} items`;

    summary.append(title, count);

    const body = document.createElement("div");
    body.className = "week-body";
    const table = document.createElement("table");
    table.className = "asset-table";
    table.innerHTML = `
      <thead>
        <tr>
          <th>Target</th>
          <th>English</th>
          <th>Type</th>
          <th>Status</th>
          <th>Transcript sentence</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;
    table.querySelector("tbody").replaceChildren(...group.items.map(buildRow));
    body.appendChild(table);

    details.append(summary, body);
    return details;
  });

  container.replaceChildren(...fragments);
}

function renderDashboard() {
  const allItems = getAllItems().filter(isItemVisible);
  const recentSeed = (state.data?.recent_items || []).filter(isItemVisible);
  const recentItems = recentSeed.length > 0
    ? recentSeed
    : allItems.slice().sort((a, b) => {
        if (a.created_at === b.created_at) {
          return b.id.localeCompare(a.id);
        }
        return b.created_at.localeCompare(a.created_at);
      }).slice(0, 12);

  const weekly = new Map();
  for (const item of allItems) {
    if (!weekly.has(item.week)) {
      weekly.set(item.week, []);
    }
    weekly.get(item.week).push(item);
  }

  const weeklyGroups = [...weekly.entries()]
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([week, items]) => ({
      week,
      count: items.length,
      items: items.slice().sort((a, b) => {
        if (a.created_at === b.created_at) {
          return b.id.localeCompare(a.id);
        }
        return b.created_at.localeCompare(a.created_at);
      }),
    }));

  renderRecent(recentItems);
  renderWeekly(weeklyGroups);
}

async function init() {
  const response = await fetch(DATA_URL, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load dashboard data: ${response.status}`);
  }

  state.data = await response.json();
  updateSummary(state.data.summary, state.data.generated_at);
  document.getElementById("reset-filters").addEventListener("click", () => {
    state.filters.type.clear();
    state.filters.status.clear();
    updateFilterUI();
    renderDashboard();
  });
  updateFilterUI();
  renderDashboard();
}

init().catch((error) => {
  const shell = document.querySelector(".shell");
  const panel = document.createElement("section");
  panel.className = "panel";
  panel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">Error</p>
        <h2>Dashboard data could not be loaded</h2>
      </div>
    </div>
    <p class="panel-note">${error.message}</p>
    <p class="panel-note">Run <code>python E:\\Personal\\学德语\\scripts\\build_shadow_dashboard.py</code> and refresh.</p>
  `;
  shell.appendChild(panel);
});
