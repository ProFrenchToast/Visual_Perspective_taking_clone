import os
import pandas as pd

# Constants and paths
TRIAL_NUM = 1000 # currently 1000 or 5000
TYPES = ["visual", "spatial"]
BASE_DIR = os.getcwd()
EXPERIMENT_DIR = os.path.join(BASE_DIR, "six_or_nine_task")
PROMPT_DF = pd.read_csv(os.path.join(EXPERIMENT_DIR, "prompts.csv"))
RESULTS_DIR = os.path.join(EXPERIMENT_DIR, "results")

def extract_correct_answer(row):
    set_name = row['set']
    type_ = row['type']
    try:
        answer_col = PROMPT_DF.loc[
            PROMPT_DF['stimulus_set'] == set_name,
            f"{type_}_correct_answer_column"
        ].values[0]
    except IndexError:
        print(f"No correct answer column found for set: {set_name}, type: {type_}")
        return None

    if answer_col not in row:
        print(f"Answer column '{answer_col}' not found in row for set {set_name}")
        return None

    answer = str(row.get(answer_col, "")).strip().upper()

    if type_ == 'visual' and set_name == "level_1":
        return {"FRONT": "CAN SEE", "BEHIND": "CANNOT SEE"}.get(answer, None)

    elif type_ == 'spatial' and set_name == "level_2":
        return answer.split("_")[-1] if answer else None

    elif set_name == "control_2" or set_name == "control_3":
        try:
            angle = float(answer)
        except ValueError:
            print("Could not convert angle:", answer)
            return None

        if 45 < angle <= 135:
            position = "TOP"
        elif 135 < angle <= 225:
            position = "LEFT"
        elif 225 < angle <= 315:
            position = "BOTTOM"
        else:
            position = "RIGHT"

        if type_ == "visual":
            return {"LEFT": "RED", "RIGHT": "GREEN", "TOP": "BLUE", "BOTTOM": "BLACK"}[position]
        else:
            return position
    else:
        return answer


# Build full DataFrame
all_rows = []
for _, prompt_row in PROMPT_DF.iterrows():
    stimulus_set = prompt_row["stimulus_set"]
    im_dir = os.path.join(EXPERIMENT_DIR, f"stimuli_{str(TRIAL_NUM)}", stimulus_set)
    metadata_path = os.path.join(im_dir, "metadata.csv")
    if not os.path.exists(metadata_path):
        continue
    temp_df = pd.read_csv(metadata_path)
    for type_ in TYPES:
        temp_df_copy = temp_df.copy()
        temp_df_copy["im_dir"] = im_dir
        temp_df_copy["set"] = stimulus_set
        temp_df_copy["type"] = type_
        temp_df_copy["question_prompt"] = prompt_row["context_prompt"] + prompt_row[f"{type_}_prompt"]
        all_rows.append(temp_df_copy)
df = pd.concat(all_rows, ignore_index=True)
df["correct_answer"] = df.apply(extract_correct_answer, axis=1)
df.to_csv(os.path.join(EXPERIMENT_DIR, f"batch_full_{TRIAL_NUM}.csv"), index=False)
