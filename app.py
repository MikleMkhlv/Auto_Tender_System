import os
import tempfile
from flask import Flask, request, jsonify, render_template
from extraction import extraction 
from comparation import TenderMatcher 

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # Убедитесь, что файл index.html находится в папке templates

@app.route('/api/match-tender', methods=['POST'])
def match_tender():
    if 'file' not in request.files:
        return jsonify({'error': 'Нет файла'}), 400

    file = request.files['file']

    # Создаем временный файл
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file.save(temp_file.name)  # Сохраняем загруженный файл
        temp_file_path = temp_file.name  # Получаем путь к временно сохраненному файлу

    try:
        user_data = extraction(temp_file_path)  # Передаем путь к временно сохраненному файлу

        matcher = TenderMatcher(db_url='postgresql://postgres:12345@localhost:5433/postgres')
        tenders_df, procurement_df = matcher.load_data()
        processed_user_data = matcher.process_user_data(user_data)
        procurement_codes = matcher.find_procurement_code(processed_user_data, procurement_df)
        similar_tenders = matcher.find_similar_tenders(processed_user_data, tenders_df, procurement_codes)

        return jsonify(similar_tenders)
    finally:
        # Удаляем временный файл после обработки
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == '__main__':
    app.run(debug=True)