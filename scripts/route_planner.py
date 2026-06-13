"""
旅游路线规划器核心模块（大圆弧均匀采样 + 严格约束）
功能：根据起点、终点和途经城市数量，生成一条合理的大圆弧路线
算法：计算起点到终点的大圆弧 → 筛选附近且不绕路的城市 → 按投影参数均匀采样 → 生成路线
"""

import math
from mysql.db_loader import get_all_cities

# ==================== 全局缓存 ====================
_distance_matrix = None
_city_ids = None
_coords = None
_cities_dict = None

def _init_route_cache():
    global _distance_matrix, _city_ids, _coords, _cities_dict
    if _distance_matrix is None:
        cities = get_all_cities()
        _city_ids = [city['id'] for city in cities]
        _coords = {city['id']: {'latitude': city['latitude'], 'longitude': city['longitude']} for city in cities}
        _cities_dict = {
            city['id']: {
                'city': city['city'],
                'country': city['country'],
                'latitude': city['latitude'],
                'longitude': city['longitude'],
                'budget_level': city['budget_level'],
                'top_trait': city['top_trait']
            } for city in cities
        }
        _distance_matrix = {}
        for i, id1 in enumerate(_city_ids):
            for j, id2 in enumerate(_city_ids):
                if i <= j:
                    dist = _haversine(_coords[id1]['latitude'], _coords[id1]['longitude'],
                                     _coords[id2]['latitude'], _coords[id2]['longitude'])
                    _distance_matrix[(id1, id2)] = dist
                    _distance_matrix[(id2, id1)] = dist

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def get_distance(id1, id2):
    _init_route_cache()
    if id1 == id2:
        return 0
    return _distance_matrix.get((id1, id2), 1e9)


# ==================== 球面几何工具 ====================
def _to_cartesian(lon, lat):
    phi = math.radians(lat)
    theta = math.radians(lon)
    x = math.cos(phi) * math.cos(theta)
    y = math.cos(phi) * math.sin(theta)
    z = math.sin(phi)
    return (x, y, z)

def _point_to_great_circle_distance(lon1, lat1, lon2, lat2, lon3, lat3):
    A = _to_cartesian(lon1, lat1)
    B = _to_cartesian(lon2, lat2)
    P = _to_cartesian(lon3, lat3)
    AB = (B[0]-A[0], B[1]-A[1], B[2]-A[2])
    AP = (P[0]-A[0], P[1]-A[1], P[2]-A[2])
    cross = (AB[1]*AP[2]-AB[2]*AP[1],
             AB[2]*AP[0]-AB[0]*AP[2],
             AB[0]*AP[1]-AB[1]*AP[0])
    norm_cross = math.sqrt(cross[0]**2 + cross[1]**2 + cross[2]**2)
    norm_AB = math.sqrt(AB[0]**2 + AB[1]**2 + AB[2]**2)
    if norm_AB == 0:
        return 0
    sin_dist = norm_cross / norm_AB
    sin_dist = min(1.0, max(0.0, sin_dist))
    angle = math.asin(sin_dist)
    return 6371 * angle

def _projection_param(lon1, lat1, lon2, lat2, lon3, lat3):
    A = _to_cartesian(lon1, lat1)
    B = _to_cartesian(lon2, lat2)
    P = _to_cartesian(lon3, lat3)
    dot_AP = A[0]*P[0] + A[1]*P[1] + A[2]*P[2]
    dot_AB = A[0]*B[0] + A[1]*B[1] + A[2]*B[2]
    dot_AP = min(1.0, max(-1.0, dot_AP))
    dot_AB = min(1.0, max(-1.0, dot_AB))
    angle_AOP = math.acos(dot_AP)
    angle_AOB = math.acos(dot_AB)
    if angle_AOB < 1e-9:
        return 0.5
    t = angle_AOP / angle_AOB
    return min(1.0, max(0.0, t))


