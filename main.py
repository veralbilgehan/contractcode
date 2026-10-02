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

# --- Request model ---
class AnalysisRequest(BaseModel):
    documentText: str
    goal: str

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

@app.post("/analyze")
async def analyze_legal_case(request: AnalysisRequest):
    logger.info("Analiz isteği alındı: amaç=%s", request.goal)
    try:
        # Define tasks
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
        logger.info("Analiz başarıyla tamamlandı.")
        return {"analysis": str(result)}
    except Exception as e:
        logger.error("Analiz hatası: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Analiz sırasında bir hata oluştu. Lütfen tekrar deneyin.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=ENV == "development")
