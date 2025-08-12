
import mysql.connector
import pandas as pd
from db_config import MYSQL_CONFIG
import os

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_team_overall_status():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    # Total matches played by each team 
    query_played = """
    SELECT team, COUNT(*) AS matches_played FROM (
        SELECT team1 AS team FROM matches
        UNION ALL
        SELECT team2 AS team FROM matches
    ) AS all_teams
    GROUP BY team;
    """
    df_played = pd.read_sql(query_played, conn)

    # Total matches won
    query_won = """
    SELECT winner AS team, COUNT(*) AS matches_won
    FROM matches
    WHERE winner IS NOT NULL
    GROUP BY winner;
    """
    df_won = pd.read_sql(query_won, conn)

    # Combining both
    df = pd.merge(df_played, df_won, on="team", how="left")
    df["matches_won"] = df["matches_won"].fillna(0).astype(int)
    df["win_percentage"] = round((df["matches_won"] / df["matches_played"]) * 100, 2)

    conn.close()
    return df

def get_season_wise_performance():
    conn = mysql.connector.connect(**MYSQL_CONFIG)

    query = """
    SELECT
        season,
        team,
        COUNT(*) AS matches_played
    FROM (
        SELECT season, team1 AS team FROM matches
        UNION ALL
        SELECT season, team2 AS team FROM matches
    ) AS all_season_teams
    GROUP BY season, team;
    """
    df_played = pd.read_sql(query, conn)

    query_won = """
    SELECT
        season,
        winner AS team,
        COUNT(*) AS matches_won
    FROM matches
    WHERE winner IS NOT NULL
    GROUP BY season, winner;
    """
    df_won = pd.read_sql(query_won, conn)

    df = pd.merge(df_played, df_won, on=["season", "team"], how="left")
    df["matches_won"] = df["matches_won"].fillna(0).astype(int)
    df["win_percentage"] = round((df["matches_won"] / df["matches_played"]) * 100, 2)

    conn.close()
    return df

def save_reports():
    overall_df = get_team_overall_status()
    season_df = get_season_wise_performance()

    overall_df.to_csv(os.path.join(OUTPUT_DIR, "team_overall_status.csv"), index=False)
    season_df.to_csv(os.path.join(OUTPUT_DIR, "season_wise_performance.csv"), index=False)

    print("Reports generated:")
    print("team_overall_status.csv")
    print("season_wise_performance.csv")

if __name__ == "__main__":
    print("Loading data..")
    from scripts.load_data import load_csv_to_mysql
    load_csv_to_mysql()

    print("Generating reports..")
    save_reports()

import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt

# Connecting  MySQL database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="SruthiSQL@369",
    database="ipl2025"
)

# List of IPL teams
present_teams = [
    "Chennai Super Kings",
    "Delhi Capitals",
    "Kolkata Knight Riders",
    "Mumbai Indians",
    "Punjab Kings",
    "Rajasthan Royals",
    "Royal Challengers Bangalore",
    "Sunrisers Hyderabad",
    "Lucknow Super Giants",
    "Gujarat Titans"
]

Team_homegrounds = {
    'Chennai Super Kings': ('M.A. Chidambaram Stadium', 'Chennai'),
    'Delhi Capitals': ('Arun Jaitley Stadium', 'Delhi'),
    'Kolkata Knight Riders': ('Eden Gardens', 'Kolkata'),
    'Lucknow Super Giants': ('BRSABV Ekana Stadium', 'Lucknow'),
    'Mumbai Indians': ('Wankhede Stadium', 'Mumbai'),
    'Punjab Kings': ('Punjab Cricket Association Stadium', 'Mohali'),
    'Rajasthan Royals': ('Sawai Mansingh Stadium', 'Jaipur'),
    'Royal Challengers Bangalore': ('M. Chinnaswamy Stadium', 'Bangalore'),
    'Sunrisers Hyderabad': ('Rajiv Gandhi Intl. Cricket Stadium', 'Hyderabad')
}


def get_matches_df():
    return pd.read_sql("SELECT * FROM matches WHERE season <= 2019", conn)

def get_deliveries_df():
    return pd.read_sql("SELECT * FROM deliveries", conn)

