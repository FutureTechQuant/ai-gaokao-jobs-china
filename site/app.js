const DATA_URL = "./data/major_ai_rate.json";
const SOFT_SCALE = ["#5f8f6b", "#8dad66", "#d2c86f", "#d8ad66", "#c9875e", "#b8655f"];

function fmtPct(v) {
  return `${Math.round(Number(v || 0) * 100)}%`;
}

function riskColor(rate, maxRate = 1) {
  const safeMax = Math.max(0.01, Number(maxRate || 0.01));
  const x = Math.max(0, Math.min(0.999999, Number(rate || 0) / safeMax));
  const idx = Math.min(SOFT_SCALE.length - 1, Math.floor(x * SOFT_SCALE.length));
  return SOFT_SCALE[idx];
}

function confidenceBadgeClass(conf) {
  if (conf === "high") return "badge high";
  if (conf === "medium") return "badge medium";
  return "badge low";
}

function groupBy(arr, keyFn) {
  const map = new Map();
  for (const item of arr) {
    const k = keyFn(item);
    if (!map.has(k)) map.set(k, []);
    map.get(k).push(item);
  }
  return map;
}

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`加载失败: ${url}`);
  return res.json();
}

function getRoundedMaxRate(rows) {
  const max = rows.reduce((m, r) => Math.max(m, Number(r.replace_rate || 0)), 0);
  return Math.max(0.01, Math.ceil(max * 100) / 100);
}

function renderKpis(rows) {
  const total = rows.length;
  const avg = rows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (total || 1);
  const high = rows.filter(r => Number(r.replace_rate || 0) >= 0.7).length;
  const highConfidence = rows.filter(r => r.confidence === "high").length;
  const maxRate = getRoundedMaxRate(rows);
  document.getElementById("kpi-total").textContent = total.toLocaleString("zh-CN");
  document.getElementById("kpi-avg").textContent = fmtPct(avg);
  document.getElementById("kpi-high").textContent = high.toLocaleString("zh-CN");
  document.getElementById("kpi-confidence").textContent = highConfidence.toLocaleString("zh-CN");
  document.getElementById("rangeMeta").textContent = `当前色阶上限 ${Math.round(maxRate * 100)}%`;
}

function fillDisciplineFilter(rows) {
  const select = document.getElementById("disciplineFilter");
  if (select.dataset.filled === "1") return;
  const values = [...new Set(rows.map(r => r.discipline).filter(Boolean))].sort();
  for (const d of values) {
    const option = document.createElement("option");
    option.value = d;
    option.textContent = d;
    select.appendChild(option);
  }
  select.dataset.filled = "1";
}

function applyFilters(rows) {
  const q = document.getElementById("searchInput").value.trim().toLowerCase();
  const discipline = document.getElementById("disciplineFilter").value;
  return rows.filter(r => {
    const haystack = [r.major_code, r.major_name, r.discipline, r.major_category].join(" ").toLowerCase();
    return (!q || haystack.includes(q)) && (!discipline || r.discipline === discipline);
  });
}

function computeDisciplineStats(rows) {
  const grouped = groupBy(rows, r => r.discipline || "未分类");
  return [...grouped.entries()].map(([name, items]) => ({
    name,
    count: items.length,
    avg: items.reduce((s, x) => s + Number(x.replace_rate || 0), 0) / (items.length || 1)
  })).sort((a, b) => b.avg - a.avg);
}

function renderRankList(containerId, items, formatter) {
  const box = document.getElementById(containerId);
  box.innerHTML = "";
  for (const item of items) {
    const el = document.createElement("div");
    el.className = "rank-item";
    el.innerHTML = formatter(item);
    box.appendChild(el);
  }
}

function buildTreemapData(rows, mode) {
  const labels = [], parents = [], values = [], ids = [], colors = [], customdata = [];
  const rootId = "root";
  labels.push("全部专业"); parents.push(""); ids.push(rootId); values.push(rows.length || 1);
  colors.push(rows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (rows.length || 1));
  customdata.push(["root", "", "", "", "", "", ""]);

  if (mode === "discipline") {
    const disciplineMap = groupBy(rows, r => r.discipline || "未分类");
    for (const [discipline, disciplineRows] of disciplineMap.entries()) {
      const disciplineId = `discipline:${discipline}`;
      labels.push(discipline); parents.push(rootId); ids.push(disciplineId); values.push(disciplineRows.length);
      colors.push(disciplineRows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (disciplineRows.length || 1));
      customdata.push(["discipline", discipline, "", "", "", "", ""]);
      const categoryMap = groupBy(disciplineRows, r => r.major_category || "未分类");
      for (const [category, categoryRows] of categoryMap.entries()) {
        const categoryId = `category:${discipline}:${category}`;
        labels.push(category); parents.push(disciplineId); ids.push(categoryId); values.push(categoryRows.length);
        colors.push(categoryRows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (categoryRows.length || 1));
        customdata.push(["category", "", category, "", "", "", ""]);
        for (const row of categoryRows) {
          labels.push(row.major_name); parents.push(categoryId); ids.push(`major:${row.major_code}`); values.push(1);
          colors.push(Number(row.replace_rate || 0));
          customdata.push(["major", row.major_code || "", row.major_name || "", row.discipline || "", row.major_category || "", row.job_count || 0, row.confidence || "low"]);
        }
      }
    }
  } else {
    const categoryMap = groupBy(rows, r => r.major_category || "未分类");
    for (const [category, categoryRows] of categoryMap.entries()) {
      const categoryId = `category:${category}`;
      labels.push(category); parents.push(rootId); ids.push(categoryId); values.push(categoryRows.length);
      colors.push(categoryRows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (categoryRows.length || 1));
      customdata.push(["category", "", category, "", "", "", ""]);
      for (const row of categoryRows) {
        labels.push(row.major_name); parents.push(categoryId); ids.push(`major:${row.major_code}`); values.push(1);
        colors.push(Number(row.replace_rate || 0));
        customdata.push(["major", row.major_code || "", row.major_name || "", row.discipline || "", row.major_category || "", row.job_count || 0, row.confidence || "low"]);
      }
    }
  }
  return { labels, parents, values, ids, colors, customdata };
}

