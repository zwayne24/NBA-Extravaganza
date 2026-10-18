"""
HTML Creator Script with Daily Guessing Game Feature
"""

# === Original Imports ===
import pandas as pd
from datetime import date
import datetime

# === Original HTML Creation Logic ===
import requests
import pandas as pd
import base64
from pathlib import Path
from datetime import date

# Function to convert image to base64
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
    
    # Create abbreviation → owner map
    owner_map = {}
    for team in ChasesTeams:
        owner_map[teamToAbbr[team]] = "Chase"
    for team in BrycesTeams:
        owner_map[teamToAbbr[team]] = "Bryce"
    for team in ZachsTeams:
        owner_map[teamToAbbr[team]] = "Zach"

    owners = ["Chase", "Bryce", "Zach"]
    results = {owner: {"teams_playing": 0, "max_wins": 0, "min_wins": 0, "favored": 0} for owner in owners}

    # Iterate through all games today
    for _, row in matchups_df.iterrows():
        home = row["home_team"].strip().upper()
        away = row["away_team"].strip().upper()
        odds = str(row["odds"]).strip().upper()

        owner_home = owner_map.get(home)
        owner_away = owner_map.get(away)

        # Skip if neither team belongs to any owner
        if not owner_home and not owner_away:
            continue

        # Count teams playing
        if owner_home:
            results[owner_home]["teams_playing"] += 1
        if owner_away:
            results[owner_away]["teams_playing"] += 1

        # --- Max/Min logic ---
        if owner_home and owner_away:
            if owner_home == owner_away:
                # Two of the same owner's teams are playing each other
                results[owner_home]["max_wins"] += 1
                results[owner_home]["min_wins"] += 1
            else:
                # Different owners face each other
                results[owner_home]["max_wins"] += 1
                results[owner_away]["max_wins"] += 1
                # Neither guaranteed a win, so min stays 0
        else:
            # Only one owner has a team in this matchup
            owned = owner_home or owner_away
            results[owned]["max_wins"] += 1
            # Could lose, so min stays 0

        # --- Favored logic ---
        if "-" in odds:
            favored_team = odds.split(" ")[0].strip()
            favored_owner = owner_map.get(favored_team)
            if favored_owner:
                results[favored_owner]["favored"] += 1

    # --- Build HTML output ---
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

ESPN_API = 'https://site.api.espn.com/apis'
ESPN_HEADERS = {'User-Agent': 'Mozilla/5.0'}

def scrape_nba_standings():
    """
    Fetch regular-season NBA standings from ESPN's JSON API
    Returns a DataFrame with team name, wins, losses, and winning percentage
    """
    response = requests.get(f'{ESPN_API}/v2/sports/basketball/nba/standings?seasontype=2', headers=ESPN_HEADERS)
    response.raise_for_status()

    all_teams = []
    for conference in response.json()['children']:
        for entry in conference['standings']['entries']:
            stats = {stat['name']: stat.get('value', 0) for stat in entry['stats']}
            all_teams.append({
                'Team': entry['team']['displayName'],
                'W': stats.get('wins', 0),
                'L': stats.get('losses', 0),
                'PCT': stats.get('winPercent', 0),
                'Streak': stats.get('streak', 0),  # +N = won N straight, -N = lost N straight
            })
    return pd.DataFrame(all_teams)

def fetch_nba_scoreboard(day):
    """Fetch the list of NBA games on a given date from ESPN's JSON API"""
    response = requests.get(f'{ESPN_API}/site/v2/sports/basketball/nba/scoreboard?dates={day.strftime("%Y%m%d")}', headers=ESPN_HEADERS)
    response.raise_for_status()
    return response.json().get('events', [])

standings = scrape_nba_standings()

ChasesTeams = ['Oklahoma City Thunder','Boston Celtics','Denver Nuggets','Toronto Raptors','Indiana Pacers','Golden State Warriors','Orlando Magic','Memphis Grizzlies','LA Clippers','Sacramento Kings']
ZachsTeams = ['San Antonio Spurs','Philadelphia 76ers','Houston Rockets','Minnesota Timberwolves','Atlanta Hawks','Portland Trail Blazers','Charlotte Hornets','Dallas Mavericks','New Orleans Pelicans','Milwaukee Bucks']
BrycesTeams = ['New York Knicks','Cleveland Cavaliers','Los Angeles Lakers','Miami Heat','Detroit Pistons','Phoenix Suns','Washington Wizards','Utah Jazz','Chicago Bulls','Brooklyn Nets']

