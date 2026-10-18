"""
HTML Creator Script - Standings Only (Last Day / Season End)
"""

import pandas as pd
from datetime import date
import datetime
import requests
from bs4 import BeautifulSoup
import base64
from pathlib import Path


def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded

def img_to_html(img_path):
    img_html = "<img src='data:image/png;base64,{0}' height='100px' class='img-fluid'>".format(
      img_to_bytes(img_path)
    )
    return img_html

def generate_daily_projection_table(matchups_df, ChasesTeams, BrycesTeams, ZachsTeams, teamToAbbr):
    owner_colors = {
        "Chase": '#2774AE',
        "Bryce": '#57068c',
        "Zach": '#e21833'
    }

    owner_map = {}
    for team in ChasesTeams:
        owner_map[teamToAbbr[team]] = "Chase"
    for team in BrycesTeams:
        owner_map[teamToAbbr[team]] = "Bryce"
    for team in ZachsTeams:
        owner_map[teamToAbbr[team]] = "Zach"

    owners = ["Chase", "Bryce", "Zach"]
    results = {owner: {"teams_playing": 0, "max_wins": 0, "min_wins": 0, "favored": 0} for owner in owners}

    for _, row in matchups_df.iterrows():
        home = str(row["home_team"]).strip().upper()
        away = str(row["away_team"]).strip().upper()
        odds = str(row["odds"]).strip().upper()

        owner_home = owner_map.get(home)
        owner_away = owner_map.get(away)

        if not owner_home and not owner_away:
            continue

        if owner_home:
            results[owner_home]["teams_playing"] += 1
        if owner_away:
            results[owner_away]["teams_playing"] += 1

        if owner_home and owner_away:
            if owner_home == owner_away:
                results[owner_home]["max_wins"] += 1
                results[owner_home]["min_wins"] += 1
            else:
                results[owner_home]["max_wins"] += 1
                results[owner_away]["max_wins"] += 1
        else:
            owned = owner_home or owner_away
            results[owned]["max_wins"] += 1

        if "-" in odds:
            favored_team = odds.split(" ")[0].strip()
            favored_owner = owner_map.get(favored_team)
            if favored_owner:
                results[favored_owner]["favored"] += 1

    html = """
    <h3 class="daily-overview-title">Daily Overview</h3>
    <table class="standings-table">
      <tr><th></th><th>Teams Playing</th><th>Max Wins</th><th>Min Wins</th><th>Favored</th></tr>
    """
    for owner in owners:
        color = owner_colors[owner]
        r = results[owner]
        html += f"<tr><td style='color:{color}; font-weight:bold;'>{owner}</td><td>{r['teams_playing']}</td><td>{r['max_wins']}</td><td>{r['min_wins']}</td><td>{r['favored']}</td></tr>"
    html += "</table>"
    return html


