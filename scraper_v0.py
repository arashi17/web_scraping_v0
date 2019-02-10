import bs4 as bs
import requests
import pprint
import json
import time

def calc_arb(game):
    odds_team_a = game[0]['odds']
    odds_team_b = game[1]['odds']
    calc = (1/odds_team_a) + (1/odds_team_b)
    return calc

def scrap(url):
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

    soup = bs.BeautifulSoup(sauce.text, 'lxml')
    scripts = soup.findAll('script', {'id':'initial-data'})
    script_text = scripts[0].text
    script_json = json.loads(script_text)
    results = []
    if len(script_json['card']['matches']) > 0:
        for j in range(len(script_json['card']['matches'][0]['cards'][0]['data'])):
            game_data = []
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
            else:
                game_info = {'arbitrage': False, 'total_odds': odds_total}
            game_data.append(game_info)
            results.append(game_data)
    return results

def save_data(data, type):
    with open('data/data_{}.json'.format(type), 'a') as f:
        json.dump(data, f)

url_nba = 'https://www.oddschecker.com/au/basketball/nba'
url_nbl = 'https://www.oddschecker.com/au/basketball/nbl'
url_ncaab = 'https://www.oddschecker.com/au/basketball/ncaab'

for i in range(48):
    print('Iteration %d of 48' % (i+1))
    print('Getting NBA data')
    res = scrap(url_nba)
    save_data(res, 'nba')
    print('Sleep for 2 min')
    time.sleep(60*2)
    print('Getting NBL data')
    res = scrap(url_nbl)
    save_data(res, 'nbl')
    print('Sleep for 2 min')
    time.sleep(60*2)
    print('Getting NBA data')
    res = scrap(url_ncaab)
    save_data(res, 'ncaab')
    print('Sleep for 26 min')
    time.sleep(60*26)
