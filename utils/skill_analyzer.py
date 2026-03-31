"""
Skill Analyzer Utility
Compares extracted resume skills against job role requirements
and calculates match scores and skill gaps.
"""

# Job role skill requirements
ROLE_REQUIREMENTS = {
    'ai': {
        'title': 'AI Engineer',
        'required_skills': {
            'technical': [
                'python', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
                'deep learning', 'machine learning', 'neural network', 'nlp',
                'computer vision', 'transformers', 'huggingface', 'llm',
                'generative ai', 'prompt engineering', 'fine-tuning', 'rag',
                'pandas', 'numpy', 'sql', 'git'
            ],
            'tools': [
                'jupyter', 'docker', 'aws', 'azure', 'gcp', 'mlops',
                'kubernetes', 'airflow', 'spark', 'kafka', 'redis',
                'postgresql', 'mongodb', 'elasticsearch', 'github'
            ],
            'soft_skills': [
                'problem solving', 'critical thinking', 'communication',
                'teamwork', 'research', 'documentation', 'agile'
            ]
        },
        'weights': {
            'technical': 0.60,
            'tools': 0.25,
            'soft_skills': 0.15
        },
        'description': 'Builds and deploys AI/ML models and systems at scale'
    },
    'data_analyst': {
        'title': 'Data Analyst',
        'required_skills': {
            'technical': [
                'python', 'r', 'sql', 'pandas', 'numpy', 'matplotlib',
                'seaborn', 'plotly', 'statistics', 'data visualization',
                'excel', 'machine learning', 'scikit-learn', 'a/b testing',
                'feature engineering', 'data cleaning', 'etl'
            ],
            'tools': [
                'tableau', 'power bi', 'looker', 'google analytics', 'jupyter',
                'postgresql', 'mysql', 'bigquery', 'snowflake', 'spark',
                'git', 'github', 'aws', 'gcp'
            ],
            'soft_skills': [
                'communication', 'storytelling', 'problem solving', 'attention to detail',
                'critical thinking', 'presentation', 'collaboration', 'business acumen'
            ]
        },
        'weights': {
            'technical': 0.55,
            'tools': 0.30,
            'soft_skills': 0.15
        },
        'description': 'Analyzes data to extract business insights and drive decisions'
    },
    'web_developer': {
        'title': 'Web Developer',
        'required_skills': {
            'technical': [
                'html', 'css', 'javascript', 'typescript', 'react', 'angular',
                'vue', 'node.js', 'rest api', 'graphql', 'sql', 'git',
                'responsive design', 'accessibility', 'testing', 'webpack',
                'sass/scss', 'next.js'
            ],
            'tools': [
                'github', 'docker', 'aws', 'azure', 'firebase', 'mongodb',
                'postgresql', 'redis', 'nginx', 'ci/cd', 'figma', 'postman',
                'vscode', 'linux', 'kubernetes'
            ],
            'soft_skills': [
                'communication', 'teamwork', 'problem solving', 'agile',
                'scrum', 'time management', 'collaboration', 'attention to detail'
            ]
        },
        'weights': {
            'technical': 0.55,
            'tools': 0.30,
            'soft_skills': 0.15
        },
        'description': 'Builds full-stack web applications and user interfaces'
    },
    'ml_engineer': {
        'title': 'ML Engineer',
        'required_skills': {
            'technical': [
                'python', 'tensorflow', 'pytorch', 'scikit-learn', 'machine learning',
                'deep learning', 'neural network', 'feature engineering', 'mlops',
                'model deployment', 'sql', 'git', 'spark', 'statistics',
                'data pipeline', 'etl', 'pandas', 'numpy'
            ],
            'tools': [
                'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'airflow',
                'kafka', 'mlflow', 'kubeflow', 'terraform', 'jenkins',
                'github actions', 'postgresql', 'redis', 'elasticsearch'
            ],
            'soft_skills': [
                'problem solving', 'critical thinking', 'communication',
                'teamwork', 'agile', 'documentation', 'research', 'collaboration'
            ]
        },
        'weights': {
            'technical': 0.60,
            'tools': 0.25,
            'soft_skills': 0.15
        },
        'description': 'Productionizes ML models and builds scalable ML infrastructure'
    },
    'devops': {
        'title': 'DevOps Engineer',
        'required_skills': {
            'technical': [
                'linux', 'bash', 'python', 'docker', 'kubernetes', 'terraform',
                'ansible', 'ci/cd', 'git', 'networking', 'security',
                'monitoring', 'logging', 'infrastructure as code', 'sql'
            ],
            'tools': [
                'aws', 'azure', 'gcp', 'jenkins', 'gitlab ci', 'github actions',
                'prometheus', 'grafana', 'nginx', 'helm', 'vault', 'consul',
                'kafka', 'elasticsearch', 'redis', 'postgresql'
            ],
            'soft_skills': [
                'problem solving', 'communication', 'teamwork', 'agile',
                'incident management', 'documentation', 'collaboration', 'time management'
            ]
        },
        'weights': {
            'technical': 0.55,
            'tools': 0.30,
            'soft_skills': 0.15
        },
        'description': 'Automates infrastructure and streamlines software delivery pipelines'
    }
}

