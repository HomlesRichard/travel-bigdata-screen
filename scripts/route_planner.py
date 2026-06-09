"""
旅游路线规划器核心模块（大圆弧版本）
功能：根据起点、终点和途经城市数量，生成多条合理的旅行路线
算法：计算起点到终点的大圆弧 → 筛选弧线附近的城市 → 按投影位置排序 → 生成路线
"""

import random
import math
from .data_loader import load_cities_data
from .city_utils import build_distance_matrix, haversine

# ==================== 全局缓存 ====================
_distance_matrix = None   # 保留以备后续可能使用（如总距离计算）
_city_ids = None
_coords = None
_cities_dict = None

def _init_route_cache():
    global _distance_matrix, _city_ids, _coords, _cities_dict
    if _distance_matrix is None:
        _distance_matrix, _city_ids, _coords = build_distance_matrix()
        df = load_cities_data()
        _cities_dict = df.set_index('id')[['city', 'country', 'latitude', 'longitude',
                                            'budget_level', 'top_trait']].to_dict(orient='index')

def get_distance(id1, id2):
    """获取两个城市之间的球面距离（km）"""
    _init_route_cache()
    if id1 == id2:
        return 0
    return _distance_matrix.get((id1, id2), 1e9)


# ==================== 球面几何工具 ====================
def _to_cartesian(lon, lat):
    """经纬度转笛卡尔坐标（单位向量）"""
    phi = math.radians(lat)
    theta = math.radians(lon)
    x = math.cos(phi) * math.cos(theta)
    y = math.cos(phi) * math.sin(theta)
    z = math.sin(phi)
    return (x, y, z)

def _point_to_great_circle_distance(lon1, lat1, lon2, lat2, lon3, lat3):
    """
    计算点 P(lon3,lat3) 到大圆弧 AB(lon1,lat1)-(lon2,lat2) 的球面距离（km）
    使用向量叉积法
    """
    # 转为笛卡尔坐标
    A = _to_cartesian(lon1, lat1)
    B = _to_cartesian(lon2, lat2)
    P = _to_cartesian(lon3, lat3)

    # 向量 AB 和 AP
    AB = (B[0] - A[0], B[1] - A[1], B[2] - A[2])
    AP = (P[0] - A[0], P[1] - A[1], P[2] - A[2])

    # 叉积
    cross = (AB[1]*AP[2] - AB[2]*AP[1],
             AB[2]*AP[0] - AB[0]*AP[2],
             AB[0]*AP[1] - AB[1]*AP[0])
    norm_cross = math.sqrt(cross[0]**2 + cross[1]**2 + cross[2]**2)
    norm_AB = math.sqrt(AB[0]**2 + AB[1]**2 + AB[2]**2)

    if norm_AB == 0:
        return 0
    sin_dist = norm_cross / norm_AB
    sin_dist = min(1.0, max(0.0, sin_dist))
    angle = math.asin(sin_dist)
    return 6371 * angle

def _projection_param(lon1, lat1, lon2, lat2, lon3, lat3):
    """
    计算点 P 在大圆弧 AB 上的投影参数 t ∈ [0,1]
    使用球面插值公式：t 近似为角 AOP 与角 AOB 之比
    更精确：计算 P 在由 A,B 张成的平面上的投影向量
    """
    # 转为笛卡尔坐标
    A = _to_cartesian(lon1, lat1)
    B = _to_cartesian(lon2, lat2)
    P = _to_cartesian(lon3, lat3)

    # 计算向量点积
    dot_AP = A[0]*P[0] + A[1]*P[1] + A[2]*P[2]
    dot_AB = A[0]*B[0] + A[1]*B[1] + A[2]*B[2]
    # 注意：A 和 B 都是单位向量，但 P 也是单位向量。
    # 大圆弧的弧长参数：t = arcsin( |投影| ) / arcsin(...) 简化处理：
    # 使用 P 在 AB 方向上的夹角余弦?
    # 简便方法：计算点积：设角 AOP = arccos(dot_AP)，角 AOB = arccos(dot_AB)
    # t = 角 AOP / 角 AOB (如果 P 在弧上)
    # 但 P 不严格在弧上，近似为投影夹角比。
    cos_AOP = dot_AP
    cos_AOB = dot_AB
    # 确保数值稳定
    cos_AOP = min(1.0, max(-1.0, cos_AOP))
    cos_AOB = min(1.0, max(-1.0, cos_AOB))
    angle_AOP = math.acos(cos_AOP)
    angle_AOB = math.acos(cos_AOB)
    if angle_AOB < 1e-9:
        return 0.5
    t = angle_AOP / angle_AOB
    return min(1.0, max(0.0, t))


