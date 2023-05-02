from flask import Flask, request
import json
import requests
from url_summarization import process_webhook
import yaml

# Read the configuration.yaml file
with open("configuration.yaml", "r") as yaml_file:
    config_data = yaml.safe_load(yaml_file)

# Get the feishu_webhook parameter
feishu_webhook = config_data["feishu_webhook"]
access_token = config_data["access_token"]


app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def receive_webhook():
    print("Receive Webhook:")
    data = request.get_data(as_text=True)
    json_dict = json.loads(data)
    print(json_dict)
    message_id = json_dict['data']['result']['message_id']
    urls = json_dict['data']['result']['urls']
    if urls:
        for i in urls:
            content = process_webhook(i)['output_text']
            print(content)
            send(message_id, content)
    print(data,'\n')
    json_dict['from server']='Webhook已经收到'
    return json.dumps(json_dict)

def send(message_id, content):
    url_back = feishu_webhook
    req = {
        "message_id": message_id, # message id
        "msg_type": "text",
        "content": content
    }
    payload = json.dumps(req)
    headers = {
        'Authorization': 'Bearer '+access_token, # your access token
        'Content-Type': 'application/json'
    }
    response = requests.post(url_back, headers=headers, data=payload)
    print(response.content) # Print Response

if __name__ == '__main__':
    app.run()
