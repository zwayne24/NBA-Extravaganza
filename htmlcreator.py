"""
HTML Creator Script with Daily Guessing Game Feature
"""

# === Original Imports ===
import pandas as pd
from datetime import date
import datetime

# === Original HTML Creation Logic ===
import requests
from bs4 import BeautifulSoup
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
    <h3>Daily Overview</h3>
    <table class="standings-table">
      <tr><th></th><th>Teams Playing</th><th>Max Wins</th><th>Min Wins</th><th>Favored</th></tr>
    """
    for owner in owners:
        color = owner_colors[owner]
        r = results[owner]
        html += f"<td style='color:{color}; font-weight:bold;'>{owner}</td><td>{r['teams_playing']}</td><td>{r['max_wins']}</td><td>{r['min_wins']}</td><td>{r['favored']}</td></tr>"
    html += "</table>"
    return html

def scrape_nba_standings(url="https://www.espn.com/nba/standings"):
    """
    Scrape NBA standings from ESPN
    Returns a DataFrame with team name, wins, losses, and winning percentage
    """
    # Send GET request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # Parse HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    all_teams = []
    
    # Find all ResponsiveTable divs (one for Eastern Conference, one for Western Conference)
    responsive_tables = soup.find_all('div', class_='ResponsiveTable')
    
    for responsive_table in responsive_tables:
        # Find the fixed-left table (contains team names)
        team_table = responsive_table.find('table', class_='Table--fixed-left')
        # Find the scrollable table (contains stats)
        stats_table = responsive_table.find('div', class_='Table__Scroller')
        
        if not team_table or not stats_table:
            continue
            
        stats_table = stats_table.find('table')
        
        # Get team rows
        team_rows = team_table.find('tbody').find_all('tr')
        # Get stat rows
        stat_rows = stats_table.find('tbody').find_all('tr')
        
        # Match team rows with stat rows (they should be in the same order)
        for team_row, stat_row in zip(team_rows, stat_rows):
            try:
                # Extract team name from the team table
                team_link = team_row.find('span', class_='hide-mobile')
                if team_link:
                    team_name = team_link.get_text(strip=True)
                else:
                    # Try mobile version
                    team_abbr = team_row.find('abbr')
                    if team_abbr:
                        team_name = team_abbr.get_text(strip=True)
                    else:
                        continue
                
                # Extract stats from the stats table
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
    
    # Create DataFrame
    df = pd.DataFrame(all_teams)
    return df

standings = scrape_nba_standings()

ChasesTeams = ['Denver Nuggets','New York Knicks','Golden State Warriors','LA Clippers','Dallas Mavericks','Boston Celtics','Miami Heat','Sacramento Kings','Phoenix Suns','Brooklyn Nets']
BrycesTeams = ['Oklahoma City Thunder','Orlando Magic','Minnesota Timberwolves','Atlanta Hawks','San Antonio Spurs','Memphis Grizzlies','Indiana Pacers','Chicago Bulls','Portland Trail Blazers','Utah Jazz']
ZachsTeams = ['Cleveland Cavaliers','Houston Rockets','Los Angeles Lakers','Detroit Pistons','Milwaukee Bucks','Philadelphia 76ers','Toronto Raptors','New Orleans Pelicans','Charlotte Hornets','Washington Wizards']

# Process standings data
standings['W'] = standings['W'].astype(int)
standings['L'] = standings['L'].astype(int)
standings['PCT'] = standings['PCT'].astype(float)
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

chaseStandingsMobile = chasesStandings.copy()
bryceStandingsMobile = brycesStandings.copy()
zachStandingsMobile = zachsStandings.copy()

chaseStandingsMobile['Team'] = chaseStandingsMobile['Team'].map(teamToAbbr)
bryceStandingsMobile['Team'] = bryceStandingsMobile['Team'].map(teamToAbbr)
zachStandingsMobile['Team'] = zachStandingsMobile['Team'].map(teamToAbbr)

chaseStandingsMobile = chaseStandingsMobile[['Team', 'W']]
bryceStandingsMobile = bryceStandingsMobile[['Team', 'W']]
zachStandingsMobile = zachStandingsMobile[['Team', 'W']]

# Calculate total wins and losses
chaseWins = chasesStandings['W'].sum()
bryceWins = brycesStandings['W'].sum()
zachWins = zachsStandings['W'].sum()

df = pd.read_excel('Wins_Over_Time.xlsx') 
# add on to end of dataframe with todays data and wins
todaysData = pd.DataFrame({'Day': date.today()-pd.Timedelta(days=1), 'Chase': [chaseWins], 'Bryce': [bryceWins], 'Zach': [zachWins]})  
df = pd.concat([df, todaysData], ignore_index=True)
# save to excel
df.to_excel('Wins_Over_Time.xlsx', index=False)
df.iloc[:, 1:] = df.iloc[:, 1:].sub(df.iloc[:, 1:].min(axis=1), axis=0)
# format dat as Oct-22
df['Day'] = pd.to_datetime(df['Day']).dt.strftime('%b-%d')

url = 'https://www.espn.com/nba/schedule'
headers = {
    'User-Agent': 'Mozilla/5.0'
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Locate the schedule table
matchups = []
yesterday = []
schedule_table = soup.find_all('div', class_='ScheduleTables')[1]
yesterday_table = soup.find_all('div', class_='ScheduleTables')[0]

if schedule_table:
    # Find each matchup row
    rows = schedule_table.find_all('tr', class_='Table__TR--sm')

    for row in rows:
        # Extract team names
        teams = row.find_all('a', class_='AnchorLink')
        away_team = teams[1]['href'].split('/')[-2] if teams else None
        home_team = teams[3]['href'].split('/')[-2] if len(teams) > 1 else None
        # Extract time
        time = row.find('td', class_='date__col').text.strip() if row.find('td', class_='date__col') else None
        
        # Extract odds (e.g., point spread)
        odds_info = row.find('div', class_='Odds__Message')
        odds = odds_info.text.strip() if odds_info else None

        # Store each matchup as a dictionary
        matchups.append({
            'away_team': away_team,
            'home_team': home_team,
            'time': time,
            'odds': odds.split('O/U')[0].split('Line: ')[1] if odds else None,
        })
                
if yesterday_table:
    rows = yesterday_table.find_all('tr', class_='Table__TR--sm')
    for row in rows:
        # Extract team names
        teams = row.find_all('a', class_='AnchorLink')
        away_team = teams[1]['href'].split('/')[-2] if teams else None
        home_team = teams[3]['href'].split('/')[-2] if len(teams) > 1 else None
        result = teams[4].text.strip() if len(teams) > 1 else None
        
        if result != "Postponed":
            yesterday.append({
                'away_team': away_team,
                'home_team': home_team,
                'result': result,
                'winner': result.split(' ')[0] if result else None,
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
    </script>
    <style>
    /* Existing styles */
    body {{
        font-family: Arial, sans-serif;
    }}

    h1 {{
        text-align: center;
        color: Green;
        font-size: 40px;
        margin: 8px;
    }}

    table {{
        margin: 0 auto;
        width: 50%;
        border-collapse: collapse;
    }}

    th, td {{
        padding: 10px;
        text-align: center;
        border: 1px solid black;
    }}

    img {{
        display: block;
        margin: 0 auto;
    }}

    .column {{
        float: left;
        width: 33.33%;
        text-align: center;
    }}

    .row:after {{
        content: "";
        display: table;
        clear: both;
    }}

    /* New styles */
    .row {{
        display: flex;
        justify-content: space-around;
        margin-top: 20px;
    }}

    .column {{
        flex: 1;
        padding: 15px;
    }}

    .card {{
        border: 1px solid #ddd;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        background-color: #f9f9f9;
        padding: 20px;
        text-align: center;
    }}

    .card-header {{
        margin-bottom: 15px;
    }}

    .card-body h2 {{
        font-size: 24px;
        color: #333;
        margin: 10px 0;
    }}

    .table-container {{
        margin-top: 15px;
        overflow-x: auto;
    }}
    
    .table-container2 {{
        margin-top: 0px;
        overflow-x: visible;
        font-size: 12px;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
    }}

    table, th, td {{
        border: 1px solid #ccc;
        padding: 10px;
    }}

    th {{
        background-color: #f2f2f2;
        color: #333;
        font-weight: bold;
    }}

    td {{
        text-align: center;
    }}
    
    #myLineChart {{
        width: 100%;
    }}
    
    .progress-container {{
            width: 100%;
            background-color: #f1f1f1;
            border-radius: 5px;
            position: relative;
    }}

    .progress-bar {{
        height: 30px;
        background-color: #4CAF50;
        text-align: center;
        color: black;
        line-height: 30px;
        border-radius: 5px;
    }}
    
    @media screen and (max-width: 600px) {{
        .column {{
            flex: 100%; /* Make each column take up full width */
            padding: 0px;
        }}
        
        .table-container {{
            display: none;
        }}
        
        .table-container2 {{
            display: "block";
        }}
    }}
    
        /* Style the tab */
    .tab {{
    overflow: hidden;
    border: 1px solid #ccc;
    background-color: #f1f1f1;
    text-align: center;
    }}

    /* Style the buttons that are used to open the tab content */
    .tab button {{
    background-color: inherit;
    border: none;
    outline: none;
    cursor: pointer;
    padding: 14px 16px;
    transition: 0.3s;
    }}

    /* Change background color of buttons on hover */
    .tab button:hover {{
    background-color: #ddd;
    }}

    /* Create an active/current tablink class */
    .tab button.active {{
    background-color: #ccc;
    }}

    /* Style the tab content */
    .tabcontent {{
    display: none;
    padding: 6px 12px;
    border: 1px solid #ccc;
    border-top: none;
    }}
    
    @media screen and (min-width: 601px) {{
        .table-container2 {{
            display: none;
        }}
        #chart-container {{
            display: none;
        }}
    }}
    
    ch {{
        text-decoration: underline;
        -webkit-text-decoration-color: red; /* safari still uses vendor prefix */
        text-decoration-color: red;
        font-size: 24px;
        font-weight:bold;
    }}

</style>

</head>
<body>

    <div class="progress-container">
        <div class="progress-bar" id="progressBar">0/0</div>
    </div>

    <script>
        let x = {chaseWins+ bryceWins + zachWins}
        let y = {1230}
        let percentage = ((x / y) * 100).toFixed(1);

        let progressBar = document.getElementById("progressBar");
        progressBar.style.width = percentage + "%";
        progressBar.innerText = percentage+ "%";
    </script>

<h1>NBA Extravaganza</h1>
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

<div class="row">
    <div class="column">
        <div class="card">
            <div class="card-header">
                {img_to_html('photos/ChaseHead.png')}
            </div>
            <hr color="#2774AE">
            <div class="card-body">
                <h2>Chase's Wins: {chaseWins}</h2>
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
            </div>
            <hr color="#57068c">
            <div class="card-body">
                <h2>Bryce's Wins: {bryceWins}</h2>
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
            </div>
            <hr color="#e21833">
            <div class="card-body">
                <h2>Zach's Wins: {zachWins}</h2>
                <div class="table-container" >
                    {zachsStandings.to_html(index=False)}
                </div>
                <div class="table-container2">
                    {zachStandingsMobile.to_html(index=False)}
                </div>
            </div>
        </div>
    </div>
</div>
<hr/>

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

</body>
</html>


"""

html_content += dpt

# Write HTML content to a file
with open('index.html', 'w') as f:
    f.write(html_content)

print("HTML file generated: index.html")