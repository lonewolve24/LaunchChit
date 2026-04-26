"""Product routes: today feed, detail, create, vote/unvote."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.product import ProductCreateIn, ProductDetailOut
from app.services.product_service import (
    create_product,
    list_today,
    get_by_slug,
    add_vote,
    remove_vote,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/today", response_model=list[dict])
async def today_feed(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Get today's feed (last 24h, sorted by votes desc then created_at desc)."""
    products = await list_today(db, current_user)
    return products


@router.get("/{slug}", response_model=ProductDetailOut)
async def get_product(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Get a product by slug."""
    product = await get_by_slug(db, slug, current_user)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=dict, status_code=201)
async def create_new_product(
    body: ProductCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new product (authenticated users only)."""
    from app.schemas.product import CreateProductResult
    result = await create_product(db, current_user, body)
    return {"slug": result.slug}


@router.post("/{product_id}/vote", status_code=204)
async def vote_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Vote for a product (409 if already voted)."""
    result = await add_vote(db, current_user, product_id)
    if result == -1:
        raise HTTPException(status_code=404, detail="Product not found")
    if result == -2:
        raise HTTPException(status_code=409, detail="Already voted")
    return None


@router.delete("/{product_id}/vote", status_code=204)
async def unvote_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove your vote from a product (404 if vote doesn't exist)."""
    result = await remove_vote(db, current_user, product_id)
    if result == -1:
        raise HTTPException(status_code=404, detail="Product not found")
    if result == -2:
        raise HTTPException(status_code=404, detail="Vote not found")
    return None
