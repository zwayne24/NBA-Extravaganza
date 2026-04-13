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

ChasesTeams = ['Denver Nuggets','New York Knicks','Golden State Warriors','LA Clippers','Dallas Mavericks','Boston Celtics','Miami Heat','Sacramento Kings','Phoenix Suns','Brooklyn Nets']
BrycesTeams = ['Oklahoma City Thunder','Orlando Magic','Minnesota Timberwolves','Atlanta Hawks','San Antonio Spurs','Memphis Grizzlies','Indiana Pacers','Chicago Bulls','Portland Trail Blazers','Utah Jazz']
ZachsTeams = ['Cleveland Cavaliers','Houston Rockets','Los Angeles Lakers','Detroit Pistons','Milwaukee Bucks','Philadelphia 76ers','Toronto Raptors','New Orleans Pelicans','Charlotte Hornets','Washington Wizards']

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

html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Standings</title>
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

<div class="row">
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

</body>
</html>
"""

with open('index.html', 'w') as f:
    f.write(html_content)

print("HTML file generated: index.html")
