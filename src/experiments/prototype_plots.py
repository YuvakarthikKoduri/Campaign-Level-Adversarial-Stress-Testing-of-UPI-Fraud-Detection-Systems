"""Dependency-free SVG figures; plotted values come from saved experiment results."""
from html import escape
import statistics


def plots(output, summaries, learning):
    colors = {"static": "#64748b", "adaptive": "#d97706", "rl": "#2563eb",
              "untrained_rl": "#9333ea"}
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="700" viewBox="0 0 1000 700">',
           '<rect width="1000" height="700" fill="white"/>',
           '<g font-family="sans-serif" fill="#172033">',
           '<text x="35" y="35" font-size="24">Synthetic campaign success</text>',
           '<text x="35" y="60" font-size="13">Mean of evaluation-seed success rates; exploratory, not real UPI validation.</text>']
    groups = sorted(set((r["detector"], r["kind"]) for r in summaries))
    for i, group in enumerate(groups):
        x, y = 45 + (i % 2) * 490, 110 + (i // 2) * 275
        svg.append(f'<text x="{x}" y="{y}" font-size="17">{escape(" / ".join(group))}</text>')
        rows = [r for r in summaries if (r["detector"], r["kind"]) == group]
        for j, r in enumerate(rows):
            yy = y + 35 + j * 46
            value = r["success_mean"]
            svg.extend([f'<text x="{x}" y="{yy}" font-size="13">{escape(r["attacker"])}</text>',
                        f'<rect x="{x+105}" y="{yy-14}" width="{270*value:.2f}" height="22" fill="{colors[r["attacker"]]}"/>',
                        f'<text x="{x+110+270*value:.2f}" y="{yy+2}" font-size="12">{100*value:.1f}%</text>'])
    svg.append('</g></svg>')
    with (output / "comparison.svg").open("x") as f:
        f.write("\n".join(svg))
    if not learning:
        return
    detector_names = sorted(set(r["detector"] for r in learning))
    series = {}
    for name in detector_names:
        values = [r for r in learning if r["detector"] == name]
        max_episode = max(r["episode"] for r in values)
        series[name] = [(min(end, max_episode), statistics.mean(r["reward"] for r in values
                                             if max(0, end-25) < r["episode"] <= end))
                        for end in range(25, max_episode+25, 25)
                        if any(max(0, end-25) < r["episode"] <= end for r in values)]
    all_y = [y for values in series.values() for _, y in values]
    low, high = min(-1.2, min(all_y)), max(1., max(all_y))
    max_x = max(x for values in series.values() for x, _ in values)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="450">',
           '<rect width="1000" height="450" fill="white"/>',
           '<g font-family="sans-serif" fill="#172033">',
           '<text x="40" y="35" font-size="23">RL training reward</text>',
           '<text x="40" y="60" font-size="13">Non-overlapping 25-episode means pooled across training seeds; reward is not detector quality.</text>']
    for j in range(5):
        val = low + (high-low)*j/4
        yy = 365 - j*65
        svg.extend([f'<path d="M75 {yy} H930" stroke="#e2e8f0"/>',
                    f'<text x="20" y="{yy+5}" font-size="12">{val:.2f}</text>'])
    for i, (name, points) in enumerate(series.items()):
        color = ("#2563eb", "#d97706")[i % 2]
        coords = " ".join(f"{75+855*x/max_x:.2f},{365-260*(y-low)/(high-low):.2f}" for x, y in points)
        svg.extend([f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="3"/>',
                    f'<text x="{100+i*300}" y="420" fill="{color}" font-size="14">{escape(name)}</text>'])
    svg.extend([f'<text x="75" y="390" font-size="12">0</text>',
                f'<text x="820" y="390" font-size="12">{max_x} episodes</text>', '</g></svg>'])
    with (output / "learning.svg").open("x") as f:
        f.write("\n".join(svg))
