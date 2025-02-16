import time
from ollama import chat
from transformers import AutoTokenizer
from Configuration import *

@singleton
class AIInterface :
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)
        self.console_position = 0
        self.last_time = time.time()
        self.chunk_count = 0

    def ask_model(self, message, part):
        print('Translating part ' + str(part) + '...')
        response = ''

        model_options = {}

        model_options['num_ctx'] = NUM_CTX
        model_options['temperature'] = MODEL_TEMPERATURE
        model_options['format'] = REQUEST_FORMAT
        model_options['top_k'] = TOP_K
        model_options['top_p'] = TOP_P
        model_options['repeat_penalty'] = REPEAT_PENALTY
        model_options['presence_penalty'] = PRESENCE_PENALTY
        model_options['frequency_penalty'] = FREQUENCY_PENALTY

        stream = chat(
            model=OLLAMA_MODEL,
            messages= [{'role': 'user', 'content': message}],
            stream=True,
            options=model_options,
        )

        max_retries = MAX_OLLAMA_REQUESTS
        while True:
            try:
                response = self.get_stream_response(stream)
                break
            except Exception as e:
                if max_retries > 0:
                    max_retries -= 1
                else:
                    raise Exception("Generation Failed, Max Retires Exceeded, Aborting")

        if response.strip() == "":
            response = self.ask_model(message)
            return response

        return response

    def get_stream_response(self, _stream):
        response: str = ""
        counter = 0
        for chunk in _stream:
            chunk_text = chunk["message"]["content"]
            response += chunk_text
            current_time = time.time()
            if current_time > self.last_time + CURRENT_SPEED_MEASUREMENT_TIME:
                print(f"\nCurrent Speed: {self.chunk_count/CURRENT_SPEED_MEASUREMENT_TIME} tokens/s >", end="", flush=True)
                self.last_time = current_time
                self.chunk_count = 0
            self.chunk_count += 1
            print('\b.>', end="", flush=True)
            #print(chunk.message.content, end="", flush=True)
            if chunk.done:
                print(f"\nSpeed: {1000000000 * chunk.eval_count / chunk.eval_duration} tokens/s")
        return response

    def tokenize(self, text):
        return len(self.tokenizer.tokenize(text))