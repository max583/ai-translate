import re
import os
import time
import chardet
from Configuration import *
import AIInterface


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
        self.translated_file_path = f'{TRANSLATED_DIRECTORY}\\{os.path.splitext(os.path.basename(self.path))[0]}.txt'
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
        file_start_time = time.time()


        file_tokens_count = self.ai_interface.tokenize(text)
        print(f'\nTranslate file {self.translated_file_path}, кодировка {encoding}, {file_tokens_count} tokens.')
        #sentences = sentence_endings.split(text)
        sentences = split_text_into_sentences(text)
        log("=================================================================================\n" + \
            f" {self.translated_file_path}\n"
            "=================================================================================")
        i = 1
        for sentence in sentences:
            log(f'{i}: {sentence}')
            i += 1
        current_part = []
        current_token_count = 0

        with open(self.translated_file_path, 'w', encoding='utf-8') as file: pass

        sentence_counter = 0
        sentences_number = len(sentences)
        part_counter = 1

        for sentence in sentences:
            sentence = sentence.strip()
            sentence_counter += 1
            if not sentence and sentence_counter != sentences_number:
                continue

            tokens_count = self.ai_interface.tokenize(sentence)

            #print(f'sentence({tokens_count}) {sentence_counter}/{sentences_number}: {sentence}')

            if len(current_part)==0 or (current_token_count + tokens_count <= MAX_PART_TOKENS and sentence_counter != sentences_number):
                #print('Path 1')
                current_part.append(sentence)
                current_token_count += tokens_count
            else:
                #print('Path 2')
                if sentence_counter == sentences_number:
                    current_part.append(sentence)
                part_text = '\n'.join(current_part)
                print(f'Translate file {self.translated_file_path} Part {part_counter}, {current_token_count} tokens.')
                log(f'Translate file {self.translated_file_path} Part {part_counter}, {current_token_count} tokens.\n{part_text}')
                start_time = time.time()
                translated_text = self.translate_text(part_text)
                end_time = time.time()
                translated_tokens_count = self.ai_interface.tokenize(translated_text)
                print(f' Translated {translated_tokens_count} tokens. Processing time {end_time - start_time} sec.')
                log(f' Translated {translated_tokens_count} tokens. Processing time {end_time - start_time} sec.\n{translated_text}')
                if translated_text:
                    #log(f'---------------------------------------------------------------------\n{translated_text}\n-----------------------------------------------------------------------')
                    with open(self.translated_file_path, "a", encoding='utf-8') as f:
                        f.write(translated_text + '\n')
                part_counter += 1
                current_part = [sentence]
                current_token_count = tokens_count

        os.rename(self.path, self.processed_file_path)
        file_end_time = time.time()
        print(f'File processing time {file_end_time - file_start_time} sec.')


    def translate_text(self, text_to_translate):

        message = f'<TEXT_TO_BE_TRANSLATED>{text_to_translate}</TEXT_TO_BE_TRANSLATED>.\n' + \
                  'You are a professional translator of fiction and literary texts. ' + \
                  'Translate the entire given Russian text into English. Preserve the meaning and style of the narrative. ' + \
                  'Use all artistic means to make the text as literary and beautiful as possible, without distorting the meaning and style. ' + \
                  'Use idiomatic expressions of the English language if necessary for the best transmission of the meaning and style. ' + \
                  'Translate one sentence after another carefully, without losing them. ' + \
                  'Be sure to translate every sentence, without skipping a single one, THIS IS VERY VERY IMPORTANT!' + \
                  'Use dashes to mark direct speech. ' + \
                  'Just translate and print the translated text, nothing more!'
        return self.ai_interface.ask_model(message)