# Snake draft order: Chase 1st, Zach 2nd, Bryce 3rd. Team arrays are in pick order.
# R1: Chase(1), Zach(2), Bryce(3) | R2: Bryce(4), Zach(5), Chase(6) | R3: Chase(7), ...
_chase_ovr = [1,  6,  7, 12, 13, 18, 19, 24, 25, 30]
_zach_ovr  = [2,  5,  8, 11, 14, 17, 20, 23, 26, 29]
_bryce_ovr = [3,  4,  9, 10, 15, 16, 21, 22, 27, 28]
draft_info = {}
for i, team in enumerate(ChasesTeams):
    ovr = _chase_ovr[i]; draft_info[team] = {'rd': (ovr - 1) // 3 + 1, 'ovr': ovr}
for i, team in enumerate(ZachsTeams):
    ovr = _zach_ovr[i];  draft_info[team] = {'rd': (ovr - 1) // 3 + 1, 'ovr': ovr}
for i, team in enumerate(BrycesTeams):
    ovr = _bryce_ovr[i]; draft_info[team] = {'rd': (ovr - 1) // 3 + 1, 'ovr': ovr}

# Process standings data
standings['W'] = standings['W'].astype(int)
standings['L'] = standings['L'].astype(int)
standings['PCT'] = standings['PCT'].astype(float)
standings['Streak'] = standings['Streak'].astype(int)

standings_sorted = standings.sort_values(by=['PCT', 'Team'], ascending=[False, True]).reset_index(drop=True)
overall_live_rank = {row['Team']: rnk + 1 for rnk, row in standings_sorted.iterrows()}

# Season badges, unlocked once 10% of the season (123 of 1230 games) has been played
#   👑 best record   🗑️ worst record   💎 / 📈 10+ / 5-9 spots better than draft slot   💀 / 📉 10+ / 5-9 spots worse
TOTAL_GAMES = 1230
games_played = standings['W'].sum()
def season_badges(row):
    if games_played < 0.10 * TOTAL_GAMES:
        return ''
    badges = ''
    if row['PCT'] == standings['PCT'].max():
        badges += ' 👑'
    if row['PCT'] == standings['PCT'].min():
        badges += ' 🗑️'
    delta = overall_live_rank[row['Team']] - draft_info[row['Team']]['ovr']
    if delta <= -10:
        badges += ' 💎'
    elif delta <= -5:
        badges += ' 📈'
    elif delta >= 10:
        badges += ' 💀'
    elif delta >= 5:
        badges += ' 📉'
    return badges
standings['Badges'] = standings.apply(season_badges, axis=1)

standings = standings.sort_values(by='W', ascending=False).drop(columns=['PCT'])

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

# Rename Oklahoma City Thunder to OKC Thunder for display
chasesStandings['Team'] = chasesStandings['Team'].replace('Oklahoma City Thunder', 'OKC Thunder')
brycesStandings['Team'] = brycesStandings['Team'].replace('Oklahoma City Thunder', 'OKC Thunder')
zachsStandings['Team'] = zachsStandings['Team'].replace('Oklahoma City Thunder', 'OKC Thunder')

chaseStandingsMobile = chasesStandings.copy()
bryceStandingsMobile = brycesStandings.copy()
zachStandingsMobile = zachsStandings.copy()

# Map using original team names for mobile
chaseStandingsMobile['Team'] = chaseStandingsMobile['Team'].replace('OKC Thunder', 'Oklahoma City Thunder').map(teamToAbbr)
bryceStandingsMobile['Team'] = bryceStandingsMobile['Team'].replace('OKC Thunder', 'Oklahoma City Thunder').map(teamToAbbr)
zachStandingsMobile['Team'] = zachStandingsMobile['Team'].replace('OKC Thunder', 'Oklahoma City Thunder').map(teamToAbbr)

# Fire / ice emoji for teams on a 5+ game win / losing streak, plus season badges
def add_streak_emoji(df):
    def emojis(streak, badges):
        e = (' 🔥' if streak >= 5 else ' 🧊' if streak <= -5 else '') + badges
        return f' <span class="badges">{e.strip()}</span>' if e else ''
    df['Team'] = [team + emojis(streak, badges) for team, streak, badges in zip(df['Team'], df['Streak'], df['Badges'])]
    return df.drop(columns=['Streak', 'Badges'])

chasesStandings = add_streak_emoji(chasesStandings)
brycesStandings = add_streak_emoji(brycesStandings)
zachsStandings = add_streak_emoji(zachsStandings)
chaseStandingsMobile = add_streak_emoji(chaseStandingsMobile)
bryceStandingsMobile = add_streak_emoji(bryceStandingsMobile)
zachStandingsMobile = add_streak_emoji(zachStandingsMobile)

chaseStandingsMobile = chaseStandingsMobile[['Team', 'W']]
bryceStandingsMobile = bryceStandingsMobile[['Team', 'W']]
zachStandingsMobile = zachStandingsMobile[['Team', 'W']]

def build_combined_value_view_html(draft_info, overall_live_rank, teamToAbbr, ChasesTeams, BrycesTeams, ZachsTeams):
    owner_colors = {'Chase': '#2774AE', 'Bryce': '#57068c', 'Zach': '#e21833'}
    owner_map = {}
    for team in ChasesTeams: owner_map[team] = 'Chase'
    for team in BrycesTeams: owner_map[team] = 'Bryce'
    for team in ZachsTeams: owner_map[team] = 'Zach'

    rows = []
    for team in list(ChasesTeams) + list(BrycesTeams) + list(ZachsTeams):
        abbr = teamToAbbr.get(team, team)
        owner = owner_map.get(team, '')
        color = owner_colors.get(owner, '#999')
        d = draft_info.get(team, {})
        draft_ovr = d.get('ovr', 0)
        live_ovr = overall_live_rank.get(team, 0)
        delta = (live_ovr - draft_ovr) if (draft_ovr and live_ovr) else 0
        rows.append((abbr, owner, color, draft_ovr, live_ovr, delta))

    rows.sort(key=lambda x: x[4])  # default sort: current rank

    html = '<table class="standings-table" id="valueTable"><thead><tr>'
    html += '<th>TEAM</th>'
    html += '<th class="sortable" onclick="sortValueTable(1)">DRAFT &#8597;</th>'
    html += '<th class="sortable" onclick="sortValueTable(2)">CURR &#8597;</th>'
    html += '<th class="sortable" onclick="sortValueTable(3)">&#916; &#8597;</th>'
    html += '</tr></thead><tbody>'

    for abbr, owner, color, draft_ovr, live_ovr, delta in rows:
        if delta < 0:
            delta_html = f"<span style='color:#22c55e;font-weight:bold;'>&#9650;&nbsp;{abs(delta)}</span>"
        elif delta > 0:
            delta_html = f"<span style='color:#ef4444;font-weight:bold;'>&#9660;&nbsp;{delta}</span>"
        else:
            delta_html = "&#8212;"
        html += f'<tr data-owner="{owner}">'
        html += f'<td style="border-left:4px solid {color};font-weight:600;padding-left:12px;">{abbr}</td>'
        html += f'<td data-val="{draft_ovr}">{draft_ovr}</td>'
        html += f'<td data-val="{live_ovr}">{live_ovr}</td>'
        html += f'<td data-val="{delta}">{delta_html}</td>'
        html += '</tr>'

    html += '</tbody></table>'
    return html

combined_value_html = build_combined_value_view_html(draft_info, overall_live_rank, teamToAbbr, ChasesTeams, BrycesTeams, ZachsTeams)

# Calculate total wins and losses
chaseWins = chasesStandings['W'].sum()
bryceWins = brycesStandings['W'].sum()
zachWins = zachsStandings['W'].sum()

df = pd.read_excel('Wins_Over_Time.xlsx')
# Normalize the Day column to just dates (no time component)
df['Day'] = pd.to_datetime(df['Day']).dt.normalize()
# Get today's date as a normalized datetime
today = pd.Timestamp(date.today()-datetime.timedelta(days=1)).normalize()
existing_row = df[df['Day'] == today]

if not existing_row.empty:
    # Update the existing row for today's date
    df.loc[df['Day'] == today, ['Chase', 'Bryce', 'Zach']] = [chaseWins, bryceWins, zachWins]
else:
    # Add new row with today's data and wins
    todaysData = pd.DataFrame({'Day': [today], 'Chase': [chaseWins], 'Bryce': [bryceWins], 'Zach': [zachWins]})
    df = pd.concat([df, todaysData], ignore_index=True)

# save to excel
df.to_excel('Wins_Over_Time.xlsx', index=False)
df.iloc[:, 1:] = df.iloc[:, 1:].sub(df.iloc[:, 1:].min(axis=1), axis=0)
# format dat as Oct-22
df['Day'] = pd.to_datetime(df['Day']).dt.strftime('%b-%d')

# Fetch today's and yesterday's games from ESPN's JSON API
matchups = []
yesterday = []

for event in fetch_nba_scoreboard(date.today()):
    competition = event['competitions'][0]
    teams = {c['homeAway']: c for c in competition['competitors']}
    odds = (competition.get('odds') or [{}])[0].get('details')
    # e.g. "10/21 - 7:00 PM EDT" -> "7:00 PM EDT"
    time = event['status']['type'].get('shortDetail', '').split(' - ')[-1]
    matchups.append({
        'away_team': teams['away']['team']['abbreviation'].lower(),
        'home_team': teams['home']['team']['abbreviation'].lower(),
        'time': time,
        'odds': odds,
    })

for event in fetch_nba_scoreboard(date.today() - datetime.timedelta(days=1)):
    if not event['status']['type'].get('completed'):
        continue  # postponed / not played
    competition = event['competitions'][0]
    teams = {c['homeAway']: c for c in competition['competitors']}
    ranked = sorted(competition['competitors'], key=lambda c: int(c.get('score', 0)), reverse=True)
    result = ', '.join(f"{c['team']['abbreviation']} {c['score']}" for c in ranked)
    yesterday.append({
        'away_team': teams['away']['team']['abbreviation'].lower(),
        'home_team': teams['home']['team']['abbreviation'].lower(),
        'result': result,
        'winner': ranked[0]['team']['abbreviation'],
    })

# Create a DataFrame from the matchups list
matchups_df = pd.DataFrame(matchups)
html_table = "<table><thead><tr><th>Home Team</th><th>Away Team</th><th>Time</th><th>Odds</th></tr></thead><tbody>"
for i, row in matchups_df.iterrows():
    # if row['Home Team'] = ChasesTeams first row
    for team in ChasesTeams:
        team = teamToAbbr[team]
        if row['home_team'] == team.lower():
            html_table += f"<td style='color:#2774AE'>{team}</td>"
    for team in BrycesTeams:
        team = teamToAbbr[team]
        if row['home_team'] == team.lower():
            html_table += f"<td style='color:#57068c'>{team}</td>"
    for team in ZachsTeams:
        team = teamToAbbr[team]
        if row['home_team'] == team.lower():
            html_table += f"<td style='color:#e21833'>{team}</td>"
    for team in ChasesTeams:
        team = teamToAbbr[team]
        if row['away_team'] == team.lower():
            html_table += f"<td style='color:#2774AE'>{team}</td>"
    for team in BrycesTeams:
        team = teamToAbbr[team]
        if row['away_team'] == team.lower():
            html_table += f"<td style='color:#57068c'>{team}</td>"
    for team in ZachsTeams:
        team = teamToAbbr[team]
        if row['away_team'] == team.lower():
            html_table += f"<td style='color:#e21833'>{team}</td>"
    html_table += f"<td>{row['time']}</td><td>{row['odds']}</td></tr>"
html_table += "</tbody></table>"

# Create a DataFrame from the matchups list
yesterday_df = pd.DataFrame(yesterday)
html_table_yesterday = "<table><thead><tr><th>Home Team</th><th>Away Team</th><th>Result</th></tr></thead><tbody>"
for i, row in yesterday_df.iterrows():
    winner = row['winner']  
    for team in ChasesTeams:
        team = teamToAbbr[team]
        if row['home_team'] == team.lower():
            if winner.lower() == row['home_team']:
                # make background #2774AE and font white
                html_table_yesterday += f"<td style='background-color:#2774AE;color:white;'> <strong>{team}</strong></td>"
            else:
                html_table_yesterday += f"<td style='color:#2774AE'>{team}</td>"
    for team in BrycesTeams:
        team = teamToAbbr[team]
        if row['home_team'] == team.lower():
            if winner.lower() == row['home_team']:
                # make background #57068c and font white
                html_table_yesterday += f"<td style='background-color:#57068c;color:white;'> <strong>{team}</strong></td>"
            else:
                html_table_yesterday += f"<td style='color:#57068c'>{team}</td>"
    for team in ZachsTeams:
        team = teamToAbbr[team]
        if row['home_team'] == team.lower():
            if winner.lower() == row['home_team']:
                # make background #e21833 and font white
                html_table_yesterday += f"<td style='background-color:#e21833;color:white;'> <strong>{team}</strong></td>"
            else:
                html_table_yesterday += f"<td style='color:#e21833'>{team}</td>"
    for team in ChasesTeams:
        team = teamToAbbr[team]
        if row['away_team'] == team.lower():
            if winner.lower() == row['away_team']:
                # make background #2774AE and font white
                html_table_yesterday += f"<td style='background-color:#2774AE;color:white;'> <strong>{team}</strong></td>"
            else:
                html_table_yesterday += f"<td style='color:#2774AE'>{team}</td>"
    for team in BrycesTeams:
        team = teamToAbbr[team]
        if row['away_team'] == team.lower():
            if winner.lower() == row['away_team']:
                # make background #57068c and font white
                html_table_yesterday += f"<td style='background-color:#57068c;color:white;'> <strong>{team}</strong></td>"
            else:
                html_table_yesterday += f"<td style='color:#57068c'>{team}</td>"
    for team in ZachsTeams:
        team = teamToAbbr[team]
        if row['away_team'] == team.lower():
            if winner.lower() == row['away_team']:
                # make background #e21833 and font white
                html_table_yesterday += f"<td style='background-color:#e21833;color:white;'> <strong>{team}</strong></td>"
            else:
                html_table_yesterday += f"<td style='color:#e21833'>{team}</td>"         
    html_table_yesterday += f"<td>{row['result']}</td></tr>"
html_table_yesterday += "</tbody></table>"

dpt = daily_projection_html = generate_daily_projection_table(matchups_df, ChasesTeams, BrycesTeams, ZachsTeams, teamToAbbr)

# Generate HTML content
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Standings</title>
    <script >
        function openCity(evt, cityName) {{
        // Declare all variables
        var i, tabcontent, tablinks;

        // Get all elements with class="tabcontent" and hide them
        tabcontent = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontent.length; i++) {{
            tabcontent[i].style.display = "none";
        }}

        // Get all elements with class="tablinks" and remove the class "active"
        tablinks = document.getElementsByClassName("tablinks");
        for (i = 0; i < tablinks.length; i++) {{
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }}

        // Show the current tab, and add an "active" class to the button that opened the tab
        document.getElementById(cityName).style.display = "block";
        evt.currentTarget.className += " active";
    }}

    var _valueViewActive = false;
    function toggleValueView() {{
        _valueViewActive = !_valueViewActive;
        document.querySelectorAll('.toggle-btn').forEach(function(b) {{
            b.classList.toggle('active', _valueViewActive);
        }});
        document.getElementById('cardsRow').style.display = _valueViewActive ? 'none' : '';
        document.getElementById('valueViewSection').style.display = _valueViewActive ? 'block' : 'none';
    }}

    var _sortCol = 2;
    var _sortAsc = true;

    function sortValueTable(col) {{
        if (_sortCol === col) {{
            _sortAsc = !_sortAsc;
        }} else {{
            _sortCol = col;
            _sortAsc = true;
        }}
        var tbody = document.querySelector('#valueTable tbody');
        var rows = Array.from(tbody.querySelectorAll('tr'));
        rows.sort(function(a, b) {{
            var aVal = parseFloat(a.cells[col].dataset.val);
            var bVal = parseFloat(b.cells[col].dataset.val);
            return _sortAsc ? aVal - bVal : bVal - aVal;
        }});
        rows.forEach(function(r) {{ tbody.appendChild(r); }});
    }}

    function filterOwner(btn, owner) {{
        document.querySelectorAll('.vf-btn').forEach(function(b) {{ b.classList.remove('active'); }});
        btn.classList.add('active');
        document.querySelectorAll('#valueTable tbody tr').forEach(function(r) {{
            r.style.display = (owner === 'all' || r.dataset.owner === owner) ? '' : 'none';
        }});
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

    /* Streak/season emojis are hidden when any of them would wrap (see fitBadges) */
    .hide-badges .badges {{
        display: none;
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

    .tab {{
        overflow: hidden;
        background: white;
        text-align: center;
        max-width: 1400px;
        margin: 30px auto;
        border-radius: 50px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        padding: 5px;
    }}

    .tab button {{
        background-color: transparent;
        border: none;
        outline: none;
        cursor: pointer;
        padding: 14px 30px;
        transition: all 0.3s;
        font-size: 16px;
        font-weight: 600;
        color: #666;
        border-radius: 50px;
        margin: 0 5px;
    }}

    .tab button:hover {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }}

    .tab button.active {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        box-shadow: 0 3px 10px rgba(16, 185, 129, 0.4);
    }}

    .tabcontent {{
        display: none;
        padding: 30px;
        background: white;
        border-radius: 20px;
        max-width: 1400px;
        margin: 20px auto;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    }}

    .tabcontent h2 {{
        color: #333;
        margin-bottom: 20px;
        font-weight: 700;
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

        .tab button {{
            padding: 10px 15px;
            font-size: 13px;
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

        .tabcontent {{
            padding: 15px;
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
    }}

    @media screen and (min-width: 601px) {{
        .table-container2 {{
            display: none;
        }}
    }}

    ch {{
        text-decoration: underline;
        -webkit-text-decoration-color: red;
        text-decoration-color: red;
        font-size: 24px;
        font-weight: bold;
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

    @media screen and (min-width: 601px) {{
        #chart-container {{
            display: none;
        }}
    }}

    .title-row {{
        display: flex;
        align-items: center;
        justify-content: center;
        max-width: 1400px;
        margin: 20px auto;
        position: relative;
    }}

    .title-row h1 {{
        margin: 0;
    }}

    .toggle-btn {{
        position: absolute;
        right: 0;
        background: rgba(255,255,255,0.2);
        border: 2px solid rgba(255,255,255,0.6);
        color: white;
        padding: 8px 18px;
        border-radius: 50px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        backdrop-filter: blur(5px);
        white-space: nowrap;
    }}

    .toggle-btn:hover {{
        background: rgba(255,255,255,0.35);
    }}

    .toggle-btn.active {{
        background: white;
        color: #059669;
        border-color: white;
    }}

    #valueViewSection {{
        display: none;
        max-width: 600px;
        margin: 20px auto;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        padding: 20px;
    }}

    .value-filter {{
        display: flex;
        justify-content: center;
        gap: 8px;
        margin-bottom: 16px;
        flex-wrap: wrap;
    }}

    .vf-btn {{
        background: transparent;
        border: 2px solid #ddd;
        padding: 6px 18px;
        border-radius: 50px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        color: #666;
    }}

    .vf-btn.active, .vf-btn:hover {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border-color: transparent !important;
    }}

    .sortable {{
        cursor: pointer;
    }}

    .sortable:hover {{
        opacity: 0.8;
    }}

    @media screen and (max-width: 600px) {{
        #valueViewSection {{
            max-width: 100%;
            padding: 12px;
            border-radius: 12px;
        }}
    }}

    .desktop-vv {{ display: inline-block; }}
    .mobile-vv  {{ display: none; }}

    @media screen and (max-width: 600px) {{
        .toggle-btn {{
            padding: 6px 10px;
            font-size: 11px;
        }}
        .desktop-vv {{ display: none; }}
        .mobile-vv  {{
            display: block;
            position: static;
            width: fit-content;
            margin: 14px auto;
        }}
    }}

</style>

</head>
<body>

    <div class="progress-container">
        <div class="progress-bar" id="progressBar">0/0</div>
    </div>

    <script>
        let x = {chaseWins+ bryceWins + zachWins}
        let y = {TOTAL_GAMES}
        let percentage = ((x / y) * 100).toFixed(1);

        let progressBar = document.getElementById("progressBar");
        progressBar.style.width = percentage + "%";
        progressBar.innerText = percentage+ "%";
    </script>

<div class="title-row">
    <h1>NBA Extravaganza</h1>
    <button id="valueViewBtn" class="toggle-btn desktop-vv" onclick="toggleValueView()">Value View</button>
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
                        display: false // Hide y-axis gridlines
                    }},
                    title: {{
                        display: false, // Show y-axis title
                    }}                
                }},
                x: {{
                    grid: {{
                        display: false // Hide x-axis gridlines
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
<button id="valueViewBtnM" class="toggle-btn mobile-vv" onclick="toggleValueView()">Value View</button>

<div class="row" id="cardsRow">
    <div class="column">
        <div class="card">
            <div class="card-header">
                {img_to_html('photos/ChaseHead.png')}
                <hr style="background: #2774AE; background-image: none; height: 3px; border: none; margin: 15px 0;"/>
            </div>
            <div class="card-body">
                <h2>Chase's Wins: <br>{chaseWins}</h2>
                <div class="table-container">
                    {chasesStandings.to_html(index=False, escape=False)}
                </div>
                <div class="table-container2">
                    {chaseStandingsMobile.to_html(index=False, escape=False)}
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
                    {brycesStandings.to_html(index=False, escape=False)}
                </div>
                <div class="table-container2">
                    {bryceStandingsMobile.to_html(index=False, escape=False)}
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
                <div class="table-container" >
                    {zachsStandings.to_html(index=False, escape=False)}
                </div>
                <div class="table-container2">
                    {zachStandingsMobile.to_html(index=False, escape=False)}
                </div>
            </div>
        </div>
    </div>
</div>

<div id="valueViewSection">
    <div class="value-filter">
        <button class="vf-btn active" data-owner="all" onclick="filterOwner(this, 'all')">All</button>
        <button class="vf-btn" data-owner="Chase" onclick="filterOwner(this, 'Chase')" style="border-color:#2774AE;color:#2774AE;">Chase</button>
        <button class="vf-btn" data-owner="Bryce" onclick="filterOwner(this, 'Bryce')" style="border-color:#57068c;color:#57068c;">Bryce</button>
        <button class="vf-btn" data-owner="Zach" onclick="filterOwner(this, 'Zach')" style="border-color:#e21833;color:#e21833;">Zach</button>
    </div>
    {combined_value_html}
</div>

<div class="tab">
  <button class="tablinks" onclick="openCity(event, 'TG')">Today's Games</button>
  <button class="tablinks" onclick="openCity(event, 'YG')">Yesterday's Games</button>
</div>


<div id="TG" class="tabcontent">
    <h2 style="text-align: center;">Today's Games</h2>
    {html_table}
</div>

<div id="YG" class="tabcontent">
  <h2 style="text-align: center;">Yesterday's Games</h2>
  {html_table_yesterday}
</div>

<script>
    // Show streak/season emojis only if every one fits on the same line as its team name
    function fitBadges() {{
        document.body.classList.remove('hide-badges');
        var wraps = Array.from(document.querySelectorAll('.badges')).some(function(badge) {{
            if (!badge.offsetParent) return false;  // in a hidden (desktop/mobile) table
            var range = document.createRange();
            range.selectNodeContents(badge.parentNode.firstChild);
            var team = range.getBoundingClientRect();
            return badge.getClientRects().length > 1 || badge.getBoundingClientRect().top >= team.bottom - 1;
        }});
        document.body.classList.toggle('hide-badges', wraps);
    }}
    window.addEventListener('load', fitBadges);
    window.addEventListener('resize', fitBadges);
</script>
</body>
</html>


"""

html_content += dpt

# Write HTML content to a file
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("HTML file generated: index.html")