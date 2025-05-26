import pandas as pd
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import os
import re
import math
from slugify import slugify # pip install python-slugify

# --- Configuration ---
INPUT_BASE_DIR = '/Users/skyeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/common_words/input/'
OUTPUT_DIR = '/Users/skyeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/common_words/output'
TEMPLATE_DIR = '/Users/skyeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/common_words/templates'
CSS_FILE = '/Users/skyeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/common_words/style.css'
DEFAULT_BOOK_TITLE = "1000 Common German Words"

# --- ИЗМЕНЕНО: Имя файла для введения ---
INTRO_CSV = 'intro.csv' # Используем ваш новый intro.csv
WORDS_CSV = 'words.csv' # Остальные файлы пока оставляем
WORDS_CATEGORY_COL = 'Широкая категория'
WORDS_WORD_COL = 'Слово/фраза'
WORDS_TRANSCRIPTION_COL = 'Транскрипция'
WORDS_TRANSLATION_COL = 'Перевод'
DIALOGUES_CSV = 'dialogs.csv'
DIALOGUES_CATEGORY_COL = 'Категория'
DIALOGUES_IMAGE_REF_COL = 'Иллюстрация'
DIALOGUES_TEXT_COL = 'Диалог'

CATEGORY_ORDER = [
    "Приветствия и знакомства", "Основные глаголы", "Покупки и магазины",
    "Рестораны и кафе", "Путешествия и транспорт", "Семья и люди",
    "Дом и быт", "Здоровье и самочувствие", "Учёба и работа",
    "Хобби и повседневная жизнь"
]

# --- ИЗМЕНЕНО: Заголовки колонок из вашего нового intro.csv ---
# Основные текстовые блоки
INTRO_TITLE_COLS = ["Title_1", "Title_2", "Title_3"]
INTRO_TEXT_COLS = ["Text_1", "Text_2", "Text_3"]
# Таблица Особенностей (Грамматика)
INTRO_GRAMMAR_COLS = ["Особенность", "Краткое объяснение", "Пример"]
# Таблица Алфавита
INTRO_ALPHABET_COLS = ["Буква", "Название буквы", "Основной звук / Примерное произношение", "Примечания"]
# Дополнительный текст
INTRO_ADD_TEXT_COL = "Table_add_text"


os.makedirs(OUTPUT_DIR, exist_ok=True)
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
env.filters['slugify'] = slugify

def sanitize_filename(name):
    if not isinstance(name, str): name = str(name)
    name = re.sub(r'[\\/*?:"<>|]',"", name); name = name.replace(" ", "_")
    return name

def find_image_path(base_image_dir, dialogue_info):
    # (без изменений)
    image_filename = dialogue_info.get(DIALOGUES_IMAGE_REF_COL)
    if image_filename and isinstance(image_filename, str) and image_filename.strip():
        potential_path = os.path.join(base_image_dir, image_filename.strip())
        if os.path.exists(potential_path): return potential_path
        else: print(f"Warning: Image file not found at '{potential_path}'"); return None
    elif image_filename and not isinstance(image_filename, str) and not math.isnan(float(image_filename)):
         image_filename_str = str(int(float(image_filename))) + ".png"
         potential_path = os.path.join(base_image_dir, image_filename_str)
         if os.path.exists(potential_path): return potential_path
         else: print(f"Warning: Image file not found at '{potential_path}'"); return None
    return None