# ==================== 核心算法：大圆弧附近城市筛选 ====================
def _filter_cities_near_great_circle(start_id, end_id, candidate_pool, num_needed, max_distance_km=500):
    """
    筛选出距离大圆弧在 max_distance_km 以内的城市，并按投影参数排序
    返回排序后的城市ID列表（从起点到终点方向）
    """
    _init_route_cache()
    start_lon = _coords[start_id]['longitude']
    start_lat = _coords[start_id]['latitude']
    end_lon = _coords[end_id]['longitude']
    end_lat = _coords[end_id]['latitude']

    # 计算每个候选城市到大圆弧的距离和投影参数
    cities_with_info = []
    for cid in candidate_pool:
        lon = _coords[cid]['longitude']
        lat = _coords[cid]['latitude']
        # 跳过起点和终点
        if cid == start_id or cid == end_id:
            continue
        dist_to_arc = _point_to_great_circle_distance(start_lon, start_lat, end_lon, end_lat, lon, lat)
        if dist_to_arc <= max_distance_km:
            t = _projection_param(start_lon, start_lat, end_lon, end_lat, lon, lat)
            cities_with_info.append((cid, t, dist_to_arc))

    # 按投影参数排序（沿大圆弧从起点到终点方向）
    cities_with_info.sort(key=lambda x: x[1])
    sorted_cities = [c[0] for c in cities_with_info]
    return sorted_cities

def generate_one_route(start_id, end_id, num_mid, candidate_pool):
    """
    生成一条路线：
    1. 筛选大圆弧附近的城市（动态调整阈值直到有足够候选）
    2. 从筛选结果中按投影顺序取均匀间隔的 num_mid 个城市
    """
    _init_route_cache()
    # 尝试的阈值范围（km）
    thresholds = [300, 500, 800, 1200, 2000, 5000]
    sorted_candidates = []
    used_threshold = None
    for thresh in thresholds:
        sorted_candidates = _filter_cities_near_great_circle(start_id, end_id, candidate_pool, num_mid, max_distance_km=thresh)
        if len(sorted_candidates) >= num_mid:
            used_threshold = thresh
            break
    if len(sorted_candidates) < num_mid:
        # 仍然不够，直接使用所有候选（但会按投影排序）
        # 重新获取不限制距离的版本
        sorted_candidates = _filter_cities_near_great_circle(start_id, end_id, candidate_pool, num_mid, max_distance_km=10000)
        if len(sorted_candidates) < num_mid:
            return None, None

    # 在排序列表中均匀选取 num_mid 个城市（保证分布均匀，避免扎堆）
    step = len(sorted_candidates) / (num_mid + 1)
    mids_idx = [int(step * (i+1)) for i in range(num_mid)]
    mids = [sorted_candidates[i] for i in mids_idx]

    # 构建路线：起点 → 按投影顺序的中间城市 → 终点
    route = [start_id] + mids + [end_id]
    # 计算总距离（使用原始距离矩阵）
    total_dist = sum(get_distance(route[i], route[i+1]) for i in range(len(route)-1))
    return route, total_dist

def plan_routes(start_id, end_id, total_cities, num_routes=5):
    """
    生成 num_routes 条不同的路线（每条路线中间城市略有不同，增加随机性）
    total_cities: 总城市数量（含起终点）
    """
    _init_route_cache()
    if total_cities < 2 or total_cities > 10:
        return []
    num_mid = total_cities - 2
    if num_mid < 0:
        return []

    # 候选池排除起终点
    candidate_pool = [cid for cid in _city_ids if cid not in (start_id, end_id)]
    if len(candidate_pool) < num_mid:
        return []

    routes = []
    attempts = 0
    max_attempts = 30
    while len(routes) < num_routes and attempts < max_attempts:
        # 每次调用 generate_one_route 会重新筛选大圆弧附近城市并均匀采样
        route, total_dist = generate_one_route(start_id, end_id, num_mid, candidate_pool)
        if route is None:
            attempts += 1
            continue
        # 去重（比较中间城市序列）
        if any(route == r['city_ids'] for r in routes):
            attempts += 1
            continue

        # 组装城市详情
        route_cities = []
        for cid in route:
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
        routes.append({
            'city_ids': route,
            'cities': route_cities,
            'total_distance_km': round(total_dist, 1)
        })
        attempts += 1

    return routes