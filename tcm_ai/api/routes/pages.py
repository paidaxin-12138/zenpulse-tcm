from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["页面"])

_LEGAL_PAGES = {
    "privacy": "frontend/legal/privacy.html",
    "terms": "frontend/legal/terms.html",
    "algorithm": "frontend/legal/algorithm.html",
}


@router.get("/")
async def root():
    return FileResponse("frontend/index.html")


@router.get("/admin")
async def admin_page():
    return FileResponse("admin/index.html")


@router.get("/legal/{page}")
async def legal_page(page: str):
    path = _LEGAL_PAGES.get(page)
    if not path:
        raise HTTPException(status_code=404, detail="页面不存在")
    return FileResponse(path)


@router.get("/@vite/client")
async def vite_client():
    return ""
