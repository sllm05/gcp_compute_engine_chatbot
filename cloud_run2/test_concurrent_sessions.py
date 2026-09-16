import asyncio
import json
import time
import sys
from datetime import datetime
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CLOUD_RUN_URL = "https://gemini-chatbot-adc-dnrhuomuhq-du.a.run.app"
CHAT_ENDPOINT = f"{CLOUD_RUN_URL}/api/chat"

QUESTIONS_SESSION_A = [
    "안녕하세요! 클라우드 런(Cloud Run)의 주요 특징 3가지를 한 줄씩 간단히 알려주세요.",
    "방금 말씀해주신 특징 중 '자동 확장(Auto-scaling)'은 0에서 몇 개까지 가능한가요?",
    "파이썬에서 비동기 프로그래밍(async/await)을 사용할 때의 핵심 이점은 무엇인가요?",
    "FastAPI와 Flask를 비교했을 때 성능과 비동기 처리 관점에서 가장 큰 차이는 무엇인가요?",
    "지금까지의 대화 내용을 바탕으로 클라우드 런에서 고성능 비동기 API 서버를 운영할 때의 핵심 요약 1줄을 남겨주세요."
]

QUESTIONS_SESSION_B = [
    "안녕하세요! Gemini 2.5 Flash 모델의 가장 큰 장점 2가지를 간단히 알려주세요.",
    "방금 언급하신 장점 중 '실시간 검색 그라운딩(Search Grounding)' 기능은 어떻게 동작하나요?",
    "대규모 언어 모델(LLM)에서 컨텍스트 윈도우(Context Window)가 크면 어떤 이점이 있나요?",
    "실시간 웹 검색을 결합한 답변과 순수 사전학습 가중치 답변의 가장 큰 차이점은 무엇인가요?",
    "오늘 서울의 날씨나 최신 주요 이슈를 실시간 검색으로 간단히 1~2줄로 브리핑해줘."
]

async def stream_turn(client: httpx.AsyncClient, session_name: str, turn_idx: int, question: str, history: list) -> tuple[str, float, list, list]:
    """단일 질의응답 턴을 SSE 스트리밍 방식으로 실행하고 응답을 수집합니다."""
    # 사용자 메시지 히스토리에 추가
    history.append({"role": "user", "content": question})
    
    payload = {
        "model": "gemini-2.5-flash",
        "messages": history,
        "enable_search": True,
        "temperature": 0.7
    }
    
    start_t = time.perf_counter()
    full_text = []
    search_queries = []
    sources = []
    
    print(f"\n[{session_name}] [Turn {turn_idx}/5] 🚀 질문 발송: {question}")
    
    try:
        async with client.stream("POST", CHAT_ENDPOINT, json=payload, timeout=60.0) as response:
            if response.status_code != 200:
                print(f"[{session_name}] [Turn {turn_idx}/5] ❌ HTTP Error: {response.status_code}")
                return f"HTTP {response.status_code}", time.perf_counter() - start_t, [], []
                
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                try:
                    data = json.loads(data_str)
                    if "text" in data:
                        full_text.append(data["text"])
                    if "grounding" in data:
                        search_queries.extend(data["grounding"].get("search_queries", []))
                        sources.extend(data["grounding"].get("sources", []))
                    if "error" in data:
                        print(f"[{session_name}] [Turn {turn_idx}/5] ⚠️ Server Error in stream: {data['error']}")
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        print(f"[{session_name}] [Turn {turn_idx}/5] 💥 통신 예외 발생: {e}")
        return f"Error: {e}", time.perf_counter() - start_t, [], []

    elapsed = time.perf_counter() - start_t
    answer = "".join(full_text).strip()
    
    # 모델 응답 히스토리에 추가
    history.append({"role": "model", "content": answer})
    
    preview = answer[:100].replace("\n", " ") + ("..." if len(answer) > 100 else "")
    print(f"[{session_name}] [Turn {turn_idx}/5] ✅ 응답 수신 완료 ({elapsed:.2f}s, {len(answer)}자)")
    print(f"   💬 요약 답변: {preview}")
    if search_queries:
        print(f"   🔍 실시간 검색어: {search_queries}")
    if sources:
        print(f"   🌐 참조 웹 소스 개수: {len(sources)}개")
        
    return answer, elapsed, search_queries, sources

async def run_session(session_name: str, questions: list[str]) -> list[dict]:
    """단일 가상 유저 세션을 연속 5턴으로 실행합니다."""
    history = []
    session_results = []
    
    # 브라우저와 동일한 헤더 설정 (ASCII 규격 준수)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
        for idx, q in enumerate(questions, 1):
            ans, duration, queries, sources = await stream_turn(client, session_name, idx, q, history)
            session_results.append({
                "turn": idx,
                "question": q,
                "answer": ans,
                "duration": duration,
                "queries": queries,
                "sources_count": len(sources)
            })
            # 브라우저 사용자 반응 시간(약간의 딜레이) 시뮬레이션
            await asyncio.sleep(0.5)
            
    return session_results

async def main():
    print("=" * 70)
    print(f"🌟 Cloud Run 동시 2개 세션 연속 5질의 부하 및 멀티턴 테스트 시작")
    print(f"대상 서비스 URL: {CLOUD_RUN_URL}")
    print(f"시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    test_start_t = time.perf_counter()
    
    # 두 세션을 동시에 병렬 실행
    results_a, results_b = await asyncio.gather(
        run_session("Session A (클라우드/아키텍처)", QUESTIONS_SESSION_A),
        run_session("Session B (AI/제미나이/검색)", QUESTIONS_SESSION_B)
    )
    
    total_elapsed = time.perf_counter() - test_start_t
    
    print("\n" + "=" * 70)
    print("📊 [테스트 결과 종합 리포트]")
    print(f"총 소요 시간: {total_elapsed:.2f}초 (동시 2개 세션 총 10회 연속 스트리밍 질의)")
    print("=" * 70)
    
    avg_a = sum(r["duration"] for r in results_a) / len(results_a)
    avg_b = sum(r["duration"] for r in results_b) / len(results_b)
    
    print(f"\n[Session A 결과]")
    print(f" - 평균 응답 시간: {avg_a:.2f}초")
    for r in results_a:
        print(f"   * Turn {r['turn']}: {r['duration']:.2f}s | Q: {r['question'][:30]}...")
        
    print(f"\n[Session B 결과]")
    print(f" - 평균 응답 시간: {avg_b:.2f}초")
    for r in results_b:
        print(f"   * Turn {r['turn']}: {r['duration']:.2f}s | Q: {r['question'][:30]}... | 검색어: {r['queries']}")

    # 결과 JSON 저장
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "total_elapsed": total_elapsed,
        "session_a": results_a,
        "session_b": results_b
    }
    with open("c:/AI-Native-Agent/gcp_compute_engine_chatbot/cloud_run2/test_results.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("\n💾 상세 결과가 test_results.json에 저장되었습니다.")

if __name__ == "__main__":
    asyncio.run(main())
