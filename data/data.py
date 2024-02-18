import json

# Utility Functions
def load_data():
    with open("data/database.json", "r") as file:
        return json.load(file)

def save_data(data):
    with open("data/database.json", "w") as file:
        json.dump(data, file, indent=4)