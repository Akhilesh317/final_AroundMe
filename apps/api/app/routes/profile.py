"""Profile and personalization endpoints"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile, ProfilePreference
from app.deps import get_db
from app.schemas.profile import (
    PreferenceListResponse,
    PreferenceUpdateRequest,
    ProfileCreate,
    Profile as ProfileSchema,
    ProfilePreferenceInDB,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/preferences", response_model=PreferenceListResponse)
async def get_preferences(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> PreferenceListResponse:
    """
    Get user preferences
    
    Requires user_id query parameter
    """
    try:
        # Get profile
        stmt = select(Profile).where(Profile.user_id == user_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            return PreferenceListResponse(preferences=[])
        
        # Get preferences
        stmt = select(ProfilePreference).where(ProfilePreference.profile_id == profile.id)
        result = await db.execute(stmt)
        preferences = result.scalars().all()
        
        return PreferenceListResponse(
            preferences=[ProfilePreferenceInDB(**pref.__dict__) for pref in preferences]
        )
        
    except Exception as e:
        logger.error("get_preferences_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences")
async def update_preferences(
    user_id: str,
    request: PreferenceUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> PreferenceListResponse:
    """
    Update user preferences
    
    Creates profile if it doesn't exist
    """
    try:
        # Get or create profile
        stmt = select(Profile).where(Profile.user_id == user_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            profile = Profile(user_id=user_id)
            db.add(profile)
            await db.flush()
        
        # Delete existing preferences
        stmt = select(ProfilePreference).where(ProfilePreference.profile_id == profile.id)
        result = await db.execute(stmt)
        existing = result.scalars().all()
        for pref in existing:
            await db.delete(pref)
        
        # Add new preferences
        new_preferences = []
        for pref in request.preferences:
            db_pref = ProfilePreference(
                profile_id=profile.id,
                key=pref.key,
                value=pref.value,
                weight=pref.weight,
            )
            db.add(db_pref)
            new_preferences.append(db_pref)
        
        await db.commit()
        
        # Refresh to get IDs and timestamps
        for pref in new_preferences:
            await db.refresh(pref)
        
        return PreferenceListResponse(
            preferences=[ProfilePreferenceInDB(**pref.__dict__) for pref in new_preferences]
        )
        
    except Exception as e:
        logger.error("update_preferences_error", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/preferences")
async def delete_preferences(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Delete all user preferences
    """
    try:
        # Get profile
        stmt = select(Profile).where(Profile.user_id == user_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            return {"deleted": 0}
        
        # Delete preferences
        stmt = select(ProfilePreference).where(ProfilePreference.profile_id == profile.id)
        result = await db.execute(stmt)
        preferences = result.scalars().all()
        
        count = len(preferences)
        for pref in preferences:
            await db.delete(pref)
        
        await db.commit()
        
        return {"deleted": count}
        
    except Exception as e:
        logger.error("delete_preferences_error", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))