def show_team_summary(team):
    matches = get_matches_df()
    deliveries = get_deliveries_df()

    team_matches = matches[(matches['team1'] == team) | (matches['team2'] == team)]

    if team_matches.empty:
        print(f"\n {team} did not play in IPL up to 2019.")
        if team=="Gujarat Titans":
            print("HomeGround : Narendra Modi Stadium")
            print("Location : Ahmedabad")
        elif team=="Lucknow Super Giants":
            print("HomeGround : BRSABV Ekana Stadium")
            print("Location : Lucknow")
        else:
            pass
        return

    # IPL titles won 
    finals = matches.groupby("season")['match_id'].max().reset_index()
    finals_matches = matches[matches['match_id'].isin(finals['match_id'])]
    titles_won = finals_matches[finals_matches['winner'] == team]


    print(f"\n {team} won {len(titles_won)} IPL Cups")
    print("Years won:", list(titles_won['season']) if not titles_won.empty else "None")

    

    # Finals reached & lost
    finals_reached = finals_matches[(finals_matches['team1'] == team) | (finals_matches['team2'] == team)]
    finals_lost = len(finals_reached) - len(titles_won)
    print(f"\n Number of Finals reached: {len(finals_reached)}")
    print(f" Number of Finals lost: {finals_lost}")
   
    if team in Team_homegrounds:
        ground, location = Team_homegrounds[team]
        print(f" Home Ground: {ground}")
        print(f" Location: {location}")
   

    # Win percentage by year comparision
    yearly = []
    for year in sorted(matches['season'].unique()):
        year_matches = matches[matches['season'] == year]
        played = year_matches[(year_matches['team1'] == team) | (year_matches['team2'] == team)]
        won = played[played['winner'] == team]
        total = len(played)
        win_pct = (len(won) / total) * 100 if total > 0 else 0
        yearly.append((year, win_pct))

    years = [y for y, _ in yearly]
    win_rates = [w for _, w in yearly]

    plt.figure(figsize=(10, 4))
    plt.plot(years, win_rates, marker='o', color='green')
    plt.title(f"{team} Win % (2008–2019)")
    plt.xlabel("Season")
    plt.ylabel("Win Percentage")
    plt.grid(True)
    plt.xticks(years)
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.show()

def show_most_runs_per_season():
    matches = get_matches_df()
    deliveries = get_deliveries_df()

    merged = pd.merge(deliveries, matches[['match_id', 'season']], left_on='match_id', right_on='match_id')
    runs = merged.groupby(['season', 'batsman'])['total_runs'].sum().reset_index()

    print("\n Most Runs by Player each Season(ORANGE CAP HOLDER):")
    for year in sorted(runs['season'].unique()):
        top = runs[runs['season'] == year].sort_values('total_runs', ascending=False).head(1)
        print(f"{year}: {top.iloc[0]['batsman']} - {top.iloc[0]['total_runs']} runs")

def show_most_wickets_per_season():
    matches = get_matches_df()
    deliveries = get_deliveries_df()

    merged = pd.merge(deliveries, matches[['match_id', 'season']], left_on='match_id', right_on='match_id')
    wickets = merged[merged['player_dismissed'].notnull()]
    count = wickets.groupby(['season', 'bowler'])['player_dismissed'].count().reset_index(name='wickets')

    print("\n Most Wickets taken by Bowler each Season(PURPLE CAP HOLDER):")
    for year in sorted(count['season'].unique()):
        top = count[count['season'] == year].sort_values('wickets', ascending=False).head(1)
        print(f"{year}: {top.iloc[0]['bowler']} - {top.iloc[0]['wickets']} wickets")

from logger_config import logger

class MenuInputError(Exception):

    pass

def show_menu():
    while True:
        logger.info("Displaying menu to user.")
        print("\n IPL Team Performance Menu:")
        for idx, team in enumerate(present_teams, 1):
            print(f"{idx}. {team}")
        print("11. Most Runs by Player(Orange Cap Holder)")
        print("12. Most Wickets by Bowler(Purple Cap Holder)")
        print("0. Exit")

        try:
            choice = int(input("Enter your choice: "))
            logger.info(f"User selected menu option: {choice}")
            if choice == 0:
                print("Sorry you exited the program...")
                logger.info("User exited the program.")
                break
            elif 1 <= choice <= 10:
                show_team_summary(present_teams[choice - 1])
            elif choice == 11:
                show_most_runs_per_season()
            elif choice == 12:
                show_most_wickets_per_season()
            else:
                logger.warning(f"Invalid menu choice: {choice}")
                raise MenuInputError("Invalid choice. Please enter a valid option.")
        except ValueError:
            logger.error("Non-integer value received.")
            print(" Please enter a valid number.")
        except MenuInputError as mie:
            logger.error(str(mie))
            print(str(mie))

if __name__ == "__main__":
    show_menu()

