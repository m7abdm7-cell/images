import os
import base64
from github import Github
from github import Auth

# --- CONFIGURATION ---
GITHUB_USER = "pawPatoes" # Your github username
REPO_NAME = "images" # The repo that u want to house all ur images
BRANCH = "main" # You can keep this as main unless u make a new branch

# 1. Setup authentication
token = os.getenv('GITHUB_PAT')

if not token:
    print("--- AUTHENTICATION ERROR ---")
    print("GITHUB_PAT environment variable not found!")
    print("\nHOW TO FIX:")
    print("1. Generate a PAT: Go to GitHub Settings > Developer settings > Personal access tokens > Tokens (classic).")
    print("2. Create one with 'repo' scope permissions. (make sure it has write access on your image repo!)")
    print("3. Run this in !PowerShell! (replace YOUR_TOKEN):")
    print("   [System.Environment]::SetEnvironmentVariable('GITHUB_PAT', 'YOUR_TOKEN', 'User')")
    print("\nAfter running the command, CLOSE AND REOPEN your terminal.")
    print("Don't be stupid and think this will hack your github, environment variables are stored ON YOUR PC.\nAnd this python only sends them to github so it can authenticate!")
    exit()

# Auth
auth = Auth.Token(token)
g = Github(auth=auth)

# Connect to specific repository
repo = g.get_user(GITHUB_USER).get_repo(REPO_NAME)

# Initialize directory
current_dir = os.getcwd()

print(f"--- GitHub Image Uploader ---")
print(f"Target: {GITHUB_USER}/{REPO_NAME}")
print(f"Current Directory: {current_dir}")
print("Commands: 'cd [folder]' to change directory, or type filename to upload.")

# 2. Main Loop
while True:
    user_input = input("\n> ").strip()

    if not user_input:
        continue

    # Handle 'cd' command
    if user_input.startswith("cd "):
        new_path = user_input[3:].strip()
        if os.path.isdir(new_path):
            os.chdir(new_path)
            current_dir = os.getcwd()
            print(f"Changed directory to: {current_dir}")
        else:
            print("Error: Directory does not exist.")
        continue

    # Handle image upload
    local_image_path = os.path.join(current_dir, user_input)
    
    if not os.path.exists(local_image_path):
        print(f"Error: File '{user_input}' not found in {current_dir}")
        continue

    # Prepare file details
    file_name = os.path.basename(local_image_path)
    github_path = f"assets/{file_name}"
    commit_message = f"Add {file_name} via Python script"

    # Read and prepare binary content
    with open(local_image_path, "rb") as image_file:
        file_data = image_file.read()

    # 3. Upload/Update
    try:
        try:
            contents = repo.get_contents(github_path)
            repo.update_file(contents.path, commit_message, file_data, contents.sha)
        except:
            repo.create_file(github_path, commit_message, file_data)
        
        print(f"Successfully uploaded: {file_name}")
        
        # Using ?raw=true
        blob_url = f"https://github.com/{GITHUB_USER}/{REPO_NAME}/blob/{BRANCH}/assets/{file_name}"
        raw_url = f"{blob_url}?raw=true"
        
        print(f"View on GitHub: {blob_url}")
        print(f"Direct Image Link: {raw_url}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
