import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from segments import Segments

#MAPA DE COLORS

def generar_mapa_clustering(segments: Segments) -> None:
    """
    Aquesta fuunció permet veure com funciona el clustering que usem per triar els nodes
    """
    N = 100 #nombre de clusters
    # Triar els centrodies
    kmeans = KMeans(n_clusters=N)

    # Clusteritzar segons columnes inici_lat i inici_lon
    kmeans.fit(segments[["inici_lat", "inici_lon"]])
    
    # Afegir els labels al dataframe
    segments['kmeans'] = kmeans.labels_
    
    # Guardar centroides
    cluster_centers = kmeans.cluster_centers_

    # Graficar
    plt.scatter(segments['inici_lon'], segments['inici_lat'], c=segments['kmeans'], cmap='Paired', s = 10)

    plt.scatter(cluster_centers[:, 1], cluster_centers[:, 0], c='black', marker='o')  # Assuming latitude is the first column and longitude is the second column

    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('KMeans Clustering')
    plt.show()

