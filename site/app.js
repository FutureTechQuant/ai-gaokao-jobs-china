const DATA_URL = "./data/major_ai_rate.json";
const SOFT_SCALE = ["#6f8f80", "#97a77b", "#c8b27e", "#c99672", "#b87478"];

function fmtPct(v) {
  return `${Math.round(Number(v || 0) * 100)}%`;
}

function riskColor(rate, maxRate = 1) {
  const safeMax = Math.max(0.01, Number(maxRate || 0.01));
  const x = Math.max(0, Math.min(1, Number(rate || 0) / safeMax));
  if (x < 0.2) return SOFT_SCALE[0];
  if (x < 0.4) return SOFT_SCALE[1];
  if (x < 0.6) return SOFT_SCALE[2];
  if (x < 0.8) return SOFT_SCALE[3];
  return SOFT_SCALE[4];
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

function renderLegend(maxRate) {
  const box = document.getElementById("legendScale");
  box.innerHTML = "";
  SOFT_SCALE.forEach(color => {
    const span = document.createElement("span");
    span.className = "legend-chip";
    span.style.background = color;
    box.appendChild(span);
  });
  document.getElementById("legendNote").textContent = `0% – ${Math.round(maxRate * 100)}%`;
  document.getElementById("rangeMeta").textContent = `当前上限 ${Math.round(maxRate * 100)}%`;
}

function renderKpis(rows) {
  const total = rows.length;
  const avg = rows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (total || 1);
  const high = rows.filter(r => Number(r.replace_rate || 0) >= 0.7).length;
  const highConfidence = rows.filter(r => r.confidence === "high").length;

  document.getElementById("kpi-total").textContent = total.toLocaleString("zh-CN");
  document.getElementById("kpi-avg").textContent = fmtPct(avg);
  document.getElementById("kpi-high").textContent = high.toLocaleString("zh-CN");
  document.getElementById("kpi-confidence").textContent = highConfidence.toLocaleString("zh-CN");
}

function fillDisciplineFilter(rows) {
  const select = document.getElementById("disciplineFilter");
  const values = [...new Set(rows.map(r => r.discipline).filter(Boolean))].sort();
  for (const d of values) {
    const option = document.createElement("option");
    option.value = d;
    option.textContent = d;
    select.appendChild(option);
  }
}

function applyFilters(rows) {
  const q = document.getElementById("searchInput").value.trim().toLowerCase();
  const discipline = document.getElementById("disciplineFilter").value;

  return rows.filter(r => {
    const haystack = [
      r.major_code,
      r.major_name,
      r.discipline,
      r.major_category
    ].join(" ").toLowerCase();

    const okQ = !q || haystack.includes(q);
    const okD = !discipline || r.discipline === discipline;
    return okQ && okD;
  });
}

function computeDisciplineStats(rows) {
  const grouped = groupBy(rows, r => r.discipline || "未分类");
  return [...grouped.entries()]
    .map(([name, items]) => ({
      name,
      count: items.length,
      avg: items.reduce((s, x) => s + Number(x.replace_rate || 0), 0) / (items.length || 1)
    }))
    .sort((a, b) => b.avg - a.avg);
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
  const labels = [];
  const parents = [];
  const values = [];
  const ids = [];
  const colors = [];
  const customdata = [];

  const rootId = "root";
  labels.push("全部专业");
  parents.push("");
  ids.push(rootId);
  values.push(rows.length || 1);
  colors.push(rows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (rows.length || 1));
  customdata.push(["root", "", "", "", "", "", ""]);

  if (mode === "discipline") {
    const disciplineMap = groupBy(rows, r => r.discipline || "未分类");
    for (const [discipline, disciplineRows] of disciplineMap.entries()) {
      const disciplineId = `discipline:${discipline}`;
      labels.push(discipline);
      parents.push(rootId);
      ids.push(disciplineId);
      values.push(disciplineRows.length);
      colors.push(disciplineRows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (disciplineRows.length || 1));
      customdata.push(["discipline", discipline, "", "", "", "", ""]);

      const categoryMap = groupBy(disciplineRows, r => r.major_category || "未分类");
      for (const [category, categoryRows] of categoryMap.entries()) {
        const categoryId = `category:${discipline}:${category}`;
        labels.push(category);
        parents.push(disciplineId);
        ids.push(categoryId);
        values.push(categoryRows.length);
        colors.push(categoryRows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (categoryRows.length || 1));
        customdata.push(["category", "", category, "", "", "", ""]);

        for (const row of categoryRows) {
          const id = `major:${row.major_code}`;
          labels.push(row.major_name);
          parents.push(categoryId);
          ids.push(id);
          values.push(1);
          colors.push(Number(row.replace_rate || 0));
          customdata.push([
            "major",
            row.major_code || "",
            row.major_name || "",
            row.discipline || "",
            row.major_category || "",
            row.job_count || 0,
            row.confidence || "low"
          ]);
        }
      }
    }
  } else {
    const categoryMap = groupBy(rows, r => r.major_category || "未分类");
    for (const [category, categoryRows] of categoryMap.entries()) {
      const categoryId = `category:${category}`;
      labels.push(category);
      parents.push(rootId);
      ids.push(categoryId);
      values.push(categoryRows.length);
      colors.push(categoryRows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (categoryRows.length || 1));
      customdata.push(["category", "", category, "", "", "", ""]);

      for (const row of categoryRows) {
        const id = `major:${row.major_code}`;
        labels.push(row.major_name);
        parents.push(categoryId);
        ids.push(id);
        values.push(1);
        colors.push(Number(row.replace_rate || 0));
        customdata.push([
          "major",
          row.major_code || "",
          row.major_name || "",
          row.discipline || "",
          row.major_category || "",
          row.job_count || 0,
          row.confidence || "low"
        ]);
      }
    }
  }

  return { labels, parents, values, ids, colors, customdata };
}

function renderDetail(row) {
  const empty = document.getElementById("detailEmpty");
  const box = document.getElementById("detailBox");

  empty.classList.add("hidden");
  box.classList.remove("hidden");

  document.getElementById("detailCode").textContent = row.major_code || "-";
  document.getElementById("detailName").textContent = row.major_name || "-";
  document.getElementById("detailRate").textContent = fmtPct(row.replace_rate || 0);
  document.getElementById("detailJobCount").textContent = String(row.job_count || 0);
  document.getElementById("detailDiscipline").textContent = row.discipline || "-";
  document.getElementById("detailCategory").textContent = row.major_category || "-";

  const conf = row.confidence || "low";
  const badge = document.getElementById("detailConfidence");
  badge.textContent = conf;
  badge.className = confidenceBadgeClass(conf);

  const jobs = document.getElementById("detailJobs");
  jobs.innerHTML = "";
  const items = Array.isArray(row.matched_job_titles_sample) ? row.matched_job_titles_sample : [];
  if (!items.length) {
    jobs.innerHTML = '<span class="tag">暂无样例</span>';
  } else {
    items.forEach(x => {
      const span = document.createElement("span");
      span.className = "tag";
      span.textContent = x;
      jobs.appendChild(span);
    });
  }
}

function renderTreemap(rows) {
  const mode = document.getElementById("modeSelect").value;
  const maxRate = getRoundedMaxRate(rows);
  const { labels, parents, values, ids, colors, customdata } = buildTreemapData(rows, mode);

  document.getElementById("resultMeta").textContent = `当前展示 ${rows.length} 个专业`;
  renderLegend(maxRate);

  const data = [{
    type: "treemap",
    branchvalues: "total",
    labels,
    parents,
    ids,
    values,
    customdata,
    textinfo: "label",
    hovertemplate:
      "<b>%{label}</b><br>" +
      "替代率: %{color:.0%}<br>" +
      "面积值: %{value}<extra></extra>",
    marker: {
      colors,
      colorscale: [
        [0.0, SOFT_SCALE[0]],
        [0.25, SOFT_SCALE[1]],
        [0.5, SOFT_SCALE[2]],
        [0.75, SOFT_SCALE[3]],
        [1.0, SOFT_SCALE[4]]
      ],
      cmin: 0,
      cmax: maxRate,
      line: {
        width: 1,
        color: "rgba(70,60,48,0.16)"
      },
      colorbar: {
        title: "替代率",
        tickformat: ".0%",
        outlinewidth: 0,
        x: 1.02,
        len: 0.75,
        tickvals: [0, maxRate / 4, maxRate / 2, maxRate * 0.75, maxRate],
        ticktext: [
          "0%",
          `${Math.round(maxRate * 25)}%`,
          `${Math.round(maxRate * 50)}%`,
          `${Math.round(maxRate * 75)}%`,
          `${Math.round(maxRate * 100)}%`
        ]
      }
    },
    pathbar: {
      visible: true,
      thickness: 28,
      textfont: {
        color: "#51483f",
        size: 13
      }
    },
    tiling: {
      packing: "squarify",
      pad: 2
    },
    root: {
      color: "rgba(255,255,255,0.02)"
    }
  }];

  const layout = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { t: 8, r: 56, b: 8, l: 8 },
    font: {
      color: "#2b2722",
      family: 'Inter, ui-sans-serif, system-ui, sans-serif'
    }
  };

  Plotly.newPlot("treemap", data, layout, {
    responsive: true,
    displayModeBar: false
  });

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

function renderTopRisk(rows) {
  const maxRate = getRoundedMaxRate(rows);
  const items = rows
    .slice()
    .sort((a, b) => Number(b.replace_rate || 0) - Number(a.replace_rate || 0))
    .slice(0, 20);

  renderRankList("topRiskList", items, (r) => `
    <div>
      <div class="rank-name">${r.major_name}</div>
      <div class="rank-meta">${r.major_code} · ${r.discipline} · 岗位数 ${r.job_count}</div>
    </div>
    <div class="rank-score" style="color:${riskColor(r.replace_rate, maxRate)}">${fmtPct(r.replace_rate)}</div>
  `);
}

function renderDisciplineList(rows) {
  const maxRate = getRoundedMaxRate(rows);
  const items = computeDisciplineStats(rows).slice(0, 20);
  renderRankList("disciplineList", items, (r) => `
    <div>
      <div class="rank-name">${r.name}</div>
      <div class="rank-meta">专业数 ${r.count}</div>
    </div>
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
    renderTreemap(safeRows);
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
  const el = document.getElementById("treemap");
  el.innerHTML = `<div style="padding:24px;color:#8a5656;">数据加载失败：请确认 site/data/major_ai_rate.json 已正确生成。</div>`;
});
