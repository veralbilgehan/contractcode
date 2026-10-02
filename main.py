import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

# --- Configuration ---
load_dotenv()  # loads .env from project root

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment
ENV = os.getenv("ENVIRONMENT", "production")
PORT = int(os.getenv("PORT", "8000"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(
    title="ContractCode API",
    docs_url="/docs" if ENV == "development" else None,
    redoc_url=None,
)

# CORS — production'da sadece izin verilen origin'ler
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# LLM setup — Gemini (native CrewAI provider)
llm = LLM(model="gemini/gemini-3.8-flash", temperature=0)

# --- Simulated Legal Tools (replace with real RAG later) ---
@tool("search_legislation")
def search_legislation(query: str) -> str:
    """Search the legislation database for relevant statutes."""
    # TODO: integrate with a vector DB or legal API
    return "Borçlar Kanunu Madde 27: Yazılı sözleşmelerin ispat gücü ve şartları..."

@tool("search_case_law")
def search_case_law(query: str) -> str:
    """Search Yargıtay case law for relevant precedents."""
    # TODO: integrate with a case law search engine
    return "Yargıtay 3. HD, 2023/523 E. Kararı: Sözleşme maddelerinin açık niyet ilkesi..."

# --- Agents ---
legislation_expert = Agent(
    role="Mevzuat Araştırmacısı",
    goal="İlgili kanun maddelerini bulmak",
    backstory="Sadece mevzuat metni getirir, yorum yapmaz.",
    tools=[search_legislation],
    llm=llm,
    verbose=ENV == "development",
)

case_law_expert = Agent(
    role="İçtihat Uzmanı",
    goal="Emsal yargı kararlarını bulmak",
    backstory="Sadece gerçek karar numaralarıyla çalışan bir hukuk araştırmacısı.",
    tools=[search_case_law],
    llm=llm,
    verbose=ENV == "development",
)

synthesis_expert = Agent(
    role="Kıdemli Hukuk Analisti",
    goal="Mevzuat ve içtihatları sentezleyerek nihai raporu hazırlamak",
    backstory="Sadece verilen verilere dayanarak rapor üretir.",
    llm=llm,
    verbose=ENV == "development",
)

# --- Request models ---
class AnalysisRequest(BaseModel):
    documentText: str
    goal: str

class SearchRequest(BaseModel):
    query: str

class ChatRequest(BaseModel):
    message: str

# --- Health check ---
@app.get("/health")
def health_check():
    return {"status": "ok", "environment": ENV}

# Serve UI on root
@app.get("/")
def get_index():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "ok", "message": "ContractCode API aktif"}

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory=os.path.dirname(__file__)), name="static")

# --- MODE 1: Sözleşme Analizi ---
@app.post("/analyze")
async def analyze_legal_case(request: AnalysisRequest):
    logger.info("Sözleşme analizi isteği: amaç=%s", request.goal)
    try:
        task_leg = Task(
            description=(
                f"Sözleşme Metni: {request.documentText}\n"
                "İlgili kanun maddelerini bulun."
            ),
            expected_output="Kanun maddeleri ve tam metinleri listesi.",
            agent=legislation_expert,
        )
        task_case = Task(
            description=(
                f"Sözleşme Metni: {request.documentText}\n"
                "Benzer Yargıtay içtihatlarını bulun, karar numarası ve özetini getir."
            ),
            expected_output="Karar numarası, tarih ve temel prensipler.",
            agent=case_law_expert,
        )
        task_report = Task(
            description=(
                f"Mevzuat ve içtihat verilerini kullanarak aşağıdaki amaçla bir rapor üret: {request.goal}. "
                "Raporu HTML formatında, bölümler: [TESPIT], [MEVZUAT], [İÇTİHAT], [EYLEM ÖNERİSİ] şeklinde oluştur."
            ),
            expected_output="HTML yapılandırılmış hukuk analizi raporu.",
            agent=synthesis_expert,
            context=[task_leg, task_case],
        )

        crew = Crew(
            agents=[legislation_expert, case_law_expert, synthesis_expert],
            tasks=[task_leg, task_case, task_report],
            process=Process.sequential,
        )

        result = await crew.kickoff_async()
        logger.info("Sözleşme analizi tamamlandı.")
        return {"analysis": str(result)}
    except Exception as e:
        logger.error("Analiz hatası: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Analiz sırasında bir hata oluştu.")

# --- MODE 2: Mevzuat & İçtihat Arama ---
@app.post("/search")
async def search_legal(request: SearchRequest):
    logger.info("Mevzuat arama isteği: %s", request.query)
    try:
        task_leg = Task(
            description=(
                f"Konu: {request.query}\n"
                "Bu konuyla ilgili tüm kanun maddelerini bul. Madde numarası, kanun adı ve tam metnini getir."
            ),
            expected_output="İlgili kanun maddeleri listesi: kanun adı, madde numarası, tam metin.",
            agent=legislation_expert,
        )
        task_case = Task(
            description=(
                f"Konu: {request.query}\n"
                "Bu konuyla ilgili emsal Yargıtay kararlarını bul. Karar numarası, tarih ve özet getir."
            ),
            expected_output="Emsal kararlar listesi: daire, karar numarası, tarih, özet.",
            agent=case_law_expert,
        )
        task_summary = Task(
            description=(
                "Bulunan mevzuat ve içtihatları düzenli bir HTML rapor olarak özetle. "
                "Bölümler: [MEVZUAT] ilgili kanun maddeleri, [İÇTİHAT] emsal kararlar, [ÖZET] kısa değerlendirme."
            ),
            expected_output="HTML formatında mevzuat ve içtihat özet raporu.",
            agent=synthesis_expert,
            context=[task_leg, task_case],
        )

        crew = Crew(
            agents=[legislation_expert, case_law_expert, synthesis_expert],
            tasks=[task_leg, task_case, task_summary],
            process=Process.sequential,
        )

        result = await crew.kickoff_async()
        logger.info("Mevzuat araması tamamlandı.")
        return {"result": str(result)}
    except Exception as e:
        logger.error("Arama hatası: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Arama sırasında bir hata oluştu.")

# --- MODE 3: Hukuki Chatbot ---
@app.post("/chat")
async def legal_chat(request: ChatRequest):
    logger.info("Chat isteği: %s", request.message[:50])
    try:
        chatbot = Agent(
            role="Hukuk Danışmanı",
            goal="Kullanıcının hukuki sorusuna açık, anlaşılır ve doğru bilgi vermek",
            backstory=(
                "Türk hukuku konusunda uzman bir danışmansın. "
                "Kullanıcıya sade ve anlaşılır dilde bilgi verirsin. "
                "Gerektiğinde ilgili kanun maddelerine atıf yaparsın. "
                "Kesin hukuki tavsiye vermekten kaçınır, yönlendirme yaparsın."
            ),
            llm=llm,
            verbose=ENV == "development",
        )

        task = Task(
            description=(
                f"Kullanıcı sorusu: {request.message}\n\n"
                "Bu soruya Türk hukuku çerçevesinde açık ve anlaşılır bir yanıt ver. "
                "Yanıtı düz metin olarak yaz, kısa ve öz tut."
            ),
            expected_output="Kullanıcının sorusuna kısa, anlaşılır yanıt.",
            agent=chatbot,
        )

        crew = Crew(agents=[chatbot], tasks=[task], process=Process.sequential)
        result = await crew.kickoff_async()
        logger.info("Chat yanıtı oluşturuldu.")
        return {"reply": str(result)}
    except Exception as e:
        logger.error("Chat hatası: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Yanıt oluşturulamadı.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=ENV == "development")

