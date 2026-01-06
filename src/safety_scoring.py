import osmnx as ox
import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib as plt
from pathlib import Path
import fiona

gpkg = (Path.cwd() / "data" / "processed" / "toronto_walk.gpkg").resolve()

edges = gpd.read_file(gpkg, layer = "edges_clean")
assaults = gpd.read_file(gpkg, layer = "assaults_clean")
collisions = gpd.read_file(gpkg, layer = "collisions_clean")

edges = edges.to_crs("EPSG:26917")
assaults = assaults.to_crs("EPSG:26917")
collisions = collisions.to_crs("EPSG:26917")

# rather than a single street line, it creates an area that is going to be used to check for crime points
buffer_dist = 150
edges_buffer = edges[['geometry']].copy()
edges_buffer['geometry'] = edges_buffer.geometry.buffer(buffer_dist)

# count the assault and collision points within each street segment within the buffer area
assault_join = gpd.sjoin(assaults[["geometry"]], edges_buffer, how = "inner", predicate = "within")
assault_count = assault_join.groupby("index_right").size()
edges["assault count"] = edges.index.map(assault_count).fillna(0).astype(int)

collisions_join = gpd.sjoin(collisions[["geometry"]], edges_buffer, how = "inner", predicate = "within")
collisions_count = collisions_join.groupby("index_right").size()
edges["collisions count"] = edges.index.map(collisions_count).fillna(0).astype(int)

# under the scenario where one crime occurs significantly less than the other, it would be neglibile to count it, which is not ideal
# as a result, we combine assault and collision fairly by comparing the current count to the max

def compare(series):
    series = series.astype(float)
    mn, mx = series.min(), series.max()
    if mn == mx:
        return pd.Series(np.zeros(len(series)), index = series.index)
    return (series - mn) / (mx - mn)

edges["assault_score"] = compare(edges["assault count"])
edges["collision_score"] = compare(edges["collisions count"])

# risk score
assault_risk = 0.7
collisions_risk = 0.3
edges["risk"] = (assault_risk * edges["assault_score"] + collisions_risk * edges["collision_score"])

edges_to_save = edges.copy()
edges_to_save.to_file(gpkg, layer= "edges_with_risk", driver="GPKG")