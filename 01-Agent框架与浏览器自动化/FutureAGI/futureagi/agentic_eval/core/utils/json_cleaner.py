import json
import os


def process_json_files(folder_path):
    # Traverse all subfolders and files using os.walk
    for root, _dirs, files in os.walk(folder_path):
        # Iterate over each JSON file in the current folder
        for json_file in files:
            if json_file.endswith(".json"):
                file_path = os.path.join(root, json_file)

                # Load the JSON data from the file
                with open(file_path) as file:
                    data = json.load(file)

                # Create a new dictionary to store the filtered data
                filtered_data = {}

                # Iterate over each question ID and its corresponding values
                for question_id, values in data.items():
                    # Check if any of the specified keys have a value equal to 0
                    if any(
                        values.get(key, 1) == 0
                        for key in ["0.25", "0.5", "0.75", "1.0"]
                    ):
                        continue  # Skip the question ID if any key has a value equal to 0
                    else:
                        # If no key has a value equal to 0, add the question ID to the filtered data
                        filtered_data[question_id] = values

                # Save the filtered data back to the same JSON file
                with open(file_path, "w") as file:
                    json.dump(filtered_data, file, indent=4)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python json_cleaner.py <folder_path>")
        sys.exit(1)
    folder_path = sys.argv[1]
    process_json_files(folder_path)
