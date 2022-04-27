import openrouteservice
import os, json
import pprint
import time

# Enter your API key
client_net = openrouteservice.Client(key='')

json_files = [pos_json for pos_json in os.listdir('.') if pos_json.endswith('.json')]

station_prices = []

req_count = 0

for file in json_files:
    with open(file) as json_file:
        if req_count > 99:
            req_count = 0
            print('waiting...')
            time.sleep(61)
            print('continuing...')

        json_text = json.load(json_file)
        for station in json_text['data']['locationBySearchTerm']['stations']['results']:
            station_dict = { 'address': station['address']['line_1'] + ' ' + station['address']['locality'] + ' ' + station['address']['region'], 'price': station['prices'][0]['credit']['price'] }
            station_dict['coordinates'] = client_net.pelias_search(station_dict['address'])['features'][0]['geometry']['coordinates']
            req_count = req_count + 1
            station_prices.append(station_dict)

out_file = open('station_prices.json', 'w')

json.dump(station_prices, out_file)

out_file.close()
