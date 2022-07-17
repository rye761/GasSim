# Gas filling simulation

## Usage

In order to run the simulation, you must setup docker and start up the openrouteservice which has been included as a sub-repo. This is what is used to calculate distance to each of the gas stations. You can also modify to use openrouteservice's online service, but this will limit the number of simulations. Also setup a virtual environment with the following packages:

- folium
- openrouteservice

## Data Credits

The data is either from openrouteservice or Gas Buddy in the case of prices. This application does not retrieve gas prices. Some miscellaneous facts come from statscan, fuelly, etc. The included excel file has data sources.
