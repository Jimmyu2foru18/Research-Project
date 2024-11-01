import openai
import os
import requests
import shutil 
from github import Github
import dspy
import json

github_token = os.getenv('GITHUB_TOKEN')  
openai.api_key = os.getenv('OPENAI_API_KEY')
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
base_directory = os.path.join(desktop_path, "repositories/")

def analyze_build_steps(readme_content):
    """Analyze README content using OpenAI to determine build steps"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.0-mini",
            messages=[
                {"role": "system", "content": "You are a build system expert. Analyze the repository README and return specific build steps in JSON format."},
                {"role": "user", "content": f"""
                Analyze this README and provide:
                1. List of required dependencies
                2. Environment setup steps
                3. Build commands
                4. Test commands
                
                Return the response in this JSON format:
                {{
                    "dependencies": ["dep1", "dep2"],
                    "setup_steps": [
                        {{"command": "actual_command", "description": "what this does"}}
                    ],
                    "build_steps": [
                        {{"command": "actual_command", "description": "what this does"}}
                    ],
                    "test_steps": [
                        {{"command": "actual_command", "description": "what this does"}}
                    ]
                }}

                README content:
                {readme_content}
                """}
            ]
        )

        build_instructions = json.loads(response.choices[0].message['content'])
        return build_instructions
    except Exception as e:
        print(f"Error analyzing build steps: {e}")
        return None

def execute_build_steps(repo_path, build_instructions):
    """Execute the build steps returned by OpenAI"""
    try:
        print("Installing dependencies...")
        for dep in build_instructions['dependencies']:
            os.system(f"pip install {dep}")
s
        print("\nExecuting setup steps...")
        for step in build_instructions['setup_steps']:
            print(f"\nExecuting: {step['description']}")
            result = os.system(f"cd {repo_path} && {step['command']}")
            if result != 0:
                print(f"Setup step failed: {step['command']}")
                return False

        print("\nExecuting build steps...")
        for step in build_instructions['build_steps']:
            print(f"\nExecuting: {step['description']}")
            result = os.system(f"cd {repo_path} && {step['command']}")
            if result != 0:
                print(f"Build step failed: {step['command']}")
                return False

        print("\nExecuting test steps...")
        for step in build_instructions['test_steps']:
            print(f"\nExecuting: {step['description']}")
            result = os.system(f"cd {repo_path} && {step['command']}")
            if result != 0:
                print(f"Test step failed: {step['command']}")
                return False
                
        return True
    except Exception as e:
        print(f"Error executing build steps: {e}")
        return False

def access_github_repo(repo_url):
    """Access GitHub repository, download content, and analyze build steps"""
    try:
        g = Github(github_token)
        repo_name = repo_url.split('/')[-1]
        repo = g.get_repo(repo_url.replace("https://github.com/", ""))

        repo_path = os.path.join(base_directory, repo_name)
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)

        for content_file in repo.get_contents(""):
            file_path = os.path.join(repo_path, content_file.name)
            if content_file.type == "file":
                with open(file_path, "wb") as f:
                    f.write(requests.get(content_file.download_url).content)
            elif content_file.type == "dir":
                os.makedirs(file_path)

        try:
            readme = repo.get_readme()
            readme_content = readme.decoded_content.decode('utf-8')

            build_instructions = analyze_build_steps(readme_content)
            
            if build_instructions:
                print("\nAnalyzed build instructions:")
                print(json.dumps(build_instructions, indent=2))
  
                if execute_build_steps(repo_path, build_instructions):
                    print("\nRepository built successfully!")
                else:
                    print("\nRepository build failed!")
            
        except Exception as e:
            print(f"Error processing README: {e}")

        return repo_path
    except Exception as e:
        print(f"Error accessing repository: {e}")
        return None

def find_missing_files(repo1_path, repo2_path):
    """Find missing files between 2 repos"""
    missing_files = []
    repo1_files = set(os.listdir(repo1_path))
    repo2_files = set(os.listdir(repo2_path))
    for file in repo1_files:
        if file not in repo2_files:
            missing_files.append(file)
    return missing_files

def run_project(repo_url1, repo_url2=None):
    """Run the full project"""

    print(f"\nProcessing repository 1: {repo_url1}")
    repo1_path = access_github_repo(repo_url1)
    
    if repo_url2:
        print(f"\nProcessing repository 2: {repo_url2}")
        repo2_path = access_github_repo(repo_url2)

        if repo1_path and repo2_path:
            missing_files = find_missing_files(repo1_path, repo2_path)
            if missing_files:
                print("\nMissing files:", missing_files)
            else:
                print("\nNo missing files found.")

if __name__ == "__main__":
    repo_url = input("Enter the GitHub repository URL to analyze and build: ")
    run_project(repo_url)
