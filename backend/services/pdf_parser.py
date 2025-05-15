import pdfplumber

class PDFToStringConverter:
    def __init__(self, file_path: str):
        """
        Инициализирует конвертер с указанным путем к PDF-файлу.
        
        :param file_path: Путь к PDF-файлу
        """
        self.file_path = file_path

    def convert_to_string(self) -> str | None:
        """
        Извлекает текст из PDF-файла и возвращает его в виде строки.
        
        :return: Текст PDF-файла или None в случае ошибки
        """
        try:
            with pdfplumber.open(self.file_path) as pdf:
                extracted_text = []
                
                # Чтение каждой страницы и извлечение текста
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text.append(text)
                
                return "\n".join(extracted_text) if extracted_text else ""
        
        except FileNotFoundError:
            print(f"Ошибка: файл '{self.file_path}' не найден.")
            return None
        except Exception as e:
            print(f"Ошибка при обработке PDF-файла: {e}")
            return None