def build_combined_value_view_html(standings, draft_info, overall_live_rank, ChasesTeams, BrycesTeams, ZachsTeams, teamToAbbr):
    owner_colors = {'Chase': '#2774AE', 'Bryce': '#57068c', 'Zach': '#e21833'}
    owner_map = {}
    for t in ChasesTeams:
        owner_map[t] = 'Chase'
    for t in BrycesTeams:
        owner_map[t] = 'Bryce'
    for t in ZachsTeams:
        owner_map[t] = 'Zach'

    html = (
        '<table id="valueTable" style="width:100%;border-collapse:collapse;">'
        '<thead><tr>'
        '<th class="sortable" onclick="sortValueTable(\'curr\')" style="text-align:left;padding-left:14px;">TEAM</th>'
        '<th class="sortable" onclick="sortValueTable(\'draft\')">DRAFT</th>'
        '<th class="sortable" onclick="sortValueTable(\'curr\')">CURR</th>'
        '<th class="sortable" onclick="sortValueTable(\'delta\')">&Delta;</th>'
        '</tr></thead><tbody>'
    )

    for idx, row in standings.reset_index(drop=True).iterrows():
        team = row['Team']
        abbr = teamToAbbr.get(team, team)
        rank = overall_live_rank.get(team, idx + 1)
        info = draft_info.get(team, {'ovr': 0, 'rd': 0})
        draft_ovr = info['ovr']
        delta = rank - draft_ovr
        owner = owner_map.get(team, '')
        color = owner_colors.get(owner, '#333')

        if delta < 0:
            delta_html = f"<span style='color:#16a34a;font-weight:700;'>&#9650; {abs(delta)}</span>"
        elif delta > 0:
            delta_html = f"<span style='color:#dc2626;font-weight:700;'>&#9660; {delta}</span>"
        else:
            delta_html = "<span style='color:#888;'>&#8212;</span>"

        html += (
            f'<tr data-owner="{owner}" data-valcurr="{rank}" data-valdraft="{draft_ovr}" data-valdelta="{delta}">'
            f'<td style="border-left:4px solid {color};padding-left:10px;font-weight:700;color:{color};text-align:left;">{abbr}</td>'
            f'<td>{draft_ovr}</td>'
            f'<td>{rank}</td>'
            f'<td>{delta_html}</td>'
            f'</tr>'
        )

    html += '</tbody></table>'
    return html


def scrape_nba_standings(url="https://www.espn.com/nba/standings"):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    all_teams = []

    responsive_tables = soup.find_all('div', class_='ResponsiveTable')

    for responsive_table in responsive_tables:
        team_table = responsive_table.find('table', class_='Table--fixed-left')
        stats_table = responsive_table.find('div', class_='Table__Scroller')

        if not team_table or not stats_table:
            continue

        stats_table = stats_table.find('table')

        team_rows = team_table.find('tbody').find_all('tr')
        stat_rows = stats_table.find('tbody').find_all('tr')

        for team_row, stat_row in zip(team_rows, stat_rows):
            try:
                team_link = team_row.find('span', class_='hide-mobile')
                if team_link:
                    team_name = team_link.get_text(strip=True)
                else:
                    team_abbr = team_row.find('abbr')
                    if team_abbr:
                        team_name = team_abbr.get_text(strip=True)
                    else:
                        continue

                stat_cells = stat_row.find_all('span', class_='stat-cell')

                if len(stat_cells) >= 3:
                    wins = stat_cells[0].get_text(strip=True)
                    losses = stat_cells[1].get_text(strip=True)
                    pct = stat_cells[2].get_text(strip=True)

                    all_teams.append({
                        'Team': team_name,
                        'W': wins,
                        'L': losses,
                        'PCT': pct
                    })
            except (IndexError, AttributeError) as e:
                print(f"Error processing row: {e}")
                continue

    return pd.DataFrame(all_teams)


standings = scrape_nba_standings()

ChasesTeams = ['Oklahoma City Thunder','Boston Celtics','Denver Nuggets','Toronto Raptors','Indiana Pacers','Golden State Warriors','Orlando Magic','Memphis Grizzlies','LA Clippers','Sacramento Kings']
ZachsTeams = ['San Antonio Spurs','Philadelphia 76ers','Houston Rockets','Minnesota Timberwolves','Atlanta Hawks','Portland Trail Blazers','Charlotte Hornets','Dallas Mavericks','New Orleans Pelicans','Milwaukee Bucks']
BrycesTeams = ['New York Knicks','Cleveland Cavaliers','Los Angeles Lakers','Miami Heat','Detroit Pistons','Phoenix Suns','Washington Wizards','Utah Jazz','Chicago Bulls','Brooklyn Nets']

# Snake draft: Chase 1st, Zach 2nd, Bryce 3rd
# Rd 1: C(1) Z(2) B(3) | Rd 2: B(4) Z(5) C(6) | Rd 3: C(7) Z(8) B(9) | ...
chase_picks = [1, 6, 7, 12, 13, 18, 19, 24, 25, 30]
zach_picks  = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29]
bryce_picks = [3, 4, 9, 10, 15, 16, 21, 22, 27, 28]

