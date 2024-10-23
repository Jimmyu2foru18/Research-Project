import os
import openai
from github import Github
import dspy

github_token = os.getenv('GITHUB_TOKEN')
openai.api_key = os.getenv('OPENAI_API_KEY')
g = Github(github_token)

def search_repositories(keyword, language="python", stars=">=100", max_repos=10):
    query = f"{keyword} language:{language} stars:{stars}"
    results = []
    try:
        for repo in g.search_repositories(query=query, sort="stars", order="desc")[:max_repos]:
            results.append({
                'full_name': repo.full_name,
                'html_url': repo.html_url,
                'description': repo.description
            })
        print(f"Found {len(results)} repositories for keyword '{keyword}'.")
    except Exception as e:
        print(f"GitHub search error: {e}")
    return results

def fetch_repository_details(repo_name):
    try:
        repo = g.get_repo(repo_name)
        return repo.get_readme().decoded_content.decode("utf-8")
    except Exception as e:
        print(f"Error fetching {repo_name}: {e}")
        return None

def analyze_readme_keywords(readme_content, keywords):
    data = dspy.DataFrame({'content': [readme_content]})
    return {keyword: data['content'].str.contains(keyword).sum() for keyword in keywords}

def process_repository(repo_full_name, keywords):
    readme_content = fetch_repository_details(repo_full_name)
    if readme_content:
        keyword_counts = analyze_readme_keywords(readme_content, keywords)
        print(f"Keyword counts for {repo_full_name}: {keyword_counts}")

if __name__ == "__main__":
    keyword = input("Enter a keyword to search for GitHub repositories: ")
    keywords = input("Enter keywords to analyze in the README (comma-separated): ").split(',')
    keywords = [k.strip() for k in keywords]

    repos = search_repositories(keyword)
    for repo in repos:
        process_repository(repo['full_name'], keywords)
        
