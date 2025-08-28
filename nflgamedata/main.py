import requests
import json
import os
import time
from typing import Dict, Optional
from datetime import datetime


class NFLDataFetcher:
    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.core_url = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
        
    def get_scoreboard(self, year: int = 2024, season_type: int = 2, week: Optional[int] = None) -> Dict:
        """Get NFL scoreboard for a specific year, season type, and optionally week.
        
        Args:
            year: NFL season year
            season_type: 1=preseason, 2=regular season, 3=postseason
            week: Specific week number (optional)
        """
        url = f"{self.base_url}/scoreboard"
        params = {
            "dates": year,
            "seasontype": season_type
        }
        if week:
            params["week"] = week
            
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching scoreboard: {e}")
            return {}
    
    def get_game_summary(self, event_id: str) -> Dict:
        """Get detailed game summary including box score for a specific game.
        
        Args:
            event_id: ESPN event ID for the game
        """
        url = f"{self.base_url}/summary"
        params = {"event": event_id}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching game summary: {e}")
            return {}
    
    def get_team_statistics(self, event_id: str, team_id: str) -> Dict:
        """Get detailed team statistics for a specific game.
        
        Args:
            event_id: ESPN event ID for the game
            team_id: ESPN team ID
        """
        url = f"{self.core_url}/events/{event_id}/competitions/{event_id}/competitors/{team_id}/statistics"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching team statistics: {e}")
            return {}
    
    def get_play_by_play(self, event_id: str, limit: int = 300) -> Dict:
        """Get play-by-play data for a specific game.
        
        Args:
            event_id: ESPN event ID for the game
            limit: Maximum number of plays to retrieve
        """
        url = f"{self.core_url}/events/{event_id}/competitions/{event_id}/plays"
        params = {"limit": limit}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching play-by-play: {e}")
            return {}
    
    def extract_clean_game_data(self, game_summary: Dict, event_data: Dict = None) -> Dict:
        """Extract only essential game data for a clean JSON output.
        
        Args:
            game_summary: Full game summary from ESPN API
            event_data: Optional event data for additional game info
        """
        clean_data = {
            "game_id": "",
            "date": "",
            "status": "",
            "venue": "",
            "attendance": 0,
            "teams": {},
            "final_score": {},
            "team_statistics": {},
            "scoring_plays": [],
            "player_statistics": {}
        }
        
        try:
            # Extract game ID and basic info from event data if provided
            if event_data:
                clean_data["game_id"] = event_data.get("id", "")
                clean_data["date"] = event_data.get("date", "")
                clean_data["status"] = event_data.get("status", {}).get("type", {}).get("description", "")
                
                # Get teams and scores from event data
                if "competitions" in event_data and event_data["competitions"]:
                    competition = event_data["competitions"][0]
                    clean_data["venue"] = competition.get("venue", {}).get("fullName", "")
                    clean_data["attendance"] = competition.get("attendance", 0)
                    
                    if "competitors" in competition:
                        for competitor in competition["competitors"]:
                            team_abbr = competitor.get("team", {}).get("abbreviation", "")
                            clean_data["teams"][team_abbr] = {
                                "name": competitor.get("team", {}).get("displayName", ""),
                                "home_away": competitor.get("homeAway", ""),
                                "record": competitor.get("records", [{}])[0].get("summary", "") if competitor.get("records") else ""
                            }
                            clean_data["final_score"][team_abbr] = int(competitor.get("score", 0))
            
            # Get additional info from game summary header if not in event data
            if "header" in game_summary and not event_data:
                header = game_summary["header"]
                if "competitions" in header and header["competitions"]:
                    competition = header["competitions"][0]
                    clean_data["date"] = competition.get("date", "")
                    clean_data["status"] = competition.get("status", {}).get("type", {}).get("description", "")
                    clean_data["venue"] = competition.get("venue", {}).get("fullName", "")
                    clean_data["attendance"] = competition.get("attendance", 0)
                    
                    if "competitors" in competition:
                        for competitor in competition["competitors"]:
                            team_abbr = competitor.get("team", {}).get("abbreviation", "")
                            clean_data["teams"][team_abbr] = {
                                "name": competitor.get("team", {}).get("displayName", ""),
                                "home_away": competitor.get("homeAway", ""),
                                "record": ""
                            }
                            clean_data["final_score"][team_abbr] = int(competitor.get("score", 0))
            
            # Extract team statistics from boxscore
            if "boxscore" in game_summary and "teams" in game_summary["boxscore"]:
                for team_data in game_summary["boxscore"]["teams"]:
                    team_abbr = team_data.get("team", {}).get("abbreviation", "")
                    if team_abbr:
                        stats = {}
                        for stat in team_data.get("statistics", []):
                            stat_label = stat.get("label", stat.get("name", ""))
                            stat_value = stat.get("displayValue", stat.get("value", ""))
                            stats[stat_label] = stat_value
                        clean_data["team_statistics"][team_abbr] = stats
            
            # Extract scoring plays
            if "scoringPlays" in game_summary:
                for play in game_summary["scoringPlays"]:
                    clean_play = {
                        "quarter": play.get("period", {}).get("number", 0),
                        "time": play.get("clock", {}).get("displayValue", ""),
                        "team": play.get("team", {}).get("abbreviation", ""),
                        "description": play.get("text", ""),
                        "away_score": play.get("awayScore", 0),
                        "home_score": play.get("homeScore", 0)
                    }
                    clean_data["scoring_plays"].append(clean_play)
            
            # Extract key player statistics with proper labels
            if "boxscore" in game_summary and "players" in game_summary["boxscore"]:
                for team_players in game_summary["boxscore"]["players"]:
                    team_abbr = team_players.get("team", {}).get("abbreviation", "")
                    if team_abbr:
                        clean_data["player_statistics"][team_abbr] = {}
                        
                        # Only get key categories: passing, rushing, receiving
                        key_categories = ["passing", "rushing", "receiving", "defensive"]
                        for stat_category in team_players.get("statistics", []):
                            category_name = stat_category.get("name", "")
                            if category_name.lower() in key_categories:
                                # Get stat labels from the first entry
                                stat_labels = []
                                if stat_category.get("labels"):
                                    stat_labels = stat_category["labels"]
                                elif stat_category.get("keys"):
                                    stat_labels = stat_category["keys"]
                                
                                players = []
                                for athlete in stat_category.get("athletes", [])[:3]:  # Top 3 players per category
                                    player_stats = {}
                                    stats_array = athlete.get("stats", [])
                                    
                                    # Map stats to their labels
                                    if stat_labels and len(stat_labels) == len(stats_array):
                                        for label, value in zip(stat_labels, stats_array):
                                            player_stats[label] = value
                                    else:
                                        # Fallback: use common stat mappings based on category
                                        if category_name.lower() == "passing":
                                            passing_labels = ["C/ATT", "YDS", "AVG", "TD", "INT", "SACKS", "QBR", "RTG"]
                                            for i, value in enumerate(stats_array[:len(passing_labels)]):
                                                if i < len(passing_labels):
                                                    player_stats[passing_labels[i]] = value
                                        elif category_name.lower() == "rushing":
                                            rushing_labels = ["CAR", "YDS", "AVG", "TD", "LONG"]
                                            for i, value in enumerate(stats_array[:len(rushing_labels)]):
                                                if i < len(rushing_labels):
                                                    player_stats[rushing_labels[i]] = value
                                        elif category_name.lower() == "receiving":
                                            receiving_labels = ["REC", "YDS", "AVG", "TD", "LONG", "TGTS"]
                                            for i, value in enumerate(stats_array[:len(receiving_labels)]):
                                                if i < len(receiving_labels):
                                                    player_stats[receiving_labels[i]] = value
                                        else:
                                            # Generic fallback
                                            for i, value in enumerate(stats_array):
                                                player_stats[f"stat_{i+1}"] = value
                                    
                                    player = {
                                        "name": athlete.get("athlete", {}).get("displayName", ""),
                                        "position": athlete.get("athlete", {}).get("position", {}).get("abbreviation", ""),
                                        "stats": player_stats if player_stats else athlete.get("stats", [])
                                    }
                                    players.append(player)
                                if players:
                                    clean_data["player_statistics"][team_abbr][category_name] = players
            
        except Exception as e:
            print(f"Error extracting clean game data: {e}")
        
        return clean_data
    
    def extract_box_score_data(self, game_summary: Dict) -> Dict:
        """Extract and format box score data from game summary.
        
        Args:
            game_summary: Game summary data from ESPN API
        """
        box_score = {
            "game_info": {},
            "team_stats": {},
            "scoring": [],
            "player_stats": {}
        }
        
        try:
            # Extract basic game info
            if "header" in game_summary:
                header = game_summary["header"]
                if "competitions" in header and header["competitions"]:
                    competition = header["competitions"][0]
                    box_score["game_info"] = {
                        "date": competition.get("date", ""),
                        "status": competition.get("status", {}).get("type", {}).get("description", ""),
                        "venue": competition.get("venue", {}).get("fullName", ""),
                        "attendance": competition.get("attendance", 0)
                    }
                    
                    # Extract team scores
                    if "competitors" in competition:
                        for team in competition["competitors"]:
                            team_name = team.get("team", {}).get("abbreviation", "")
                            box_score["team_stats"][team_name] = {
                                "score": team.get("score", 0),
                                "home_away": team.get("homeAway", ""),
                                "record": team.get("record", [])
                            }
            
            # Extract detailed box score stats
            if "boxscore" in game_summary:
                boxscore = game_summary["boxscore"]
                
                # Team statistics
                if "teams" in boxscore:
                    for idx, team_data in enumerate(boxscore["teams"]):
                        team_stats = team_data.get("statistics", [])
                        team_name = team_data.get("team", {}).get("abbreviation", f"Team{idx+1}")
                        
                        if team_name not in box_score["team_stats"]:
                            box_score["team_stats"][team_name] = {}
                        
                        # Parse team statistics - they're stored as individual stat objects
                        stats_dict = {}
                        for stat in team_stats:
                            stat_name = stat.get("name", "")
                            stat_value = stat.get("displayValue", stat.get("value", ""))
                            stat_label = stat.get("label", stat_name)
                            stats_dict[stat_label] = stat_value
                        
                        box_score["team_stats"][team_name]["statistics"] = stats_dict
                
                # Player statistics
                if "players" in boxscore:
                    for team_players in boxscore["players"]:
                        team_name = team_players.get("team", {}).get("abbreviation", "")
                        box_score["player_stats"][team_name] = {}
                        
                        for stat_category in team_players.get("statistics", []):
                            category_name = stat_category.get("name", "")
                            box_score["player_stats"][team_name][category_name] = []
                            
                            for athlete in stat_category.get("athletes", []):
                                player_data = {
                                    "name": athlete.get("athlete", {}).get("displayName", ""),
                                    "position": athlete.get("athlete", {}).get("position", {}).get("abbreviation", ""),
                                    "stats": athlete.get("stats", [])
                                }
                                box_score["player_stats"][team_name][category_name].append(player_data)
            
            # Extract scoring plays
            if "scoringPlays" in game_summary:
                for play in game_summary["scoringPlays"]:
                    scoring_play = {
                        "quarter": play.get("period", {}).get("number", 0),
                        "time": play.get("clock", {}).get("displayValue", ""),
                        "team": play.get("team", {}).get("abbreviation", ""),
                        "description": play.get("text", ""),
                        "score_home": play.get("homeScore", 0),
                        "score_away": play.get("awayScore", 0)
                    }
                    box_score["scoring"].append(scoring_play)
            
        except Exception as e:
            print(f"Error extracting box score data: {e}")
        
        return box_score
    
    def download_season_games(self, year: int = 2023, output_dir: str = "nflgames") -> None:
        """Download all games from an NFL season and save to individual JSON files.
        
        Args:
            year: NFL season year (default 2023 for last complete season)
            output_dir: Directory to save game files
        """
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")
        
        print(f"\nDownloading all games from {year} NFL season...")
        print("="*60)
        
        total_games_downloaded = 0
        failed_games = []
        
        # NFL season structure:
        # Preseason: 3 weeks (season_type=1)
        # Regular season: 18 weeks (season_type=2)
        # Postseason: 5 weeks (season_type=3)
        
        # For testing, you can limit weeks by modifying these numbers
        season_structure = [
            {"type": 2, "weeks": 18, "name": "Regular Season"},  # Regular season
            {"type": 3, "weeks": 5, "name": "Postseason"}  # Playoffs
        ]
        
        # Quick test mode - uncomment to test with just week 1
        # season_structure = [{"type": 2, "weeks": 1, "name": "Regular Season (Test)"}]
        
        for season_info in season_structure:
            season_type = season_info["type"]
            num_weeks = season_info["weeks"]
            season_name = season_info["name"]
            
            print(f"\n{season_name}:")
            print("-"*40)
            
            for week in range(1, num_weeks + 1):
                print(f"\nWeek {week}:")
                
                # Get scoreboard for this week
                scoreboard = self.get_scoreboard(year=year, season_type=season_type, week=week)
                
                if not scoreboard or "events" not in scoreboard:
                    print(f"  No games found for week {week}")
                    continue
                
                events = scoreboard["events"]
                print(f"  Found {len(events)} games")
                
                for event in events:
                    try:
                        # Extract game info for filename
                        event_id = event["id"]
                        game_date = event.get("date", "")
                        
                        # Parse date for filename
                        date_str = "unknown_date"
                        if game_date:
                            try:
                                dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                                date_str = dt.strftime("%Y%m%d")
                            except (ValueError, AttributeError):
                                date_str = game_date[:10].replace("-", "")
                        
                        # Get team abbreviations
                        away_team = ""
                        home_team = ""
                        if "competitions" in event and event["competitions"]:
                            competitors = event["competitions"][0].get("competitors", [])
                            if len(competitors) >= 2:
                                # ESPN lists teams, need to check homeAway field
                                for competitor in competitors:
                                    if competitor.get("homeAway") == "home":
                                        home_team = competitor["team"]["abbreviation"]
                                    else:
                                        away_team = competitor["team"]["abbreviation"]
                        
                        # Create filename: YYYYMMDD_AWAY_at_HOME.json
                        filename = f"{date_str}_{away_team}_at_{home_team}.json"
                        filepath = os.path.join(output_dir, filename)
                        
                        # Skip if file already exists
                        if os.path.exists(filepath):
                            print(f"    ✓ {away_team} @ {home_team} - Already downloaded")
                            continue
                        
                        # Fetch game summary
                        print(f"    Downloading: {away_team} @ {home_team}...", end="")
                        game_summary = self.get_game_summary(event_id)
                        
                        if game_summary:
                            # Extract clean data
                            clean_game_data = self.extract_clean_game_data(game_summary, event)
                            
                            # Save to file
                            with open(filepath, "w") as f:
                                json.dump(clean_game_data, f, indent=2)
                            
                            print(f" ✓ Saved as {filename}")
                            total_games_downloaded += 1
                            
                            # Small delay to be respectful to the API
                            time.sleep(0.5)
                        else:
                            print(" ✗ Failed to fetch data")
                            failed_games.append(f"{away_team} @ {home_team} (Week {week})")
                    
                    except Exception as e:
                        print(f" ✗ Error: {e}")
                        failed_games.append(f"Game ID {event.get('id', 'unknown')} (Week {week})")
        
        # Print summary
        print("\n" + "="*60)
        print("DOWNLOAD COMPLETE")
        print("="*60)
        print(f"Total games downloaded: {total_games_downloaded}")
        print(f"Files saved to: {output_dir}/")
        
        if failed_games:
            print(f"\nFailed to download {len(failed_games)} games:")
            for game in failed_games:
                print(f"  - {game}")
        
        # List all files in directory
        files = sorted([f for f in os.listdir(output_dir) if f.endswith('.json')])
        print(f"\nTotal files in directory: {len(files)}")
    
    def print_formatted_box_score(self, box_score: Dict):
        """Print a nicely formatted box score.
        
        Args:
            box_score: Extracted box score data
        """
        print("\n" + "="*80)
        print("NFL GAME BOX SCORE")
        print("="*80)
        
        # Game info
        if box_score["game_info"]:
            print(f"\nDate: {box_score['game_info'].get('date', 'N/A')}")
            print(f"Venue: {box_score['game_info'].get('venue', 'N/A')}")
            print(f"Attendance: {box_score['game_info'].get('attendance', 'N/A'):,}")
            print(f"Status: {box_score['game_info'].get('status', 'N/A')}")
        
        # Team scores and stats
        if box_score["team_stats"]:
            print("\n" + "-"*40)
            print("FINAL SCORE")
            print("-"*40)
            for team, stats in box_score["team_stats"].items():
                print(f"{team}: {stats.get('score', 0)} ({stats.get('home_away', '').title()})")
            
            print("\n" + "-"*40)
            print("TEAM STATISTICS")
            print("-"*40)
            
            # Display stats side by side for comparison
            teams = list(box_score["team_stats"].keys())
            if len(teams) >= 2 and all("statistics" in box_score["team_stats"][t] for t in teams):
                team1, team2 = teams[0], teams[1]
                stats1 = box_score["team_stats"][team1].get("statistics", {})
                stats2 = box_score["team_stats"][team2].get("statistics", {})
                
                # Get all stat names
                all_stats = set(stats1.keys()) | set(stats2.keys())
                
                print(f"\n{'Stat':<30} {team1:>10} {team2:>10}")
                print("-" * 52)
                for stat_name in sorted(all_stats):
                    val1 = stats1.get(stat_name, "-")
                    val2 = stats2.get(stat_name, "-")
                    print(f"{stat_name:<30} {str(val1):>10} {str(val2):>10}")
        
        # Scoring plays
        if box_score["scoring"]:
            print("\n" + "-"*40)
            print("SCORING PLAYS")
            print("-"*40)
            for play in box_score["scoring"]:
                print(f"Q{play['quarter']} {play['time']}: {play['team']} - {play['description']}")
                print(f"  Score: Away {play['score_away']} - Home {play['score_home']}")
        
        # Player stats (abbreviated for brevity)
        if box_score["player_stats"]:
            print("\n" + "-"*40)
            print("TOP PERFORMERS")
            print("-"*40)
            for team, categories in box_score["player_stats"].items():
                print(f"\n{team}:")
                for category, players in categories.items():
                    if players and len(players) > 0:
                        print(f"  {category}: {players[0]['name']} ({players[0]['position']})")
                        break  # Just show first player per category for brevity


