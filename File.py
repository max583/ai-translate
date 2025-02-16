import re
import os
import time
import chardet
from Configuration import *
import AIInterface
import concurrent.futures

def split_text_into_sentences(text):
    # Регулярное выражение для поиска концов предложений
    sentence_endings = r'(?<=[.!?…])\s+(?=[А-ЯA-Z])'

    # Разбиваем текст на предложения с учётом прямой речи
    sentences = re.split(sentence_endings, text)

    # Объединяем предложения, если они являются частью прямой речи
    merged_sentences = []
    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        # Проверяем, начинается ли предложение с тире (прямая речь)
        if sentence.startswith('—'):
            # Если следующее предложение также начинается с тире, объединяем их
            while i + 1 < len(sentences) and sentences[i + 1].startswith('—'):
                sentence += ' ' + sentences[i + 1]
                i += 1
        merged_sentences.append(sentence)
        i += 1

    return merged_sentences

def log(text):
    with open(f'{PROCESSED_DIRECTORY}\\log.txt', 'a', encoding='utf-8') as f:
        f.write(f'{text}\n')

class File :
    def __init__(self, path):
        self.path = path
        self.translated_file_path = f'{TRANSLATED_DIRECTORY}\\{os.path.basename(self.path)}'
        self.processed_file_path = f'{PROCESSED_DIRECTORY}\\{os.path.basename(self.path)}'
        self.ai_interface = AIInterface.AIInterface()
        if not os.path.isdir(TRANSLATED_DIRECTORY):
            os.mkdir(TRANSLATED_DIRECTORY)
        if not os.path.isdir(PROCESSED_DIRECTORY):
            os.mkdir(PROCESSED_DIRECTORY)

    def translate_file(self):
        try:
            # Определяем кодировку
            with open(self.path, 'rb') as file:
                raw_data = file.read(10000)
                result = chardet.detect(raw_data)
                encoding = result['encoding']

            # Открываем файл с определённой кодировкой
            with open(self.path, 'r', encoding=encoding) as file:
                text = file.read()
        except Exception as e:
            print(f"Error reading {self.path}: {e}")
            return

        # Замеряем время начала обработки файла
        file_start_time = time.time()

        # Подсчитываем общее количество токенов во входном тексте
        total_tokens = self.ai_interface.tokenize(text)
        print(
            f'\nTranslate file {self.path} -> {self.translated_file_path}\n Coding {encoding}, {total_tokens} tokens.')

        # Разбиваем текст на предложения
        sentences = split_text_into_sentences(text)
        log("=================================================================================\n" + \
            f" {self.path}\n"
            "=================================================================================")
        i = 1
        for sentence in sentences:
            log(f'{i}: {sentence}')
            i += 1

        print(f'Number of sentences: {len(sentences)}')

        # Объединяем предложения в части текста с учетом ограничения по количеству токенов в одной части
        current_part = []
        current_token_count = 0
        text_parts = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            tokens_count = self.ai_interface.tokenize(sentence)

            if len(current_part) == 0 or (current_token_count + tokens_count <= MAX_PART_TOKENS):
                current_part.append(sentence)
                current_token_count += tokens_count
            else:
                part_text = '\n'.join(current_part)
                text_parts.append(part_text)
                current_part = [sentence]
                current_token_count = tokens_count

        if current_part:
            part_text = '\n'.join(current_part)
            text_parts.append(part_text)

        print(f'Number of parts: {len(text_parts)}')

        # Переводим части параллельно
        translated_parts = [''] * len(text_parts)
        start_translation_time = time.time()  # Начало перевода
        total_translated_tokens = 0  # Счетчик переведенных токенов

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
            future_to_part = {}
            part_number = 1  # Номер части

            # Отправляем части на перевод
            for part in text_parts:
                future = executor.submit(self.translate_text, part, part_number)
                print(f'Sent part {part_number}/{len(text_parts)}...')
                future_to_part[future] = (part, part_number)
                part_number += 1

            # Обрабатываем завершенные части
            for future in concurrent.futures.as_completed(future_to_part):
                part, part_num = future_to_part[future]
                try:
                    translated_text = future.result()
                    print(f'Received part {part_num}/{len(text_parts)}...')
                    log(f'Translated part {part_num}:\n{translated_text}')
                    translated_parts[part_num - 1] = translated_text

                    # Подсчитываем количество токенов в переведенной части
                    translated_tokens = self.ai_interface.tokenize(translated_text)
                    total_translated_tokens += translated_tokens

                    # Рассчитываем текущую скорость перевода
                    current_time = time.time()
                    elapsed_time = current_time - start_translation_time
                    current_speed = total_translated_tokens / elapsed_time if elapsed_time > 0 else 0

                    print(
                        f'Translated part {part_num}/{len(text_parts)}. Current speed: {current_speed:.2f} tokens/sec')
                except Exception as exc:
                    print(f'Part {part_num} translation generated an exception: {exc}')

        end_translation_time = time.time()  # Конец перевода
        total_translation_time = end_translation_time - start_translation_time

        # Рассчитываем общую скорость перевода в токенах в секунду
        overall_speed = total_tokens / total_translation_time if total_translation_time > 0 else 0
        print(f'Total translation speed: {overall_speed:.2f} tokens/sec')

        print(f'Total translated parts: {len(translated_parts)}')
        log(f'Translated parts: {translated_parts}')

        # Записываем переведенный текст в файл
        with open(self.translated_file_path, 'w', encoding='utf-8') as file:
            for part in translated_parts:
                file.write('\n' + part)

        os.rename(self.path, self.processed_file_path)
        file_end_time = time.time()
        print(f'File processing time {file_end_time - file_start_time} sec.')


    def translate_text(self, text_to_translate, part):

        message = f'<TEXT_TO_BE_TRANSLATED>{text_to_translate}</TEXT_TO_BE_TRANSLATED>      \n' + \
                  'You are a professional translator of fiction and literary texts. ' + \
                  'Translate the entire given Russian text into English. Preserve the meaning and style of the narrative. ' + \
                  'Use all artistic means to make the text as literary and beautiful as possible, without distorting the meaning and style. ' + \
                  'Use idiomatic expressions of the English language if necessary for the best transmission of the meaning and style. ' + \
                  'Translate one sentence after another carefully, without losing them. ' + \
                  'Be sure to translate every sentence, without skipping a single one, THIS IS VERY VERY IMPORTANT!' + \
                  'Use dashes to mark direct speech. ' + \
                  'Just translate and print the translated text, nothing more!'
        return self.ai_interface.ask_model(message,part)