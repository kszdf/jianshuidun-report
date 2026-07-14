"""
配置API - 科目映射、标准科目、系统配置
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_company_id
from app.models.config import CfgStdSubject, CfgSubjectMapping
from app.models.business import BizProject, BizCustomer, BizBankAccount

router = APIRouter()


# ============================================================
# 标准科目
# ============================================================

@router.get("/std-subjects", summary="获取标准科目列表")
def get_std_subjects(
    subject_type: Optional[str] = Query(None, description="科目类型"),
    report_category: Optional[str] = Query(None, description="报表分类"),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """获取建筑行业标准科目列表"""
    query = db.query(CfgStdSubject).filter(
        (CfgStdSubject.company_id == 0) | (CfgStdSubject.company_id == company_id)
    )
    if subject_type:
        query = query.filter(CfgStdSubject.subject_type == subject_type)
    if report_category:
        query = query.filter(CfgStdSubject.report_category == report_category)

    subjects = query.order_by(CfgStdSubject.subject_code).all()
    return {"total": len(subjects), "items": subjects}


# ============================================================
# 科目映射
# ============================================================

@router.get("/subject-mapping", summary="获取科目映射列表")
def get_subject_mapping(
    is_mapped: Optional[bool] = Query(None, description="是否已映射"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """获取企业科目与标准科目的映射关系"""
    query = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.company_id == company_id
    )
    if is_mapped is not None:
        query = query.filter(CfgSubjectMapping.is_mapped == is_mapped)
    if keyword:
        query = query.filter(
            (CfgSubjectMapping.source_name.like(f"%{keyword}%")) |
            (CfgSubjectMapping.source_code.like(f"%{keyword}%"))
        )

    total = query.count()
    items = query.order_by(CfgSubjectMapping.source_code).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 统计
    mapped_count = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.company_id == company_id,
        CfgSubjectMapping.is_mapped == True,
    ).count()
    unmapped_count = total - mapped_count

    return {
        "total": total,
        "mapped_count": mapped_count,
        "unmapped_count": unmapped_count,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


class MappingUpdateReq(BaseModel):
    id: int
    std_subject_id: int
    std_subject_code: str
    std_subject_name: str


@router.post("/subject-mapping/update", summary="更新科目映射")
def update_subject_mapping(
    req: MappingUpdateReq,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """手动更新单个科目的映射关系"""
    mapping = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.id == req.id,
        CfgSubjectMapping.company_id == company_id,
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="映射记录不存在")

    mapping.std_subject_id = req.std_subject_id
    mapping.std_subject_code = req.std_subject_code
    mapping.std_subject_name = req.std_subject_name
    mapping.match_type = "manual"
    mapping.is_mapped = True
    mapping.match_confidence = 100

    db.commit()
    return {"message": "映射更新成功", "id": mapping.id}


class BatchMappingReq(BaseModel):
    items: List[MappingUpdateReq]


@router.post("/subject-mapping/batch-update", summary="批量更新科目映射")
def batch_update_mapping(
    req: BatchMappingReq,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """批量更新科目映射"""
    success_count = 0
    for item in req.items:
        mapping = db.query(CfgSubjectMapping).filter(
            CfgSubjectMapping.id == item.id,
            CfgSubjectMapping.company_id == company_id,
        ).first()
        if mapping:
            mapping.std_subject_id = item.std_subject_id
            mapping.std_subject_code = item.std_subject_code
            mapping.std_subject_name = item.std_subject_name
            mapping.match_type = "manual"
            mapping.is_mapped = True
            mapping.match_confidence = 100
            success_count += 1

    db.commit()
    return {"message": f"成功更新 {success_count} 条映射", "success_count": success_count}


# ============================================================
# 项目管理
# ============================================================

@router.get("/projects", summary="获取项目列表")
def get_projects(
    status: Optional[str] = Query(None, description="项目状态"),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """获取项目列表"""
    query = db.query(BizProject).filter(BizProject.company_id == company_id)
    if status:
        query = query.filter(BizProject.status == status)

    projects = query.order_by(BizProject.id.desc()).all()
    return {"total": len(projects), "items": projects}


# ============================================================
# 银行账户
# ============================================================

@router.get("/bank-accounts", summary="获取银行账户列表")
def get_bank_accounts(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """获取银行账户列表"""
    accounts = db.query(BizBankAccount).filter(
        BizBankAccount.company_id == company_id
    ).order_by(BizBankAccount.sort_order, BizBankAccount.id).all()
    return {"total": len(accounts), "items": accounts}
