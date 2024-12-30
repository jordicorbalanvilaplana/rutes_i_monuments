import haversine as hs
import math
from yogi import *
from segments import *
from monuments import *
from graphmaker import *
from viewer import *
from routes import *


import chardet  # per llegir accents
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def get_coordinates(location: str) -> tuple:
    """A partir d'un string, obté les seves coordenades"""
    geolocator = Nominatim(user_agent="geoapiExercises")

    try:
        location = geolocator.geocode(location)
        return location.latitude, location.longitude # type: ignore
    except:
        print("Error: Geocoder service timed out")
        return None, None


def calcular_box(p: Point, d: float) -> Box:
    """
    A partir d'un punt inicial i una distància màxima en km,
    retorna la caixa quadrada amb centre p i diagonal 2d.
    """
    bottom_left = hs.inverse_haversine((p.lat, p.lon), d, math.pi * 1.25)
    top_right = hs.inverse_haversine((p.lat, p.lon), d, math.pi * 0.25)

    return Box(Point(bottom_left[0], bottom_left[1]), Point(top_right[0], top_right[1]))


def wait_for_keypress():
    """ 
    Espera a que una tecla sigui polsada.
    """
    try:
        input()
    except KeyboardInterrupt:
        pass


def llegir_dades_inicials() -> tuple[Box, Point, str]:
    """
    Llegeix les dades inicials
    """
    # Mostra instruccions inicials
    with open("introduccio.txt", "rb") as f:
        result = chardet.detect(f.read())
    with open("introduccio.txt", "r", encoding=result["encoding"]) as file:
        content = file.read()
    print(content)

    wait_for_keypress()

    # Obtenir punt inicial.
    lat, lon = None, None
    while lat == None or lon == None:
        exact = str(input("Conèixes les coordenades exactes de la localització on vols buscar monuments? (s/n): "))
        if exact == "s":
            lat = float(input("Quina és la teva latitud?: "))
            lon = float(input("Quina és la teva longitud?: "))

        else:
            location = str(input("Quina és l'adreça o prop de quina localització vols buscar monuments?: "))
            lat, lon = get_coordinates(location)
            if (lat, lon) == (None, None):
                print("Vaja! No s'ha pogut trobar l'adreça, hauras de tornar a provar")

    punt_inicial = Point(lat, lon) # type: ignore 

    # Obtenir Box
    dist = int(input("Com de lluny estaries disposat a anar(km): "))
    filename = str(input("Quin nom voldras que tingui aquest projecte?: "))
    box = calcular_box(punt_inicial, dist)

    return box, punt_inicial, filename


def main() -> None:

    box, p0, filename = llegir_dades_inicials()

    # Guardar i visualitzar segments
    segments = get_segments(box, filename)

    
    show = str(input("Desitges veure les rutes? (s/n): "))
    save_segments_map(segments, filename, show == "s")

    # Guardar el graf.
    g = make_graph(segments)

    # Simplificar el graf.
    simplify_graph(g)

    # Exportar graf.
    show = str(input("Desitges veure el graf de les rutes simplificades? (s/n): "))
    export_PNG(g, filename, show == "s")
    export_KML(g, filename)

    # Monuments.
    monuments = get_monuments(box, False)

    if len(monuments) == 0:
        raise ValueError("Vaja! No s'han trobat monuments a la teva zona...")
    assign_nodes_to_monuments(g, monuments)

    # Resultat final
    arbre = create_tree(g, p0)

    show_mon = str(input("Vols veure la localització dels monuments en el mapa final? (s/n): "))
    export_PNG_routes(arbre, filename, show_mon == "s", True)
    export_KML(arbre, f'{filename}_tree')


main()
