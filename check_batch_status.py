import os
import pandas as pd
import base64
from datetime import datetime
import time
from openai import AzureOpenAI
from dotenv import load_dotenv
import json
import argparse

def main(experiment_type, model_name):
    path = os.getcwd()
    load_dotenv()

    endpoint = os.getenv("ENDPOINT_URL", "https://syntax-task.openai.azure.com/")
    deployment = os.getenv("DEPLOYMENT_NAME", model_name)
    subscription_key = os.getenv("AZURE_API_KEY")

    ## paths
    experiment_dir = os.path.join(path, "six_or_nine_task")
    prompt_df = pd.read_csv(os.path.join(experiment_dir, "prompts.csv"))
    batch_file_dir = os.path.join(experiment_dir, "batch")
    results_dir = os.path.join(experiment_dir, "results")

    ## client
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=subscription_key,
        api_version="2025-01-01-preview",
    )

    ## Get job info
    batch_filename = f"batch_id_{experiment_type}_{deployment}.txt"
    with open(batch_filename, "r") as f:
        batch_id = f.read().strip()
    batch_response = client.batches.retrieve(batch_id)
    status = batch_response.status
    print(f"{datetime.now()} Batch Id: {batch_id},  Status: {status}")

    ## Print error if failed
    if batch_response.status == "failed":
        for error in batch_response.errors.data:
            print(f"Error code {error.code} Message {error.message}")

    ## Get results if finished
    if batch_response.status == "completed":
        output_file_id = batch_response.output_file_id or batch_response.error_file_id
        if output_file_id:
            file_response = client.files.content(output_file_id)
            raw_responses = file_response.text.strip().split('\n')
            rows = []
            for raw_response in raw_responses:
                json_response = json.loads(raw_response)
                row = {
                    'id': json_response.get('custom_id'),
                    'content': json_response.get('response', {}).get('body', {}).get('choices', [{}])[0]
                        .get('message', {}).get('content'),
                }
                rows.append(row)
            results_df = pd.DataFrame(rows)

            df = pd.read_csv(os.path.join(experiment_dir, f"batch_{experiment_type}.csv"))
            df['request-id'] = [f'request-{i+1}' for i in range(len(df))]
            results_df.rename(columns={"id": "request-id"}, inplace=True)

            merged_df = df.merge(results_df, on='request-id', how='left')
            short_model_name = deployment.split("-batch")[0]
            merged_df["model"] = short_model_name
            merged_df.rename(columns={"content": "answer"}, inplace=True)

            output_filename = f"SoN_{short_model_name}_{experiment_type}_T{merged_df['temperature'].iloc[0]}.csv"
            merged_df.to_csv(os.path.join(results_dir, output_filename), index=False)
            print(f"Results saved in {results_dir}/{output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check batch job status and retrieve results.")
    parser.add_argument("experiment_type", type=str, help="Experiment type (e.g., full_1000)")
    parser.add_argument("model_name", type=str, help="Model name (e.g., o4-mini-batch)")
    args = parser.parse_args()
    main(args.experiment_type, args.model_name)
