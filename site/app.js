const DATA_URL = "./data/major_ai_rate.json";

function fmtPct(v) {
  return `${(Number(v || 0) * 100).toFixed(1)}%`;
}

function riskColor(rate) {
  const x = Number(rate || 0);
  if (x < 0.2) return "#22c55e";
  if (x < 0.4) return "#84cc16";
  if (x < 0.6) return "#facc15";
  if (x < 0.8) return "#fb923c";
  return "#f43f5e";
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

function buildTreemapData(rows, mode, sizeMode) {
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
  values.push(rows.reduce((s, r) => s + (sizeMode === "job_count" ? Math.max(1, Number(r.job_count || 0)) : 1), 0));
  colors.push(rows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (rows.length || 1));
  customdata.push(["root", "", "", "", "", "", ""]);

  if (mode === "discipline") {
    const disciplineMap = groupBy(rows, r => r.discipline || "未分类");
    for (const [discipline, disciplineRows] of disciplineMap.entries()) {
      const disciplineId = `discipline:${discipline}`;
      labels.push(discipline);
      parents.push(rootId);
      ids.push(disciplineId);
      values.push(disciplineRows.reduce((s, r) => s + (sizeMode === "job_count" ? Math.max(1, Number(r.job_count || 0)) : 1), 0));
      colors.push(disciplineRows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (disciplineRows.length || 1));
      customdata.push(["discipline", discipline, "", "", "", "", ""]);

      const categoryMap = groupBy(disciplineRows, r => r.major_category || "未分类");
      for (const [category, categoryRows] of categoryMap.entries()) {
        const categoryId = `category:${discipline}:${category}`;
        labels.push(category);
        parents.push(disciplineId);
        ids.push(categoryId);
        values.push(categoryRows.reduce((s, r) => s + (sizeMode === "job_count" ? Math.max(1, Number(r.job_count || 0)) : 1), 0));
        colors.push(categoryRows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (categoryRows.length || 1));
        customdata.push(["category", "", category, "", "", "", ""]);

        for (const row of categoryRows) {
          const id = `major:${row.major_code}`;
          labels.push(row.major_name);
          parents.push(categoryId);
          ids.push(id);
          values.push(sizeMode === "job_count" ? Math.max(1, Number(row.job_count || 0)) : 1);
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
      values.push(categoryRows.reduce((s, r) => s + (sizeMode === "job_count" ? Math.max(1, Number(r.job_count || 0)) : 1), 0));
      colors.push(categoryRows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (categoryRows.length || 1));
      customdata.push(["category", "", category, "", "", "", ""]);

      for (const row of categoryRows) {
        const id = `major:${row.major_code}`;
        labels.push(row.major_name);
        parents.push(categoryId);
        ids.push(id);
        values.push(sizeMode === "job_count" ? Math.max(1, Number(row.job_count || 0)) : 1);
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
  const sizeMode = document.getElementById("sizeSelect").value;
  const { labels, parents, values, ids, colors, customdata } = buildTreemapData(rows, mode, sizeMode);

  document.getElementById("resultMeta").textContent = `当前展示 ${rows.length} 个专业`;

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
      "替代率: %{color:.2%}<br>" +
      "面积值: %{value}<extra></extra>",
    marker: {
      colors,
      colorscale: [
        [0.0, "#22c55e"],
        [0.25, "#84cc16"],
        [0.5, "#facc15"],
        [0.75, "#fb923c"],
        [1.0, "#f43f5e"]
      ],
      cmin: 0,
      cmax: 1,
      line: {
        width: 1,
        color: "rgba(255,255,255,0.15)"
      },
      colorbar: {
        title: "替代率",
        tickformat: ".0%",
        outlinewidth: 0,
        x: 1.03
      }
    },
    pathbar: {
      visible: true,
      thickness: 28,
      textfont: {
        color: "#dbe8ff",
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
      color: "#eef4ff",
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
  const items = rows
    .slice()
    .sort((a, b) => Number(b.replace_rate || 0) - Number(a.replace_rate || 0))
    .slice(0, 20);

  renderRankList("topRiskList", items, (r) => `
    <div>
      <div class="rank-name">${r.major_name}</div>
      <div class="rank-meta">${r.major_code} · ${r.discipline} · 岗位数 ${r.job_count}</div>
    </div>
    <div class="rank-score" style="color:${riskColor(r.replace_rate)}">${fmtPct(r.replace_rate)}</div>
  `);
}

function renderDisciplineList(rows) {
  const items = computeDisciplineStats(rows).slice(0, 20);
  renderRankList("disciplineList", items, (r) => `
    <div>
      <div class="rank-name">${r.name}</div>
      <div class="rank-meta">专业数 ${r.count}</div>
    </div>
    <div class="rank-score" style="color:${riskColor(r.avg)}">${fmtPct(r.avg)}</div>
  `);
}

async function main() {
  const rows = await fetchJson(DATA_URL);

  renderKpis(rows);
  fillDisciplineFilter(rows);

  const rerender = () => {
    const filtered = applyFilters(rows);
    renderTreemap(filtered);
    renderTopRisk(filtered);
    renderDisciplineList(filtered);
    document.getElementById("updatedAt").textContent = `Updated: ${new Date().toLocaleString("zh-CN")}`;
  };

  document.getElementById("searchInput").addEventListener("input", rerender);
  document.getElementById("disciplineFilter").addEventListener("change", rerender);
  document.getElementById("modeSelect").addEventListener("change", rerender);
  document.getElementById("sizeSelect").addEventListener("change", rerender);

  rerender();
}

main().catch((err) => {
  console.error(err);
  const el = document.getElementById("treemap");
  el.innerHTML = `<div style="padding:24px;color:#ff9cb0;">数据加载失败：请确认 site/data/major_ai_rate.json 已正确生成。</div>`;
});