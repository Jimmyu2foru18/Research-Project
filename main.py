import os
import openai
import logging
from github import Github

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize GitHub and OpenAI clients
github_token = os.getenv('GITHUB_TOKEN')  # Change to your environment variable name
openai.api_key = os.getenv('OPENAI_API_KEY')  # Change to your environment variable name
g = Github(github_token)

def search_repositories(keyword, language="python", stars=">=100", max_repos=10):
    """Search GitHub repositories by keyword and return relevant info."""
    query = f"{keyword} language:{language} stars:{stars}"
    results = []
    try:
        for repo in g.search_repositories(query=query, sort="stars", order="desc")[:max_repos]:
            results.append({
                'full_name': repo.full_name,
                'html_url': repo.html_url,
                'description': repo.description
            })
        logging.info(f"Found {len(results)} repositories for keyword '{keyword}'.")
    except Exception as e:
        logging.error(f"GitHub search error: {e}")
    return results

def fetch_repository_details(repo_name):
    """Fetch the README and specific files from a repository."""
    try:
        repo = g.get_repo(repo_name)
        readme = repo.get_readme().decoded_content.decode("utf-8")
        logging.info(f"Fetched README from {repo_name}")

        files = {}
        for file_name in ["setup.txt", ".gitignore"]:
            try:
                files[file_name] = repo.get_contents(file_name).decoded_content.decode("utf-8")
                logging.info(f"Fetched {file_name} from {repo_name}")
            except Exception:
                logging.warning(f"{file_name} not found in {repo_name}")

        return readme, files
    except Exception as e:
        logging.error(f"Error fetching {repo_name}: {e}")
        return None, None

def summarize_readme(readme_content):
    """Summarize the README content using OpenAI's API."""
    prompt = f"Here is the README file of a GitHub project:\n\n{readme_content}\n\nPlease summarize it."
    try:
        response = openai.Completion.create(model="gpt-4o-mini", prompt=prompt, max_tokens=150)
        return response.choices[0].text.strip()
    except Exception as e:
        logging.error(f"Error summarizing README: {e}")
        return None

def process_repository(repo_full_name):
    """Process a repository by fetching and summarizing its README."""
    readme_content, repo_files = fetch_repository_details(repo_full_name)
    if readme_content:
        summary = summarize_readme(readme_content)
        if summary:
            logging.info(f"\nSummary for {repo_full_name}:\n{summary}\n")
        else:
            logging.error(f"Could not summarize README for {repo_full_name}")

    missing_files = [file for file in ["requirements.txt", "setup.py", ".gitignore"] if file not in repo_files]
    if missing_files:
        logging.warning(f"Missing files in {repo_full_name}: {', '.join(missing_files)}")
    else:
        logging.info(f"All key files found in {repo_full_name}.")

if __name__ == "__main__":
    keyword = input("Enter a keyword to search for GitHub repositories: ")
    repos = search_repositories(keyword)
    for repo in repos:
        process_repository(repo['full_name'])

