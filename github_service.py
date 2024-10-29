from github import Github
import os
import requests
from src.config import GITHUB_TOKEN, BASE_DIRECTORY

class GitHubService:
    def __init__(self):
        self.github = Github(GITHUB_TOKEN)
    
    def validate_token(self):
        """Validate GitHub token is present and valid"""
        if not GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        try:
            self.github.get_user().login
            return True
        except Exception as e:
            raise ValueError(f"Invalid GitHub token: {str(e)}")

    def download_repository(self, repo_url):
        """Download repository contents"""
        try:
            self.validate_token()
            
            # Extract owner and repo name from URL
            url_parts = repo_url.replace("https://github.com/", "").split('/')
            if len(url_parts) != 2:
                raise ValueError("Invalid GitHub repository URL format")
                
            owner, repo_name = url_parts
            repo = self.github.get_repo(f"{owner}/{repo_name}")

            # Create repository directory
            repo_path = os.path.join(BASE_DIRECTORY, repo_name)
            
            # If directory exists, remove it first to ensure clean state
            if os.path.exists(repo_path):
                import shutil
                shutil.rmtree(repo_path)
            
            os.makedirs(repo_path)

            # Download repository contents recursively
            def download_contents(contents, current_path):
                for content_file in contents:
                    file_path = os.path.join(current_path, content_file.name)
                    if content_file.type == "file":
                        with open(file_path, "wb") as f:
                            f.write(requests.get(content_file.download_url).content)
                    elif content_file.type == "dir":
                        os.makedirs(file_path, exist_ok=True)
                        download_contents(repo.get_contents(content_file.path), file_path)

            # Start recursive download from root
            download_contents(repo.get_contents(""), repo_path)
            return repo_path, repo
            
        except Exception as e:
            print(f"Error downloading repository: {e}")
            return None, None

    def get_readme_content(self, repo):
        """Get README content from repository"""
        try:
            readme = repo.get_readme()
            return readme.decoded_content.decode('utf-8')
        except Exception as e:
            print(f"Error getting README: {e}")
            return None