/* Tiny dependency-free SVG charts (work offline). */
const LMSCharts = (function () {

    const NS = "http://www.w3.org/2000/svg";
    const COLORS = ["#2563eb", "#9ca3af", "#16a34a", "#f59e0b", "#8b5cf6", "#dc2626"];

    function esc(t) {
        return String(t).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
    }

    function mount(el, svg, legend) {
        el.innerHTML = '<svg xmlns="' + NS + '" viewBox="0 0 600 300" width="100%" ' +
            'preserveAspectRatio="xMidYMid meet" role="img">' + svg + '</svg>' + (legend || "");
    }

    function legendHtml(items) {
        return '<div class="chart-legend">' + items.map(i =>
            '<span><i style="background:' + i.color + '"></i>' + esc(i.label) + '</span>').join("") + '</div>';
    }

    function axes(max) {
        let out = "";
        for (let i = 0; i <= 4; i++) {
            const v = max * i / 4, y = 260 - (i * 55);
            out += '<line x1="50" x2="590" y1="' + y + '" y2="' + y + '" stroke="#e5e7eb"/>' +
                   '<text x="44" y="' + (y + 4) + '" font-size="11" text-anchor="end" fill="#6b7280">' + Math.round(v) + '</text>';
        }
        return out;
    }

    /* Grouped vertical bars. datasets: [{label, data, color}] */
    function bars(el, labels, datasets, max) {
        max = max || 100;
        const groupW = 540 / labels.length, barW = Math.min(36, (groupW - 12) / datasets.length);
        let svg = axes(max);
        labels.forEach((lab, i) => {
            const gx = 50 + i * groupW + (groupW - barW * datasets.length) / 2;
            datasets.forEach((ds, k) => {
                const v = Math.max(0, Math.min(max, ds.data[i] || 0)), h = v / max * 220;
                svg += '<rect x="' + (gx + k * barW) + '" y="' + (260 - h) + '" width="' + (barW - 2) + '" height="' + h +
                       '" rx="3" fill="' + (ds.color || COLORS[k]) + '"><title>' + esc(ds.label + ": " + Math.round(v)) + '</title></rect>';
            });
            svg += '<text x="' + (50 + i * groupW + groupW / 2) + '" y="280" font-size="11" text-anchor="middle" fill="#374151">' +
                   esc(lab.length > 14 ? lab.slice(0, 13) + "…" : lab) + '</text>';
        });
        mount(el, svg, datasets.length > 1 ? legendHtml(datasets.map((d, k) => ({label: d.label, color: d.color || COLORS[k]}))) : "");
    }

    /* Horizontal bars for a single series (0-100) */
    function hbars(el, labels, values, colors) {
        let svg = "";
        const rowH = 280 / labels.length;
        labels.forEach((lab, i) => {
            const y = 10 + i * rowH, w = Math.max(0, Math.min(100, values[i] || 0)) / 100 * 380;
            svg += '<text x="120" y="' + (y + rowH / 2) + '" font-size="13" text-anchor="end" fill="#374151">' + esc(lab) + '</text>' +
                   '<rect x="130" y="' + (y + 6) + '" width="400" height="' + (rowH - 18) + '" rx="4" fill="#f3f4f6"/>' +
                   '<rect x="130" y="' + (y + 6) + '" width="' + w + '" height="' + (rowH - 18) + '" rx="4" fill="' + (colors[i % colors.length]) + '"/>' +
                   '<text x="' + (136 + w) + '" y="' + (y + rowH / 2) + '" font-size="12" fill="#111827">' + Math.round(values[i] || 0) + '%</text>';
        });
        mount(el, svg);
    }

    /* Line chart, single series 0-100. tips: optional tooltip text per point */
    function line(el, labels, values, tips) {
        if (!values.length) { return; }
        const n = values.length, step = n > 1 ? 520 / (n - 1) : 0;
        const pts = values.map((v, i) => [n > 1 ? 60 + i * step : 320, 260 - Math.max(0, Math.min(100, v)) / 100 * 220]);
        let svg = axes(100);
        svg += '<polyline fill="none" stroke="#2563eb" stroke-width="3" points="' + pts.map(p => p.join(",")).join(" ") + '"/>';
        pts.forEach((p, i) => {
            svg += '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="5" fill="#2563eb"><title>' +
                   esc((tips && tips[i] ? tips[i] + " — " : "") + labels[i] + ": " + Math.round(values[i]) + "%") + '</title></circle>';
        });
        const every = Math.ceil(n / 8);
        labels.forEach((lab, i) => {
            if (i % every === 0) {
                svg += '<text x="' + pts[i][0] + '" y="282" font-size="10" text-anchor="middle" fill="#6b7280">' + esc(lab.slice(0, 5)) + '</text>';
            }
        });
        mount(el, svg);
    }

    /* Doughnut with legend */
    function doughnut(el, labels, values, colors) {
        const total = values.reduce((a, b) => a + b, 0);
        let svg = "";
        if (!total) {
            svg = '<text x="300" y="150" text-anchor="middle" fill="#6b7280">No data yet</text>';
            mount(el, svg);
            return;
        }
        let angle = -Math.PI / 2;
        const cx = 300, cy = 145, R = 120, r = 70;
        values.forEach((v, i) => {
            if (!v) { return; }
            const a2 = angle + v / total * 2 * Math.PI;
            if (v === total) {
                svg += '<circle cx="' + cx + '" cy="' + cy + '" r="' + ((R + r) / 2) + '" fill="none" stroke="' + colors[i] + '" stroke-width="' + (R - r) + '"/>';
            } else {
                const large = a2 - angle > Math.PI ? 1 : 0;
                const p = (rad, a) => (cx + rad * Math.cos(a)).toFixed(1) + "," + (cy + rad * Math.sin(a)).toFixed(1);
                svg += '<path d="M' + p(R, angle) + " A" + R + "," + R + " 0 " + large + " 1 " + p(R, a2) +
                       " L" + p(r, a2) + " A" + r + "," + r + " 0 " + large + " 0 " + p(r, angle) + ' Z" fill="' + colors[i] +
                       '"><title>' + esc(labels[i] + ": " + v) + '</title></path>';
            }
            angle = a2;
        });
        svg += '<text x="300" y="152" font-size="28" font-weight="bold" text-anchor="middle" fill="#111827">' + total + '</text>';
        mount(el, svg, legendHtml(labels.map((l, i) => ({label: l + " (" + values[i] + ")", color: colors[i]}))));
    }

    return {bars, hbars, line, doughnut};
})();
