import networkx as nx
from segments import *
from graphmaker import *
from simplekml import Kml
from staticmap import *


def export_PNG(graph: nx.Graph, filename: str, show: bool) -> None:
    """
    Exporta el graf a un fitxer {filename}_graph_map.png usant staticmap
    Si show és True, mostra el mapa per pantalla.
    """
    # Crear un staticmap.
    mymap = StaticMap(800, 600)

    # Afegir nodes.
    for node, data in graph.nodes(data=True):
        lon, lat = data["location"].lon, data["location"].lat
        marker = CircleMarker((lon, lat), "red", 5)
        mymap.add_marker(marker)

    # Afegir arestes.
    for u, v, data in graph.edges(data=True):
        lon1, lat1 = graph.nodes[u]["location"].lon, graph.nodes[u]["location"].lat
        lon2, lat2 = graph.nodes[v]["location"].lon, graph.nodes[v]["location"].lat
        line = Line(((lon1, lat1), (lon2, lat2)), "blue", 1)
        mymap.add_line(line)

    # Guardar (i mostrar).
    try:
        image = mymap.render()
        image.save(f"{filename}.graph_map.png") 
        if show:
            image.show()
    except Exception as e:
        print("Error: Ho sentim, no s'han trobat rutes.")


def export_KML(graph: nx.Graph, filename: str) -> None:
    """
    Exporta el graf a un fitxer {filename}_graph_map.kml 
    """
    kml = Kml()

    # Afegir nodes.
    for node, data in graph.nodes(data=True):
        lon, lat = data["location"].lon, data["location"].lat
        point = kml.newpoint(name=str(node), coords=[(lon, lat)])

        #Si té monuments, afegir-los
        if "monuments" in data and "path_weight" in data:
            point.description = f"{data['monuments']} (Path weight: {data['path_weight']})"
            point.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/paddle/red-circle.png"
        elif "start" in data:
            point.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/paddle/blu-circle.png"

    # Afegir arestes i pesos.
    for u, v, data in graph.edges(data=True):
        lon1, lat1 = graph.nodes[u]["location"].lon, graph.nodes[u]["location"].lat
        lon2, lat2 = graph.nodes[v]["location"].lon, graph.nodes[v]["location"].lat
        line = kml.newlinestring(name=f"Edge {u}-{v}", coords=[(lon1, lat1), (lon2, lat2)])

    # Guardar fitxer.
    kml.save(f"{filename}_graph_map.kml")


def export_PNG_routes(graph: nx.Graph, filename: str, monuments_show: bool, show: bool) -> None:
    """
    Exporta el graf a un fitxer {filename}_tree_map.png usant staticmap.
    Si monuments és True, mostra els monuments al mapa.
    Si show és True, mostra el mapa per pantalla.
    """
    mymap = StaticMap(1000, 800)

    # Afegir nodes.
    for node, data in graph.nodes(data=True):
        lon, lat = data["location"].lon, data["location"].lat
        
        # Color del node segons rol.
        if data["monuments"]: color,mida = "red",20
        elif "start" in data: color,mida = "blue",20  
        else: color,mida = "black",10

        marker = CircleMarker((lon, lat), color, mida)
        mymap.add_marker(marker)

        # Mostrar monuments (opcional).
        if monuments_show:
            for monument in data["monuments"]:
                # Afegir punt.
                lon, lat = monument.location.lon, monument.location.lat
                mon_marker = CircleMarker((lon, lat), "purple", 10)

                mymap.add_marker(mon_marker)

    # Afegir arestes.
    for u, v, data in graph.edges(data=True):
        lon1, lat1 = graph.nodes[u]["location"].lon, graph.nodes[u]["location"].lat
        lon2, lat2 = graph.nodes[v]["location"].lon, graph.nodes[v]["location"].lat
        line = Line(((lon1, lat1), (lon2, lat2)), "black", 2)
        mymap.add_line(line)

    # Guardar (i mostrar).
    try:
        image = mymap.render()
        image.save(f"{filename}_tree_map.png")
        
        if show: image.show()
    except Exception as e:
        print("Error: Ho sentim, no s'han trobat rutes ni monuments.")