# --- ИЗМЕНЕНО: Функция парсинга intro.csv v4 ---
def parse_intro_data_v4(intro_df):
    """
    Парсит DataFrame из intro.csv со сложной структурой колонок.
    """
    intro_elements = []
    grammar_table_data = {'headers': INTRO_GRAMMAR_COLS, 'rows': []}
    alphabet_table_data = {'headers': INTRO_ALPHABET_COLS, 'rows': []}
    # Флаги, чтобы таблицы добавлялись в elements только один раз
    grammar_table_added = False
    alphabet_table_added = False

    for index, row in intro_df.iterrows():
        # Пропускаем строки, где все значения - NaN
        if row.isnull().all():
            continue

        # 1. Проверяем блоки Title/Text
        for i in range(3):
            title_col = INTRO_TITLE_COLS[i]
            text_col = INTRO_TEXT_COLS[i]
            if title_col in row and pd.notna(row[title_col]):
                # Считаем Title всегда заголовком H3 (можно изменить на H2)
                intro_elements.append({'type': 'h2', 'content': str(row[title_col]).strip()})
            if text_col in row and pd.notna(row[text_col]):
                # Считаем Text потенциально содержащим HTML
                intro_elements.append({'type': 'html_content', 'content': str(row[text_col]).strip()})

        # 2. Проверяем строку для таблицы Особенностей (Грамматики)
        # Считаем, что если есть значение в первой колонке таблицы, то это строка таблицы
        grammar_col1 = INTRO_GRAMMAR_COLS[0]
        if grammar_col1 in row and pd.notna(row[grammar_col1]):
            # Если таблица еще не добавлена в основной список, добавляем ее
            if not grammar_table_added:
                 intro_elements.append({'type': 'grammar_table', **grammar_table_data})
                 grammar_table_added = True
            # Добавляем данные строки
            grammar_table_data['rows'].append({
                'col1': str(row[grammar_col1]).strip(),
                'col2': str(row[INTRO_GRAMMAR_COLS[1]]).strip() if INTRO_GRAMMAR_COLS[1] in row and pd.notna(row[INTRO_GRAMMAR_COLS[1]]) else '',
                'col3': str(row[INTRO_GRAMMAR_COLS[2]]).strip() if INTRO_GRAMMAR_COLS[2] in row and pd.notna(row[INTRO_GRAMMAR_COLS[2]]) else ''
            })

        # 3. Проверяем строку для таблицы Алфавита
        alphabet_col1 = INTRO_ALPHABET_COLS[0]
        if alphabet_col1 in row and pd.notna(row[alphabet_col1]):
             if not alphabet_table_added:
                  intro_elements.append({'type': 'alphabet_table', **alphabet_table_data})
                  alphabet_table_added = True
             alphabet_table_data['rows'].append({
                'letter': str(row[alphabet_col1]).strip(),
                'name': str(row[INTRO_ALPHABET_COLS[1]]).strip() if INTRO_ALPHABET_COLS[1] in row and pd.notna(row[INTRO_ALPHABET_COLS[1]]) else '',
                'sound': str(row[INTRO_ALPHABET_COLS[2]]).strip() if INTRO_ALPHABET_COLS[2] in row and pd.notna(row[INTRO_ALPHABET_COLS[2]]) else '',
                'notes': str(row[INTRO_ALPHABET_COLS[3]]).strip() if INTRO_ALPHABET_COLS[3] in row and pd.notna(row[INTRO_ALPHABET_COLS[3]]) else ''
             })

        # 4. Проверяем дополнительный текст
        if INTRO_ADD_TEXT_COL in row and pd.notna(row[INTRO_ADD_TEXT_COL]):
             # Добавляем как параграф ПОСЛЕ таблицы, к которой он может относиться
             # (Эвристика: если последним элементом была таблица, добавляем после нее, иначе - просто в конец)
             # Простая версия: просто добавляем как параграф
             intro_elements.append({'type': 'p', 'content': str(row[INTRO_ADD_TEXT_COL]).strip()})


    # Очищаем пустые таблицы, если они были добавлены, но не наполнились
    final_elements = []
    for elem in intro_elements:
        if elem['type'] in ['grammar_table', 'alphabet_table']:
            if elem['rows']: # Добавляем таблицу, только если в ней есть строки
                final_elements.append(elem)
        else:
            final_elements.append(elem)


    return final_elements


