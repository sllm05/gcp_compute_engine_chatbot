import os
import json
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gemini-chatbot-adc")

# Google GenAI SDK 내부 AFC 권고 경고 필터링
logging.getLogger("google_genai.models").setLevel(logging.ERROR)

# GCP 프로젝트 및 리전 설정 (환경변수 자동 감지 또는 기본값)
PROJECT_ID = (
    os.environ.get("GOOGLE_CLOUD_PROJECT")
    or os.environ.get("GCP_PROJECT")
    or "iceu-songpa09"
)
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"

from google import genai
from google.genai import types

def get_client() -> genai.Client:
    """
    GCP Agent Platform / Vertex AI 기반 ADC(Application Default Credentials) 클라이언트 초기화.
    API 키 없이 인프라 자체의 서비스 계정 자격 증명을 자동으로 사용하여 인증합니다.
    """
    try:
        return genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION
        )
    except Exception as e:
        logger.error(f"ADC Client 초기화 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ADC(Application Default Credentials) 인증에 실패했습니다: {str(e)}"
        )

app = FastAPI(
    title="Gemini Chatbot Web Service (ADC / Agent Platform)",
    description="Google Cloud Run 기반 ADC(Application Default Credentials) 연동 챗봇"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 파비콘 404 방지 핸들러
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# 데이터 모델 정의
class MessageItem(BaseModel):
    role: str  # 'user' 또는 'model'
    content: str

class ChatRequest(BaseModel):
    model: str = "gemini-2.5-flash"
    messages: List[MessageItem]
    system_instruction: Optional[str] = (
        "당신은 Google Cloud Agent Platform 기반 첨단 AI 어시스턴트 Gemini입니다. "
        "사용자에게 친절하고 신속하며 정확한 답변을 제공하세요. "
        "최신 정보, 뉴스, 날씨, 주가, 환율 등 실시간 정보가 필요한 질의에는 "
        "실시간 웹 검색(Google Search)을 적극 활용하여 가장 정확한 출처와 정보를 제공하세요. "
        "수식이나 코드가 포함된 경우 마크다운 형식으로 가독성 높게 작성하세요."
    )
    temperature: Optional[float] = 0.7
    enable_search: Optional[bool] = True

# Agent Platform / Vertex AI 지원 모델 목록
AVAILABLE_MODELS = [
    {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "shortName": "Flash 2.5",
        "badge": "ADC Flash",
        "version": "2.5",
        "description": "Agent Platform 초고속 플래시 모델 + 실시간 검색 그라운딩",
        "isDefault": True,
        "supportsSearch": True,
    },
    {
        "id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "shortName": "Pro 2.5",
        "badge": "ADC Pro",
        "version": "2.5",
        "description": "Agent Platform 고성능 심층 추론 프로 모델",
        "isDefault": False,
        "supportsSearch": True,
    }
]

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "platform": "Google Cloud Run (Vertex AI / Agent Platform)",
        "authMode": "ADC (Application Default Credentials - Keyless)",
        "projectId": PROJECT_ID,
        "location": LOCATION,
        "defaultModel": "gemini-2.5-flash",
        "realtimeSearchSupported": True,
        "models": [m["id"] for m in AVAILABLE_MODELS]
    }

@app.get("/api/models")
async def list_models():
    return {"models": AVAILABLE_MODELS}

@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    selected_model = request.model
    # 모델 유효성 검사 (기본값: gemini-2.5-flash)
    valid_ids = [m["id"] for m in AVAILABLE_MODELS]
    if selected_model not in valid_ids:
        selected_model = "gemini-2.5-flash"

    client = get_client()

    # Gemini 메시지 포맷 변환
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

            # ADC를 통한 스트리밍 생성 호출
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
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