draft_info = {}
for i, team in enumerate(BrycesTeams):
    ovr = bryce_picks[i]
    draft_info[team] = {'rd': (ovr - 1) // 3 + 1, 'ovr': ovr}
for i, team in enumerate(ZachsTeams):
    ovr = zach_picks[i]
    draft_info[team] = {'rd': (ovr - 1) // 3 + 1, 'ovr': ovr}
for i, team in enumerate(ChasesTeams):
    ovr = chase_picks[i]
    draft_info[team] = {'rd': (ovr - 1) // 3 + 1, 'ovr': ovr}

standings['W'] = standings['W'].astype(int)
standings['L'] = standings['L'].astype(int)
standings['PCT'] = standings['PCT'].astype(float)
standings = standings.sort_values(by='W', ascending=False).drop(columns=['PCT'])

overall_live_rank = {row['Team']: idx + 1 for idx, row in standings.reset_index(drop=True).iterrows()}

chasesStandings = standings[standings['Team'].isin(ChasesTeams)].reset_index(drop=True)
chasesStandings.index += 1
brycesStandings = standings[standings['Team'].isin(BrycesTeams)].reset_index(drop=True)
brycesStandings.index += 1
zachsStandings = standings[standings['Team'].isin(ZachsTeams)].reset_index(drop=True)
zachsStandings.index += 1

teamToAbbr = {
    'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN', 'Charlotte Hornets': 'CHA', 'Chicago Bulls': 'CHI',
    'Cleveland Cavaliers': 'CLE', 'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN', 'Detroit Pistons': 'DET', 'Golden State Warriors': 'GS',
    'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND', 'LA Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Memphis Grizzlies': 'MEM',
    'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL', 'Minnesota Timberwolves': 'MIN', 'New Orleans Pelicans': 'NO', 'New York Knicks': 'NY',
    'Oklahoma City Thunder': 'OKC', 'Orlando Magic': 'ORL', 'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX', 'Portland Trail Blazers': 'POR',
    'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SA', 'Toronto Raptors': 'TOR', 'Utah Jazz': 'UTAH', 'Washington Wizards': 'WSH'
}

chasesStandings['Team'] = chasesStandings['Team'].replace('Oklahoma City Thunder', 'OKC Thunder')
brycesStandings['Team'] = brycesStandings['Team'].replace('Oklahoma City Thunder', 'OKC Thunder')
zachsStandings['Team'] = zachsStandings['Team'].replace('Oklahoma City Thunder', 'OKC Thunder')

chaseStandingsMobile = chasesStandings.copy()
bryceStandingsMobile = brycesStandings.copy()
zachStandingsMobile = zachsStandings.copy()

chaseStandingsMobile['Team'] = chaseStandingsMobile['Team'].replace('OKC Thunder', 'Oklahoma City Thunder').map(teamToAbbr)
bryceStandingsMobile['Team'] = bryceStandingsMobile['Team'].replace('OKC Thunder', 'Oklahoma City Thunder').map(teamToAbbr)
zachStandingsMobile['Team'] = zachStandingsMobile['Team'].replace('OKC Thunder', 'Oklahoma City Thunder').map(teamToAbbr)

chaseStandingsMobile = chaseStandingsMobile[['Team', 'W']]
bryceStandingsMobile = bryceStandingsMobile[['Team', 'W']]
zachStandingsMobile = zachStandingsMobile[['Team', 'W']]

combined_value_html = build_combined_value_view_html(
    standings, draft_info, overall_live_rank,
    ChasesTeams, BrycesTeams, ZachsTeams, teamToAbbr
)

chaseWins = chasesStandings['W'].sum()
bryceWins = brycesStandings['W'].sum()
zachWins = zachsStandings['W'].sum()

df = pd.read_excel('Wins_Over_Time.xlsx')
df['Day'] = pd.to_datetime(df['Day']).dt.normalize()
today = pd.Timestamp(date.today()-datetime.timedelta(days=1)).normalize()
existing_row = df[df['Day'] == today]

if not existing_row.empty:
    df.loc[df['Day'] == today, ['Chase', 'Bryce', 'Zach']] = [chaseWins, bryceWins, zachWins]
else:
    todaysData = pd.DataFrame({'Day': [today], 'Chase': [chaseWins], 'Bryce': [bryceWins], 'Zach': [zachWins]})
    df = pd.concat([df, todaysData], ignore_index=True)

df.to_excel('Wins_Over_Time.xlsx', index=False)
df.iloc[:, 1:] = df.iloc[:, 1:].sub(df.iloc[:, 1:].min(axis=1), axis=0)
df['Day'] = pd.to_datetime(df['Day']).dt.strftime('%b-%d')

# Schedule scraping for matchups_df (used by generate_daily_projection_table)
matchups = []
try:
    sched_url = 'https://www.espn.com/nba/schedule'
    sched_response = requests.get(sched_url, headers={'User-Agent': 'Mozilla/5.0'})
    sched_soup = BeautifulSoup(sched_response.text, 'html.parser')
    schedule_tables = sched_soup.find_all('div', class_='ScheduleTables')
    schedule_table = schedule_tables[1] if len(schedule_tables) > 1 else None
    if schedule_table:
        rows = schedule_table.find_all('tr', class_='Table__TR--sm')
        for row in rows:
            teams = row.find_all('a', class_='AnchorLink')
            away_team = teams[1]['href'].split('/')[-2] if len(teams) > 1 else None
            home_team = teams[3]['href'].split('/')[-2] if len(teams) > 3 else None
            time_cell = row.find('td', class_='date__col')
            game_time = time_cell.text.strip() if time_cell else None
            try:
                odds_info = row.find('div', class_='Odds__Message')
                odds = odds_info.text.strip() if odds_info else None
                odds = odds.split('O/U')[0].split('Line: ')[1]
            except Exception:
                odds = None
            matchups.append({'away_team': away_team, 'home_team': home_team, 'time': game_time, 'odds': odds})
except Exception as e:
    print(f"Schedule scrape failed (no games today?): {e}")

matchups_df = pd.DataFrame(matchups) if matchups else pd.DataFrame(columns=['away_team', 'home_team', 'time', 'odds'])

dpt = generate_daily_projection_table(matchups_df, ChasesTeams, BrycesTeams, ZachsTeams, teamToAbbr)

html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Standings</title>
    <script>
        function openCity(evt, cityName) {{
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].style.display = "none";
            }}
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {{
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }}
            document.getElementById(cityName).style.display = "block";
            evt.currentTarget.className += " active";
        }}

        let _valueViewActive = false;
        function toggleValueView() {{
            _valueViewActive = !_valueViewActive;
            document.getElementById('cardsRow').style.display = _valueViewActive ? 'none' : '';
            document.getElementById('valueViewSection').style.display = _valueViewActive ? 'block' : 'none';
            document.querySelectorAll('.toggle-btn').forEach(function(btn) {{
                btn.classList.toggle('active', _valueViewActive);
            }});
        }}

        let _sortCol = 'curr', _sortAsc = true;
        function sortValueTable(col) {{
            if (_sortCol === col) {{ _sortAsc = !_sortAsc; }}
            else {{ _sortCol = col; _sortAsc = true; }}
            const tbody = document.querySelector('#valueTable tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            rows.sort(function(a, b) {{
                const av = parseFloat(a.dataset['val' + col]);
                const bv = parseFloat(b.dataset['val' + col]);
                return _sortAsc ? av - bv : bv - av;
            }});
            rows.forEach(function(r) {{ tbody.appendChild(r); }});
        }}

        function filterOwner(btn, owner) {{
            const isAll = owner === 'all';
            document.querySelectorAll('#valueTable tbody tr').forEach(function(row) {{
                row.style.display = (isAll || row.dataset.owner === owner) ? '' : 'none';
            }});
            document.querySelectorAll('.vf-btn').forEach(function(b) {{ b.classList.remove('active'); }});
            btn.classList.add('active');
        }}
    </script>
    <style>
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}

    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        min-height: 100vh;
        padding: 20px;
    }}

    h1 {{
        text-align: center;
        color: #ffffff;
        font-size: 48px;
        margin: 20px 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        font-weight: 700;
        letter-spacing: 2px;
    }}

    h2 {{
        color: #333;
        font-weight: 600;
    }}

    h3 {{
        color: #555;
        font-size: 28px;
        margin: 20px 0 15px 0;
        font-weight: 600;
    }}

    table {{
        margin: 0 auto;
        width: 100%;
        border-collapse: collapse;
        background: white;
        border-radius: 8px;
        overflow: hidden;
    }}

    th, td {{
        padding: 14px 16px;
        text-align: center;
        font-size: 16px;
    }}

    th {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 14px;
        letter-spacing: 1px;
    }}

    td {{
        border-bottom: 1px solid #f0f0f0;
    }}

    img {{
        display: block;
        margin: 0 auto;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        height: 120px;
        width: auto;
    }}

    .row {{
        display: flex;
        justify-content: space-around;
        margin-top: 30px;
        gap: 20px;
        max-width: 1400px;
        margin-left: auto;
        margin-right: auto;
    }}

    .column {{
        flex: 1;
        padding: 0;
        min-width: 0;
    }}

    .card {{
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        padding: 30px;
        text-align: center;
        height: 100%;
    }}

    .card-header {{
        margin-bottom: 20px;
    }}

    .card-body h2 {{
        font-size: 32px;
        color: #333;
        margin: 15px 0;
        font-weight: 700;
    }}

    .table-container {{
        margin-top: 20px;
        overflow-x: auto;
        border-radius: 8px;
    }}

    .table-container2 {{
        margin-top: 0px;
        overflow-x: visible;
        font-size: 12px;
    }}

    .table-container table,
    .table-container2 table {{
        border-radius: 8px;
        overflow: hidden;
    }}

    #myLineChart {{
        width: 100%;
        max-width: 600px;
        margin: 20px auto;
    }}

    .progress-container {{
        width: 100%;
        max-width: 1400px;
        margin: 0 auto 20px auto;
        background-color: rgba(255, 255, 255, 0.3);
        border-radius: 50px;
        position: relative;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}

    .progress-bar {{
        height: 40px;
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        text-align: center;
        color: white;
        line-height: 40px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 16px;
        transition: width 0.5s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }}

    hr {{
        border: none;
        height: 3px;
        background: linear-gradient(90deg, transparent, currentColor, transparent);
        margin: 15px 0;
    }}

    .standings-table {{
        background: white;
        border-radius: 12px;
        overflow: hidden;
        margin: 20px auto;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    }}

    .standings-table th {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        padding: 14px 16px;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: white;
    }}

    .standings-table td {{
        padding: 14px 16px;
        font-weight: 600;
        font-size: 16px;
    }}

    .daily-overview-title {{
        color: white;
        padding: 5px;
        text-align: center;
        margin: 5px auto;
        max-width: 1400px;
        font-weight: 700;
    }}

    /* Title row with toggle button */
    .title-row {{
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        max-width: 1400px;
        margin: 0 auto;
    }}

    .toggle-btn {{
        background: rgba(255, 255, 255, 0.25);
        border: 2px solid white;
        color: white;
        padding: 10px 24px;
        border-radius: 50px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 600;
        backdrop-filter: blur(10px);
        transition: all 0.3s;
        white-space: nowrap;
    }}

    .toggle-btn:hover, .toggle-btn.active {{
        background: white;
        color: #059669;
    }}

    .desktop-vv {{
        position: absolute;
        right: 0;
    }}

    .mobile-vv {{
        position: static;
        display: block;
        margin: 10px auto;
    }}

    /* Value View section */
    #valueViewSection {{
        display: none;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        padding: 30px;
        max-width: 1400px;
        margin: 20px auto;
        overflow-x: auto;
    }}

    .value-filter {{
        display: flex;
        gap: 10px;
        justify-content: center;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }}

    .vf-btn {{
        padding: 8px 20px;
        border-radius: 50px;
        border: 2px solid #ccc;
        background: white;
        cursor: pointer;
        font-size: 14px;
        font-weight: 600;
        transition: all 0.3s;
    }}

    .vf-btn.active, .vf-btn:hover {{
        background: linear-gradient(135deg, #7c3aed, #5b21b6) !important;
        color: white !important;
        border-color: transparent !important;
    }}

    .sortable {{
        cursor: pointer;
        user-select: none;
    }}

    .sortable:hover {{
        opacity: 0.85;
    }}

    /* Chart container styling */
    #chart-container {{
        background: white;
        border-radius: 20px;
        padding: 10px;
        margin: 10px auto;
        max-width: 95%;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    }}

    ch {{
        text-decoration: underline;
        -webkit-text-decoration-color: red;
        text-decoration-color: red;
        font-size: 24px;
        font-weight: bold;
    }}

    @media screen and (max-width: 600px) {{
        .column {{
            flex: 1;
            padding: 3px;
            min-width: 0;
        }}

        .row {{
            flex-direction: row;
            gap: 3px;
            margin-top: 15px;
        }}

        .table-container {{
            display: none;
        }}

        .table-container2 {{
            display: block;
        }}

        .table-container2 table {{
            font-size: 12px;
        }}

        .table-container2 th,
        .table-container2 td {{
            padding: 8px 4px;
        }}

        .table-container2 th {{
            font-size: 11px;
        }}

        h1 {{
            font-size: 28px;
            margin: 10px 0;
            letter-spacing: 1px;
        }}

        .card {{
            padding: 10px;
            border-radius: 12px;
        }}

        .card-body h2 {{
            font-size: 20px;
            margin: 8px 0;
            font-weight: 700;
        }}

        .card-header {{
            margin-bottom: 10px;
        }}

        .card-header img {{
            height: 90px;
            width: auto;
        }}

        hr {{
            margin: 8px 0;
            height: 2px;
        }}

        body {{
            padding: 8px;
        }}

        .progress-bar {{
            height: 32px;
            line-height: 32px;
            font-size: 13px;
        }}

        .progress-container {{
            margin-bottom: 15px;
        }}

        tr:hover td {{
            background-color: transparent;
        }}

        .daily-overview-title {{
            font-size: 20px;
            margin: 10px auto;
        }}

        .standings-table {{
            font-size: 14px;
        }}

        .standings-table th {{
            font-size: 12px;
            padding: 10px 5px;
        }}

        .standings-table td {{
            font-size: 14px;
            padding: 8px 4px;
        }}

        .desktop-vv {{
            display: none;
        }}

        .mobile-vv {{
            position: static;
        }}

        #valueViewSection {{
            padding: 15px;
        }}
    }}

    @media screen and (min-width: 601px) {{
        .table-container2 {{
            display: none;
        }}

        .mobile-vv {{
            display: none;
        }}

        #chart-container {{
            display: none;
        }}
    }}

    </style>
