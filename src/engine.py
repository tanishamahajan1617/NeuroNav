import osmnx as ox
import networkx as nx
import get_map
import traceback
from geopy.geocoders import Nominatim
from scipy.spatial import cKDTree  
class NeuroRoutingEngine:
    def __init__(self, city_name):
        self.city_name = city_name
        print(f" Initializing Smart Engine for {city_name}...")
        self.G = get_map.load_or_download_map(city_name)
        
        self.geolocator = Nominatim(user_agent="NeuroNav_Pathankot_App")

        self.known_places = {
            "pathankot cantt": (32.2475, 75.6455),
            "pathankot junction": (32.2733, 75.6522),
            "bus stand": (32.2683, 75.6521),
            "environment park": (32.2705, 75.6552)
        }

        # 🧠 CUSTOM LIGHTNING FAST KD-TREE (Built ONCE)
        print(" Building Smart Map Index... (Takes 2 seconds)")
        nodes_data = {n: (d['x'], d['y']) for n, d in self.G.nodes(data=True)}
        self.node_ids = list(nodes_data.keys())
        self.node_coords = list(nodes_data.values())
        self.kdtree = cKDTree(self.node_coords) # Map ke saare coordinates ka smart tree
        print("Index Built Successfully!")

    def get_coords_from_text(self, place_text):
        if isinstance(place_text, (tuple, list)):
            return place_text
            
        clean_text = str(place_text).lower().strip()
        if clean_text in self.known_places:
            print(f" Instant Match Found for '{place_text}' in Local Data!")
            return self.known_places[clean_text]

        try:
            query = f"{place_text}, Pathankot, Punjab, India"
            print(f" Searching Internet for: {query}...")
            location = self.geolocator.geocode(query, timeout=10)
            
            if location:
                print(f" Found: {location.address}")
                return (location.latitude, location.longitude)
            else:
                print(f" Could not find exact location for: {place_text}")
                return None
        except Exception as e:
            print(f" Internet Search failed: {e}")
            return None

    def get_route_by_text(self, start_text, end_text):
        print("\n--- Step 1: Understanding Locations ---")
        start_raw = self.get_coords_from_text(start_text)
        end_raw = self.get_coords_from_text(end_text)

        if not start_raw: start_raw = self.known_places["pathankot cantt"]
        if not end_raw: end_raw = self.known_places["pathankot junction"]

        def force_num(val, as_int=False):
            while True:
                if isinstance(val, (list, tuple)): val = val
                elif hasattr(val, 'item'): val = val.item()
                else: break
            return int(val) if as_int else float(val)

        try:
            print("\n--- Step 2: Finding Nearest Roads (Custom Fast Search) ---")
            lat1, lng1 = force_num(start_raw), force_num(start_raw)
            lat2, lng2 = force_num(end_raw), force_num(end_raw)

            # 🚀 MILLISECOND SEARCH USING CUSTOM KD-TREE
            _, orig_idx = self.kdtree.query((lng1, lat1))
            _, dest_idx = self.kdtree.query((lng2, lat2))
            
            orig_node = self.node_ids[orig_idx]
            dest_node = self.node_ids[dest_idx]
            print(f" Snapped to nearest roads instantly!")

            print("\n--- Step 3: Calculating Smart Path (A-Star Algorithm) ---")
            route_nodes = nx.astar_path(self.G, orig_node, dest_node, weight='length')
            
            route_coords = [[force_num(self.G.nodes[n]['x']), force_num(self.G.nodes[n]['y'])] for n in route_nodes]
            
            print(f" Route Success! Generated {len(route_coords)} GPS points for the map.")
            return route_coords

        except nx.NetworkXNoPath:
            print(" No path found between these two locations.")
            return None
        except Exception as e:
            print(f" Routing Logic Error: {e}")
            traceback.print_exc()
            return None

if __name__ == "__main__":
    TARGET = "Pathankot, Punjab, India"
    engine = NeuroRoutingEngine(TARGET)

    START_PLACE = "Pathankot Cantt"  
    END_PLACE = "Pathankot Junction"

    path = engine.get_route_by_text(START_PLACE, END_PLACE)

