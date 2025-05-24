import os
import tempfile
import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from services.extraction import extraction
from services.comparation import TenderMatcher
from services.contacts_matcher import CompanyContactMatcher
from services.mapper import ContractFiller
app = FastAPI()

# Подключаем статические файлы для HTML-шаблонов
app.mount("/static", StaticFiles(directory="C:\\Users\\mi\\Documents\\Diplom_Ali4i4\\Auto_Tender_System\\static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(
        "C:\\Users\\mi\\Documents\\Diplom_Ali4i4\\Auto_Tender_System\\static\\index.html",
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as f:
        return f.read()
    
@app.get("/offer", response_class=HTMLResponse)
async def index():
    with open(
        "C:\\Users\\mi\\Documents\\Diplom_Ali4i4\\Auto_Tender_System\\static\\offer.html",
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as f:
        return f.read()
    
@app.get("/home", response_class=HTMLResponse)
async def index():
    with open(
        "C:\\Users\\mi\\Documents\\Diplom_Ali4i4\\Auto_Tender_System\\static\\home.html",
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as f:
        return f.read()


@app.post("/api/analyze-file")
async def match_tender(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="Нет файла")

    # Создаем временный файл с расширением .msg
    temp_file_path = tempfile.mktemp(suffix=".msg")
    contents = await file.read()

    # Сохраняем загруженный файл
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(contents)

    try:
        time.sleep(5)
        # user_data = extraction(
        #     temp_file_path
        # )  # Передаем путь к временно сохраненному файлу

        # matcher = TenderMatcher(
        #     db_url="postgresql://postgres:12345@localhost:5433/postgres"
        # )
        # tenders_df, procurement_df = matcher.load_data()
        # processed_user_data = matcher.process_user_data(user_data)
        # procurement_codes = matcher.find_procurement_code(
        #     processed_user_data, procurement_df
        # )
        # similar_tenders = matcher.find_similar_tenders(
        #     processed_user_data, tenders_df, procurement_codes
        # )
        # contacts_matcher = CompanyContactMatcher(threshold=70, synonyms=None)
        # contacts = contacts_matcher.find_contacts(set(user_data["Тендер"]["Возможные_поставщики"]))

        return {}  
    finally:
        # Удаляем временный файл после обработки
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/api/fill_NDA")
async def fill_NDA(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="Нет файла")

    # Создаем временный файл с расширением .msg
    temp_file_path = tempfile.mktemp(suffix=".xlsx")
    contents = await file.read()

    # Сохраняем загруженный файл
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(contents)
    
    filler = ContractFiller(template_path = "C:\\Users\\mi\\Documents\\Diplom_Ali4i4\\Auto_Tender_System\\NDA.docx",
                            output_path="C:\\Users\\mi\\Documents\\Diplom_Ali4i4\\Auto_Tender_System\\готовый_NDA.docx",
                            excel_path=temp_file_path)
    try:
        filler.run()
        return FileResponse(
            path="C:\\Users\\mi\\Documents\\Diplom_Ali4i4\\Auto_Tender_System\\готовый_NDA.docx",
            filename="filled_NDA.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    finally:
        # Удаляем временный файл после обработки
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
