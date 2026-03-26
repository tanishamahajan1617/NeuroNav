import osmnx as ox
import networkx as nx
import get_map
import traceback  # Yeh humein batayega error exactly kahan hai!

class NeuroRoutingEngine:
    def __init__(self, city_name):
        self.city_name = city_name
        print(f"Initializing Smart Engine for {city_name}...")
        self.G = get_map.load_or_download_map(city_name)

    def get_coords_from_text(self, place_text):
        try:
            query = f"{place_text}, Pathankot"
            print(f"Searching for: {query}")
            return ox.geocode(query)
        except:
            print(f" Search failed for: {place_text}")
            return None

    def get_route_by_text(self, start_text, end_text):
        start_raw = self.get_coords_from_text(start_text)
        end_raw = self.get_coords_from_text(end_text)

        # Fallback agar search fail ho (Pathankot points)
        if not start_raw: start_raw = (32.2475, 75.6455) 
        if not end_raw: end_raw = (32.2733, 75.6522)

        # --- THE DRILL-DOWN TOOL ---
        # Yeh chahe list ho, tuple ho ya numpy array... andar ghus kar number nikalega
        def force_num(val, as_int=False):
            while True:
                if isinstance(val, (list, tuple)):
                    val = val  # Agar list/tuple hai toh pehla element lo
                elif hasattr(val, 'item'):
                    val = val.item()  # Agar numpy array hai toh item() se pure number nikalo
                else:
                    break
            return int(val) if as_int else float(val)

        try:
            # 1. Drill-down Lat & Lng
            lat1, lng1 = force_num(start_raw), force_num(start_raw)
            lat2, lng2 = force_num(end_raw), force_num(end_raw)

            # 2. Find Nearest Nodes
            orig_raw = ox.distance.nearest_nodes(self.G, X=lng1, Y=lat1)
            dest_raw = ox.distance.nearest_nodes(self.G, X=lng2, Y=lat2)
            
            # 3. Drill-down Node IDs
            orig_node = force_num(orig_raw, as_int=True)
            dest_node = force_num(dest_raw, as_int=True)

            print(f" Start Node: {orig_node}, End Node: {dest_node}")

            # 4. Dijkstra Algorithm
            route_nodes = nx.shortest_path(self.G, orig_node, dest_node, weight='length')
            
            # 5. Get GPS Coordinates for Map
            route_coords = [[force_num(self.G.nodes[n]['x']), force_num(self.G.nodes[n]['y'])] for n in route_nodes]
            
            print(f"Route Success! Total points: {len(route_coords)}")
            return route_coords

        except Exception as e:
            print(f"  Routing Logic Error: {e}")
            print("--- DETAILED ERROR LOG ---")
            traceback.print_exc()  # Yeh ab humein exact line batayega!
            print("--------------------------")
            return None

if __name__ == "__main__":
    TARGET = "Pathankot, Punjab, India"
    engine = NeuroRoutingEngine(TARGET)

    START_PLACE = "Pathankot Cantt"  
    END_PLACE = "Pathankot Junction"

    path = engine.get_route_by_text(START_PLACE, END_PLACE)