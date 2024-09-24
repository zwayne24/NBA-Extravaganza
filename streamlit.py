# beautiful soup https://www.espn.com/nba/standings
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import base64

url = 'https://www.espn.com/nba/standings/_/group/league'
headers = {
    'User-Agent': 'Mozilla/5.0'
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

standings = pd.DataFrame(columns=['Team', 'W', 'L','PCT'])

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
        standings = standings.append({'Team': team_name_list[i-15], 'W': wins, 'L': losses, 'PCT': pct}, ignore_index=True)
    i += 1
    
i = 0    
for team in soup.find_all('tr', class_='filled Table__TR Table__TR--sm Table__even'):
    if i < 15:
        team_name = team.find('span', class_='hide-mobile').text
        team_name_list.append(team_name)
    if i >= 15 and i < 30:
        wins = team.find('span', class_='stat-cell').text
        losses = team.find_all('span', class_='stat-cell')[1].text
        pct = team.find_all('span', class_='stat-cell')[2].text
        standings = standings.append({'Team': team_name_list[i], 'W': wins, 'L': losses, 'PCT': pct}, ignore_index=True)
    i += 1
    
quotes = pd.read_csv('quotesRemaining.csv')
#pick one quote, delete it from the list, and save the list
quote = quotes.sample()
quotes = quotes.drop(quote.index)
quotes.to_csv('quotesRemaining.csv', index=False)

allNBAs = pd.read_csv('allNBARemaining.csv')
#pick one quote, delete it from the list, and save the list
allNBA = allNBAs.sample()
allNBAs = allNBAs.drop(allNBA.index)
allNBAs.to_csv('allNBARemaining.csv', index=False)
    
AidansTeams = ['Minnesota Timberwolves','Milwaukee Bucks','Phoenix Suns','Orlando Magic','Miami Heat','Golden State Warriors','Houston Rockets','Los Angeles Clippers','Portland Trail Blazers','Brooklyn Nets']
BrycesTeams = ['Oklahoma City Thunder','Denver Nuggets','Philadelphia 76ers','Sacramento Kings','Memphis Grizzlies','San Antonio Spurs','Toronto Raptors','Atlanta Hawks','Utah Jazz','Detroit Pistons'] 
ZachsTeams = ['Boston Celtics', 'Dallas Mavericks', 'New York Knicks','Indiana Pacers', 'Cleveland Cavaliers', 'New Orleans Pelicans','Los Angeles Lakers','Chicago Bulls','Charlotte Hornets', 'Washington Wizards']
              
#sort standings by pct
standings['W'] = standings['W'].astype(int)
standings['L'] = standings['L'].astype(int)
standings['PCT'] = standings['PCT'].astype(float)
standings = standings.sort_values(by='PCT', ascending=False)

# remove pct column
standings = standings.drop(columns=['PCT'])


aidansStandings = standings[standings['Team'].isin(AidansTeams)]
aidansStandings = aidansStandings.reset_index(drop=True)
# start at 1
aidansStandings.index += 1
brycesStandings = standings[standings['Team'].isin(BrycesTeams)]
brycesStandings = brycesStandings.reset_index(drop=True)
brycesStandings.index += 1
zachsStandings = standings[standings['Team'].isin(ZachsTeams)]
zachsStandings = zachsStandings.reset_index(drop=True)
zachsStandings.index += 1

aidanWins = aidansStandings['W'].sum()
bryceWins = brycesStandings['W'].sum()
zachWins = zachsStandings['W'].sum()
aidanLosses = aidansStandings['L'].sum()
bryceLosses = brycesStandings['L'].sum()
zachLosses = zachsStandings['L'].sum()

# Set the page configuration
st.set_page_config(layout="wide")

# Path to your local image
image_path = "SIT2022.jpg"
image_zach = "ZachHead.png"
image_bryce = "BryceHead.png"
image_aidan = "ZachHead.png"

# Display the title
st.markdown("<h1 style='text-align: center; color: Green;font-size: 60px'>\'Welcome to the Jungle\' NBA Extravaganza</h1>", unsafe_allow_html=True)

# Create three columns for the players' images, wins, and standings
col1, col2, col3 = st.columns(3)

import base64
from pathlib import Path

def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded
def img_to_html(img_path, width=100):
    img_html = "<img src='data:image/png;base64,{0}' width='{1}' class='img-fluid'>".format(
      img_to_bytes(img_path), width
    )
    return img_html

# First column (Aidan)
with col1:
    st.markdown("<p style='text-align: center; color: grey;'>"+img_to_html('ZachHead.png')+"</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: Green;font-size: 40px'><strong>{aidanWins}<strong></p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: Black;font-size: 30px'>Aidan's Wins</p>", unsafe_allow_html=True)
    st.table(aidansStandings)

# Second column (Bryce)
with col2:
    st.markdown("<p style='text-align: center; color: grey;'>"+img_to_html('BryceCrown.png',109.49)+"</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: Green;font-size: 40px'><strong>{bryceWins}<strong></p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: Black;font-size: 30px'>Bryce's Wins</p>", unsafe_allow_html=True)
    st.table(brycesStandings)

# Third column (Zach)
with col3:
    st.markdown("<p style='text-align: center; color: grey;'>"+img_to_html('ZachCrown.png')+"</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: Green;font-size: 40px'><strong>{zachWins}</strong></p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: Black;font-size: 30px'>Zach's Wins</p>", unsafe_allow_html=True)
    st.table(zachsStandings)

st.markdown(f"<p style='text-align: center; color: Black;font-size: 20px'><strong>QOTD</strong>: {quote['Quotes'].values[0]}</p>", unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align: center;">
    <details>
        <summary style="font-size: 20px;">Said by:</summary>
        <p>{quote['Speaker'].values[0]}</p>
    </details>
</div>
""", unsafe_allow_html=True)

st.markdown(f"<p style='text-align: center; color: Black;font-size: 20px'>All-NBA Teams: {allNBA['Team_List'].str.replace('[^a-zA-Z, 1-9]', '').values[0].replace(',', ', ')}</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: Black;font-size: 20px'>All-NBA Between: {allNBA['First_Season'].values[0]} and {allNBA['Last_Season'].values[0]}</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: Black;font-size: 20px'>Position: {allNBA['Positions'].str.replace('[^a-zA-Z, 1-9]', '').values[0].replace(',', ', ')}</p>", unsafe_allow_html=True)
