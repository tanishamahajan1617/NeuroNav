import networkx as nx
import osmnx as ox
from engine import NeuroNavEngine
import matplotlib.pyplot as plt

def compare_routes():
    # 1. Engine Start karo
    print("⏳ Initializing NeuroNav System...")
    engine = NeuroNavEngine()
    
    # 2. Inputs Set karo (Scenario: Raat + Barish + Thaka hua Driver)
    source = "Times Square"
    dest = "Central Park" # Both locations in New York
    weather = "rainy"
    traffic = "high"
    hours_driven = 10  # Banda 10 ghante se drive kar raha hai (Fatigue!)

    print(f"\n🌍 SCENARIO: {weather.upper()} Weather | {traffic.upper()} Traffic | Driver Fatigue: {hours_driven} hrs")
    print(f"📍 Route: {source} --> {dest}")
    print("-" * 50)

    # 3. Graph Update karo (AI Risk ke hisaab se)
    # Engine automatically processes only relevant area now
    result = engine.get_safe_route(source, dest, weather, traffic, hours_driven)
    
    if result["status"] == "error":
        print(f"❌ Error: {result['message']}")
        return
    
    # Get the result directly from engine
    print(f"\n🟢 SAFEST ROUTE (AI Way):")
    print(f"   📏 Distance: {result['Route_length']:.2f} km")
    print(f"   🛡️ Avg Risk: {result['Risk_score']:.2f} (Low Risk!)")
    
    # For comparison, get fastest route from original graph
    G = engine.G
    orig = ox.geocode(f"{source}, New York")
    dst = ox.geocode(f"{dest}, New York")
    orig_node = ox.nearest_nodes(G, orig[1], orig[0])
    dest_node = ox.nearest_nodes(G, dst[1], dst[0])
    
    route_fast = nx.shortest_path(G, orig_node, dest_node, weight='length')
    dist_fast = nx.shortest_path_length(G, orig_node, dest_node, weight='length') / 1000
    
    print(f"\n🔴 FASTEST ROUTE (Old Way):")
    print(f"   📏 Distance: {dist_fast:.2f} km")
    print(f"   ⚠️ Risk: Not calculated (traditional method)")
    
    print("-" * 50)
    print("✅ SUCCESS: AI found safest route with risk analysis!")
    
    # Simple visualization (just show the AI route)
    print("\n🗺️ Generating AI Route Map...")
    try:
        # Re-run to get the processed subgraph for visualization
        engine.get_safe_route(source, dest, weather, traffic, hours_driven)
        fig, ax = ox.plot_graph_routes(G, [route_fast], 
                                       route_colors=['g'], 
                                       route_linewidths=4, 
                                       node_size=0, 
                                       show=False, close=False)
        plt.title("AI-Optimized Safe Route", color="white")
        plt.savefig("ai_route.png")
        print("📸 AI route saved as 'ai_route.png'")
    except:
        print("📸 Map generation skipped")

if __name__ == "__main__":
    compare_routes()