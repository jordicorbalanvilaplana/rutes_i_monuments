import networkx as nx
import numpy as np
import haversine as hs
from segments import *
from sklearn.cluster import KMeans
from typing import Iterator, TypeAlias


# Declaració de tipus
Aresta: TypeAlias = tuple[int, int, dict[str, int]]


def get_clusters(segments: Segments, n: int) -> list[Point]:
    """
    Retorna llista de n centroides, i afegeix una columna al dataframe de segments.
    Aquesta indica a quin centroide esta associat el punt de l'origen d'aquell segment.
    Numeració: el centroide (i) serà el cluster a cluster_centers[i].
    """

    # Fer el clustering pels nostres punts d'inici de cada segment.
    kmeans = KMeans(n_clusters=n)
    try:
        kmeans.fit(segments[["inici_lat", "inici_lon"]])
    except Exception as e:
        print("Error: No s'han pogut trobar suficients segments per fer el clustering.")
        exit()

    # Afegir una columna amb el nombre de cluster al df.
    segments["cluster_id"] = kmeans.labels_

    # Guardar els centroides com a llista de tuples
    cluster_centers: list[tuple[float, float]] = kmeans.cluster_centers_

    # Transformar els clusters en format Punt geogràfic
    return [Point(p[0], p[1]) for p in cluster_centers]


def get_edges(segments: Segments, centroids: list[Point] ) -> Iterator[Aresta]:  # (edge,edge, dist) 
    """
    Donat un dataframe de segments (on cada punt inicial té un centroide associat a la columna "cluster_id") i una llista de centroides:
    Retorna una aresta entre dos clusters i la seva distància si es compleixen les dues:
    - Hi ha com a mínim {Min_ways} segments entre els dos clusters
    - La distancia entre els dos clusters es menor a Dmax_edge
    """
    Min_ways = 2 if segments.tail(1).iloc[0]["track_id"] > 100 else 1  # Per assegurar la certesa dels camins.
    Dmax_edge = 0.2 # km

    n = len(centroids)
    # Matriu per guardar el nombre de segments que connecten centroides (n.clusters no molt elevat)
    n_ways: list[list[int]] = [[0 for _ in range(n)] for _ in range(n)] # [i][j]+[j][i] = nombre de segments que connecten centroides i amb j.

    for i, row in segments.iloc[0:-1].iterrows():

        # Mirem que els clusters siguin diferents.
        c1 = row["cluster_id"]
        c2 = segments.iloc[i + 1]["cluster_id"] # type: ignore

        if c1 != c2:

            # Mirem que formin part del mateix Track
            p1_track_id = row["track_id"]
            p2_track_id =segments.iloc[i + 1]["track_id"] # type: ignore

            if p1_track_id == p2_track_id:  
                n_ways[c1][c2] += 1 

                if  n_ways[c1][c2] + n_ways[c2][c1] == Min_ways:  # Retorna aresta (si es valida) quan arriba al mínim imposat

                    dist = hs.haversine((centroids[c1].lat, centroids[c1].lon), (centroids[c2].lat, centroids[c2].lon))

                    if dist > Dmax_edge:
                        yield (c1, c2, {"weight": dist})


def make_graph(segments: Segments) -> nx.Graph:
    """
    Crea el graf induit a partir dels segments.
    """
    N_clusters: int = 100

    # Obtenir centroides.
    centroids: list[Point] = get_clusters(segments, N_clusters) 

    # Afegir nodes al graf.
    graph: nx.Graph = nx.empty_graph(N_clusters) 

    # Afegir característiques de cada node. (Cada node del graf té: localització i monuments associats).
    for node_id, coord in enumerate(centroids):
        graph.nodes[node_id]["location"] = coord
        graph.nodes[node_id]["monuments"] = []

    # Afegir arestes des d'un iterador.
    graph.add_edges_from(get_edges(segments, centroids))  

    return graph


def simplify_graph(g: nx.Graph) -> None:
    """
    Simplifica el graf.
    """
    simplify_by_angle(g)
    simplify_empty_nodes(g)


def simplify_empty_nodes(graph: nx.Graph) -> None:
    """
    Simplifica el graf eliminant tots els nodes sense aresta.
    """
    # Obtenir els nodes sense aresta.
    nodes_to_remove = [node for node in graph.nodes(data=False) if graph.degree(node) == 0]

    graph.remove_nodes_from(nodes_to_remove)


def simplify_by_angle(graph: nx.Graph) -> None:
    """
    Simplifica el graf eliminant els nodes que només tinguin 2 connexions i amb un angle menor que Epsilon.
    Post: Substitueix el node per una aresta entre les seves dues connexions.
    """
    Epsilon = 10

    nodes_to_remove: list[int] = []

    for node in graph.nodes(data=False): 
        if graph.degree(node) == 2: # Iterar per tots els nodes amb grau 2.

            neighbors: list[int] = list(graph.neighbors(node))

            # Mirar l'angle.
            p1 = Point(graph.nodes[neighbors[0]]["location"].lat, graph.nodes[neighbors[0]]["location"].lon,)
            p2 = Point(graph.nodes[node]["location"].lat, graph.nodes[node]["location"].lon)
            p3 = Point( graph.nodes[neighbors[1]]["location"].lat, graph.nodes[neighbors[1]]["location"].lon)

            angle = calculate_angle(p1, p2, p3)

            if abs(180-angle) < Epsilon:  
                # Crear nova aresta.
                new_dist: float = hs.haversine((p1.lat,p1.lon),(p3.lat,p3.lon))  
                graph.add_edge(neighbors[0], neighbors[1], weight = new_dist)

                # Afegim el Node a la llista de nodes a eliminar.
                nodes_to_remove.append(node)

    # Eliminar nodes simplificats.
    graph.remove_nodes_from(nodes_to_remove)


def calculate_angle(p1: Point, p2: Point, p3: Point) -> float:
    """
    Retorna l'angle entre els vectors (p1 -> p3) and (p2 -> p3).
    """
    v1 = (p1.lat - p2.lat, p1.lon - p2.lon)
    v2 = (p3.lat - p2.lat, p3.lon - p2.lon)

    angle = np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

    return np.degrees(angle)
