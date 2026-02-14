import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import osmnx as ox
import networkx as nx
import tensorflow as tf
import joblib
import numpy as np

class NeuroNavEngine:
    def __init__(self):
        self.G = ox.load_graphml('data/new_york_drive.graphml')
        self.model = tf.keras.models.load_model('data/driver_risk_model.h5')
        self.le_road = joblib.load('data/le_road.pkl')
        self.le_weather = joblib.load('data/le_weather.pkl')
        self.traffic = joblib.load('data/le_traffic.pkl')

    def get_safe_route(self, source , dest , weather,traffic,hours_driven):
        try:
            w_val = self.le_weather.transform([weather])[0]
            t_val = self.traffic.transform([traffic])[0]
        except:
            w_val ,t_val = 0,0

        # First find the route area to limit processing
        try:
            orig = ox.geocode(f"{source}, NY")
            dest_coords = ox.geocode(f"{dest}, NY")
            orig_node = ox.nearest_nodes(self.G, orig[1], orig[0])
            dest_node = ox.nearest_nodes(self.G, dest_coords[1], dest_coords[0])
            
            # Get subgraph around the route area (much smaller)
            route_nodes = set(nx.shortest_path(self.G, orig_node, dest_node, weight='length'))
            subgraph_nodes = set()
            for node in route_nodes:
                subgraph_nodes.update(self.G.neighbors(node))
            subgraph_nodes.update(route_nodes)
            
            # Create subgraph for processing
            G_sub = self.G.subgraph(subgraph_nodes).copy()
            
        except Exception as e:
            print(f"Error finding route area: {e}")
            return {"status": "error", "message": str(e)}

        # Update only edges in subgraph with risk scores
        for u, v, k, data in G_sub.edges(data=True, keys=True):
            rtype = data.get('highway', 'primary')
            if isinstance(rtype, list):
                rtype = rtype[0]
            try:
                r_val = self.le_road.transform([rtype])[0]
            except:
                r_val = 0

            speed = float(data.get('maxspeed', 30)) if isinstance(data.get('maxspeed'), (int, float)) else 30
            features = np.array([[r_val, speed, w_val, t_val, hours_driven]])
            risk = self.model.predict(features ,verbose=0)[0][0]
            fatigue_penalty = 20 if hours_driven > 8 else 5
            
            G_sub[u][v][k]['safety_cost'] = data['length'] * (1 + risk + fatigue_penalty)
            G_sub[u][v][k]['risk_score'] = float(risk)

        # Find the safest route in subgraph
        try:
            route = nx.shortest_path(G_sub, orig_node, dest_node, weight='safety_cost')
            total_dist = nx.shortest_path_length(G_sub, orig_node, dest_node, weight='length')
            avg_risk = np.mean([G_sub[u][v][0]['risk_score'] for u, v in zip(route[:-1], route[1:])])

            return {
                "Route_length": round(total_dist/1000, 2),
                "Risk_score": round(float(avg_risk), 2),
                "status": "success"
            }
        except Exception as e:
            print(f"Error finding route: {e}")
            return {"status": "error", "message": str(e)}