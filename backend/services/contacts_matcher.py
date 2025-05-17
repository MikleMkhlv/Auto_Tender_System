import pandas as pd
import re
from fuzzywuzzy import fuzz, process
import transliterate
from sqlalchemy import create_engine
import pandas as pd

class CompanyContactMatcher:
    def __init__(self, threshold=85, synonyms=None):
        self.threshold = threshold
        self.synonyms = synonyms or {}
        self.contacts_df = None
        self.normalized_contacts = None
        self.engine = create_engine('postgresql://postgres:12345@localhost:5433/postgres')

    def load_contacts(self):
        self.contacts_df = pd.read_sql('SELECT * FROM contracts', self.engine)
        self._prepare_contacts()

    def _prepare_contacts(self):
        if self.contacts_df is None:
            raise ValueError("Contacts data not loaded")

        self.contacts_df['normalized'] = self.contacts_df['supplier_sap_name'].apply(
            self._normalize_name
        )
        self.normalized_contacts = dict(
            zip(self.contacts_df['normalized'], self.contacts_df['Main_Point_of _Contact'])
        )

    def _normalize_name(self, name):
        # Проверка на кириллицу для транслитерации
        if any('\u0400' <= c <= '\u04FF' for c in str(name)):
            try:
                name = transliterate.translit(str(name), reversed=True)
            except:
                pass

        patterns = [
            r'\b(?:llc|inc|ltd|gmbh|ооо|ао|зао|пао|нко|ип|тд|оао|zao)\b',
            r'[^a-zа-я0-9\s]'
        ]
        name = re.sub('|'.join(patterns), '', str(name).lower(), flags=re.IGNORECASE)
        name = re.sub(r'\s+', ' ', name).strip()
        return self.synonyms.get(name, name)

    def _generate_email(self, normalized_name):
        """Генерация email адреса на основе нормализованного названия"""
        if pd.isna(normalized_name) or not normalized_name:
            return "sup_info@unknown.com"
            
        clean = re.sub(r'[^a-zа-я0-9]', '', normalized_name.lower())
        
        # Транслитерация кириллицы
        try:
            clean = transliterate.translit(clean, reversed=True)
        except:
            pass
            
        # Фильтрация оставшихся символов
        clean = re.sub(r'[^a-z0-9]', '', clean)
        return f"sup_info@{clean[:25]}.com" if clean else "sup_info@unknown.com"

    def find_contacts(self, company_names):
        if self.normalized_contacts is None:
            raise ValueError("Contacts data not prepared")

        normalized_input = [self._normalize_name(name) for name in company_names]
        results = []
        
        for orig, norm in zip(company_names, normalized_input):
            match = self._find_best_match(norm)
            results.append(self._format_result(orig, norm, match))
            
        results_df = pd.DataFrame(results)
        results_df['contact_info'] = results_df['contact_info'].fillna(
            results_df['normalized_name'].apply(self._generate_email)
        )
        
        return results_df.to_dict(orient='list')

    def _find_best_match(self, norm_name):
        best_match = process.extractOne(
            norm_name,
            self.normalized_contacts.keys(),
            scorer=fuzz.token_set_ratio
        )
        if best_match and best_match[1] >= self.threshold:
            return {
                'matched_name': best_match[0],
                'confidence': best_match[1],
                'contact_info': self.normalized_contacts[best_match[0]]
            }
        return None

    def _format_result(self, orig, norm, match):
        return {
            'original_name': orig,
            'normalized_name': norm,
            'matched_company': match['matched_name'] if match else None,
            'confidence': match['confidence'] if match else 0,
            'contact_info': match['contact_info'] if match else None
        }

# Пример использования
if __name__ == "__main__":
    # Пример данных
    contacts_data = {
        'supplier_sap_name': [
            'Delta Origin Ltd.', 
            'Algimed LLC', 
            'AppScience Inc.',
            'Фармреактив ООО'
        ],
        'Main Point of Contact': [
            'contact@delta.com', 
            'info@algimed.ru', 
            'support@appscience.org',
            'pharm@mail.ru'
        ]
    }
    contacts_df = pd.DataFrame(contacts_data)

    # Инициализация объекта
    matcher = CompanyContactMatcher(
        threshold=70,
        synonyms=None
    )

    # Загрузка контактов
    matcher.load_contacts()

    # Поиск контактов
    company_set = {'ООО Дельта Ориджин', 'Альгимед OOO', 'AppScience', 'Фармреактив'}
    results = matcher.find_contacts(company_set)
    
    print(results)