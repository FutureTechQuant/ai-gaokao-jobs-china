function riskColor(rate) {
  if (rate < 0.2) return "#1db954";
  if (rate < 0.4) return "#6cc24a";
  if (rate < 0.6) return "#ffcc00";
  if (rate < 0.8) return "#ff8c42";
  return "#ff4d6d";
}

function fmtPct(x) {
  return `${(Number(x || 0) * 100).toFixed(1)}%`;
}

function badgeClass(conf) {
  if (conf === "high") return "badge conf-high";
  if (conf === "medium") return "badge conf-medium";
  return "badge conf-low";
}

async function loadData() {
  const res = await fetch("./data/major_ai_rate.json");
  if (!res.ok) throw new Error("加载 major_ai_rate.json 失败");
  return res.json();
}

function computeDisciplineStats(rows) {
  const map = new Map();
  rows.forEach(r => {
    const key = r.discipline || "未分类";
    if (!map.has(key)) map.set(key, { count: 0, sum: 0 });
    const x = map.get(key);
    x.count += 1;
    x.sum += Number(r.replace_rate || 0);
  });
  return [...map.entries()]
    .map(([name, v]) => ({
      name,
      avg: v.count ? v.sum / v.count : 0,
      count: v.count
    }))
    .sort((a, b) => b.avg - a.avg);
}

function renderKpis(rows) {
  const total = rows.length;
  const avg = rows.reduce((s, r) => s + Number(r.replace_rate || 0), 0) / (total || 1);
  const high = rows.filter(r => Number(r.replace_rate || 0) >= 0.7).length;
  const highConf = rows.filter(r => r.confidence === "high").length;

  document.getElementById("kpi-total").textContent = total.toLocaleString("zh-CN");
  document.getElementById("kpi-avg").textContent = fmtPct(avg);
  document.getElementById("kpi-high").textContent = high.toLocaleString("zh-CN");
  document.getElementById("kpi-confidence").textContent = highConf.toLocaleString("zh-CN");
}

function renderFilters(rows) {
  const disciplines = [...new Set(rows.map(x => x.discipline).filter(Boolean))].sort();
  const select = document.getElementById("disciplineFilter");
  disciplines.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d;
    opt.textContent = d;
    select.appendChild(opt);
  });
}

function applyFilter(rows) {
  const q = document.getElementById("search").value.trim().toLowerCase();
  const d = document.getElementById("disciplineFilter").value;
  const sortBy = document.getElementById("sortBy").value;

  let out = rows.filter(r => {
    const okQ = !q || [
      r.major_code,
      r.major_name,
      r.discipline,
      r.major_category
    ].join(" ").toLowerCase().includes(q);

    const okD = !d || r.discipline === d;
    return okQ && okD;
  });

  if (sortBy === "replace_desc") out.sort((a, b) => b.replace_rate - a.replace_rate);
  if (sortBy === "replace_asc") out.sort((a, b) => a.replace_rate - b.replace_rate);
  if (sortBy === "count_desc") out.sort((a, b) => b.job_count - a.job_count);
  if (sortBy === "code_asc") out.sort((a, b) => String(a.major_code).localeCompare(String(b.major_code)));

  return out;
}

function renderTable(rows) {
  const tbody = document.getElementById("tbody");
  tbody.innerHTML = "";
  document.getElementById("resultCount").textContent = `结果 ${rows.length} 条`;

  rows.forEach(r => {
    const tr = document.createElement("tr");
    const color = riskColor(r.replace_rate);
    tr.innerHTML = `
      <td>${r.major_code || ""}</td>
      <td>${r.major_name || ""}</td>
      <td>${r.discipline || ""}</td>
      <td>${r.major_category || ""}</td>
      <td>
        <div class="rate">
          <div class="bar"><span style="width:${Math.max(2, r.replace_rate * 100)}%;background:${color}"></span></div>
          <span>${fmtPct(r.replace_rate)}</span>
        </div>
      </td>
      <td>${r.job_count || 0}</td>
      <td><span class="${badgeClass(r.confidence)}">${r.confidence || "low"}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderTopRisk(rows) {
  const box = document.getElementById("topRisk");
  box.innerHTML = "";
  rows.slice().sort((a, b) => b.replace_rate - a.replace_rate).slice(0, 20).forEach(r => {
    const div = document.createElement("div");
    div.className = "rank-item";
    div.innerHTML = `
      <div>
        <div class="name">${r.major_name}</div>
        <div class="meta">${r.major_code} · ${r.discipline} · 岗位数 ${r.job_count}</div>
      </div>
      <div class="score" style="color:${riskColor(r.replace_rate)}">${fmtPct(r.replace_rate)}</div>
    `;
    box.appendChild(div);
  });
}

function renderDisciplineStats(rows) {
  const stats = computeDisciplineStats(rows).slice(0, 20);
  const box = document.getElementById("disciplineStats");
  box.innerHTML = "";
  stats.forEach(r => {
    const div = document.createElement("div");
    div.className = "rank-item";
    div.innerHTML = `
      <div>
        <div class="name">${r.name}</div>
        <div class="meta">专业数 ${r.count}</div>
      </div>
      <div class="score" style="color:${riskColor(r.avg)}">${fmtPct(r.avg)}</div>
    `;
    box.appendChild(div);
  });
}

async function main() {
  const data = await loadData();
  const rows = Array.isArray(data) ? data : [];

  renderKpis(rows);
  renderFilters(rows);

  const rerender = () => {
    const filtered = applyFilter([...rows]);
    renderTable(filtered);
    renderTopRisk(filtered);
    renderDisciplineStats(filtered);
    document.getElementById("updatedAt").textContent = `Updated: ${new Date().toLocaleString("zh-CN")}`;
  };

  document.getElementById("search").addEventListener("input", rerender);
  document.getElementById("disciplineFilter").addEventListener("change", rerender);
  document.getElementById("sortBy").addEventListener("change", rerender);

  rerender();
}

main().catch(err => {
  console.error(err);
  document.getElementById("tbody").innerHTML =
    `<tr><td colspan="7">数据加载失败，请确认 site/data/major_ai_rate.json 已生成。</td></tr>`;
});