# Priority skills by role (the most critical ones)
PRIORITY_SKILLS = {
    'ai': ['python', 'pytorch', 'tensorflow', 'llm', 'deep learning', 'nlp', 'generative ai', 'mlops'],
    'data_analyst': ['sql', 'python', 'tableau', 'power bi', 'statistics', 'data visualization'],
    'web_developer': ['javascript', 'react', 'html', 'css', 'node.js', 'rest api'],
    'ml_engineer': ['python', 'mlops', 'docker', 'kubernetes', 'model deployment', 'airflow'],
    'devops': ['docker', 'kubernetes', 'terraform', 'ci/cd', 'aws', 'linux']
}


def normalize_skill(skill):
    """Normalize a skill string for comparison."""
    skill = skill.lower().strip()
    # Map common aliases
    aliases = {
        'js': 'javascript',
        'ts': 'typescript',
        'py': 'python',
        'k8s': 'kubernetes',
        'sklearn': 'scikit-learn',
        'nodejs': 'node.js',
        'node': 'node.js',
        'ml': 'machine learning',
        'dl': 'deep learning',
        'ai': 'artificial intelligence',
        'cv': 'computer vision',
        'nlp': 'natural language processing',
        'pg': 'postgresql',
        'psql': 'postgresql',
        'mongo': 'mongodb',
        'tf': 'tensorflow',
        'pt': 'pytorch',
    }
    return aliases.get(skill, skill)


def calculate_category_score(user_skills, required_skills):
    """Calculate the match score for a category of skills."""
    if not required_skills:
        return 0.0, [], []

    normalized_user = {normalize_skill(s) for s in user_skills}
    normalized_required = [normalize_skill(s) for s in required_skills]

    matched = []
    missing = []

    for skill in normalized_required:
        # Check exact match or partial match
        if skill in normalized_user:
            matched.append(skill)
        else:
            # Check partial matches (e.g., "scikit-learn" matches "scikit")
            found = False
            for user_skill in normalized_user:
                if skill in user_skill or user_skill in skill:
                    matched.append(skill)
                    found = True
                    break
            if not found:
                missing.append(skill)

    score = len(matched) / len(normalized_required) if normalized_required else 0.0
    return score, matched, missing


def analyze_skills(user_skills, role_key):
    """
    Main function to analyze user skills against a target role.
    Returns comprehensive analysis with scores and gaps.
    """
    if role_key not in ROLE_REQUIREMENTS:
        role_key = 'ai'  # Default to AI Engineer

    role = ROLE_REQUIREMENTS[role_key]
    required = role['required_skills']
    weights = role['weights']

    # Calculate scores per category
    tech_score, tech_matched, tech_missing = calculate_category_score(
        user_skills, required['technical']
    )
    tools_score, tools_matched, tools_missing = calculate_category_score(
        user_skills, required['tools']
    )
    soft_score, soft_matched, soft_missing = calculate_category_score(
        user_skills, required['soft_skills']
    )

    # Calculate weighted overall score
    overall_score = (
        tech_score * weights['technical'] +
        tools_score * weights['tools'] +
        soft_score * weights['soft_skills']
    )
    overall_pct = round(overall_score * 100)

    # All matched and missing skills
    all_matched = tech_matched + tools_matched + soft_matched
    all_missing = tech_missing + tools_missing + soft_missing

    # Priority missing skills
    role_priorities = PRIORITY_SKILLS.get(role_key, [])
    priority_missing = [s for s in role_priorities if normalize_skill(s) in all_missing]
    # Also add top missing technical skills not already in priority
    for skill in tech_missing[:5]:
        if skill not in priority_missing:
            priority_missing.append(skill)
    priority_missing = priority_missing[:8]  # Limit to 8

    # Generate recommendation level
    if overall_pct >= 80:
        readiness = 'Advanced'
        recommendation = 'You are well-prepared for this role. Focus on advanced topics and specializations.'
    elif overall_pct >= 60:
        readiness = 'Intermediate'
        recommendation = 'Good foundation! Fill in the identified gaps to become job-ready.'
    elif overall_pct >= 40:
        readiness = 'Beginner-Intermediate'
        recommendation = 'You have some relevant skills. Significant upskilling needed in core areas.'
    else:
        readiness = 'Beginner'
        recommendation = 'Start with foundational skills. Follow the recommended learning path carefully.'

    return {
        'role_key': role_key,
        'role_title': role['title'],
        'role_description': role['description'],
        'overall_score': overall_pct,
        'readiness_level': readiness,
        'recommendation': recommendation,
        'category_scores': {
            'technical': round(tech_score * 100),
            'tools': round(tools_score * 100),
            'soft_skills': round(soft_score * 100)
        },
        'skills_matched': all_matched,
        'skills_missing': all_missing,
        'skills_priority': priority_missing,
        'total_required': len(required['technical']) + len(required['tools']) + len(required['soft_skills']),
        'total_matched': len(all_matched),
        'breakdown': {
            'technical': {
                'score': round(tech_score * 100),
                'matched': tech_matched,
                'missing': tech_missing,
                'total': len(required['technical'])
            },
            'tools': {
                'score': round(tools_score * 100),
                'matched': tools_matched,
                'missing': tools_missing,
                'total': len(required['tools'])
            },
            'soft_skills': {
                'score': round(soft_score * 100),
                'matched': soft_matched,
                'missing': soft_missing,
                'total': len(required['soft_skills'])
            }
        }
    }


