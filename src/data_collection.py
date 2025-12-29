import os
import osmnx as ox
import geopandas as gpd
import numpy as np
import re
import pandas as pd

def main():
    place = "Toronto, Canada"
    out_dir = "data/processed"

    os.makedirs(out_dir, exist_ok=True)

    network = ox.graph_from_place(place, network_type="walk")
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(network)

    gdf_edges = gdf_edges[gdf_edges["length"] > 0]

    gdf_edges["highway"] = gdf_edges["highway"].astype(str)
    gdf_edges["name"] = gdf_edges["name"].fillna("unnamed")

    gdf_edges["maxspeed_clean"] = (
        gdf_edges["maxspeed"]
        .astype(str)
        .str.extract(r"(\d+)")
        .astype(float)
    )

    gdf_edges = gdf_edges[gdf_edges["access"].fillna("public") != "private"]

    gdf_edges = gdf_edges.drop(
        columns=[
            "oneway", "lanes", "width", "est_width",
            "bridge", "tunnel", "junction",
            "service", "area"
        ],
        errors="ignore"
    )
    gdf_nodes = gdf_nodes.drop(columns=["ref"], errors="ignore")

    gdf_nodes["highway"] = gdf_nodes["highway"].apply(
        lambda v: v[0] if isinstance(v, list) else v
    )

    gdf_nodes["is_traffic_signal"] = gdf_nodes["highway"] == "traffic_signals"
    gdf_nodes["is_crossing"] = gdf_nodes["highway"] == "crossing"

    print("Saving cleaned data to", out_dir)

    ox.save_graphml(network, f"{out_dir}/toronto_walk.graphml")

    gdf_nodes.to_file(
        f"{out_dir}/toronto_walk.gpkg",
        layer="nodes",
        driver="GPKG"
    )
    gdf_edges.to_file(
        f"{out_dir}/toronto_walk.gpkg",
        layer="edges",
        driver="GPKG"
    )

    print("Done.")

if __name__ == "__main__":
    main()



