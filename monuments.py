from segments import Point, Box
from dataclasses import dataclass
from typing import TypeAlias
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import os
import csv


# Declaració de tipus.
@dataclass
class Monument:
    name: str
    location: Point

Monuments: TypeAlias = pd.DataFrame  # columns: Title,Latitude,Longitude.


def download_monuments(filename: str) -> None:
    """
    Descarregar tots els monuments de Catalunya i les seves coordenades a partir del codi font de la web de Catalunya Medieval.
    """

    comarques = [
        "alt-camp",
        "alt-emporda",
        "alt-penedes",
        "alt-urgell",
        "alta-ribagorca",
        "anoia",
        "vall-daran",
        "bages",
        "baix-camp",
        "baix-ebre",
        "baix-emporda",
        "baix-llobregat",
        "baix-penedes",
        "barcelones",
        "bergueda",
        "cerdanya",
        "conca-de-barbera",
        "garraf",
        "garrigues",
        "garrotxa",
        "girones",
        "llucanes",
        "maresme",
        "moianes",
        "montsia",
        "noguera",
        "osona",
        "pallars-jussa",
        "pallars-sobira",
        "pla-durgell",
        "pla-de-lestany",
        "priorat",
        "ribera-debre",
        "ripolles",
        "segarra",
        "segria",
        "selva",
        "solsones",
        "tarragones",
        "terra-alta",
        "urgell",
        "valles-occidental",
        "valles-oriental",
    ]

    # Crear fitxer csv i escriure titols de les columnes.
    with open("{filename}.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["name", "lat", "lon"])
        
        # Iterar per les comarques per buscar noms i coordenades de monuments.
        for comarca in comarques:
            url = f"https://www.catalunyamedieval.es/mapa/{comarca}/"
            page = requests.get(url)
            
            #'Descarregar' contingut html de la web.
            monuments = BeautifulSoup(page.text, "html.parser")
            
            # Filtrar i agafar nomes el que comença per script i, a més, conté var nomComarca.
            scripts = monuments.find_all("script")
            js_content = ""
            for script in scripts:
                if "var nomComarca" in str(script):
                    js_content += script.string

            # Indagar en el contingut per trobar els noms i coordenades dels monuments
            pattern = r'"title":"(.*?)","link":".*?","position":{"lat":"(.*?)","long":"(.*?)"}'
            matches = re.findall(pattern, js_content)

            # Esciure les dades al fitxer csv
            for match in matches:
                writer.writerow(match)


def get_region_monuments(box: Box) -> Monuments:
    """
    Filtra el dataframe de monuments per només retornar-ne els que estan inclosos dins de la box.
    """
    monuments = pd.read_csv(f"monuments.csv")

    # Només agafem monuments dins del box.
    region_monuments = monuments[
        (box.bottom_left.lat < monuments["lat"])
        & (monuments["lat"] < box.top_right.lat)
        & (box.bottom_left.lon < monuments["lon"])
        & (monuments["lon"] < box.top_right.lon)
    ]

    return region_monuments


def get_monuments(box: Box, update: bool) -> Monuments:
    """
    Retorna tots els monuments dins la box.
    Si update es True o monuments.csv no existeix, abans descarregarà els monuments i els guardarà en un fitxer csv.  
    """
    if update or not os.path.exists("monuments.csv"): 
        download_monuments("monuments")
    
    return get_region_monuments(box)


