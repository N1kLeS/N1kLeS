import json
import math
import os
import urllib.request
from html import escape

token = os.environ["GITHUB_TOKEN"]
username = os.environ["GITHUB_USERNAME"]

query = """
query($login: String!) {
  user(login: $login) {
    repositories(
      first: 100,
      ownerAffiliations: OWNER,
      isFork: false,
      privacy: PUBLIC,
      orderBy: {field: PUSHED_AT, direction: DESC}
    ) {
      nodes {
        languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {"login": username}
}).encode()

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())

repos = data["data"]["user"]["repositories"]["nodes"]

totals = {}
colors = {}

for repo in repos:
    for edge in repo["languages"]["edges"]:
        name = edge["node"]["name"]
        color = edge["node"]["color"] or "#999999"
        size = edge["size"]
        totals[name] = totals.get(name, 0) + size
        colors[name] = color

items = sorted(totals.items(), key=lambda x: x[1], reverse=True)

if not items:
    items = [("No data", 1)]
    colors["No data"] = "#999999"

total_size = sum(v for _, v in items)

width = 570
legend_x = 47
legend_box = 25
legend_text_x = 79
legend_start_y = 110
legend_gap = 50
title_y = 61
height = max(355, legend_start_y + len(items) * legend_gap + 30)

cx = 425
cy = height // 2 + 10
r = 91
stroke_width = 47
circ = 2 * math.pi * r

circles = []
offset = 0.0

for name, value in items:
    part = value / total_size
    dash = circ * part
    color = colors.get(name, "#999999")
    circles.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-dasharray="{dash:.2f} {circ:.2f}" stroke-dashoffset="{-offset:.2f}" '
        f'transform="rotate(-90 {cx} {cy})"/>'
    )
    offset += dash

legend = []
for i, (name, value) in enumerate(items):
    y = legend_start_y + i * legend_gap
    pct = value / total_size * 100
    color = colors.get(name, "#999999")
    label = f"{name} {pct:.1f}%"
    legend.append(f'<rect x="{legend_x}" y="{y - 12}" width="{legend_box}" height="{legend_box}" fill="{color}"/>')
    legend.append(
        f'<text x="{legend_text_x}" y="{y + 11}" class="label">{escape(label)}</text>'
    )

svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .title {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        font-size: 44px;
        font-weight: 500;
        fill: #ff4fa3;
      }}

      .label {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        font-size: 28px;
        font-weight: 600;
        fill: #b9fff7;
      }}

      .donut {{
        transform-box: fill-box;
        transform-origin: center;
        animation: spin 9s linear infinite;
      }}

      @keyframes spin {{
        from {{
          transform: rotate(0deg);
        }}

        to {{
          transform: rotate(360deg);
        }}
      }}
    </style>
  </defs>

  <rect width="{width}" height="{height}" fill="#171421"/>

  <text x="24" y="{title_y}" class="title">Languages by Repo</text>

  {''.join(legend)}

  <g class="donut">
    {''.join(circles)}
  </g>

  <circle cx="{cx}" cy="{cy}" r="67" fill="#171421"/>
</svg>
'''

os.makedirs("assets", exist_ok=True)

with open("assets/top-languages.svg", "w", encoding="utf-8") as f:
    f.write(svg)
