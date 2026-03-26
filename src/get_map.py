import osmnx as ox
import os
import pandas as pd
import geopandas as gpd

try:
    import pydeck as pdk
except ImportError:
    print("Please install pydeck and geopandas: pip install pydeck pandas geopandas")
    raise
def load_or_download_map(place_name):
    """
    Sirf place_name ke basis par map download ya load karta hai.
    Cache file ka naam automatically generate hota hai.
    """
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        
    # YAHAN FIX KIYA GAYA HAI: add kar diya
    shabdon_ki_list = place_name.split(',')
    safe_city_name = shabdon_ki_list[0].strip().replace(" ", "_").lower()
    dynamic_filename = f"{safe_city_name}_drive.graphml"
    
    file_path = os.path.join(cache_dir, dynamic_filename)
    
    if os.path.exists(file_path):
        print(f"Loading map from cache: {file_path}...")
        G = ox.load_graphml(file_path)
    else:
        print(f"Downloading road graph for {place_name}...")
        G = ox.graph_from_place(place_name, network_type='drive')
        ox.save_graphml(G, file_path)
        print("Map downloaded and saved!")
    
    return G

def prepare_data_for_pydeck(G):
    """NetworkX graph ko GeoDataFrame mein convert karna (Same as before)"""
    print("Preparing road data for 3D visualization...")
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
    
    edges_df = gdf_edges[['name', 'length', 'geometry']].copy()
    edges_df.reset_index(drop=True, inplace=True)
    return edges_df, gdf_nodes

def visualize_map_free_trendy(edges_data, nodes_data, place_name):
     
    print(f"Generating dark mode map for {place_name}...")

    city_lat = nodes_data['y'].mean()
    city_lng = nodes_data['x'].mean()

    # 1. Road Layer (Neon Green)
    road_layer = pdk.Layer(
        "GeoJsonLayer",
        edges_data,
        pickable=True,
        stroked=True,
        filled=False,
        get_line_width=3, 
        get_line_color=[0, 255, 0],  # Yeh raha hamara Neon Green!
        opacity=0.8,
    )

    view_state = pdk.ViewState(
        latitude=city_lat,
        longitude=city_lng,
        zoom=13,
        pitch=45, 
        bearing=0
    )

    # 2. Dark Mode Settings
    r = pdk.Deck(
        layers=[road_layer],
        initial_view_state=view_state,
        map_provider='carto',           
        map_style='https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json', # Direct style link
        tooltip={"text": "Road: {name}"},
        # Background ko forcefully black karne ke liye
        parameters={
            "backgroundColor": 
         [0, 0, 0, 255] } # RGBA format mein pure black
    )
    shabdon_ki_list = place_name.split(',')
    safe_city_name = shabdon_ki_list[0].strip().replace(" ", "_").lower()

    output_html = f"{safe_city_name}_free_trendy_map.html"
    
    r.to_html(output_html, open_browser=True)
    print(f"Success! Map saved as {output_html} and opening in your browser.")
# --- Test System ---
if __name__ == "__main__":
    # Ab aap yahan koi bhi city daalengi, map automatically wahan center ho jayega!
    TARGET_CITY = "Pathankot, Punjab, India" 
    
    # 1. Map load karo
    city_graph = load_or_download_map(place_name=TARGET_CITY)
    
    # 2. Data process karo (Ab humein dono edges aur nodes chahiye)
    prepared_edges, prepared_nodes = prepare_data_for_pydeck(city_graph)
    
    # 3. Dynamic map open karo
    visualize_map_free_trendy(prepared_edges, prepared_nodes, TARGET_CITY)

# --- Test System ---
if __name__ == "__main__":
    # 1. Map load karo
    TARGET_CITY = "Pathankot, Punjab, India" 
    city_graph = load_or_download_map(place_name=TARGET_CITY)
    
    # 2. Data process karo
    prepared_edges, _ = prepare_data_for_pydeck(city_graph)
    
    # 3. BINA token ke trendy map open karo
    visualize_map_free_trendy(prepared_edges, _, TARGET_CITY)