def main():
    # Initialize the NFL data fetcher
    fetcher = NFLDataFetcher()
    
    print("NFL Data Fetcher - Using ESPN's Public API")
    print("="*50)
    
    # Check if user wants to download full season or just examples
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "download-season":
        # Download full season mode
        year = 2023  # Last complete season
        if len(sys.argv) > 2:
            try:
                year = int(sys.argv[2])
            except ValueError:
                print(f"Invalid year: {sys.argv[2]}, using 2023")
        
        fetcher.download_season_games(year=year)
        return
    
    # Default mode: Show examples
    print("\n1. Fetching recent NFL games from 2024 season...")
    scoreboard = fetcher.get_scoreboard(year=2024, season_type=2, week=1)
    
    if scoreboard and "events" in scoreboard:
        events = scoreboard["events"]
        print(f"Found {len(events)} games")
        
        # Show first few games
        for i, event in enumerate(events[:3], 1):
            print(f"\nGame {i}:")
            competitors = event.get("competitions", [{}])[0].get("competitors", [])
            if len(competitors) >= 2:
                away_team = competitors[0]["team"]["abbreviation"]
                home_team = competitors[1]["team"]["abbreviation"]
                away_score = competitors[0].get("score", "0")
                home_score = competitors[1].get("score", "0")
                event_id = event["id"]
                print(f"  {away_team} @ {home_team}: {away_score}-{home_score}")
                print(f"  Event ID: {event_id}")
                print(f"  Date: {event.get('date', 'N/A')}")
                print(f"  Status: {event.get('status', {}).get('type', {}).get('description', 'N/A')}")
        
        # Example 2: Get detailed box score for the first game
        if events:
            print("\n" + "="*50)
            print("2. Fetching detailed box score for the first game...")
            first_event = events[0]
            first_event_id = first_event["id"]
            
            # Get game summary with box score
            game_summary = fetcher.get_game_summary(first_event_id)
            
            if game_summary:
                # Extract and print formatted box score
                box_score = fetcher.extract_box_score_data(game_summary)
                fetcher.print_formatted_box_score(box_score)
                
                # Save CLEAN data (not raw) to file
                clean_game_data = fetcher.extract_clean_game_data(game_summary, first_event)
                with open("game_summary.json", "w") as f:
                    json.dump(clean_game_data, f, indent=2)
                print("\n[Clean box score data saved to game_summary.json]")
            
            # Example 3: Get play-by-play data
            print("\n" + "="*50)
            print("3. Fetching play-by-play data (first 10 plays)...")
            plays_data = fetcher.get_play_by_play(first_event_id, limit=10)
            
            if plays_data and "items" in plays_data:
                print(f"Retrieved {len(plays_data['items'])} plays")
                for i, play in enumerate(plays_data["items"][:5], 1):
                    # Handle different play data structures
                    if isinstance(play, dict):
                        # Try to get text from various possible locations
                        if "text" in play:
                            if isinstance(play["text"], dict):
                                play_text = play["text"].get("shortText", play["text"].get("text", "N/A"))
                            else:
                                play_text = play["text"]
                        else:
                            play_text = play.get("description", play.get("play", {}).get("text", "N/A"))
                    else:
                        play_text = str(play)
                    print(f"  Play {i}: {play_text}")
    else:
        print("No games found or error fetching data")
        print("\nTrying with a different week...")
        
        # Try week 10 as fallback
        scoreboard = fetcher.get_scoreboard(year=2023, season_type=2, week=10)
        if scoreboard and "events" in scoreboard:
            print(f"Found {len(scoreboard['events'])} games from 2023 Week 10")
    
    print("\n" + "="*50)
    print("Note: This uses ESPN's public API endpoints.")
    print("\nTo download all games from a season, run:")
    print("  uv run main.py download-season [year]")
    print("\nExample:")
    print("  uv run main.py download-season 2023")
    print("\nThis will save all games to the 'nflgames' folder.")


if __name__ == "__main__":
    main()
