import numpy as np
from .data_loader import load_cities_data


def haversine(lon1, lat1, lon2, lat2):
    """计算球面距离（km）"""
    R = 6371
    dlon = np.radians(lon2 - lon1)
    dlat = np.radians(lat2 - lat1)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def build_distance_matrix():
    """预计算所有城市之间的距离矩阵，返回字典 {(id1,id2): distance}"""
    df = load_cities_data()
    city_ids = df['id'].tolist()
    coords = df.set_index('id')[['longitude', 'latitude']].to_dict(orient='index')

    dist = {}
    for i, id1 in enumerate(city_ids):
        for id2 in city_ids[i + 1:]:
            d = haversine(coords[id1]['longitude'], coords[id1]['latitude'],
                          coords[id2]['longitude'], coords[id2]['latitude'])
            dist[(id1, id2)] = d
            dist[(id2, id1)] = d
    return dist, city_ids, coords