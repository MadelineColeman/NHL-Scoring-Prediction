from nhlpy import NHLClient
import pandas as pd

def playtime_to_hour(time_str):
    # Converts a "mm:ss" string to a decimal number equivalent of an hour
    mins, secs = map(int, time_str.split(':'))
    return mins/60 + secs/3600;

def get_scoring_players(client, date):
    # Return a list of player id's corresponding to all players that scored on a specific date
    scoring_players = []
    data = client.schedule.get_schedule(date=date)
    games = data["gameWeek"]["date" == date]["games"]
    for game in games:
        # game_ids.append(game["id"])
        plays = client.game_center.play_by_play(game["id"])["plays"]
        scoring_plays = [item for item in plays if item.get("typeDescKey") == 'goal']
        for item in scoring_plays:
            scoring_players.append(item['details'].get('scoringPlayerId'))

    scoring_players = list(set(scoring_players))
    return scoring_players

def get_all_players(client, date):
    # Returns a list of player id's corresponding to all players that played on a specific date
    players = []
    data = client.schedule.get_schedule(date=date)
    games = data["gameWeek"]["date" == date]["games"]
    for game in games:
        # Get all players that played on a specific date
        player_stats = client.game_center.boxscore(game["id"])['playerByGameStats']
        forward_ids = [player["playerId"] for team_data in player_stats.values() for player in team_data.get("forwards", [])]
        defense_ids = [player["playerId"] for team_data in player_stats.values() for player in team_data.get("defense", [])]
        players.extend(forward_ids)
        players.extend(defense_ids)
    return players


def get_team_stats(date, player_stats):
    # Read data for both teams in game
    date = int(''.join(date.split('-')))
    team_data = pd.read_csv(f"team_data/{player_stats['Team']}.csv")
    opp_data = pd.read_csv(f"team_data/{player_stats['Opponent']}.csv")

    # Filter by date
    team_data = team_data[team_data['gameDate'] < date]
    opp_data = opp_data[opp_data['gameDate'] < date]
    opp_data.rename(columns=lambda x: 'Opp' + x, inplace=True)

    # Grab only data
    team_data = team_data.iloc[:, 10:-1]
    opp_data = opp_data.iloc[:, 10:-1]

    # Take Avg and Convert to a dict
    team_dict = team_data.mean().to_dict()
    opp_dict = opp_data.mean().to_dict()

    merged_data = {**player_stats, **team_dict, **opp_dict, 'teamGamesPlayed': len(team_data), 'oppGamesPlayed': len(opp_data)}

    return merged_data

def stats_as_of_date(client, player_id_num, date, num_games = None):
    # Returns a player's summed stats as of a specified date. If num_games is specified, only the num_games most recent games are used
    career_stats = client.stats.player_career_stats(player_id_num)
    first_name = career_stats.get('firstName')['default']
    last_name = career_stats.get('lastName')['default']

    season_games = client.stats.player_game_log(player_id = player_id_num, season_id = '20232024', game_type = 2)
    if num_games != None:
        season_games = season_games[0:min(num_games+1, len(season_games))]
    

    
    curr_game = next((game for game in season_games if game.get('gameDate') == date), None)
    team = curr_game['teamAbbrev']
    opponent = curr_game['opponentAbbrev']

    df = pd.DataFrame(season_games)
    df = df[df['gameDate'] < date]
    df = df[['goals', 'assists','points', 'plusMinus',
       'powerPlayGoals', 'powerPlayPoints', 'gameWinningGoals', 'otGoals',
       'shots', 'shifts', 'shorthandedGoals', 'shorthandedPoints', 'pim', 'toi']]
    df['toi'] = df['toi'].apply(playtime_to_hour)

    mean_dict = df.mean().to_dict()

    basic_stats = {'playerID':player_id_num, 'first name': first_name, 'last name': last_name, 'Team': team, 'Opponent': opponent,
                   'Scored?': 0, 'games_played' : len(df), **mean_dict}

    merged_data = get_team_stats(date, basic_stats)
    
    return merged_data



client = NHLClient(timeout=20)

dates = ['2023-12-11','2023-12-10','2023-12-09','2023-12-08','2023-12-07',
         '2023-12-06','2023-12-05','2023-12-04','2023-12-03','2023-12-02',
         '2023-12-01','2023-11-30','2023-11-29','2023-11-28','2023-11-27',]


for date in dates:
    players = get_all_players(client, date)
    scoring_players = get_scoring_players(client, date)
    data_list = []

    # stats_as_of_date
    for player in players:
        player_data = stats_as_of_date(client, player, date)

        if player in scoring_players:
            player_data['Scored?'] = 1
        
        data_list.append(player_data)
    
    df = df = pd.DataFrame(data_list)
    df.to_csv(f"all_data/{date}_data.csv", index = False)


