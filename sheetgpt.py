import json
import os

from flask import Flask, jsonify, request
import openai
from dotenv import load_dotenv
import hashlib
from apig_wsgi import make_lambda_handler
import boto3

app = Flask(__name__)


# Just to be sure that the endpoint itself works
@app.route('/')
def main():
    return "working"


@app.route('/api/get_completion', methods=['POST'])
def post_data():
    data = request.get_json()
    # print(data.keys())

    prompt = data['prompt']
    res,cache_key = get_openai_response(prompt)
    try:
        res = json.loads(res, strict=False)
    except Exception as err:
        print('non-json response', err, prompt, res)
        return jsonify({"err": "non-json-response-from-oai"}), 400

    content = None
    try:
        content = res['choices'][0]['message']['content']
    except:
        print('res:', res)
        return jsonify({"err": "oai-response-wrong-format", "cache_key": cache_key}), 400

    try:
        print('content: ', content)
        content = json.loads(content, strict=False)
    except Exception as inst:
        print('request:', request.data)
        print('response:', res)
        print('decoding error', inst)
        print('cache key', cache_key)
        return jsonify({"err": "cgpt-response-not-in-json", "cache_key": cache_key}), 400
    # print(content)

    return jsonify(content)


class LocalCacher:
    def __init__(self, cache_dir='./.cache'):
        self.dir = cache_dir

    def key_exists(self, key):
        return os.path.isfile(os.path.join(self.dir, key))

    def get(self, key):
        file_name = os.path.join(self.dir, key)
        with open(file_name, 'r') as f:
            return f.read()

    def put(self, key, value):
        file_name = os.path.join(self.dir, key)
        with open(file_name, 'w') as f:
            f.write(value)


class S3Cacher:
    def __init__(self, bucket_name, prefix='cache'):
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.s3 = boto3.client('s3')

    def get_key(self, key):
        return f"{self.prefix}/{key}" if self.prefix else key

    def key_exists(self, key):
        s3_key = self.get_key(key)
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except:
            return False

    def get(self, key):
        s3_key = self.get_key(key)
        obj = self.s3.get_object(Bucket=self.bucket_name, Key=s3_key)
        return obj['Body'].read().decode('utf-8')

    def put(self, key, value):
        s3_key = self.get_key(key)
        self.s3.put_object(Bucket=self.bucket_name, Key=s3_key, Body=value)


def get_openai_response(prompt, system="you are a helpful assistant", suffix=None):
    """
    Makes a cached API call to OpenAI
    :param prompt:
    :param system:
    :param suffix:
    :return:
    """
    cacher = None
    if 'S3_BUCKET' in os.environ:
        # TODO: instantiate S3 cacher
        cacher = S3Cacher(os.environ['S3_BUCKET'])
        pass
    else:
        cacher = LocalCacher()

    cache_key = f"{prompt.strip()}{system.strip()}{suffix.strip() if suffix is not None else ''}"
    h = hashlib.new('sha256')
    h.update(cache_key.encode('utf-8'))
    cache_key = h.hexdigest()
    if cacher.key_exists(cache_key):
        contents = cacher.get(cache_key)
        return contents, cache_key
    newline = '\n'
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"{prompt.strip()}{f'{newline}{suffix}' if suffix is not None else ''}"},
    ]
    print('begin resp')
    oai_response = get_raw_openai_response(messages)
    print('end resp')

    cacher.put(cache_key, json.dumps(oai_response))
    return json.dumps(oai_response), cache_key


# makes an actual OpenAI request
def get_raw_openai_response(messages):
    model = "gpt-3.5-turbo"
    # print(messages)
    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0
    )
    return resp


# if you need an example recursive request to play with
# example_req = """
# Act as a c-level executive assistant. You are tasked to write press release and an FAQ about new product launch.
# It should conform to Amazon's Working Backwards process,
# The product is a new plush toy headcrab from HalfLife, it will be sold in our e-shop and delivered globally.
# Ask required questions and write a resulting document when ready.
# answer only in JSON of the following format:
# {
# "questions": [ "question1", "question2",...],
# "prfaq": "prfaq",
# "comments": "if you want to add something freeform"
# }
# """

# entry point for a lambda function
lambda_handler = make_lambda_handler(app)

# entry point for the local startup
if __name__ == '__main__':
    load_dotenv()
    app.run(debug=True)
