from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api import router as chat_router
from config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

# 注册 API 路由
app.include_router(chat_router)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """返回首页"""
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
