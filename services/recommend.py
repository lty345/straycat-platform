# =============================================================================
# services/recommend.py —— 规则版推荐打分（项目核心）
# =============================================================================
# 【为什么放在 services/ 而不是 apis/feed/repository/】
#   它要同时看 user（兴趣标签、城市）和 content（标签、情绪、城市、时间），
#   还要读 user_event 的聚合结果 —— 跨表编排，按项目分层约定归 services/。
#   规矩：这里不许写 select，也不许抛 HTTPException。
#
# 【打分公式（来自 docs/MVP-边界.md）】
#   score = 3 × 标签匹配数
#         + 2 × 情绪偏好匹配
#         + 1 × 同城加权
#         + 0.5 × 热度（近 7 天点赞数，归一化到 0~1）
#   最后整体 × 时间衰减：0.5 ** (已发布天数 / 7)
#
# 【为什么要乘时间衰减，而不是加】
#   加法只能让新内容"多一点点"；乘法是整体打折——一条两年前的爆款
#   (0.5^(730/7) ≈ 0) 会被压到底，而新鲜的热门能起来。这才是"时间衰减"的本意。
# =============================================================================
from datetime import datetime

from db.model import AppUser, Content

# 权重写在这里，方便调参，也方便面试时指着说"这四个数是我定的"
W_TAG = 3.0        # 标签匹配（最准的信号）
W_MOOD = 2.0       # 情绪偏好（次之）
W_CITY = 1.0       # 同城（弱信号）
W_HOT = 0.5        # 热度（最容易过拟合，给最低权重）
DECAY_HALF_LIFE_DAYS = 7.0   # 时间衰减半衰期：7 天分数砍半


def score_one(
    *,
    user: AppUser,
    content: Content,
    like_count_7d: int,
    max_like_count: int,
    preferred_mood: str | None,
    now: datetime,
) -> tuple[float, str]:
    user_tags    = {t.strip() for t in (user.interest_tags or "").split(",") if t.strip()}
    content_tags = {t.strip() for t in (content.tags or "").split(",") if t.strip()}
    hit = set(user_tags) & set(content_tags)                      # 用语法 ③

    # ---- ② 四项分（用语法 ④⑤）
    tag_score  = W_TAG * len(hit)
    mood_score = W_MOOD if (content.mood and content.mood == preferred_mood) else 0
    city_score = W_CITY if (content.city and content.city == user.city) else 0
    hot_score  = W_HOT * (like_count_7d / max_like_count) if max_like_count else 0     # 提示：like_count_7d / max_like_count

    # ---- ③ 时间衰减
    published = content.pub_time or content.create_time    # None 就兜底
    days = (now - published).days
    decay = 0.5 ** (days / DECAY_HALF_LIFE_DAYS)                                            # 0.5 ** (days / 7)

    # ---- ④ 合计
    score = (tag_score + mood_score + city_score + hot_score) * decay

    # ---- ⑤ 理由（f-string 拚字符串）
    reason = f"标签×{len(hit)}({','.join(sorted(hit))}) + 情绪×{mood_score} + 同城×{city_score} + 热度×{hot_score:.2f} 衰减×{decay:.2f}"
    return score, reason


def rank_contents(
    *,
    user: AppUser,
    contents: list[Content],
    like_counts_7d: dict[int, int],
    preferred_mood: str | None,
    now: datetime,
) -> list[tuple[Content, float, str]]:
    """给一批内容打分并按分数倒序返回。

    ★ 这个我写好了，你不用动 —— 你只需要实现上面的 score_one。

    返回 [(content, score, reason), ...]，分数高的在前。
    """
    max_like_count = max(like_counts_7d.values(), default=0)

    scored: list[tuple[Content, float, str]] = []
    for content in contents:
        score, reason = score_one(
            user=user,
            content=content,
            like_count_7d=like_counts_7d.get(content.id, 0),
            max_like_count=max_like_count,
            preferred_mood=preferred_mood,
            now=now,
        )
        scored.append((content, score, reason))

    # 分数相同的时候用 id 兜底，保证翻页顺序稳定（和分页那几个坑同一个道理）
    scored.sort(key=lambda item: (item[1], item[0].id), reverse=True)
    return scored
