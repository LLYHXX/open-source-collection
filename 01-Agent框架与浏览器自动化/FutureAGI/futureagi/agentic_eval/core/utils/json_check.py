import json
import os


def count_question_ids(folder_path):
    # Traverse all subfolders and files using os.walk
    for root, _dirs, files in os.walk(folder_path):
        # Iterate over each JSON file in the current folder
        for json_file in files:
            if json_file.endswith(".json"):
                file_path = os.path.join(root, json_file)

                # Load the JSON data from the file
                with open(file_path) as file:
                    json.load(file)

                # Count the number of question IDs in the JSON file
                # num_question_ids = len(data)

                # Print the JSON file name and the number of question IDs
                # print(f"File: {json_file}, Question IDs: {num_question_ids}")


def count_zero_values(folder_path):
    # Initialize counters for each key
    count_0_25 = 0
    count_0_5 = 0
    count_0_75 = 0
    count_1 = 0

    # Traverse all subfolders and files using os.walk
    for root, _dirs, files in os.walk(folder_path):
        # Iterate over each JSON file in the current folder
        for json_file in files:
            if json_file.endswith(".json"):
                file_path = os.path.join(root, json_file)

                # Load the JSON data from the file
                with open(file_path) as file:
                    data = json.load(file)

                # Iterate over each question ID and its corresponding values
                for _question_id, values in data.items():
                    # Check if each key has a value of 0
                    if values.get("0.25", 1) == 0:
                        count_0_25 += 1
                    if values.get("0.5", 1) == 0:
                        count_0_5 += 1
                    if values.get("0.75", 1) == 0:
                        count_0_75 += 1
                    if values.get("1.0", 1) == 0:
                        count_1 += 1


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python json_check.py <folder_path>")
        sys.exit(1)
    folder_path = sys.argv[1]
    count_zero_values(folder_path)
    count_question_ids(folder_path)