</head>
<body>

    <div class="progress-container">
        <div class="progress-bar" id="progressBar">0/0</div>
    </div>

    <script>
        let x = {chaseWins + bryceWins + zachWins}
        let y = {1230}
        let percentage = ((x / y) * 100).toFixed(1);

        let progressBar = document.getElementById("progressBar");
        progressBar.style.width = percentage + "%";
        progressBar.innerText = percentage + "%";
    </script>

<div class="title-row">
    <h1>NBA Extravaganza</h1>
    <button class="toggle-btn desktop-vv" onclick="toggleValueView()">Value View</button>
</div>

<div id="chart-container">
    <canvas id="myLineChart"></canvas>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    console.log('Creating chart...');
    var ctx = document.getElementById('myLineChart').getContext('2d');

    const myLineChart = new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: {df['Day'].to_list()},
            datasets: [{{
                label: 'Chase',
                data: {df['Chase'].to_list()},
                fill: false,
                borderColor: '#2774AE',
                tension: 0.1,
                pointRadius: 0
            }},
            {{
                label: 'Bryce',
                data: {df['Bryce'].to_list()},
                fill: false,
                borderColor: '#57068c',
                tension: 0.1,
                pointRadius: 0
            }},
            {{
                label: 'Zach',
                data: {df['Zach'].to_list()},
                fill: false,
                borderColor: '#e21833',
                tension: 0.1,
                pointRadius: 0
            }}]
        }},
        options: {{
            responsive: false,
            scales: {{
                y: {{
                    beginAtZero: true,
                    grid: {{
                        display: false
                    }},
                    title: {{
                        display: false,
                    }}
                }},
                x: {{
                    grid: {{
                        display: false
                    }}
                }}
            }},
            plugins: {{
                legend: {{
                    display: false,
                    position: 'left',
                    fullSize: false,
                }},
                title: {{
                    display: true,
                    text: 'Wins Margin',
                    font: {{
                        size: 15
                    }},
                    align: 'start',
                    color: 'black'
                }},
            }}
        }}
    }});
