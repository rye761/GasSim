import openrouteservice
import folium
import random
import json
import pprint
import os

def rand_coord_in_range(x, y):
    x_int = int(x * 10000000)
    y_int = int(y * 10000000)
    rand = random.randrange(min(x_int, y_int), max(x_int, y_int))
    return rand / 10000000


LONDON_BBOX = [[-81.398485, 43.006537], [-81.122701, 42.945282]]

"""
client_local = openrouteservice.Client(base_url='http://localhost:5000') # Specify your personal API key

pois = client_local.places(request='pois', bbox=LONDON_BBOX, filter_category_ids=[596], validate=False)

station_locations = [station['geometry']['coordinates'] for station in pois['features']]
"""

# get locations and prices from pre-made json file

price_file = open('station_prices_reduced_network.json')

price_data = json.load(price_file)

print(str(len(price_data)))

station_locations = [station['coordinates'] for station in price_data]

true_costco_index = next((z for z, st in enumerate(price_data) if st['price'] == 159.9), -1)

client_local_ors = openrouteservice.Client(base_url='http://localhost:8080/ors')

def simulate_best_station():
    vehicle_category = random.random() # generate a random between 0 and 1 and use tranches to determine vehicle type

    if vehicle_category < .17:
        # Vehicle is a truck
        BASE_FILL_L = 95 * 0.8
        FUEL_BURN_L_PER_100KM = 14
    elif vehicle_category < (.17 + .47):
        # Vehicle is an SUV
        BASE_FILL_L = 60 * 0.8
        FUEL_BURN_L_PER_100KM = 9
    elif vehicle_category < (.17 + .47 + .29):
        # Vehicle is a car
        BASE_FILL_L = 45 * 0.8
        FUEL_BURN_L_PER_100KM = 7
    else:
        # Vehicle is a van
        BASE_FILL_L = 76 * 0.8
        FUEL_BURN_L_PER_100KM = 12

    starting_location = [rand_coord_in_range(LONDON_BBOX[0][0], LONDON_BBOX[1][0]), rand_coord_in_range(LONDON_BBOX[0][1], LONDON_BBOX[1][1])]

    temp_station_locations = station_locations.copy()
    temp_price_data = price_data.copy()

    removed_costco = False
    if random.random() < (1.0 if os.getenv('REMOVE_COSTCO', False) else 0.5):
        temp_station_locations.pop(true_costco_index)
        temp_price_data.pop(true_costco_index)
        removed_costco = True

    locations = [starting_location] + temp_station_locations

    matrix = client_local_ors.distance_matrix(locations=locations, destinations=list(range(1, len(locations))), sources=[0], profile='driving-car', metrics=['distance'], validate=False)

    closest_station_index = matrix['distances'][0].index(min(matrix['distances'][0]))

    cost_matrix = []
    fuel_burn_matrix = []

    for i in range(len(temp_price_data)):
        station = temp_price_data[i]
        base_cost = BASE_FILL_L * station['price']
        on_route_fuel_burn = matrix['distances'][0][i] / 1000 / 100 * FUEL_BURN_L_PER_100KM * 2 # the distance is in meters so we convert to km, then we see what portion of 100 that is multiplied by fuel burn. We multiply by 2 to consider the return fuel burn
        on_route_fuel_cost = on_route_fuel_burn * station['price']
        total_fuel_cost = on_route_fuel_cost + base_cost
        cost_matrix.append(total_fuel_cost)
        fuel_burn_matrix.append(on_route_fuel_burn + BASE_FILL_L)

    lowest_cost_station_index = cost_matrix.index(min(cost_matrix))

    # note that the map will show the last route decision where this function was run multiple times
    # we use reversed here to reverse coords because the map uses lat, lon and the rest of the apis use lon,lat
    m = folium.Map(location=list(reversed(starting_location)))

    folium.Marker(location=list(reversed(starting_location)), popup="starting point", icon=folium.Icon(color="green")).add_to(m)

    folium.Marker(location=list(reversed(temp_station_locations[closest_station_index])), popup="Nearest station \n Price: " + str(temp_price_data[closest_station_index]['price']), icon=folium.Icon(color="blue")).add_to(m)
    folium.Marker(location=list(reversed(temp_station_locations[lowest_cost_station_index])), popup="Cheapest station \n Price: " + str(temp_price_data[lowest_cost_station_index]['price']), icon=folium.Icon(color="red")).add_to(m)


    m.save('map.html')

    return { 'nearest_price': temp_price_data[closest_station_index]['price'], 'cheapest_price': temp_price_data[lowest_cost_station_index]['price'], 'additional_burn_l': fuel_burn_matrix[lowest_cost_station_index] - fuel_burn_matrix[closest_station_index], 'total_savings': (cost_matrix[closest_station_index] - cost_matrix[lowest_cost_station_index]) / 100, 'nearest_is_best': closest_station_index == lowest_cost_station_index, 'costco_is_best': lowest_cost_station_index == true_costco_index and not removed_costco }

total_additional_burn = 0
total_savings = 0
nearest_best = 0
costco_best = 0

TOTAL_RUNS = 10000

for run in range(TOTAL_RUNS):
    result = simulate_best_station()
    total_additional_burn += result['additional_burn_l']
    total_savings += result['total_savings']
    if result['nearest_is_best']:
        nearest_best += 1
    if result['costco_is_best']:
        costco_best += 1

print('The total additional fuel burn was ' + str(total_additional_burn) + ' which saved consumers $' + str(round(total_savings, 2)) + ' a lower-priced station was optimal for ' + str(round((1 - (nearest_best / TOTAL_RUNS)) * 100, 1)) + ' % of drivers. ' + str(round(costco_best / TOTAL_RUNS * 100, 1)) + ' % of drivers would choose costco.')
