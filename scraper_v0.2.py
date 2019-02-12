import bs4 as bs
import requests
import pprint
import json
import time
import datetime as dt

# Calculates combined odds
def calc_arb(game):
    odds_team_a = game[0]['odds']
    odds_team_b = game[1]['odds']
    calc = (1/odds_team_a) + (1/odds_team_b)
    return calc

# Gets webpage in requests format
# url: single url
def req_get(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    retry = True
    retries = 0
    while retry:
        try:
            sauce = requests.get(url, headers=headers)
            retry = False
        except requests.exceptions.RequestException as e:
            print(e)
            retries +=1
            print('Retries: %d' % retries)
            time.sleep(60)
    return sauce

# Converts webpage to json format
# sauce: webpage in requests format
def convert_to_json(sauce):
    soup = bs.BeautifulSoup(sauce.text, 'lxml')
    scripts = soup.findAll('script', {'id':'initial-data'})
    script_text = scripts[0].text
    script_json = json.loads(script_text)
    return script_json

# From webpage in json, returns a list of urls
# Ex: from basketball webpage, returns all basketball leagues
# script_json: webpage in json
def create_url_list(script_json):
    base_url = script_json['config']['baseUrl']
    url_list = []
    name_list = []
    for i in range(len(script_json['nav']['eventMenu']['select']['menu'])):
        name_list.append(script_json['nav']['eventMenu']['select']['menu'][i]['name'])
        comp_url = script_json['nav']['eventMenu']['select']['menu'][i]['url']
        url_list.append(base_url + comp_url)
    return url_list, name_list

# From webpage in json, returns a list of games with arbitrage opportunities
# Ex: from NBA league, returns all games with arbitrage opportunities
# script_json: webpage in json
def get_games_data(script_json):
    results = []
    if 'card' in script_json.keys():
        if len(script_json['card']['matches']) > 0:
            for j in range(len(script_json['card']['matches'][0]['cards'][0]['data'])):
                game_data = []
                if len(script_json['card']['matches'][0]['cards'][0]['data'][j]['bets']) == 2:
                    odds_total = 1.0
                    for i in range(2):
                        temp = script_json['card']['matches'][0]['cards'][0]['data'][j]['bets'][i]
                        odds_data = {}
                        odds_data['name'] = temp['name']
                        odds_data['odds'] = temp['bestOddsDecimal']
                        odds_data['where'] = temp['bestOddsBookmakers']
                        game_data.append(odds_data)
                    odds_total = calc_arb(game_data)
                    if odds_total < 1.0:
                        game_info = {'arbitrage': True, 'total_odds': odds_total}
                        timestamp = str(dt.datetime.now())
                        result = [timestamp, game_data, game_info]
                        results.append(result)
    return results

def save_data(data, type):
    with open('data/data_{}.json'.format(type), 'a') as f:
        json.dump(data, f)

# For each sport, returns all arbitrage opportunities
# url: sport url
def scrap(url):
    # Get sport main webpage
    sauce = req_get(url)
    # Convert to json
    script_json = convert_to_json(sauce)
    # Get a list of urls and league names
    url_list, name_list = create_url_list(script_json)
    # Cycle thru all lists
    for i in range(len(url_list)):
        print('Getting {} data'.format(name_list[i]))
        # Get league webpage
        sauce = req_get(url_list[i])
        # Convert to json
        script_json = convert_to_json(sauce)
        # Get a list of games with arbitrage opportunities
        results_list = get_games_data(script_json)
        if len(results_list) > 0:
            save_data(results_list, 'all')

url = ['https://www.oddschecker.com/au/tennis',\
'https://www.oddschecker.com/au/basketball', 'https://www.oddschecker.com/au/boxing-mma/ufc-mma']
minutes = 29
for i in range(48):
    print('Iteration %d of 48' % (i+1))
    for j in range(len(url)):
        scrap(url[j])
        time.sleep(1)
    print('Sleep for %d minutes' % minutes)
    time.sleep(minutes*60)
