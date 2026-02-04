"""
Normalizer Service - Handles data normalization and skill extraction.
"""
import re
from collections import Counter


# Common tech skills to extract (can be expanded)
KNOWN_SKILLS = [
    # Programming Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
    
    # Frontend
    "react", "reactjs", "react.js", "vue", "vuejs", "vue.js", "angular",
    "svelte", "next.js", "nextjs", "nuxt", "gatsby", "html", "css", "sass",
    "tailwind", "tailwindcss", "bootstrap", "jquery",
    
    # Backend
    "node.js", "nodejs", "express", "fastapi", "django", "flask", "spring",
    "spring boot", "asp.net", ".net", "rails", "laravel", "gin", "fiber",
    
    # Databases
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "dynamodb", "cassandra", "sqlite", "oracle", "sql server", "supabase",
    "firebase", "neo4j", "graphql",
    
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud", "docker",
    "kubernetes", "k8s", "terraform", "ansible", "jenkins", "github actions",
    "gitlab ci", "circleci", "vercel", "netlify", "heroku",
    
    # AI/ML
    "machine learning", "ml", "deep learning", "tensorflow", "pytorch",
    "keras", "scikit-learn", "pandas", "numpy", "opencv", "nlp",
    "natural language processing", "llm", "langchain", "openai", "gpt",
    "hugging face", "transformers",
    
    # Data
    "apache spark", "hadoop", "kafka", "airflow", "snowflake", "databricks",
    "power bi", "tableau", "looker", "dbt", "etl", "data pipeline",
    
    # Mobile
    "react native", "flutter", "ios", "android", "swift", "objective-c",
    
    # Tools
    "git", "github", "gitlab", "jira", "confluence", "slack", "figma",
    "postman", "linux", "bash", "vim", "vscode",
    
    # Concepts
    "rest", "restful", "api", "microservices", "serverless", "ci/cd",
    "agile", "scrum", "tdd", "unit testing", "integration testing"
]


def normalize_skill_name(skill: str) -> str:
    """Normalize skill name for consistent storage."""
    # Common variations
    mappings = {
        "reactjs": "react",
        "react.js": "react",
        "vuejs": "vue",
        "vue.js": "vue",
        "nodejs": "node.js",
        "golang": "go",
        "postgresql": "postgres",
        "amazon web services": "aws",
        "google cloud": "gcp",
        "k8s": "kubernetes",
        "ml": "machine learning"
    }
    
    normalized = skill.lower().strip()
    return mappings.get(normalized, normalized)


def extract_skills_from_text(text: str) -> list[dict]:
    """
    Extract known skills from text using keyword matching.
    
    Args:
        text: Job description or discussion body
        
    Returns:
        List of {skill_name, skill_name_normalized, mention_count}
    """
    if not text:
        return []
    
    text_lower = text.lower()
    found_skills = Counter()
    
    for skill in KNOWN_SKILLS:
        # Use word boundary matching
        pattern = r'\b' + re.escape(skill) + r'\b'
        matches = re.findall(pattern, text_lower)
        if matches:
            found_skills[skill] += len(matches)
    
    results = []
    for skill, count in found_skills.items():
        results.append({
            "skill_name": skill,
            "skill_name_normalized": normalize_skill_name(skill),
            "mention_count": count
        })
    
    return results


def normalize_job_title(title: str) -> str:
    """Normalize job title for grouping."""
    # Remove common prefixes/suffixes
    title = title.lower().strip()
    
    # Remove seniority levels for grouping
    title = re.sub(r'\b(senior|junior|mid-level|lead|principal|staff|entry-level)\b', '', title)
    
    # Remove common suffixes
    title = re.sub(r'\b(engineer|developer|programmer)\b', 'developer', title)
    
    return title.strip()
