MODEL_TEMPERATURE = 0
TOP_K = 0
TOP_P = 0
REQUEST_FORMAT = 'text'
REPEAT_PENALTY = 1
PRESENCE_PENALTY = 1
FREQUENCY_PENALTY = 1
MAX_OLLAMA_REQUESTS = 3
NUM_CTX = 2048
OLLAMA_MODEL = 'Sunfall-NemoMix-translate:latest'
TOKENIZER_MODEL = "Vdr1/Sunfall-NemoMix-Unleashed-12B-v0.6.1"
SOURCE_DIRECTORY = 'd:\\ai\\learn'
TRANSLATED_DIRECTORY = f'{SOURCE_DIRECTORY}\\english'
PROCESSED_DIRECTORY = f'{SOURCE_DIRECTORY}\\processed'
MAX_PART_TOKENS = 500

from functools import wraps

def singleton(class_):
    instances = {}
    @wraps(class_)
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance
