from __future__ import annotations

from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class MakerName(BaseModel):
    username: str


class ProductFeedItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    tagline: str
    logo_url: str | None
    vote_count: int
    has_voted: bool
    maker: MakerName
    created_at: datetime


class MakerDetail(BaseModel):
    id: int
    username: str
    avatar_url: str | None = None


class ProductDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    tagline: str
    description: str
    website_url: str
    logo_url: str | None
    vote_count: int
    has_voted: bool
    maker: MakerDetail
    created_at: datetime


class ProductCreateIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=80)
    tagline: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2000)
    website_url: AnyHttpUrl
    logo_url: AnyHttpUrl | None = None


class CreateProductResult(BaseModel):
    slug: str


class VoteCountOut(BaseModel):
    vote_count: int
