import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from services.extraction import extraction
from services.comparation import TenderMatcher
from services.contacts_matcher import CompanyContactMatcher

app = FastAPI()

# Подключаем статические файлы для HTML-шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(
        "C:\\Users\\mi\\Documents\\Diplom_Ali4i4\\static\\index.html",
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
        user_data = extraction(
            temp_file_path
        )  # Передаем путь к временно сохраненному файлу

        matcher = TenderMatcher(
            db_url="postgresql://postgres:12345@localhost:5433/postgres"
        )
        tenders_df, procurement_df = matcher.load_data()
        processed_user_data = matcher.process_user_data(user_data)
        procurement_codes = matcher.find_procurement_code(
            processed_user_data, procurement_df
        )
        similar_tenders = matcher.find_similar_tenders(
            processed_user_data, tenders_df, procurement_codes
        )
        contacts_matcher = CompanyContactMatcher(threshold=70, synonyms=None)
        contacts = contacts_matcher.find_contacts(set(user_data["Тендер"]["Возможные_поставщики"]))

        return user_data, similar_tenders, contacts
    finally:
        # Удаляем временный файл после обработки
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
