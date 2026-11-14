from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apis.feed.repository import feed_repo
from apis.feed.schemas.feed import FeedItem, FeedPage
from db.database import get_db_session
from exts.exceptions.exception import BusinessError, ExceptionEnum
from exts.responses.json_response import Success
from services import recommend

router_feed = APIRouter(prefix="/api/v1", tags=["推荐"])


@router_feed.get("/feed", summary="个性化推荐流")
async def get_feed(
    user_id: int = Query(..., ge=1, description="用户 id"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db_session),
):
    """按规则给当前用户排一条内容流。

    【链路】
      取用户 → 取全部内容 → 取近 7 天点赞数 → 判断是不是冷启动
        → 冷启动：按热度排（热门兜底）
        → 否则：services.recommend 打分后排序
      → 切片分页 → 包装成 FeedItem（带 score / reason）

    【为什么这里要判冷启动】
      新用户没有兴趣标签、也没有任何行为，四项里三项都算不出分，
      排序会退化成"按时间"，还不如直接给全站最热的内容。
    """
    user = await feed_repo.get_user(db, user_id)
    if user is None:
        raise BusinessError(ExceptionEnum.USER_NO_DATA)

    contents = await feed_repo.list_all_contents(db)
    now = datetime.now()
    like_counts = await feed_repo.like_counts_since(db, now - timedelta(days=7))

    has_tags = bool(user.interest_tags and user.interest_tags.strip())
    has_events = await feed_repo.has_events(db, user_id)
    cold_start = not has_tags and not has_events

    if cold_start:
        # 热门兜底：近 7 天点赞数优先，其次按发布时间（新的在前）
        ordered = sorted(
            contents,
            key=lambda c: (like_counts.get(c.id, 0), c.pub_time or c.create_time),
            reverse=True,
        )
        ranked = [
            (c, float(like_counts.get(c.id, 0)), "冷启动兜底：按近 7 天热度排序")
            for c in ordered
        ]
        preferred_mood = None
    else:
        preferred_mood = await feed_repo.preferred_mood(db, user_id)
        ranked = recommend.rank_contents(
            user=user,
            contents=contents,
            like_counts_7d=like_counts,
            preferred_mood=preferred_mood,
            now=now,
        )

    total = len(ranked)
    offset = (page - 1) * page_size
    page_slice = ranked[offset : offset + page_size]

    items = [
        FeedItem(
            id=c.id,
            title=c.title,
            summary=c.summary,
            tags=c.tags,
            mood=c.mood,
            city=c.city,
            cover_url=c.cover_url,
            pub_time=c.pub_time,
            score=round(score, 3),
            reason=reason,
        )
        for c, score, reason in page_slice
    ]

    return Success(
        api_code=200,
        message="获取成功",
        result=FeedPage(
            list=items,
            total=total,
            cold_start=cold_start,
            preferred_mood=preferred_mood,
        ),
    )