def load_and_prepare_data(book_input_dir):
    """Loads data from CSVs and prepares it for templating."""
    data = {}
    words_df = pd.DataFrame()
    dialogues_df = pd.DataFrame()
    data['intro_elements'] = []

    # --- Load Intro ---
    intro_csv_path = os.path.join(book_input_dir, INTRO_CSV)
    if os.path.exists(intro_csv_path):
        try:
            # --- ИЗМЕНЕНО: Читаем CSV С ЗАГОЛОВКОМ ---
            # Предполагаем, что первая строка intro.csv - это заголовки колонок
            intro_df = pd.read_csv(intro_csv_path, header=0) # header=0 читает первую строку как заголовки
            data['intro_elements'] = parse_intro_data_v4(intro_df)
        except Exception as e:
            print(f"Warning: Could not load or parse intro CSV {intro_csv_path}: {e}")
            data['intro_elements'] = [{'type':'p', 'content':'Error loading introduction.'}]
    else:
         print(f"Warning: Intro CSV '{INTRO_CSV}' not found at {intro_csv_path}")

    # --- Load Words (без изменений) ---
    words_csv_path = os.path.join(book_input_dir, WORDS_CSV)
    # ... (код загрузки, сортировки, нумерации слов) ...
    if os.path.exists(words_csv_path):
        try:
            words_df = pd.read_csv(words_csv_path)
            words_df.dropna(subset=[WORDS_CATEGORY_COL, WORDS_WORD_COL], inplace=True)
            words_df = words_df.fillna('')
            words_df[WORDS_CATEGORY_COL] = pd.Categorical(words_df[WORDS_CATEGORY_COL], categories=CATEGORY_ORDER, ordered=True)
            ordered_words_df = words_df.sort_values(by=[WORDS_CATEGORY_COL, WORDS_WORD_COL], na_position='last').copy()
            ordered_words_df['global_index'] = range(1, len(ordered_words_df) + 1)
            data['words_by_category'] = ordered_words_df.groupby(WORDS_CATEGORY_COL, observed=True).apply(lambda x: x.to_dict('records')).to_dict()
        except Exception as e: print(f"Error loading and processing words CSV {words_csv_path}: {e}"); return None
    else: print(f"Error: Words CSV not found at {words_csv_path}"); return None


    # --- Load Dialogues (без изменений) ---
    dialogues_csv_path = os.path.join(book_input_dir, DIALOGUES_CSV)
    # ... (код загрузки диалогов и картинок) ...
    if os.path.exists(dialogues_csv_path):
         try:
            dialogues_df = pd.read_csv(dialogues_csv_path, dtype={DIALOGUES_IMAGE_REF_COL: str})
            dialogues_df.dropna(subset=[DIALOGUES_CATEGORY_COL, DIALOGUES_TEXT_COL], inplace=True)
            dialogues_df[[DIALOGUES_TEXT_COL, DIALOGUES_IMAGE_REF_COL]] = dialogues_df[[DIALOGUES_TEXT_COL, DIALOGUES_IMAGE_REF_COL]].fillna('')
            dialogues_df = dialogues_df.fillna('')
            data['dialogues_by_category'] = dialogues_df.groupby(DIALOGUES_CATEGORY_COL).apply(lambda x: x.to_dict('records')).to_dict()
            image_dir = os.path.join(book_input_dir, 'images')
            if os.path.isdir(image_dir):
                 for category in data['dialogues_by_category']:
                     for dialogue_info in data['dialogues_by_category'][category]:
                         dialogue_info['image_path'] = find_image_path(image_dir, dialogue_info)
            else: print(f"Warning: Image directory not found at {image_dir}")
         except Exception as e: print(f"Warning: Could not load dialogues CSV {dialogues_csv_path}: {e}"); data['dialogues_by_category'] = {}
    else: print(f"Warning: Dialogues CSV not found at {dialogues_csv_path}"); data['dialogues_by_category'] = {}

    data['category_order'] = CATEGORY_ORDER
    return data

def parse_dialogue_text(dialogue_text):
    """
    Парсит текст диалога и возвращает структурированные данные для chat-style.
    Ожидаемый формат: "Имя: текст" или "A: текст"
    """
    lines = dialogue_text.split('\n')
    parsed_lines = []
    speakers = {}
    speaker_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Пытаемся найти паттерн "Говорящий: текст"
        if ':' in line:
            parts = line.split(':', 1)
            potential_speaker = parts[0].strip()
            
            # Проверяем, что это действительно имя говорящего (не слишком длинное)
            if len(potential_speaker) <= 20 and not any(char in potential_speaker for char in ['?', '!', '.', ',']):
                speaker = potential_speaker
                text = parts[1].strip() if len(parts) > 1 else ''
                
                # Присваиваем каждому новому говорящему индекс
                if speaker not in speakers:
                    speaker_count += 1
                    speakers[speaker] = {
                        'index': speaker_count,
                        'initial': speaker[0].upper(),
                        'class': ['speaker-a', 'speaker-b', 'speaker-c', 'speaker-d'][(speaker_count - 1) % 4]
                    }
                
                parsed_lines.append({
                    'type': 'message',
                    'speaker': speaker,
                    'speaker_data': speakers[speaker],
                    'text': text,
                    'is_alt': speaker_count % 2 == 0  # Чередуем стороны для разных говорящих
                })
            else:
                # Это не реплика, а обычный текст
                parsed_lines.append({
                    'type': 'system',
                    'text': line
                })
        else:
            # Строка без двоеточия - системное сообщение
            parsed_lines.append({
                'type': 'system',
                'text': line
            })
    
    return parsed_lines

