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

# Scrape standings from ESPN
url = 'https://www.espn.com/nba/standings/_/group/league'
headers = {
    'User-Agent': 'Mozilla/5.0'
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

standings = pd.DataFrame(columns=['Team', 'W', 'L', 'PCT'])

i = 0
team_name_list = []
for team in soup.find_all('tr', class_='Table__TR Table__TR--sm Table__even'):
    if i < 15:
        team_name = team.find('span', class_='hide-mobile').text
        team_name_list.append(team_name)
    if i >= 15 and i < 30:
        wins = team.find('span', class_='stat-cell').text
        losses = team.find_all('span', class_='stat-cell')[1].text
        pct = team.find_all('span', class_='stat-cell')[2].text
        new_row = pd.DataFrame([{'Team': team_name_list[i-15], 'W': wins, 'L': losses, 'PCT': pct}])
        standings = pd.concat([standings, new_row], ignore_index=True)
    i += 1

# Continue with the data extraction...
i = 0
for team in soup.find_all('tr', class_='filled Table__TR Table__TR--sm Table__even'):
    if i < 15:
        team_name = team.find('span', class_='hide-mobile').text
        team_name_list.append(team_name)
    if i >= 15 and i < 30:
        wins = team.find('span', class_='stat-cell').text
        losses = team.find_all('span', class_='stat-cell')[1].text
        pct = team.find_all('span', class_='stat-cell')[2].text
        new_row = pd.DataFrame([{'Team': team_name_list[i], 'W': wins, 'L': losses, 'PCT': pct}])
        standings = pd.concat([standings, new_row], ignore_index=True)
    i += 1

# Read All-NBA data from CSV
allNBAs = pd.read_csv('allNBARemaining.csv')
allNBA = allNBAs.sample()
allNBAs = allNBAs.drop(allNBA.index)
allNBAs.to_csv('allNBARemaining.csv', index=False)

# Define team lists for Chase, Bryce, and Zach
ChasesTeams = ['Minnesota Timberwolves', 'Milwaukee Bucks', 'Phoenix Suns', 'Orlando Magic', 'Miami Heat', 'Golden State Warriors', 'Houston Rockets', 'LA Clippers', 'Portland Trail Blazers', 'Brooklyn Nets']
BrycesTeams = ['Oklahoma City Thunder', 'Denver Nuggets', 'Philadelphia 76ers', 'Sacramento Kings', 'Memphis Grizzlies', 'San Antonio Spurs', 'Toronto Raptors', 'Atlanta Hawks', 'Utah Jazz', 'Detroit Pistons']
ZachsTeams = ['Boston Celtics', 'Dallas Mavericks', 'New York Knicks', 'Indiana Pacers', 'Cleveland Cavaliers', 'New Orleans Pelicans', 'Los Angeles Lakers', 'Chicago Bulls', 'Charlotte Hornets', 'Washington Wizards']

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
    'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SA', 'Toronto Raptors': 'TOR', 'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS'
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

if allNBA['Last_Season'].values[0] == allNBA['First_Season'].values[0]:
    Years = allNBA['First_Season'].values[0]
else:
    Years = "Between "+allNBA['First_Season'].values[0] + ' and ' + allNBA['Last_Season'].values[0]
    
Teams = allNBA['Team_List'].values[0].replace('[', '').replace(']', '').replace('\'', '')
Pos = allNBA['Positions'].values[0].replace('[', '').replace(']', '').replace('\'', '')

url = 'https://www.espn.com/nba/schedule'
headers = {
    'User-Agent': 'Mozilla/5.0'
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Locate the schedule table
matchups = []

schedule_table = soup.find('div', class_='ScheduleTables')

if schedule_table:
    # Find each matchup row
    rows = schedule_table.find_all('tr', class_='Table__TR--sm')

    for row in rows:
        # Extract team names
        teams = row.find_all('a', class_='AnchorLink')
        away_team = teams[1].text.strip() if teams else None
        home_team = teams[3].text.strip() if len(teams) > 1 else None
        
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
        
# Create a DataFrame from the matchups list
matchups_df = pd.DataFrame(matchups)
html_table = "<table><thead><tr><th>Home Team</th><th>Away Team</th><th>Time</th><th>Odds</th></tr></thead><tbody>"
for i, row in matchups_df.iterrows():
    # if row['Home Team'] = ChasesTeams first row
    for team in ChasesTeams:
        if row['home_team'] == ' '.join(team.split(' ')[:-1]):
            html_table += f"<td style='color:#2774AE'>{team}</td>"
    for team in BrycesTeams:
        if row['home_team'] == ' '.join(team.split(' ')[:-1]):
            html_table += f"<td style='color:#57068c'>{team}</td>"
    for team in ZachsTeams:
        if row['home_team'] == ' '.join(team.split(' ')[:-1]):
            html_table += f"<td style='color:#e21833'>{team}</td>"
    for team in ChasesTeams:
        if row['away_team'] == ' '.join(team.split(' ')[:-1]):
            html_table += f"<td style='color:#2774AE'>{team}</td>"
    for team in BrycesTeams:
        if row['away_team'] == ' '.join(team.split(' ')[:-1]):
            html_table += f"<td style='color:#57068c'>{team}</td>"
    for team in ZachsTeams:
        if row['away_team'] == ' '.join(team.split(' ')[:-1]):
            html_table += f"<td style='color:#e21833'>{team}</td>"
    html_table += f"<td>{row['time']}</td><td>{row['odds']}</td></tr>"
html_table += "</tbody></table>"

# Generate HTML content
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Standings</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
    /* Existing styles */
    body {{
        font-family: Arial, sans-serif;
    }}

    h1 {{
        text-align: center;
        color: Green;
        font-size: 60px;
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

<h1>NBA Extravaganza</h1>
<div id="chart-container">
    <canvas id="myLineChart"></canvas>
</div>
<script>
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

<h2 style="text-align: center;">Today's Games</h2>
{html_table}

<h2 style="text-align: center;">All-NBA Player of the Day</h2>
<div style="text-align: center;">
    <details>
        <summary><b>Who am I?</b></summary>
        <p style="font-size:20px";><b>{allNBA['Players'].values[0]}</b></p>
    </details>
</div>
<p style="text-align: center;"><b>All-NBA Teams:</b> {Teams}</h2>
<p style="text-align: center;"><b>All-NBA:</b> {Years}</p>
<p style="text-align: center;"><b>Position:</b> {Pos}</p>
<p style="text-align: center;"><b>Teams Made:</b> {allNBA['Times_First_Team'].values[0]+allNBA['Times_Second_Team'].values[0]+allNBA['Times_Third_Team'].values[0]}x</p>

</body>
</html>
"""
# Write HTML content to a file
with open('index.html', 'w') as f:
    f.write(html_content)

print("HTML file generated: index.html")
