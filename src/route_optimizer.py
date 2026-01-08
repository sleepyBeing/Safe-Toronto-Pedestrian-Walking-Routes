import osmnx as ox
import geopandas as gpd
from pathlib import Path
import math 
import heapq
import networkx as nx

gpkg = (Path.cwd() / "data" / "processed" / "toronto_walk.gpkg").resolve()
edges_risk = gpd.read_file(gpkg, layer = "edges_with_risk")

graphml = (Path.cwd() / "data" / "processed" / "toronto_walk_clean.graphml").resolve()
graph = ox.load_graphml(graphml)

lookup = edges_risk.set_index(edges_risk["osmid"].astype(str))["risk"].to_dict()

# attach the risk of each street segment to the graph's edges
miss = 0
for u, v, k, data in graph.edges(keys = True, data = True): 
    osmid= data.get("osmid")
    if isinstance(osmid, list):
        candidates = [str(x) for x in osmid]
    elif osmid is None:
        candidates = []
    else:
        candidates = [str(osmid)]
    risk = None
    for omd in candidates:
        if omd in lookup:
            risk = float(lookup[omd])
            break
    if risk is None: 
        data["risk"] = 0.5 # because of buffering, it provides unknown risk score of certain street segments, hence we give it a neutral risk score (was previously 0.0)
        miss +=1
    else:
        data["risk"] = risk

# sanity checks regarding # of edges without risk score
# total = graph.number_of_edges()
# print("total:", total)
# print("missing:", miss)
# print("missing %:", round(miss/total*100, 2))

# missing_examples = []
# for u, v, k, data in graph.edges(keys=True, data=True):
#     if data.get("risk", 0) == 0.0: 
#         osmid = data.get("osmid")
#         missing_examples.append(osmid)
#     if len(missing_examples) >= 30:
#         break

# print(missing_examples)
# print({type(x) for x in missing_examples})

# none_count = 0
# list_count = 0

# for _, _, _, data in graph.edges(keys=True, data=True):
#     if data.get("risk", 0) == 0.0:
#         osmid = data.get("osmid")
#         if osmid is None:
#             none_count += 1
#         elif isinstance(osmid, list):
#             list_count += 1

# print("missing with osmid=None:", none_count)
# print("missing with osmid=list:", list_count)

# cost equation
def costs(graph, lambd = 0.5):
    for u, v, k, d in graph.edges(keys=True, data=True):
        length = float(d.get("length", 0.0))
        risk = float(d.get("risk", 0.5))
        d["cost"] = length * (1 + lambd * risk)

# Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  #radius of Earth in meteres
    # convert to radians and the difference between the latitudes and longitudes 
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # calculate intermediate value 'a'
    a = math.sin(delta_phi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2)**2
    # calculate central angle 'c'
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    # calculate distance 
    return R * c

# Heuristic function
def heuristic(graph, u, v):
    u_data = graph.nodes[u]
    v_data = graph.nodes[v]
    return haversine(u_data['y'], u_data['x'], v_data['y'], v_data['x'])

def a_star_path(graph, source, target, weight="cost"):
    # Priority queue, open list
    open_set = []
    heapq.heappush(open_set, (0, source))
    
    # g score
    g = {node: float('inf') for node in graph.nodes}
    g[source] = 0
    
    # f score
    f = {node: float('inf') for node in graph.nodes}
    f[source] = heuristic(graph, source, target)
    
    came_from = {}
    
    while open_set:
        # node with lowest f
        current_f, current = heapq.heappop(open_set)
        
        # If we reached the target, reconstruct and return the path
        if current == target:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(source)
            return path[::-1] 

        # Optimization: Skip if we found a better path to this node already
        if current_f > f[current]:
            continue
            
        # Explore neighbors
        for neighbor in graph.neighbors(current):
            min_edge_weight = float('inf')
            edges = graph[current][neighbor]
            for key in edges:
                edge_weight = edges[key].get(weight, float('inf'))
                if edge_weight < min_edge_weight:
                    min_edge_weight = edge_weight
            
            # Calculate tentative g-score
            tentative_g = g[current] + min_edge_weight
            
            # If this path is better than the previous, remember it
            if tentative_g < g[neighbor]:
                came_from[neighbor] = current
                g[neighbor] = tentative_g
                f[neighbor] = tentative_g + heuristic(graph, neighbor, target)
                heapq.heappush(open_set, (f[neighbor], neighbor))
                
    raise nx.NetworkXNoPath(f"No path between {source} and {target}.")

# A star algorithm implementation
def route(graph, latitude, longitude, final_latitude, final_longitude, lambd=0.5):
    costs(graph, lambd=lambd)

    origin = ox.nearest_nodes(graph, X=longitude, Y=latitude)
    destination = ox.nearest_nodes(graph, X=final_longitude, Y=final_latitude)

    path = a_star_path(graph, origin, destination, weight="cost")

    route_edges = ox.utils_graph.route_to_gdf(graph, path)
    geometry = route_edges.geometry.unary_union
    distance = float(route_edges["length"].sum())

    # length-weighted average risk
    avg_risk = float((route_edges["risk"] * route_edges["length"]).sum() / route_edges["length"].sum())

    walk_speed = 1.4 #meters per second
    
    time_min = distance / walk_speed / 60.0

    return {
        "path_nodes": path,
        "distance_m": distance,
        "time_min": time_min,
        "avg_risk": avg_risk,
        "geometry": geometry.__geo_interface__
    }