</script>

<button class="toggle-btn mobile-vv" onclick="toggleValueView()">Value View</button>

<div id="cardsRow" class="row">
    <div class="column">
        <div class="card">
            <div class="card-header">
                {img_to_html('photos/ChaseHead.png')}
                <hr style="background: #2774AE; background-image: none; height: 3px; border: none; margin: 15px 0;"/>
            </div>
            <div class="card-body">
                <h2>Chase's Wins: <br>{chaseWins}</h2>
                <div class="table-container">
                    {chasesStandings.to_html(index=False)}
                </div>
                <div class="table-container2">
                    {chaseStandingsMobile.to_html(index=False)}
                </div>
            </div>
        </div>
    </div>

    <div class="column">
        <div class="card">
            <div class="card-header">
                {img_to_html('photos/BryceHead.png')}
                <hr style="background: #57068c; background-image: none; height: 3px; border: none; margin: 15px 0;"/>
            </div>
            <div class="card-body">
                <h2>Bryce's Wins: <br>{bryceWins}</h2>
                <div class="table-container">
                    {brycesStandings.to_html(index=False)}
                </div>
                <div class="table-container2">
                    {bryceStandingsMobile.to_html(index=False)}
                </div>
            </div>
        </div>
    </div>

    <div class="column">
        <div class="card">
            <div class="card-header">
                {img_to_html('photos/ZachHead.png')}
                <hr style="background: #e21833; background-image: none; height: 3px; border: none; margin: 15px 0;"/>
            </div>
            <div class="card-body">
                <h2>Zach's Wins: <br>{zachWins}</h2>
                <div class="table-container">
                    {zachsStandings.to_html(index=False)}
                </div>
                <div class="table-container2">
                    {zachStandingsMobile.to_html(index=False)}
                </div>
            </div>
        </div>
    </div>
</div>

<div id="valueViewSection">
    <div class="value-filter">
        <button class="vf-btn active" onclick="filterOwner(this, 'all')">All</button>
        <button class="vf-btn" style="border-color:#2774AE;color:#2774AE;" onclick="filterOwner(this, 'Chase')">Chase</button>
        <button class="vf-btn" style="border-color:#57068c;color:#57068c;" onclick="filterOwner(this, 'Bryce')">Bryce</button>
        <button class="vf-btn" style="border-color:#e21833;color:#e21833;" onclick="filterOwner(this, 'Zach')">Zach</button>
    </div>
    {combined_value_html}
</div>

</body>
</html>
"""

html_content += dpt

with open('index.html', 'w') as f:
    f.write(html_content)

print("HTML file generated: index.html")
