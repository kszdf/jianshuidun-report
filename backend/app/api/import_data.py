"""
导入API - Excel数据导入
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_company_id, get_current_user
from app.models.system import SysUser
from app.services.import_service import (
    import_balance_file,
    import_voucher_file,
    detect_excel_type,
    save_upload_file,
)
from app.services.mapping_service import get_mapping_stats, auto_map_subjects

router = APIRouter()


@router.post("/preview", summary="预览上传文件 - 识别类型")
async def preview_file(
    file: UploadFile = File(...),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """上传文件并预览，自动识别文件类型"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="请上传文件")

    # 检查文件类型
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="仅支持Excel文件(.xlsx, .xls)")

    # 保存文件
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=400, detail="文件大小不能超过50MB")

    file_path = save_upload_file(content, file.filename)

    # 识别类型
    try:
        file_type, header_row, col_mapping = detect_excel_type(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    type_names = {
        "balance": "科目余额表",
        "voucher": "凭证表/序时账",
        "unknown": "无法识别",
    }

    return {
        "filename": file.filename,
        "file_type": file_type,
        "file_type_name": type_names.get(file_type, "未知"),
        "header_row": header_row,
        "columns_detected": col_mapping,
        "can_import": file_type != "unknown",
        "file_path": file_path,
    }


@router.post("/balance", summary="导入科目余额表")
async def import_balance(
    file: UploadFile = File(...),
    period: Optional[str] = Form(None, description="期间 YYYY-MM，默认本月"),
    source_software: Optional[str] = Form(None, description="来源财务软件"),
    company_id: int = Depends(get_current_company_id),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """导入科目余额表Excel，自动识别并映射科目"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="请上传文件")

    content = await file.read()
    file_path = save_upload_file(content, file.filename)

    try:
        result = import_balance_file(
            db=db,
            company_id=company_id,
            file_path=file_path,
            source_file=file.filename,
            source_software=source_software or "",
            period=period,
        )
        result["imported_by"] = current_user.username
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")


@router.post("/voucher", summary="导入凭证表/序时账")
async def import_voucher(
    file: UploadFile = File(...),
    source_software: Optional[str] = Form(None, description="来源财务软件"),
    company_id: int = Depends(get_current_company_id),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """导入凭证表/序时账Excel，自动识别并映射科目"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="请上传文件")

    content = await file.read()
    file_path = save_upload_file(content, file.filename)

    try:
        result = import_voucher_file(
            db=db,
            company_id=company_id,
            file_path=file_path,
            source_file=file.filename,
            source_software=source_software or "",
        )
        result["imported_by"] = current_user.username
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")


@router.post("/auto-map", summary="重新执行自动科目映射")
def re_auto_map(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """基于已有企业科目，重新执行一遍自动映射（不覆盖手动映射）"""
    from app.models.config import CfgSubjectMapping

    # 收集所有企业科目
    mappings = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.company_id == company_id
    ).all()

    subjects = [{
        "code": m.source_code,
        "name": m.source_name,
        "full_name": m.source_full_name,
    } for m in mappings if m.match_type != "manual"]

    if not subjects:
        return {"message": "没有需要重新映射的科目", "total": 0}

    result = auto_map_subjects(db, company_id, subjects)
    return result


@router.get("/mapping-stats", summary="获取科目映射统计")
def mapping_stats(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """获取科目映射完成度统计"""
    return get_mapping_stats(db, company_id)


@router.get("/batches", summary="获取导入批次列表")
def get_import_batches(
    import_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """获取导入历史批次"""
    from app.models.finance import ImpBatch

    query = db.query(ImpBatch).filter(ImpBatch.company_id == company_id)
    if import_type:
        query = query.filter(ImpBatch.import_type == import_type)

    total = query.count()
    batches = query.order_by(ImpBatch.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": batches,
    }
