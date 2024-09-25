import requests
from bs4 import BeautifulSoup
import pandas as pd
import base64
from pathlib import Path

# Function to convert image to base64
def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded

def img_to_html(img_path, width=100):
    img_html = "<img src='data:image/png;base64,{0}' width='{1}' class='img-fluid'>".format(
      img_to_bytes(img_path), width
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
standings = standings.sort_values(by='PCT', ascending=False).drop(columns=['PCT'])

chasesStandings = standings[standings['Team'].isin(ChasesTeams)].reset_index(drop=True)
chasesStandings.index += 1
brycesStandings = standings[standings['Team'].isin(BrycesTeams)].reset_index(drop=True)
brycesStandings.index += 1
zachsStandings = standings[standings['Team'].isin(ZachsTeams)].reset_index(drop=True)
zachsStandings.index += 1

# Calculate total wins and losses
chaseWins = chasesStandings['W'].sum()
bryceWins = brycesStandings['W'].sum()
zachWins = zachsStandings['W'].sum()

if allNBA['Last_Season'].values[0] == allNBA['First_Season'].values[0]:
    Years = allNBA['First_Season'].values[0]
else:
    Years = "Between "+allNBA['First_Season'].values[0] + ' and ' + allNBA['Last_Season'].values[0]
    
Teams = allNBA['Team_List'].str.replace('[^a-zA-Z, 1-9]', '').values[0].replace(',', ', ')
Pos = allNBA['Positions'].str.replace('[^a-zA-Z, 1-9]', '').values[0].replace(',', ', ')

# Generate HTML content
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Standings</title>
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
</style>

</head>
<body>

<h1>NBA Extravaganza</h1>

<div class="row">
    <div class="column">
        <div class="card">
            <div class="card-header">
                {img_to_html('photos/ChaseHead.png', 100)}
            </div>
            <div class="card-body">
                <h2>Chase's Wins: {chaseWins}</h2>
                <div class="table-container">
                    {chasesStandings.to_html(index=False)}
                </div>
            </div>
        </div>
    </div>

    <div class="column">
        <div class="card">
            <div class="cfard-header">
                {img_to_html('photos/BryceHead.png', 109)}
            </div>
            <div class="card-body">
                <h2>Bryce's Wins: {bryceWins}</h2>
                <div class="table-container">
                    {brycesStandings.to_html(index=False)}
                </div>
            </div>
        </div>
    </div>

    <div class="column">
        <div class="card">
            <div class="card-header">
                {img_to_html('photos/ZachHead.png', 100)}
            </div>
            <div class="card-body">
                <h2>Zach's Wins: {zachWins}</h2>
                <div class="table-container">
                    {zachsStandings.to_html(index=False)}
                </div>
            </div>
        </div>
    </div>
</div>

<hr/>

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
