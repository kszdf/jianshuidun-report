"""
税检康线索提交 API
用户在税检康H5页面提交检测结果后，写入飞书多维表
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import json

from app.services.feishu_bitable import get_bitable_service
from app.core.config import settings

router = APIRouter()


class TaxCheckSubmission(BaseModel):
    """税检康检测结果提交"""
    phone: str = Field(..., description="手机号")
    company_name: Optional[str] = Field("", description="企业名称")
    contact_name: Optional[str] = Field("", description="联系人")
    industry: Optional[str] = Field("", description="所属行业")
    total_score: Optional[float] = Field(0, description="检测总分")
    risk_level: Optional[str] = Field("", description="风险等级")
    dimension_scores: Optional[Dict[str, Any]] = Field(default_factory=dict, description="各维度得分")
    answers: Optional[Dict[str, Any]] = Field(default_factory=dict, description="答题详情")
    submit_time: Optional[str] = Field("", description="提交时间")


@router.post("/submit")
async def submit_tax_check(data: TaxCheckSubmission):
    """
    提交税检康检测结果，写入飞书多维表
    """
    try:
        # 构造飞书多维表字段
        fields = {
            "手机号": data.phone,
            "企业名称": data.company_name or "",
            "联系人": data.contact_name or "",
            "所属行业": data.industry or "",
            "检测总分": data.total_score or 0,
            "风险等级": data.risk_level or "",
            "维度得分": json.dumps(data.dimension_scores, ensure_ascii=False) if data.dimension_scores else "",
            "答题详情": json.dumps(data.answers, ensure_ascii=False) if data.answers else "",
            "跟进状态": "待跟进",
            "跟进备注": "",
            "提交时间": data.submit_time or "",
        }

        # 调用飞书多维表服务
        bitable = get_bitable_service()
        app_token = getattr(settings, 'FEISHU_BITABLE_APP_TOKEN', '')
        table_id = getattr(settings, 'FEISHU_BITABLE_TABLE_ID', '')

        if not app_token or not table_id:
            # 未配置飞书多维表时，返回模拟成功（不影响用户体验）
            return {
                "success": True,
                "simulated": True,
                "message": "未配置飞书多维表，模拟提交成功",
                "record_id": "simulated"
            }

        record = bitable.add_record(app_token, table_id, fields)

        return {
            "success": True,
            "simulated": False,
            "message": "提交成功",
            "record_id": record.get("record_id", ""),
            "data": record
        }

    except Exception as e:
        # 出错时返回成功但标记失败，不影响用户体验
        return {
            "success": False,
            "message": f"提交失败: {str(e)}"
        }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "taxcheck-api"}
