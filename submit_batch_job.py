import os
import pandas as pd
import base64
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv
import json
import argparse

def encode_image_to_base64(impath):
    with open(impath, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def main(experiment_type, model_name):
    path = os.getcwd()
    load_dotenv()

    endpoint = os.getenv("ENDPOINT_URL", "https://syntax-task.openai.azure.com/")
    deployment = os.getenv("DEPLOYMENT_NAME", model_name)
    subscription_key = os.getenv("AZURE_API_KEY")

    ## Experiment variables
    max_tokens = 800
    top_p = 0.95
    temperature = 0.0

    ## Load experiment file
    experiment_file = f"batch_{experiment_type}.csv"
    experiment_dir = os.path.join(path, "six_or_nine_task")
    batch_file_dir = os.path.join(experiment_dir, "batch")
    df = pd.read_csv(os.path.join(experiment_dir, experiment_file))
    df["max_tokens"] = max_tokens
    df["top_p"] = top_p
    df["temperature"] = temperature
    df.to_csv(os.path.join(experiment_dir, experiment_file), index=False)

    ## create json
    jsonl_lines = []
    supports_params = deployment in ["gpt-4o-batch"]
    for i, row in df.iterrows():
        image_b64 = encode_image_to_base64(os.path.join(row["im_dir"], row["filename"]))
        text = row["question_prompt"]
        text = text.encode('utf-8').decode('unicode_escape')
        body = {
            "model": deployment,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                ]}
            ],
        }
        if supports_params:
            body["temperature"] = temperature
            body["top_p"] = top_p
            body["max_tokens"] = max_tokens
        request = {
            "custom_id": f"request-{i+1}",
            "method": "POST",
            "url": "/chat/completions",
            "body": body
        }
        jsonl_lines.append(json.dumps(request))

    batch_file_path = os.path.join(batch_file_dir, f"SoN_{experiment_type}_{deployment}_{temperature}.jsonl")
    with open(batch_file_path, "w", encoding="utf-8") as f:
        for line in jsonl_lines:
            f.write(line + "\n")

    ## upload json to Azure
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=subscription_key,
        api_version="2025-01-01-preview",
    )
    with open(batch_file_path, "rb") as f:
        file = client.files.create(
            file=f,
            purpose="batch",
            extra_body={
                "expires_after": {
                    "seconds": 1209600,
                    "anchor": "created_at"
                }
            }
        )
    print(file.model_dump_json(indent=2))
    if file.expires_at:
        print(f"File expiration: {datetime.fromtimestamp(file.expires_at)}")
    else:
        print("File expiration: Not set")
    file_id = file.id
    print(f"Uploaded File ID: {file_id}")

    ## submit batch job
    batch_response = client.batches.create(
        input_file_id=file_id,
        endpoint="/chat/completions",
        completion_window="24h"
    )
    batch_id = batch_response.id
    print(batch_response.model_dump_json(indent=2))
    with open(f"batch_id_{experiment_type}_{deployment}.txt", "w") as f:
        f.write(batch_id)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare and submit a batch job to Azure OpenAI.")
    parser.add_argument("experiment_type", type=str, help="Experiment type (e.g., full_1000)")
    parser.add_argument("model_name", type=str, help="Model name (e.g., o4-mini-batch)")
    args = parser.parse_args()
    main(args.experiment_type, args.model_name)
