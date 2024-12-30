import networkx as nx
import haversine as hs
from dataclasses import dataclass
from segments import Point
from monuments import Monument, Monuments
from typing import TypeAlias
from graphmaker import simplify_empty_nodes


# Declaració de tipus.
Route: TypeAlias = list[int]

Routes: TypeAlias = dict[int, Route]


def assign_nodes_to_monuments(g: nx.Graph, monuments: Monuments) -> None:
    """
    Associa cada monument al node del graf que sigui més proper.
    Pre: cada node del graf té un atribut Point anomenat "location".
    Post: Els monuments associats a cada node apareixen a node["monuments"].
    """
    for _, info in monuments.iterrows():  # Per cada monument:

        monument_location = Point(info["lat"], info["lon"])
        nearest_node = get_closest_node(g,monument_location) # Obtenim id del node

        g.nodes[nearest_node]["monuments"].append(Monument(info["name"],monument_location))  # Afegir el monument al Node.


def get_closest_node(g: nx.Graph, p: Point) -> int:
    """
    Retorna el node del graf que és més proper al punt p.
    """
    min_distance = None

    # Recorrer tots els nodes i retornar el que fa la distància a p mínima.
    for node, info in g.nodes(data=True):  
        node_location: Point = info["location"]
        distance = hs.haversine((node_location.lat, node_location.lon), (p.lat, p.lon))

        if not min_distance or distance < min_distance:
            min_distance = distance
            nearest_node = node

    return nearest_node


def find_routes(graph: nx.Graph, start: int) -> tuple[Routes, dict[int,float]]:
    """
    Busca la ruta més propera més curta des del node start fins a tots els nodes del graf.
    Pre: el graf no és buit
    Post: Retorna 
    - un diccionari de rutes {node d'arribada: seqüència de nodes fins al node d'arribada}
    - un diccionari {node d'arribada: distancia minima des de s}
    """

    total_weights, routes = nx.single_source_dijkstra(graph, start, weight="weight")  # type: ignore
    
    return (routes, total_weights)


def create_tree(graph: nx.Graph, start: Point) -> nx.Graph:
    """
    Retorna un Graf (arbre) amb el camí més curt a tots els nodes amb monuments associats.
    L'arrel de l'arbre és el start.
    """
    start_node = get_closest_node(graph, start) # Obtenir node inicial (arrel de l'arbre).

    routes, total_weights = find_routes(graph, start_node)  # dict[node, ruta de nodes per arribar] , dict[node, km per arribar].

    # Crear l'arbre.
    routes_tree = nx.Graph()
    routes_tree.add_nodes_from(graph.nodes(data=True))
    
    routes_tree.nodes[start_node]["start"] = True

    # Afegir arestes dels camins fins a monuments.
    for endpoint, route in routes.items():  # Separar les rutes en nodes i rutes
        if graph.nodes[endpoint]["monuments"]:  # Filtrar les rutes que porten a monuments.
            for i in range(len(route) - 1):
                routes_tree.add_edge(route[i], route[i + 1])  # Afegir aresta al graf.

            # Guardar en el node de destí la ruta i distància total des de l'inici.
            routes_tree.nodes[endpoint]["shortest_path"] = route
            routes_tree.nodes[endpoint]["path_weight"] = total_weights[endpoint]

    simplify_empty_nodes(routes_tree)

    return routes_tree