# ==================== 核心路线生成（严格约束） ====================
def plan_route_with_mid_cities(start_id, end_id, total_cities):
    """
    生成一条经过大圆弧附近城市的路线，中间城市数量 = total_cities - 2
    严格约束：t ∈ [0.05, 0.95]，且满足三角不等式（绕路系数 ≤ 1.2）
    距离阈值动态调整：基于起点终点距离的 0.2 倍，最小 500 km，最大 2000 km
    """
    _init_route_cache()
    if total_cities < 2:
        return []
    num_mid = total_cities - 2
    if num_mid < 0:
        return []

    candidate_pool = [cid for cid in _city_ids if cid not in (start_id, end_id)]
    if len(candidate_pool) < num_mid:
        return []

    start_lon = _coords[start_id]['longitude']
    start_lat = _coords[start_id]['latitude']
    end_lon = _coords[end_id]['longitude']
    end_lat = _coords[end_id]['latitude']
    dist_ab = get_distance(start_id, end_id)
    max_thresh = max(500, min(2000, dist_ab * 0.2))
    max_detour_ratio = 1.2

    cities_with_t = []
    for cid in candidate_pool:
        lon = _coords[cid]['longitude']
        lat = _coords[cid]['latitude']
        dist_to_arc = _point_to_great_circle_distance(start_lon, start_lat, end_lon, end_lat, lon, lat)
        if dist_to_arc > max_thresh:
            continue
        t = _projection_param(start_lon, start_lat, end_lon, end_lat, lon, lat)
        if t < 0.05 or t > 0.95:
            continue
        if get_distance(start_id, cid) + get_distance(cid, end_id) > max_detour_ratio * dist_ab:
            continue
        cities_with_t.append((cid, t, dist_to_arc))

    if len(cities_with_t) < num_mid:
        return []

    cities_with_t.sort(key=lambda x: x[1])

    step = len(cities_with_t) / (num_mid + 1)
    mids_idx = [int(step * (i+1)) for i in range(num_mid)]
    mids = [cities_with_t[i][0] for i in mids_idx]

    route_ids = [start_id] + mids + [end_id]
    total_dist = sum(get_distance(route_ids[i], route_ids[i+1]) for i in range(len(route_ids)-1))

    route_cities = []
    for cid in route_ids:
        c = _cities_dict[cid]
        route_cities.append({
            'id': cid,
            'city': c['city'],
            'country': c['country'],
            'latitude': c['latitude'],
            'longitude': c['longitude'],
            'budget_level': c['budget_level'],
            'top_trait': c['top_trait']
        })

    return [{
        'city_ids': route_ids,
        'cities': route_cities,
        'total_distance_km': round(total_dist, 1)
    }]


# ==================== 点对点直达路线 ====================
def plan_direct_route(start_id, end_id):
    _init_route_cache()
    if start_id == end_id:
        return []
    dist = get_distance(start_id, end_id)
    start_city = _cities_dict[start_id]
    end_city = _cities_dict[end_id]
    route_cities = [
        {'id': start_id, 'city': start_city['city'], 'country': start_city['country'],
         'latitude': start_city['latitude'], 'longitude': start_city['longitude'],
         'budget_level': start_city['budget_level'], 'top_trait': start_city['top_trait']},
        {'id': end_id, 'city': end_city['city'], 'country': end_city['country'],
         'latitude': end_city['latitude'], 'longitude': end_city['longitude'],
         'budget_level': end_city['budget_level'], 'top_trait': end_city['top_trait']}
    ]
    return [{'city_ids': [start_id, end_id], 'cities': route_cities, 'total_distance_km': round(dist, 1)}]


# ==================== 统一接口 ====================
def plan_routes(start_id, end_id, total_cities, num_routes=5):
    routes = []
    direct = plan_direct_route(start_id, end_id)
    if direct:
        routes.extend(direct)
    if total_cities >= 3:
        sampled = plan_route_with_mid_cities(start_id, end_id, total_cities)
        if sampled:
            routes.extend(sampled)
    return routes
