from numpy import place
import osmnx as ox

def download_map():
    place = "New York, NY, USA"
    G = ox.graph_from_place(place, network_type='drive')
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    
    ox.save_graphml(G, 'data/new_york_drive.graphml')


if __name__ == "__main__":
    download_map()
