#!/usr/bin/env python3
"""Refresh a local contribution SVG from the live GitHub GraphQL API."""
import argparse
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
from pathlib import Path
import subprocess

COLORS = {
    'NONE': '#161b22', 'FIRST_QUARTILE': '#0e4429',
    'SECOND_QUARTILE': '#006d32', 'THIRD_QUARTILE': '#26a641',
    'FOURTH_QUARTILE': '#39d353',
}


def render(calendar, login):
    """Render the API's calendar deterministically, without remote assets."""
    weeks = calendar['weeks']
    days = [day for week in weeks for day in week['contributionDays']]
    total = calendar['totalContributions']
    if sum(day['contributionCount'] for day in days) != total:
        raise ValueError('Contribution total does not match calendar cells')
    start, end = min(day['date'] for day in days), max(day['date'] for day in days)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="240" viewBox="0 0 800 240" role="img" aria-labelledby="title desc">',
        f'<title id="title">GitHub activity — {escape(login)}</title>',
        f'<desc id="desc">{total} contributions from {start} through {end}. GitHub API data, not a commit count.</desc>',
        '<rect x="0.5" y="0.5" width="799" height="239" rx="10" fill="#0d1117" stroke="#30363d"/>',
        '<g font-family="ui-monospace, SFMono-Regular, Consolas, monospace">',
        '<text x="24" y="29" fill="#8b949e" font-size="11" letter-spacing="1.4">GITHUB / CONTRIBUTIONS</text>',
        f'<text x="24" y="58" fill="#e6edf3" font-size="20">{total:,} contributions</text>',
        f'<text x="775" y="29" fill="#8b949e" font-size="11" text-anchor="end">{escape(login)}</text>',
        f'<text x="775" y="55" fill="#8b949e" font-size="11" text-anchor="end">{start} → {end}</text>',
    ]
    last_month = None
    for index, week in enumerate(weeks):
        first = date.fromisoformat(week['contributionDays'][0]['date'])
        x = 56 + index * 13
        if first.month != last_month:
            parts.append(f'<text x="{x}" y="82" fill="#8b949e" font-size="10">{first.strftime("%b")}</text>')
            last_month = first.month
        for day in week['contributionDays']:
            dt = date.fromisoformat(day['date'])
            y = 94 + ((dt.weekday() + 1) % 7) * 15
            color = COLORS[day['contributionLevel']]
            parts.append(f'<rect x="{x}" y="{y}" width="10" height="12" rx="2" fill="{color}" stroke="#30363d" stroke-width="0.3"><title>{dt}: {day["contributionCount"]} contributions</title></rect>')
    for label, row in [('Mon', 1), ('Wed', 3), ('Fri', 5)]:
        parts.append(f'<text x="24" y="{103 + row * 15}" fill="#8b949e" font-size="9">{label}</text>')
    parts.append('<text x="24" y="221" fill="#8b949e" font-size="10">Rolling year · updated daily · GitHub API</text>')
    parts.append('<text x="617" y="221" fill="#8b949e" font-size="10">Less</text>')
    for index, color in enumerate(COLORS.values()):
        parts.append(f'<rect x="{650 + index * 15}" y="211" width="11" height="11" rx="2" fill="{color}"/>')
    parts.extend(['<text x="733" y="221" fill="#8b949e" font-size="10">More</text>', '</g></svg>'])
    return '\n'.join(parts) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--login', default='abduvaliy-engineer')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'assets/github-activity.svg')
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    start = datetime.combine(now.date() - timedelta(days=364), datetime.min.time(), tzinfo=timezone.utc)
    query = '''query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar { totalContributions weeks { contributionDays {
            date contributionCount contributionLevel
          } } }
        }
      }
    }'''
    response = subprocess.run(
        ['gh', 'api', 'graphql', '-f', f'query={query}', '-f', f'login={args.login}',
         '-f', f'from={start.isoformat()}', '-f', f'to={now.isoformat()}'],
        check=True, capture_output=True, text=True, timeout=60,
    )
    payload = json.loads(response.stdout)
    if payload.get('errors'):
        raise SystemExit('GitHub GraphQL returned errors; existing graphic retained.')
    calendar = payload['data']['user']['contributionsCollection']['contributionCalendar']
    svg = render(calendar, args.login)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix('.svg.tmp')
    temporary.write_text(svg, encoding='utf-8')
    temporary.replace(args.output)
    print(f'Updated {args.output}: {calendar["totalContributions"]} GitHub contributions')
