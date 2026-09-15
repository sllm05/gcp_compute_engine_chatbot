import os
import json
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# 환경변수 로드 (.env 파일이 있으면 로드, 시스템 환경변수 우선)
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gemini-chatbot")

# Gemini API Client 초기화
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not api_key:
    logger.warning("경고: GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.")

from google import genai
from google.genai import types

def get_client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise HTTPException(
            status_code=500,
            detail="서버 환경변수에 GEMINI_API_KEY가 설정되어 있지 않습니다."
        )
    return genai.Client(api_key=key)

app = FastAPI(title="Gemini Chatbot Web Service")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터 모델 정의
class MessageItem(BaseModel):
    role: str  # 'user' 또는 'model'
    content: str

class ChatRequest(BaseModel):
    model: str = "gemini-3.8-flash"
    messages: List[MessageItem]
    system_instruction: Optional[str] = (
        "당신은 Google의 첨단 AI 어시스턴트 Gemini입니다. "
        "사용자에게 친절하고 신속하며 유익한 답변을 제공하세요. "
        "최신 정보, 뉴스, 날씨, 주가, 환율 등 실시간 정보가 필요한 질의에는 "
        "실시간 웹 검색(Google Search)을 적극 활용하여 가장 정확한 최신 정보를 제공하세요. "
        "수식이나 코드가 포함된 경우 마크다운 형식으로 가독성 높게 작성하세요."
    )
    temperature: Optional[float] = 0.7
    enable_search: Optional[bool] = True

AVAILABLE_MODELS = [
    {
        "id": "gemini-3.8-flash",
        "name": "Gemini 3.8 Flash",
        "shortName": "Flash 3.8",
        "badge": "Flash",
        "version": "3.8",
        "description": "최신 고속 플래시 모델 + 실시간 검색 그라운딩",
        "isDefault": True,
        "supportsSearch": True,
    },
    {
        "id": "gemini-3.7-flash",
        "name": "Gemini 3.7 Flash",
        "shortName": "Flash 3.7",
        "badge": "Flash",
        "version": "3.7",
        "description": "고효율 멀티모달 플래시 모델 + 실시간 검색 지원",
        "isDefault": False,
        "supportsSearch": True,
    }
]

@app.get("/api/health")
async def health_check():
    key_exists = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    return {
        "status": "ok",
        "apiKeyConfigured": key_exists,
        "defaultModel": "gemini-3.8-flash",
        "realtimeSearchSupported": True,
        "models": [m["id"] for m in AVAILABLE_MODELS]
    }

@app.get("/api/models")
async def list_models():
    return {"models": AVAILABLE_MODELS}

@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    selected_model = request.model
    # 모델 유효성 검사 (기본값: gemini-3.8-flash)
    valid_ids = [m["id"] for m in AVAILABLE_MODELS]
    if selected_model not in valid_ids:
        selected_model = "gemini-3.8-flash"

    try:
        client = get_client()
    except Exception as e:
        logger.error(f"Client init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Gemini 메시지 포맷으로 변환
    formatted_contents = []
    for msg in request.messages:
        role = "user" if msg.role == "user" else "model"
        formatted_contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg.content)]
            )
        )

    if not formatted_contents:
        raise HTTPException(status_code=400, detail="메시지가 비어 있습니다.")

    async def event_generator():
        try:
            # 실시간 웹 검색 (Google Search Grounding) 도구 설정
            tools = []
            if request.enable_search:
                tools.append(types.Tool(google_search=types.GoogleSearch()))

            config = types.GenerateContentConfig(
                system_instruction=request.system_instruction,
                temperature=request.temperature,
                tools=tools if tools else None,
            )

            # 스트리밍 생성 호출
            response_stream = client.models.generate_content_stream(
                model=selected_model,
                contents=formatted_contents,
                config=config,
            )

            search_queries_set = set()
            sources_list = []
            seen_uris = set()

            for chunk in response_stream:
                # 1. 텍스트 청크 전송
                if chunk.text:
                    payload = json.dumps({"text": chunk.text}, ensure_ascii=False)
                    yield f"data: {payload}\n\n"

                # 2. 실시간 검색 메타데이터(Grounding Metadata) 확인 및 추출
                if chunk.candidates and len(chunk.candidates) > 0:
                    cand = chunk.candidates[0]
                    gm = getattr(cand, "grounding_metadata", None)
                    if gm:
                        # 검색 질의어 추출
                        if getattr(gm, "web_search_queries", None):
                            for q in gm.web_search_queries:
                                if q and q not in search_queries_set:
                                    search_queries_set.add(q)

                        # 검색 출처(웹사이트 링크 및 제목) 추출
                        if getattr(gm, "grounding_chunks", None):
                            for g_chunk in gm.grounding_chunks:
                                web = getattr(g_chunk, "web", None)
                                if web and getattr(web, "uri", None):
                                    uri = web.uri
                                    if uri not in seen_uris:
                                        seen_uris.add(uri)
                                        sources_list.append({
                                            "title": getattr(web, "title", "웹 출처") or "웹 출처",
                                            "uri": uri
                                        })

            # 실시간 검색 결과 메타데이터가 존재하면 전송
            if search_queries_set or sources_list:
                grounding_payload = json.dumps({
                    "grounding": {
                        "search_queries": list(search_queries_set),
                        "sources": sources_list
                    }
                }, ensure_ascii=False)
                yield f"data: {grounding_payload}\n\n"

            # 완료 신호 전송
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as err:
            logger.error(f"Generation error: {err}")
            error_payload = json.dumps({"error": str(err)}, ensure_ascii=False)
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

# static 디렉터리 서빙 (정적 웹 프론트엔드)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # GCP Compute Engine 및 로컬 모두에서 접근 가능하도록 0.0.0.0 바인딩
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
