import sys
import subprocess
import os
import time
import threading
import requests
import webbrowser
# --- only change these if the actions thing didnt work!
GITHUB_USER = "pawPatoes"
REPO_NAME = "images"
BRANCH = "main"
# --- dont change anything from here! ---

# --- AUTOMATIC DEPENDENCY INSTALLER ---
def install_and_import(package, import_name=None):
    if import_name is None: import_name = package
    try: return __import__(import_name)
    except ImportError:
        print(f"--- Missing {package}! Installing now... ---")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return __import__(import_name)

os = install_and_import("os")
time = install_and_import("time")
threading = install_and_import("threading")
requests = install_and_import("requests")
try: readline = install_and_import("pyreadline3", "readline")
except: readline = install_and_import("readline")
Github = install_and_import("PyGithub", "github").Github
Auth = install_and_import("PyGithub", "github.Auth").Auth

loading = False
loading_msg = "loading"
remote_cache = [] 

def loading_animation():
    i = 0
    while loading:
        sys.stdout.write(f"\r{loading_msg}{'.' * (i % 4)}   ")
        sys.stdout.flush()
        i += 1
        time.sleep(0.5)
    sys.stdout.write("\r" + " " * 30 + "\r")

def handle_duplicate(filename):
    if not os.path.exists(filename): return filename
    choice = input(f"File '{filename}' already exists. [Y] Replace, [N] Ignore, [R] Rename to '{os.path.splitext(filename)[0]}_2{os.path.splitext(filename)[1]}': ").lower()
    if choice == 'y': return filename
    if choice == 'r':
        name, ext = os.path.splitext(filename)
        return f"{name}_2{ext}"
    return None

# --- TAB COMPLETION ---
def completer(text, state):
    buffer = readline.get_line_buffer()
    text_lower = text.lower()
    
    if buffer.lower().startswith(('delete ', 'download ')):
        # Prioritize GitHub remote cache for delete/download
        options = remote_cache
    elif buffer.lower().startswith('upload '):
        options = [f for f in os.listdir('.') if os.path.isfile(f)]
    elif buffer.lower().startswith('cd '):
        options = [d for d in os.listdir('.') if os.path.isdir(d)]
    else:
        options = ["upload ", "download ", "delete ", "view", "files", "cd ", "help", "bsod"]
        
    matches = [opt for opt in options if opt.lower().startswith(text_lower)]
    return matches[state] if state < len(matches) else None

readline.set_completer(completer)
readline.parse_and_bind("tab: complete")
readline.parse_and_bind("set completion-query-items 0")
readline.parse_and_bind("set show-all-if-ambiguous on")

# INITIALIZATION
loading = True; loading_msg = "initializing"
t_init = threading.Thread(target=loading_animation); t_init.start()

token = os.getenv('GITHUB_PAT')
if not token:
    loading = False; t_init.join()
    print("\n" + "!"*40)
    print("ERROR: GITHUB_PAT environment variable not found!")
    print("How to set your PAT:")
    print("1. Create a Personal Access Token at: https://github.com/settings/tokens")
    print("2. Ensure the token has 'repo' permissions.")
    print("3. Add it to your System Environment Variables as 'GITHUB_PAT'.")
    print("   On Windows: Search 'Edit the system environment variables' -> Environment Variables -> New.")
    print("!"*40)
    exit()

try:
    auth = Auth.Token(token)
    g = Github(auth=auth)
    repo = g.get_user(GITHUB_USER).get_repo(REPO_NAME)
except Exception as e:
    loading = False; t_init.join()
    print("\n" + "!"*40)
    print(f"ERROR: Authentication failed: {e}")
    print("How to set your PAT:")
    print("1. Create a Personal Access Token at: https://github.com/settings/tokens")
    print("2. Ensure the token has 'repo' permissions.")
    print("3. Copy it (You won't be able to see it again!)")
    print("4. Add it to your System Environment Variables as 'GITHUB_PAT'.")
    print("   On Windows: Search 'Edit the system environment variables' -> Environment Variables -> New.")
    print("!"*40)
    exit()

loading = False; t_init.join()

def help_txt():
    print(f"--- GitHub Image Uploader ---")
    print("Commands:")
    print("  upload [filename] - Upload a local file to /assets.")
    print("  cd [dir]          - Change local directory (Tab to autocomplete).")
    print("  files             - List all local files and folders.")
    print("  view              - List remote files in /assets.")
    print("  delete [file]     - Delete a file from /assets.")
    print("  download [file]   - Download a file from /assets.")
    print("  help              - Shows this text.")
    print("Keybinds:")
    print("  Tab               - Auto-complete filenames/folders based on the command.")

current_dir = os.getcwd()
help_txt()