def get_role_list():
    """Return a list of available roles with basic info."""
    return [
        {
            'key': key,
            'title': role['title'],
            'description': role['description']
        }
        for key, role in ROLE_REQUIREMENTS.items()
    ]


def get_ats_suggestions(user_skills, role_key, resume_text=''):
    """
    Generate ATS optimization suggestions for a resume.
    Returns keyword gaps and formatting suggestions.
    """
    if role_key not in ROLE_REQUIREMENTS:
        role_key = 'ai'

    role = ROLE_REQUIREMENTS[role_key]
    all_required = (
        role['required_skills']['technical'] +
        role['required_skills']['tools']
    )

    normalized_user = {normalize_skill(s) for s in user_skills}
    missing_keywords = [
        s for s in all_required
        if normalize_skill(s) not in normalized_user
    ]

    # ATS score estimate (keyword coverage)
    keyword_coverage = 1 - (len(missing_keywords) / len(all_required)) if all_required else 1
    ats_score = round(keyword_coverage * 100)

    suggestions = []

    # High priority suggestions
    if len(missing_keywords) > 5:
        suggestions.append({
            'priority': 'high',
            'category': 'Keywords',
            'suggestion': f'Add {len(missing_keywords)} missing role-specific keywords to your resume',
            'detail': f'Missing: {", ".join(missing_keywords[:8])}'
        })

    if not any(s in normalized_user for s in ['github', 'gitlab', 'git']):
        suggestions.append({
            'priority': 'high',
            'category': 'Tools',
            'suggestion': 'Add version control experience (Git/GitHub)',
            'detail': 'Version control is expected in all technical roles'
        })

    # Medium priority suggestions
    suggestions.append({
        'priority': 'medium',
        'category': 'Formatting',
        'suggestion': 'Use bullet points to describe achievements with quantifiable metrics',
        'detail': 'e.g., "Improved model accuracy by 15%" instead of "Worked on ML models"'
    })

    suggestions.append({
        'priority': 'medium',
        'category': 'Structure',
        'suggestion': 'Add a Skills section with relevant technical keywords prominently',
        'detail': 'ATS systems scan for keyword density in dedicated skills sections'
    })

    if ats_score < 60:
        suggestions.append({
            'priority': 'high',
            'category': 'Content',
            'suggestion': 'Tailor your resume specifically for this job role',
            'detail': 'Generic resumes score poorly on ATS systems'
        })
    else:
        suggestions.append({
            'priority': 'medium',
            'category': 'Content',
            'suggestion': 'Mirror language from the job description',
            'detail': 'Use the same terminology as the target job posting'
        })

    suggestions.append({
        'priority': 'low',
        'category': 'Format',
        'suggestion': 'Use a clean, single-column layout for ATS compatibility',
        'detail': 'Avoid tables, graphics, and headers/footers that confuse ATS parsers'
    })

    return {
        'ats_score': ats_score,
        'missing_keywords': missing_keywords[:10],
        'suggestions': suggestions
    }
