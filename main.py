import os
import openai
import logging
from github import Github
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

github_token = os.getenv('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')
openai_api_key = os.getenv('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')

g = Github(github_token)
openai.api_key = openai_api_key

def search_github_repositories(keyword, language="python", stars=">=100", max_repos=10):
    """
    Search GitHub for repositories based on keywords, language, and stars filter.
    """
    try:
        query = f"{keyword} language:{language} stars:{stars}"
        search_results = g.search_repositories(query=query, sort="stars", order="desc")
        
        results = []
        for repo in search_results[:max_repos]:
            results.append({
                'full_name': repo.full_name,
                'html_url': repo.html_url,
                'description': repo.description
            })

        logging.info(f"Found {len(results)} repositories for keyword '{keyword}' with at least {stars} stars.")
        return results
    except Exception as e:
        logging.error(f"Error during GitHub search: {e}")
        return []

def fetch_github_repo(repo_name):
    """
    Fetch the README and files (requirements.txt, setup.py) from a given GitHub repository.
    """
    try:
        repo = g.get_repo(repo_name)
        readme = repo.get_readme().decoded_content.decode("utf-8")
        logging.info(f"Fetched README from {repo_name}")

        files = {}
        for file_name in ["requirements.txt", "setup.py", ".gitignore"]:
            try:
                file_content = repo.get_contents(file_name).decoded_content.decode("utf-8")
                files[file_name] = file_content
                logging.info(f"Fetched {file_name} from {repo_name}")
            except:
                logging.warning(f"{file_name} not found in {repo_name}")
        return readme, files
    except Exception as e:
        logging.error(f"Error fetching repository {repo_name}: {e}")
        return None, None

def summarize_readme(readme_content):
    """
    Use GPT-4.o to summarize the README file with more context.
    """
    try:
        prompt = f"""
        Here is the README file of a GitHub project:

        {readme_content}

        Please provide a detailed summary of the project and its purpose, what are some key features and technologies used in it.
        """
        response = openai.Completion.create(
            model="gpt-4o-mini",
            prompt=prompt,
            max_tokens=500
        )
        summary = response.choices[0].text.strip()
        return summary
    except Exception as e:
        logging.error(f"Error summarizing README: {e}")
        return None

def process_single_repository(repo_full_name):
    """
    Process a single repository: fetch README and files, summarize the README.
    """
    readme_content, repo_files = fetch_github_repo(repo_full_name)
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

def process_repositories_in_parallel(keyword):
    """
    Search GitHub, fetch README files, check for key files, and summarize them using GPT-4.0 Mini.
    This is done in parallel using ThreadPoolExecutor.
    """
    repositories = search_github_repositories(keyword)
    if not repositories:
        logging.error("No repositories found.")
        return

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_single_repository, repo['full_name']) for repo in repositories]
        for future in as_completed(futures):
            future.result() 

if __name__ == "__main__":
    keyword = input("Enter a keyword to search for GitHub repositories: ")
    process_repositories_in_parallel(keyword)