function renderDetail(row) {
  document.getElementById("detailEmpty").classList.add("hidden");
  document.getElementById("detailBox").classList.remove("hidden");
  document.getElementById("detailCode").textContent = row.major_code || "-";
  document.getElementById("detailName").textContent = row.major_name || "-";
  document.getElementById("detailRate").textContent = fmtPct(row.replace_rate || 0);
  document.getElementById("detailJobCount").textContent = String(row.job_count || 0);
  document.getElementById("detailDiscipline").textContent = row.discipline || "-";
  document.getElementById("detailCategory").textContent = row.major_category || "-";
  const conf = row.confidence || "low";
  const badge = document.getElementById("detailConfidence");
  badge.textContent = conf; badge.className = confidenceBadgeClass(conf);
  const jobs = document.getElementById("detailJobs"); jobs.innerHTML = "";
  const items = Array.isArray(row.matched_job_titles_sample) ? row.matched_job_titles_sample : [];
  if (!items.length) {
    jobs.innerHTML = '<span class="tag">暂无样例</span>';
  } else {
    items.forEach(x => { const span = document.createElement("span"); span.className = "tag"; span.textContent = x; jobs.appendChild(span); });
  }
}

function renderTreemap(rows) {
  const mode = document.getElementById("modeSelect").value;
  const maxRate = getRoundedMaxRate(rows);
  const { labels, parents, values, ids, colors, customdata } = buildTreemapData(rows, mode);
  document.getElementById("resultMeta").textContent = `当前展示 ${rows.length} 个专业`;
  const data = [{
    type: "treemap",
    branchvalues: "total",
    labels, parents, ids, values, customdata,
    textinfo: "label",
    hovertemplate: "<b>%{label}</b><br>替代率: %{color:.0%}<br>面积值: %{value}<extra></extra>",
    marker: {
      colors,
      colorscale: [[0.0, SOFT_SCALE[0]], [0.2, SOFT_SCALE[1]], [0.4, SOFT_SCALE[2]], [0.6, SOFT_SCALE[3]], [0.8, SOFT_SCALE[4]], [1.0, SOFT_SCALE[5]]],
      cmin: 0,
      cmax: maxRate,
      line: { width: 1, color: "rgba(70,60,48,0.16)" },
      showscale: false
    },
    pathbar: { visible: true, thickness: 28, textfont: { color: "#51483f", size: 13 } },
    tiling: { packing: "squarify", pad: 2 },
    root: { color: "rgba(255,255,255,0.02)" }
  }];
  const layout = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { t: 8, r: 8, b: 8, l: 8 },
    font: { color: "#2b2722", family: 'Inter, ui-sans-serif, system-ui, sans-serif' }
  };
  Plotly.newPlot("treemap", data, layout, { responsive: true, displayModeBar: false });
  const plot = document.getElementById("treemap");
  plot.on("plotly_click", (evt) => {
    const point = evt.points && evt.points[0];
    if (!point || !point.customdata) return;
    const [type, majorCode] = point.customdata;
    if (type !== "major") return;
    const row = rows.find(x => String(x.major_code) === String(majorCode));
    if (row) renderDetail(row);
  });
}

function renderTable(rows) {
  const tbody = document.getElementById("majorTableBody");
  tbody.innerHTML = "";
  rows.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.major_name || ""}</td>
      <td>${row.major_category || ""}</td>
      <td>${fmtPct(row.adjusted_replace_rate || row.replace_rate)}</td>
      <td>${row.job_count || 0} / ${row.category_major_count || 0}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderDisciplineList(rows) {
  const maxRate = getRoundedMaxRate(rows);
  const items = computeDisciplineStats(rows).slice(0, 20);
  renderRankList("disciplineList", items, (r) => `
    <div><div class="rank-name">${r.name}</div><div class="rank-meta">专业数 ${r.count}</div></div>
    <div class="rank-score" style="color:${riskColor(r.avg, maxRate)}">${fmtPct(r.avg)}</div>
  `);
}

async function main() {
  const rows = await fetchJson(DATA_URL);
  renderKpis(rows);
  fillDisciplineFilter(rows);
  const rerender = () => {
    const filtered = applyFilters(rows);
    const safeRows = filtered.length ? filtered : rows;
    renderKpis(safeRows);
    renderTable(safeRows);
    renderTopRisk(safeRows);
    renderDisciplineList(safeRows);
    document.getElementById("updatedAt").textContent = `Updated: ${new Date().toLocaleString("zh-CN")}`;
  };
  document.getElementById("searchInput").addEventListener("input", rerender);
  document.getElementById("disciplineFilter").addEventListener("change", rerender);
  document.getElementById("modeSelect").addEventListener("change", rerender);
  rerender();
}

main().catch((err) => {
  console.error(err);
  document.getElementById("majorTableBody").innerHTML = `<tr><td colspan="4" style="padding:24px;color:#8a5656;">数据加载失败：请确认 site/data/major_ai_rate.json 已正确生成。</td></tr>`;
});
