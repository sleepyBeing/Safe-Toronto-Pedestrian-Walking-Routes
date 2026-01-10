# StreetSmart

## Inspiration
  The GTA is an interesting and entertaining urban city of Ontario that attracts many people to explore its restaurants and attractions. I personally love to walk around Eaton centre, eating good food, shopping at famous clothing stores, and enjoying the busy atmosphere of people walking to work. However, the numerous crime incidents that have occured recently at Scarborough and the increasingly number of people roaming the streets of Toronto whilst under the influences of dangerous chemicals scares me. Hence, I have built StreetSmart. 

## What Does It Do?
StreetSmart makes people feel safer with its intelligent pathing!
* Finds Safer Walks: Instead of just showing the shortest way, it finds walking routes in Toronto that help you avoid risky streets
* Lets You Choose: You can decide if you want to stick to the fastest path or take a slightly longer route to be safer
* Simple Directions: Just like a normal map app, you tell it where you are and where you want to go, and it calculates the best path for you

## How We Built It
* OSMnx: Modelled Toronto's pedestrian network using real-world street data. 🗺️
* GeoPandas: Integrated safety scores into every street segment for granular risk analysis. 🛡️
* Custom A Algorithm*: Engineered a specialized pathfinding system to balance travel time against safety. 🧠
* NetworkX: Powered the graph computations to process thousands of nodes and edges instantly. 🕸️
* Flask: Deployed a RESTful API to calculate and serve optimal routes in real-time. ⚡
* OpenStreetMap: Leveraged open-source mapping data to ensure comprehensive city coverage. 🌍

## Challenges We Ran Into
* Working with OSMnx for the very first time
* Handling street data that lacked safety scores by using default risk values
* Some Openstreetmap data are separated even though it looks like they are connected to the rest of Toronto producing routing failures

## Accomplishments
* Understanding the A* algorithm and implementing it into the project
* Flawlessly connecting the backend and frontend with Flask
* Using Jupyter Notebook to conduct data analysis to smoothly clean dataframes
