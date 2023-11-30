from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
from flask_cors import CORS
import time

load_dotenv()

assistant_id = os.getenv("assistant_id")
openai_api_key = os.getenv("openai_api_key")
client = OpenAI(api_key = openai_api_key)
thread_id = os.getenv("thread_id")


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def get_message():
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    if messages.data[0].role == "user":
        time.sleep(5)
        get_message()
    else:
        print(type(messages.data[0].content[0].text.value))
        return messages.data[0].content[0].text.value

@app.route('/')
def index():
    file_list = []
    files = client.beta.assistants.files.list(assistant_id=assistant_id)
    
    for file in files:  
        real_file = client.files.retrieve(file.id)
        file_dict = {}
        file_dict['id'] = file.id
        file_dict['name'] = real_file.filename
        file_list.append(file_dict)
        
    return render_template('index.html', files=file_list)


@app.route('/file_upload', methods=['POST'])
def file_upload():
    file = request.files['file']
    file.save('uploads/' + file.filename)
    
    added_file = client.files.create(file=open(f"uploads/{file.filename}", "rb"), purpose="assistants")
    
    client.beta.assistants.files.create(assistant_id=assistant_id, file_id=added_file.id)

    os.remove('uploads/' + file.filename)
    
    return index()

@app.route('/file_delete', methods=['POST'])
def file_delete():
    data = request.form
    file_id = data.get('id')

    try:
        client.beta.assistants.files.delete(
            assistant_id=assistant_id,
            file_id=file_id
        )

        client.files.delete(file_id)

    except:
        msg = "File is not deleted."

    else:
        msg = "File is deleted."

    finally:
        return jsonify({"answer": msg})
    
@app.route('/query', methods=['POST'])
def query():
    data = request.form
    query = data.get('query')
    
    client.beta.threads.messages.create(thread_id, role="user", content=query)

    client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

    while True:
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        if messages.data[0].role == "user":
            time.sleep(5)
            get_message()
        else:
            msg = messages.data[0].content[0].text.value
            break
        
    return jsonify({"answer": msg})
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)