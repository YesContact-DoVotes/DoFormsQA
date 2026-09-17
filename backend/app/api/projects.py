from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.session import TestSession
from backend.app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(
        name=payload.name,
        base_url=payload.base_url,
        description=payload.description or "",
        requirements_text=payload.requirements_text or ""
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    resp = ProjectResponse.model_validate(project)
    resp.sessions_count = 0
    return resp


@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    
    response_list = []
    for p in projects:
        # Count sessions
        count_res = await db.execute(select(func.count(TestSession.id)).where(TestSession.project_id == p.id))
        sessions_count = count_res.scalar() or 0
        
        resp = ProjectResponse.model_validate(p)
        resp.sessions_count = sessions_count
        response_list.append(resp)
        
    return response_list


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    count_res = await db.execute(select(func.count(TestSession.id)).where(TestSession.project_id == project.id))
    sessions_count = count_res.scalar() or 0

    resp = ProjectResponse.model_validate(project)
    resp.sessions_count = sessions_count
    return resp


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, payload: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.name is not None:
        project.name = payload.name
    if payload.base_url is not None:
        project.base_url = payload.base_url
    if payload.description is not None:
        project.description = payload.description
    if payload.requirements_text is not None:
        project.requirements_text = payload.requirements_text

    await db.commit()
    await db.refresh(project)

    count_res = await db.execute(select(func.count(TestSession.id)).where(TestSession.project_id == project.id))
    sessions_count = count_res.scalar() or 0

    resp = ProjectResponse.model_validate(project)
    resp.sessions_count = sessions_count
    return resp


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()
    return None
