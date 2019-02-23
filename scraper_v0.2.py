import bs4 as bs
import requests
import json
import time
import datetime as dt
import authentication as auth
from twilio.rest import Client

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
    all_results = []
    for i in range(len(url_list)):
        print('Getting {} data'.format(name_list[i]))
        # Get league webpage
        sauce = req_get(url_list[i])
        # Convert to json
        script_json = convert_to_json(sauce)
        # Get a list of games with arbitrage opportunities
        results_list = get_games_data(script_json)
        all_results.append(results_list)
    return all_results

def convert_bookmaker(code):
    if code == 'PO':
        return 'POINTSBET'
    elif code == 'B3':
        return 'BET365'
    elif code == 'CR':
        return 'BETEASY'
    elif code == 'SP':
        return 'SPORTSBET'
    elif code == 'TF':
        return 'TABSPORTS'
    elif code == 'LA':
        return 'LADBROKES'
    elif code == 'UA':
        return 'UNIBET'
    elif code == 'PB':
        return 'PALMERBET'
    elif code == 'TP':
        return 'TOPBETTA'
    elif code == 'CS':
        return 'CLASSICBET'
    elif code == 'TS':
        return 'TOPSPORT'
    elif code == 'ST':
        return 'BETSTAR'
    elif code == 'BM':
        return 'BOOKMAKER'
    elif code == 'BF':
        return 'BETFAIR'
    else:
        return code

def pick_data_to_send(league_results):
    if len(league_results) > 0:
        message = ''
        for i in range(len(league_results)):
            for j in range(len(league_results[i])):
                team_a = league_results[i][j][1][0]['name']
                odds_a = league_results[i][j][1][0]['odds']
                where_a = convert_bookmaker(league_results[i][j][1][0]['where'])
                team_b = league_results[i][j][1][1]['name']
                odds_b = league_results[i][j][1][1]['odds']
                where_b = convert_bookmaker(league_results[i][j][1][1]['where'])
                odds = str(round(1 / league_results[i][j][2]['total_odds'], 4))
                bet_a = str(round(100 * odds_b / (odds_a + odds_b), 2))
                bet_b = str(round(100 * odds_a / (odds_a + odds_b), 2))
                message += team_a + ' ' + where_a + ' ' + str(odds_a) + ' ' + bet_a + '-'
                message += team_b + ' ' + where_b + ' ' + str(odds_b) + ' ' + bet_b + ' '
                message += odds + '*'
    return message

def whats_message(message, account_sid, auth_token, client):
    message = dt.datetime.now().strftime('%m-%d %H:%M') + ' ' + message
    message_length = len(message)
    print(message_length)
    if message_length > 140:
        number_of_messages = int(message_length / 140) + 1
        for i in range(number_of_messages):
            message_limited = message[140*i:140*i+140]
            whats = client.messages.create(
                    body=message_limited,
                    from_='whatsapp:+14155238886',
                    to='whatsapp:+61404320180')
            print('Message sent: ' + whats.sid)
    else:
        whats = client.messages.create(
                body=message,
                from_='whatsapp:+14155238886',
                to='whatsapp:+61404320180')
        print('Message sent: ' + whats.sid)

url = ['https://www.oddschecker.com/au/tennis',\
'https://www.oddschecker.com/au/basketball', 'https://www.oddschecker.com/au/boxing-mma/ufc-mma']
minutes = 30

account_sid = auth.sid()
auth_token = auth.token()
client = Client(account_sid, auth_token)
default_message = 'No opportunities found'
count = 0
while True:
    count += 1
    print(dt.datetime.now())
    print('Iteration %d' % (count))
    message = ''
    for j in range(len(url)):
        league_results = scrap(url[j])
        message += pick_data_to_send(league_results)
    if len(message) > 0:
        print(message)
        whats_message(message, account_sid, auth_token, client)
    else:
        print(default_message)
        whats_message(default_message, account_sid, auth_token, client)
    print('Sleep for %d minutes' % minutes)
    for i in range(5):
        time.sleep(minutes*12)
        print('%.2f minutes' % (i * minutes / 5))
