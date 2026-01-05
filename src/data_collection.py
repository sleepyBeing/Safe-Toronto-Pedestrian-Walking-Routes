import os
import osmnx as ox
import geopandas as gpd
import numpy as np
import re
import pandas as pd
from pathlib import Path
import fiona

def main():
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    out_dir = project_root / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    gpkg_path = out_dir / "toronto_walk.gpkg"
    graphml_path = out_dir / "toronto_walk_clean.graphml"

# Download Toronto network
    place = "Toronto, Canada"
    network = ox.graph_from_place(place, network_type="walk")
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(network)

# Clean network
    if "length" in gdf_edges.columns:
        gdf_edges = gdf_edges[gdf_edges["length"] > 0].copy()

    if "highway" in gdf_edges.columns:
        gdf_edges["highway"] = gdf_edges["highway"].astype(str)

    if "name" in gdf_edges.columns:
        gdf_edges["name"] = gdf_edges["name"].fillna("unnamed")

    if "maxspeed" in gdf_edges.columns:
        gdf_edges["maxspeed_clean"] = (
            gdf_edges["maxspeed"]
            .astype(str)
            .str.extract(r"(\d+)", expand=False)
            .astype(float)
        )
    else:
        gdf_edges["maxspeed_clean"] = pd.NA

    if "access" in gdf_edges.columns:
        gdf_edges = gdf_edges[gdf_edges["access"].fillna("public") != "private"].copy()

    gdf_edges = gdf_edges.drop(
        columns=[
            "oneway", "lanes", "width", "est_width",
            "bridge", "tunnel", "junction",
            "service", "area",
        ],
        errors="ignore",
    )
    gdf_nodes = gdf_nodes.drop(columns=["ref"], errors="ignore")

    if "highway" in gdf_nodes.columns:
        gdf_nodes["highway"] = gdf_nodes["highway"].apply(
            lambda v: v[0] if isinstance(v, list) and len(v) > 0 else v
        )
        gdf_nodes["is_traffic_signal"] = gdf_nodes["highway"] == "traffic_signals"
        gdf_nodes["is_crossing"] = gdf_nodes["highway"] == "crossing"
    else:
        gdf_nodes["is_traffic_signal"] = False
        gdf_nodes["is_crossing"] = False

    gdf_nodes.to_file(gpkg_path, layer="nodes_clean", driver="GPKG")
    gdf_edges.to_file(gpkg_path, layer="edges_clean", driver="GPKG")

    try:
        network_clean = ox.graph_from_gdfs(gdf_nodes, gdf_edges)
        ox.save_graphml(network_clean, graphml_path)
    except Exception as e:
        print("Warning: could not save cleaned graphml:", e)

# Raw datasets
    crime_assault = pd.read_csv(raw_dir/'Assault_Open_Data_6843660120719629610.csv')
    crime_collision = pd.read_csv(raw_dir/'Traffic_Collisions_Open_Data_3719442797094142699.csv')

# Clean crime_assault
    crime_assault["LAT_WGS84"] = pd.to_numeric(crime_assault["LAT_WGS84"], errors="coerce")
    crime_assault["LONG_WGS84"] = pd.to_numeric(crime_assault["LONG_WGS84"], errors="coerce")

    crime_assault = crime_assault[
        (crime_assault["NEIGHBOURHOOD_158"] != "NSA") &
        (crime_assault["NEIGHBOURHOOD_140"] != "NSA") & 
        (crime_assault["LONG_WGS84"] != 0) &
        (crime_assault["LAT_WGS84"] != 0) &
        (crime_assault["LONG_WGS84"].notna()) &
        (crime_assault["LAT_WGS84"].notna())
    ].copy()

# Clean crime_collision
    crime_collision["LAT_WGS84"] = pd.to_numeric(crime_collision["LAT_WGS84"], errors="coerce")
    crime_collision["LONG_WGS84"] = pd.to_numeric(crime_collision["LONG_WGS84"], errors="coerce")

    crime_collision = crime_collision[
        (crime_collision["NEIGHBOURHOOD_158"] != "NSA")
        & (crime_collision["LONG_WGS84"] != 0)
        & (crime_collision["LAT_WGS84"] != 0)
        & (crime_collision["LONG_WGS84"].notna())
        & (crime_collision["LAT_WGS84"].notna())
    ].copy()

# Convert crimes to GeoDataFrames and save into the same gpkg
    assaults_gdf = gpd.GeoDataFrame(
        crime_assault,
        geometry=gpd.points_from_xy(crime_assault["LONG_WGS84"], crime_assault["LAT_WGS84"]),
        crs="EPSG:4326",
    )

    collisions_gdf = gpd.GeoDataFrame(
        crime_collision,
        geometry=gpd.points_from_xy(crime_collision["LONG_WGS84"], crime_collision["LAT_WGS84"]),
        crs="EPSG:4326",
    )

    assaults_gdf.to_file(gpkg_path, layer="assaults_clean", driver="GPKG")
    collisions_gdf.to_file(gpkg_path, layer="collisions_clean", driver="GPKG")

if __name__ == "__main__":
    main()