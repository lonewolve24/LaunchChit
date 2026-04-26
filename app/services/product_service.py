from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Union

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models import Product, User, Vote
from app.schemas.product import (
    CreateProductResult,
    MakerDetail,
    ProductCreateIn,
    ProductDetailOut,
)
from app.utils.slug import build_product_slug

_TODAY = timedelta(hours=24)
_MAX_SLUG_ATTEMPTS = 12


async def _slug_exists(db: AsyncSession, slug: str) -> bool:
    r = await db.execute(select(Product.id).where(Product.slug == slug).limit(1))
    return r.scalar_one_or_none() is not None


async def _allocate_slug(db: AsyncSession, name: str) -> str:
    last_err: Exception | None = None
    for _ in range(_MAX_SLUG_ATTEMPTS):
        try:
            slug = build_product_slug(name)
        except ValueError as e:
            last_err = e
            break
        if not await _slug_exists(db, slug):
            return slug
    raise ValueError("Could not generate a unique slug; try a different name") from last_err


async def create_product(
    db: AsyncSession, maker: User, data: ProductCreateIn
) -> CreateProductResult:
    slug = await _allocate_slug(db, data.name)
    p = Product(
        slug=slug,
        name=data.name,
        tagline=data.tagline,
        description=data.description,
        website_url=str(data.website_url),
        logo_url=str(data.logo_url) if data.logo_url is not None else None,
        maker_id=maker.id,
        vote_count=0,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return CreateProductResult(slug=p.slug)


def _out_product_feed_item(
    p: Any,
    maker: User,
    has_voted: bool,
) -> dict[str, Any]:
    return {
        "id": p.id,
        "slug": p.slug,
        "name": p.name,
        "tagline": p.tagline,
        "logo_url": p.logo_url,
        "vote_count": p.vote_count,
        "has_voted": has_voted,
        "maker": {"username": maker.username},
        "created_at": p.created_at,
    }


async def _voted_set_for_user(
    db: AsyncSession, user_id: int, product_ids: list[int]
) -> set[int]:
    if not product_ids:
        return set()
    r = await db.execute(
        select(Vote.product_id).where(
            Vote.user_id == user_id,
            Vote.product_id.in_(product_ids),
        )
    )
    return set(r.scalars().all())


async def list_today(
    db: AsyncSession, user: User | None
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    since = now - _TODAY
    result = await db.execute(
        select(Product, User)
        .join(User, Product.maker_id == User.id)
        .where(Product.created_at >= since)
        .order_by(desc(Product.vote_count), desc(Product.created_at))
    )
    rows = result.all()
    pids = [p.id for p, _ in rows]
    voted: set[int] = set()
    if user and pids:
        voted = await _voted_set_for_user(db, user.id, pids)
    return [
        _out_product_feed_item(
            p, u, p.id in voted if user else False
        )
        for p, u in rows
    ]


async def get_by_slug(
    db: AsyncSession, slug: str, user: User | None
) -> ProductDetailOut | None:
    r = await db.execute(
        select(Product, User)
        .join(User, Product.maker_id == User.id)
        .where(Product.slug == slug)
    )
    row = r.first()
    if row is None:
        return None
    p, maker = row
    has_voted = False
    if user:
        v = await db.execute(
            select(Vote)
            .where(
                Vote.user_id == user.id,
                Vote.product_id == p.id,
            )
            .limit(1)
        )
        has_voted = v.scalar_one_or_none() is not None
    return ProductDetailOut(
        id=p.id,
        slug=p.slug,
        name=p.name,
        tagline=p.tagline,
        description=p.description,
        website_url=p.website_url,
        logo_url=p.logo_url,
        vote_count=p.vote_count,
        has_voted=has_voted,
        maker=MakerDetail(id=maker.id, username=maker.username, avatar_url=None),
        created_at=p.created_at,
    )


# Return codes: -1 = product not found, -2 = duplicate vote, else = new vote count
AddVoteResult = Union[Literal[-1, -2], int]


async def add_vote(
    db: AsyncSession, user: User, product_id: int
) -> AddVoteResult:
    p = await db.get(Product, product_id)
    if p is None:
        return -1
    v = Vote(user_id=user.id, product_id=product_id)
    db.add(v)
    p.vote_count += 1
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return -2
    await db.refresh(p)
    return p.vote_count


# -1 = product not found, -2 = no vote to remove, else = new count
RemoveVoteResult = Union[Literal[-1, -2], int]


async def remove_vote(
    db: AsyncSession, user: User, product_id: int
) -> RemoveVoteResult:
    p = await db.get(Product, product_id)
    if p is None:
        return -1
    r = await db.execute(
        delete(Vote).where(
            Vote.user_id == user.id,
            Vote.product_id == product_id,
        )
    )
    n = r.rowcount or 0
    if n < 1:
        await db.rollback()
        return -2
    p.vote_count = max(0, p.vote_count - 1)
    await db.commit()
    await db.refresh(p)
    return p.vote_count
