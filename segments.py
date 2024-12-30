from typing import TypeAlias
from dataclasses import dataclass
from staticmap import StaticMap, Line
import os
import requests
import gpxpy
import pandas as pd


# Declaració de tipus.
@dataclass
class Point:
    lat: float
    lon: float

@dataclass
class Box:
    bottom_left: Point
    top_right: Point

Segments: TypeAlias = pd.DataFrame  # columns: segment id,inici_lat,inici_long,t_inici,final_lat,final_long,t_final.


def download_segments(box: Box, filename: str) -> None:
    """
    Descarrega tots els segments dintre de la box i els guarda en un fitxer csv amb el nom filename_segments.csv.
    """

    print(f"Descarregant totes les rutes prop de {filename}... (Això pot trigar una estona)")
    box_string = f"{box.bottom_left.lon},{box.bottom_left.lat},{box.top_right.lon},{box.top_right.lat}"

    # Defineix el titol de les columnes.
    columns = ("segment_id,inici_lat,inici_lon,t_inici,final_lat,final_lon,t_final,track_id")

    # Crea el fitxer i escriu els titols de les columnes.
    segments_data = open(f"{filename}_segments.csv", "w")
    segments_data.write(f"{columns}\n")

    page, segment_id, track_id = 0, 1, 0

    # Descarrega segments i els escriu al csv.
    while True:
        url = f"https://api.openstreetmap.org/api/0.6/trackpoints?bbox={box_string}&page={page}"
        response = requests.get(url)
        gpx_content = response.content.decode("utf-8")
        gpx = gpxpy.parse(gpx_content)

        if len(gpx.tracks) == 0:
            break

        for track in gpx.tracks:
            for segment in track.segments:
                if all(point.time is not None for point in segment.points):
                    segment.points.sort(key=lambda p: p.time)
                    for i in range(len(segment.points) - 1):
                        p1, p2 = segment.points[i], segment.points[i + 1]
                        if segment_valid(p1, p2):  # Filtrar segments.
                            segments_data.write(
                                f"{segment_id},{p1.latitude},{p1.longitude},{p1.time},{p2.latitude},{p2.longitude},{p2.time},{track_id}\n"
                            )
                            segment_id += 1
            track_id += 1

        page += 1

        print(f"S'han obtingut {track_id} rutes.")    


def segment_valid(p1, p2) -> bool:
    """
    Retorna cert, si el segment entre p1 i p2 és vàlid; es a dir, la distància del segment es menor a Delta
    Pre: p1 i p2 són punts del mòdul gpxpy.
    """

    # En el terreny que ens ocupa (Catalunya), podem assimilar la graella de lat i lon a uns eixos de coordenades estandard.
    # Per tant, comparem el quadrat de les "distancies" usant lat i lon com a eixos, i l'algorisme de validació és molt eficient.
    # Altrament, en una altra zona més al nord o al sud s'haurien de calcular les distancies de haversine.

    Delta = 0.00000210697  # 120 m
    return (p1.latitude - p2.latitude) ** 2 + (p1.longitude - p2.longitude) ** 2 < Delta


def load_segments(filename: str) -> Segments:
    """
    Retorna els segments inclosos en el fitxer.
    """

    return pd.read_csv(f"{filename}_segments.csv")


def get_segments(box: Box, filename: str) -> Segments:
    """
    Retorna els segments dins del box.
    Si existeix el fitxer, els carrega d'aquest i si no existeix, els descarrega i els retorna.
    """

    if not os.path.exists(f"{filename}_segments.csv"):
        download_segments(box, filename)

    return load_segments(filename)


def save_segments_map(segments: Segments, filename: str, show: bool) -> None:
    """
    Fa i guarda un gràfic amb tots els segments usant staticmap.
    El nom del fitxer es segments_map.png.
    Mostra el gràfic en pantalla si show es True.
    """

    # Crea un objecte amb staticmap.
    mymap = StaticMap(800, 600)

    # Afegeix els segments al mapa
    for _, seg in segments.iterrows():

        line = Line(((seg["inici_lon"], seg["inici_lat"]),(seg["final_lon"], seg["final_lat"]),),"red",1,)

        mymap.add_line(line)

    # Renderitza i guarda (i mostra) el mapa.
    try:
        image = mymap.render()
        image.save(f"{filename}_segments_map.png")

        if show:
            image.show()
    except Exception as e:
        print("Error: No s'han trobat rutes.")