# --- generate_html_content (без изменений) ---
def generate_html_content(template_data, book_input_dir):
    """Generates the full HTML string using Jinja2 templates."""
    cover_template = env.get_template('cover.html')
    intro_template = env.get_template('intro.html')
    word_template = env.get_template('word_section.html')
    dialogue_template = env.get_template('dialog_section.html')
    logo_svg_path = os.path.join(book_input_dir, 'images', 'Skyeng Brand Icon.svg') # Лого для обложки

    cover_html = cover_template.render(
        title=template_data.get('book_title', DEFAULT_BOOK_TITLE),
        subtitle=template_data.get('book_subtitle', "Learn the Essentials"),
        logo_path = logo_svg_path if os.path.exists(logo_svg_path) else None
    )
    intro_html = intro_template.render(
         intro_elements=template_data.get('intro_elements', [])
    )
    category_sections_html = []
    for category in template_data['category_order']:
        # ... (логика рендеринга слов и диалогов) ...
        if category not in template_data['words_by_category'] and category not in template_data['dialogues_by_category']:
             print(f"Info: Category '{category}' from defined order not found. Skipping.")
             continue
        words = template_data['words_by_category'].get(category, [])
        if words:
            mapped_words = [{'global_index': w.get('global_index'), 'german_word': w.get(WORDS_WORD_COL),'transcription': w.get(WORDS_TRANSCRIPTION_COL), 'translation': w.get(WORDS_TRANSLATION_COL)} for w in words]
            category_sections_html.append(word_template.render(category_name=category, words=mapped_words))
        dialogues = template_data['dialogues_by_category'].get(category, [])
        if dialogues:
            mapped_dialogues = []
            for d in dialogues:
                dialogue_data = {
                    'title': d.get('Dialogue Title Column', None),
                    'image_path': d.get('image_path'),
                    'text': d.get(DIALOGUES_TEXT_COL, ''),
                    'parsed_lines': parse_dialogue_text(d.get(DIALOGUES_TEXT_COL, ''))
                }
            mapped_dialogues.append(dialogue_data)
            category_slug = slugify(category)
            category_sections_html.append(dialogue_template.render(category_name=category, dialogues=mapped_dialogues, category_slug=category_slug))


    full_html = f"""
    <!DOCTYPE html><html lang="de"><head><meta charset="UTF-8"><title>{template_data.get('book_title', DEFAULT_BOOK_TITLE)}</title></head>
    <body><div id="cover-page">{cover_html}</div><div id="intro-pages">{intro_html}</div><div id="main-content">{''.join(category_sections_html)}</div></body></html>
    """
    return full_html

# --- generate_book (без изменений) ---
def generate_book(book_id):
    print(f"--- Generating book: {book_id} ---")
    book_input_dir = os.path.join(INPUT_BASE_DIR, book_id)
    if not os.path.isdir(book_input_dir): print(f"Error: Input directory not found: {book_input_dir}"); return
    template_data = load_and_prepare_data(book_input_dir)
    if template_data is None: print(f"Failed to load data for {book_id}. Skipping."); return
    template_data['book_title'] = f"{DEFAULT_BOOK_TITLE} ({book_id})"
    print("Generating HTML content...")
    full_html_content = generate_html_content(template_data, book_input_dir)
    debug_html_path = os.path.join(OUTPUT_DIR, f"{sanitize_filename(book_id)}_debug.html")
    try:
        with open(debug_html_path, 'w', encoding='utf-8') as f: f.write(full_html_content)
        print(f"Debug HTML saved to: {debug_html_path}")
    except Exception as e: print(f"Warning: Could not save debug HTML: {e}")
    print("Generating PDF...")
    try:
        html = HTML(string=full_html_content, base_url=book_input_dir)
        css = CSS(filename=CSS_FILE)
        output_pdf_filename = os.path.join(OUTPUT_DIR, f"{sanitize_filename(book_id)}.pdf")
        html.write_pdf(output_pdf_filename, stylesheets=[css])
        print(f"Successfully generated: {output_pdf_filename}")
    except Exception as e: print(f"Error generating PDF for {book_id}: {e}")

if __name__ == "__main__":
    book_to_generate = "book_1"
    generate_book(book_to_generate)