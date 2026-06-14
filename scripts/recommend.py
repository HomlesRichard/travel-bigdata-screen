import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from mysql.db_loader import get_all_cities

# 特征列（9个维度）
TRAIT_COLS = ['culture', 'adventure', 'nature', 'beaches',
              'nightlife', 'cuisine', 'wellness', 'urban', 'seclusion']

# 全局缓存：特征矩阵和城市ID列表
_city_ids = None
_feature_matrix = None
_city_dict = None


def load_feature_matrix():
    """加载所有城市的特征向量（已归一化）"""
    global _city_ids, _feature_matrix, _city_dict
    if _feature_matrix is not None:
        return

    cities = get_all_cities()
    _city_dict = {c['id']: c for c in cities}
    _city_ids = [c['id'] for c in cities]

    # 构建特征矩阵（未归一化）
    raw_matrix = []
    for c in cities:
        vec = [float(c[col]) for col in TRAIT_COLS]
        raw_matrix.append(vec)
    raw_matrix = np.array(raw_matrix)

    # 行归一化（使每个城市的向量模长为1，便于余弦相似度计算）
    norms = np.linalg.norm(raw_matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1  # 避免除零
    _feature_matrix = raw_matrix / norms


def recommend_by_city_ids(like_city_ids, top_n=10):
    """基于喜欢的城市列表推荐相似城市（物品协同过滤）"""
    load_feature_matrix()
    if not like_city_ids:
        return []

    # 获取喜欢城市的索引
    indices = []
    for cid in like_city_ids:
        if cid in _city_dict:
            idx = _city_ids.index(cid)
            indices.append(idx)
    if not indices:
        return []

    # 计算相似度：取喜欢城市特征向量的平均作为用户偏好向量
    pref_vec = np.mean(_feature_matrix[indices], axis=0).reshape(1, -1)
    similarities = cosine_similarity(pref_vec, _feature_matrix).flatten()

    # 排除已喜欢的城市，按相似度降序取 top_n
    liked_set = set(like_city_ids)
    candidates = [(i, sim) for i, sim in enumerate(similarities)
                  if _city_ids[i] not in liked_set]
    candidates.sort(key=lambda x: x[1], reverse=True)

    results = []
    for idx, sim in candidates[:top_n]:
        city = _city_dict[_city_ids[idx]]
        results.append({
            'id': city['id'],
            'city': city['city'],
            'country': city['country'],
            'region': city['region'],
            'budget_level': city['budget_level'],
            'top_trait': city['top_trait'],
            'similarity': round(float(sim), 3)
        })
    return results


def recommend_by_trait_weights(weights, top_n=10):
    """根据用户指定的特质权重推荐城市（基于内容的匹配）"""
    load_feature_matrix()
    # weights 应为长度为9的列表，与 TRAIT_COLS 顺序一致
    if len(weights) != len(TRAIT_COLS):
        return []
    # 归一化权重向量
    w = np.array(weights).reshape(1, -1)
    w = w / (np.linalg.norm(w) + 1e-8)
    # 计算加权相似度（点积）
    scores = np.dot(_feature_matrix, w.T).flatten()
    # 按分数降序
    candidates = [(i, scores[i]) for i in range(len(_city_ids))]
    candidates.sort(key=lambda x: x[1], reverse=True)

    results = []
    for idx, sim in candidates[:top_n]:
        city = _city_dict[_city_ids[idx]]
        results.append({
            'id': city['id'],
            'city': city['city'],
            'country': city['country'],
            'region': city['region'],
            'budget_level': city['budget_level'],
            'top_trait': city['top_trait'],
            'similarity': round(float(sim), 3)
        })
    return results