# --- MAIN LOOP ---
while True:
    try: user_input = input(f"\n{current_dir}>").strip().replace("\"", "")
    except EOFError: break
    if not user_input: continue

    if user_input.lower() == "view":
        loading = True; loading_msg = "fetching and caching"; t = threading.Thread(target=loading_animation); t.start()
        try:
            files = repo.get_contents("assets")
            remote_cache = [f.name for f in files]
            loading = False; t.join()
            print("\nFiles in /assets (cached):")
            for name in remote_cache: print(f"- {name}")
        except: loading = False; t.join(); print("\nAssets directory empty/not found.")
        continue

    if user_input.lower().startswith('download '):
        target_input = user_input.split(' ', 1)[1].strip()
        target_file = next((f for f in remote_cache if f.lower() == target_input.lower()), None)
        if not target_file:
            for ext in ['.png', '.jpg', '.jpeg', '.gif', '.mp4']:
                match = next((f for f in remote_cache if f.lower() == (target_input + ext).lower()), None)
                if match: target_file = match; break
        
        if not target_file: print("File not found in cache. Run 'view'."); continue
        final_name = handle_duplicate(target_file)
        if final_name:
            loading = True; loading_msg = f"downloading {target_file}"; t = threading.Thread(target=loading_animation); t.start()
            try:
                contents = repo.get_contents(f"assets/{target_file}")
                resp = requests.get(contents.download_url)
                with open(final_name, "wb") as f: f.write(resp.content)
                loading = False; t.join()
                done = False 
                while done == False:
                    print(f"\nSaved as: {final_name}, found at {current_dir}")
                    open_file = input("Open file? (Y/N): ").lower().strip()
                    if open_file.startswith('y'): 
                        file_to_open = os.path.join( current_dir, final_name)
                        webbrowser.open("file://" + file_to_open)
                        done = True
                    elif open_file.startswith('n'): 
                        done = True
                    else: 
                        print("Your response wasn't Y nor N!")
            except Exception as e: 
                loading = False; t.join()
                print(f"\nError: {e}")
        continue

    if user_input.lower().startswith('delete '):
        if user_input.lower() == "delete .gitkeep":
            print(".gitkeep cannot be deleted!"); continue
        target_input = user_input.split(' ', 1)[1].strip()
        target_file = next((f for f in remote_cache if f.lower() == target_input.lower()), None)
        if not target_file: print("File not found in cache."); continue
        loading = True; loading_msg = f"deleting {target_file}"; t = threading.Thread(target=loading_animation); t.start()
        try:
            repo.delete_file(repo.get_contents(f"assets/{target_file}").path, f"Delete {target_file}", repo.get_contents(f"assets/{target_file}").sha)
            if target_file in remote_cache: remote_cache.remove(target_file)
            print(f"\nDeleted: {target_file}")
        except Exception as e: print(f"\nError: {e}")
        finally: loading = False; t.join()
        continue
    if user_input.lower().startswith("bsod"):
        bro_cooked = input("ARE YOU ABSOLUTELY SURE YOU WANT TO BLUE SCREEN OF DEATH YOUR COMPUTER?\nTHIS MIGHT CAUSE CORRUPTION OR OTHER PROBLEMS (Y/N): ")
        if bro_cooked.lower().startswith("n"):
            continue
        elif bro_cooked.lower().startswith("y"):
            bro_cooked2boogalo = input("ACTUALLY SURE?? THIS IS NOT A JOKE! IT WILL HAPPEN! (Y/N): ")
            if bro_cooked2boogalo.lower().startswith("n"):
                continue
            elif bro_cooked2boogalo.lower().startswith("y"):
                print("Don't say I didn't warn you, one last chance, click ctrl+c to stop, you have 5 seconds\n\n")
                time.sleep(5)
                print("Yeah.. I'm not actually gonna make that happen LOL\nIf I did kids would be angry at me cuz they lost smth/their computer no work anymore!")
        continue

    if user_input.lower() in ("help", "cmd", "commands", "command"):
        help_txt(); continue

    if user_input.lower() == "files":
        for item in os.listdir('.'): print(f"[{'DIR' if os.path.isdir(item) else 'FILE'}] {item}")
    elif user_input.lower().startswith("cd "):
        try:
            os.chdir(user_input[3:].strip())
            current_dir = os.getcwd()
        except: print("Error: Directory not found.")
    elif user_input.lower().startswith("upload "):
        file_path = user_input.split(' ', 1)[1].strip()
        file_path = file_path.encode("ascii", "ignore").decode("ascii")
        local_path = os.path.join(current_dir, file_path)
        
        if os.path.exists(local_path):
            loading = True; loading_msg = "uploading"; t = threading.Thread(target=loading_animation); t.start()
            try:
                file_name = os.path.basename(local_path)
                
                with open(local_path, "rb") as f: 
                    binary_data = f.read()
                
                if not binary_data:
                    raise ValueError("File is empty.")

                try:
                    contents = repo.get_contents(f"assets/{file_name}")
                    repo.update_file(contents.path, f"update {file_name}", binary_data, contents.sha)
                except: 
                    repo.create_file(f"assets/{file_name}", f"add {file_name}", binary_data)
                
                loading = False; t.join()
                blob_url = f"https://github.com/{GITHUB_USER}/{REPO_NAME}/blob/{BRANCH}/assets/{file_name}".replace(" ", "%20")
                print(f"\nUploaded: {file_name}\nView on github: {blob_url}\nDirect Link: {blob_url}?raw=true")
            except Exception as e: 
                loading = False; t.join(); print(f"\nError: {e}")
        else:
            print("Error: File not found.")
    else:
        print("Error: Command not found, showing help text\n")
        help_txt()
