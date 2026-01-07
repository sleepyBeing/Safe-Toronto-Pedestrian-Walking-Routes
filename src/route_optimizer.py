import osmnx as ox
import geopandas as gpd
from pathlib import Path
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

# Djikstra's algorithm implementation
def route(graph, latitude, longitude, final_latitude, final_longitude, lambd=0.5):
    costs(graph, lambd=lambd)

    origin = ox.nearest_nodes(graph, X=longitude, Y=latitude)
    destination = ox.nearest_nodes(graph, X=final_longitude, Y=final_latitude)

    path = nx.dijkstra_path(graph, origin, destination, weight="cost")

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