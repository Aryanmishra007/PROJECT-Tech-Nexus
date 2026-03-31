"""
AI Service Utility
Provides AI-powered features: diagnostic tests, learning paths,
interview questions, and answer feedback using rule-based + template logic.
"""

import random

# ─────────────────────────────────────────────
# Diagnostic Test Questions per Skill
# ─────────────────────────────────────────────

DIAGNOSTIC_QUESTIONS = {
    'python': [
        {
            'question': 'What is the output of `list(range(2, 10, 3))`?',
            'options': ['[2, 5, 8]', '[2, 4, 6, 8]', '[2, 3, 6, 9]', '[3, 6, 9]'],
            'answer': 0,
            'explanation': 'range(2, 10, 3) starts at 2, steps by 3: 2, 5, 8'
        },
        {
            'question': 'Which of the following is used for list comprehension in Python?',
            'options': ['(x for x in list)', '[x for x in list]', '{x for x in list}', 'All of the above'],
            'answer': 3,
            'explanation': 'All three are valid: list comprehension [], generator (), set comprehension {}'
        },
        {
            'question': 'What does the `*args` syntax do in a Python function definition?',
            'options': [
                'Passes a dictionary of keyword arguments',
                'Passes a variable number of positional arguments as a tuple',
                'Multiplies the arguments',
                'Unpacks a list into separate arguments'
            ],
            'answer': 1,
            'explanation': '*args collects extra positional arguments into a tuple'
        },
        {
            'question': 'Which data structure uses key-value pairs in Python?',
            'options': ['List', 'Tuple', 'Dictionary', 'Set'],
            'answer': 2,
            'explanation': 'Dictionaries store data as key-value pairs in Python'
        }
    ],
    'machine learning': [
        {
            'question': 'What is the purpose of the train/test split in machine learning?',
            'options': [
                'To increase training data size',
                'To evaluate model performance on unseen data',
                'To reduce computational cost',
                'To clean the dataset'
            ],
            'answer': 1,
            'explanation': 'Test split evaluates how well the model generalizes to new, unseen data'
        },
        {
            'question': 'Which metric is most appropriate for an imbalanced classification problem?',
            'options': ['Accuracy', 'F1-Score', 'Mean Squared Error', 'R-squared'],
            'answer': 1,
            'explanation': 'F1-Score balances precision and recall, making it suitable for imbalanced datasets'
        },
        {
            'question': 'What is overfitting in machine learning?',
            'options': [
                'When a model performs poorly on training data',
                'When a model learns noise in training data and fails to generalize',
                'When training takes too long',
                'When the model has too few parameters'
            ],
            'answer': 1,
            'explanation': 'Overfitting occurs when a model memorizes training data including noise, reducing generalization'
        },
        {
            'question': 'Which algorithm is a supervised learning technique for classification?',
            'options': ['K-Means', 'PCA', 'Random Forest', 'DBSCAN'],
            'answer': 2,
            'explanation': 'Random Forest is a supervised ensemble learning method for classification and regression'
        }
    ],
    'deep learning': [
        {
            'question': 'What is the role of the activation function in a neural network?',
            'options': [
                'To initialize weights',
                'To normalize the input data',
                'To introduce non-linearity into the model',
                'To reduce overfitting'
            ],
            'answer': 2,
            'explanation': 'Activation functions introduce non-linearity, enabling networks to learn complex patterns'
        },
        {
            'question': 'What does "backpropagation" refer to in neural networks?',
            'options': [
                'Forward pass through the network',
                'Algorithm to compute gradients and update weights',
                'Regularization technique',
                'Data augmentation method'
            ],
            'answer': 1,
            'explanation': 'Backpropagation computes gradients of the loss w.r.t. weights using chain rule'
        },
        {
            'question': 'Which layer type is most commonly used in image recognition tasks?',
            'options': ['Dense (Fully Connected)', 'Recurrent (RNN)', 'Convolutional (CNN)', 'Embedding'],
            'answer': 2,
            'explanation': 'CNNs use spatial convolutions that are highly effective for image feature extraction'
        },
        {
            'question': 'What problem does batch normalization help solve?',
            'options': [
                'Overfitting only',
                'Internal covariate shift and training instability',
                'Underfitting',
                'Data imbalance'
            ],
            'answer': 1,
            'explanation': 'Batch normalization normalizes layer inputs, reducing internal covariate shift and speeding training'
        }
    ],
    'nlp': [
        {
            'question': 'What does TF-IDF stand for?',
            'options': [
                'Total Frequency - Inverse Data Format',
                'Term Frequency - Inverse Document Frequency',
                'Text Feature - Information Dense Format',
                'Token Filter - Index Data Feature'
            ],
            'answer': 1,
            'explanation': 'TF-IDF measures word importance by balancing frequency in a document vs. rarity across documents'
        },
        {
            'question': 'What is tokenization in NLP?',
            'options': [
                'Converting tokens to embeddings',
                'Breaking text into individual words or sub-word units',
                'Removing stop words from text',
                'Translating text between languages'
            ],
            'answer': 1,
            'explanation': 'Tokenization splits raw text into tokens (words, subwords, or characters) for processing'
        },
        {
            'question': 'What is the main innovation of the Transformer architecture?',
            'options': [
                'Convolutional layers for text',
                'Self-attention mechanism enabling parallel processing',
                'Recurrent connections between layers',
                'Bidirectional LSTM cells'
            ],
            'answer': 1,
            'explanation': 'Transformers use self-attention to process all tokens in parallel, unlike sequential RNNs'
        },
        {
            'question': 'Which technique is used to generate fixed-size vector representations of words?',
            'options': ['Stemming', 'Lemmatization', 'Word Embeddings (Word2Vec/GloVe)', 'POS Tagging'],
            'answer': 2,
            'explanation': 'Word embeddings map words to dense vector spaces capturing semantic relationships'
        }
    ],
    'sql': [
        {
            'question': 'Which SQL clause is used to filter grouped results?',
            'options': ['WHERE', 'HAVING', 'FILTER', 'GROUP FILTER'],
            'answer': 1,
            'explanation': 'HAVING filters groups created by GROUP BY, whereas WHERE filters rows before grouping'
        },
        {
            'question': 'What is the difference between INNER JOIN and LEFT JOIN?',
            'options': [
                'No difference',
                'INNER JOIN returns only matching rows; LEFT JOIN returns all left rows plus matches',
                'LEFT JOIN is faster',
                'INNER JOIN includes NULL values'
            ],
            'answer': 1,
            'explanation': 'INNER JOIN returns rows with matches in both tables; LEFT JOIN retains all left table rows'
        },
        {
            'question': 'Which SQL aggregate function returns the number of rows?',
            'options': ['SUM()', 'AVG()', 'COUNT()', 'MAX()'],
            'answer': 2,
            'explanation': 'COUNT() returns the number of rows matching the query condition'
        },
        {
            'question': 'What does the DISTINCT keyword do in SQL?',
            'options': [
                'Sorts results in descending order',
                'Returns only unique/non-duplicate values',
                'Filters NULL values',
                'Groups rows by a column'
            ],
            'answer': 1,
            'explanation': 'DISTINCT eliminates duplicate rows from the result set'
        }
    ],
    'docker': [
        {
            'question': 'What is a Docker image?',
            'options': [
                'A running container instance',
                'A lightweight, read-only template used to create containers',
                'A Docker configuration file',
                'A virtual machine snapshot'
            ],
            'answer': 1,
            'explanation': 'Docker images are immutable templates that define the container environment and files'
        },
        {
            'question': 'Which command is used to build a Docker image from a Dockerfile?',
            'options': ['docker run', 'docker pull', 'docker build', 'docker create'],
            'answer': 2,
            'explanation': '`docker build -t image-name .` builds an image from the Dockerfile in the current directory'
        },
        {
            'question': 'What is the purpose of the EXPOSE instruction in a Dockerfile?',
            'options': [
                'Opens the port on the host machine',
                'Documents which ports the container listens on at runtime',
                'Forwards traffic to the container',
                'Sets environment variables'
            ],
            'answer': 1,
            'explanation': 'EXPOSE is documentation only; actual port publishing requires the -p flag in docker run'
        },
        {
            'question': 'What is Docker Compose used for?',
            'options': [
                'Building single Docker images',
                'Defining and running multi-container Docker applications',
                'Monitoring container performance',
                'Pushing images to Docker Hub'
            ],
            'answer': 1,
            'explanation': 'Docker Compose uses YAML files to configure and run multi-container applications'
        }
    ],
    'kubernetes': [
        {
            'question': 'What is a Kubernetes Pod?',
            'options': [
                'A cluster of nodes',
                'The smallest deployable unit containing one or more containers',
                'A load balancer',
                'A storage volume'
            ],
            'answer': 1,
            'explanation': 'A Pod is the basic execution unit in Kubernetes, encapsulating containers and shared resources'
        },
        {
            'question': 'Which Kubernetes object ensures a specified number of Pod replicas are running?',
            'options': ['Service', 'ConfigMap', 'ReplicaSet', 'Namespace'],
            'answer': 2,
            'explanation': 'ReplicaSet maintains the desired number of identical pod replicas at all times'
        },
        {
            'question': 'What is the role of a Kubernetes Service?',
            'options': [
                'To schedule pods to nodes',
                'To provide stable network access to a set of pods',
                'To store configuration data',
                'To manage persistent storage'
            ],
            'answer': 1,
            'explanation': 'Services provide stable IPs and DNS names for accessing pods, enabling load balancing'
        },
        {
            'question': 'What does `kubectl apply -f deployment.yaml` do?',
            'options': [
                'Deletes the deployment',
                'Creates or updates resources defined in the YAML file',
                'Only validates the YAML file',
                'Scales the deployment'
            ],
            'answer': 1,
            'explanation': '`kubectl apply` creates or updates Kubernetes resources from a manifest file declaratively'
        }
    ],
    'react': [
        {
            'question': 'What is the purpose of React hooks?',
            'options': [
                'To style components',
                'To use state and lifecycle features in function components',
                'To connect to a database',
                'To handle routing'
            ],
            'answer': 1,
            'explanation': 'Hooks like useState and useEffect allow functional components to use state and side effects'
        },
        {
            'question': 'What does the useEffect hook do with an empty dependency array `[]`?',
            'options': [
                'Runs on every render',
                'Runs only once after the initial render',
                'Runs before every render',
                'Never runs'
            ],
            'answer': 1,
            'explanation': 'Empty dependency array means the effect runs only once, equivalent to componentDidMount'
        },
        {
            'question': 'What is "prop drilling" in React?',
            'options': [
                'Optimizing component rendering',
                'Passing props through many nested component levels unnecessarily',
                'Using the Context API',
                'Lazy loading components'
            ],
            'answer': 1,
            'explanation': 'Prop drilling is when props are passed through many levels of components that don\'t need them'
        },
        {
            'question': 'Which method triggers a re-render of a React component?',
            'options': ['this.forceUpdate()', 'setState()', 'Both A and B', 'Neither'],
            'answer': 2,
            'explanation': 'Both forceUpdate() in class components and setState() trigger re-renders in React'
        }
    ],
    'default': [
        {
            'question': 'What is the primary benefit of version control systems like Git?',
            'options': [
                'Faster code execution',
                'Tracking changes and enabling collaboration on code',
                'Automatic bug fixing',
                'Database management'
            ],
            'answer': 1,
            'explanation': 'Version control tracks code history, enables branching, and facilitates team collaboration'
        },
        {
            'question': 'What does API stand for?',
            'options': [
                'Application Protocol Interface',
                'Automated Program Interaction',
                'Application Programming Interface',
                'Advanced Processing Integration'
            ],
            'answer': 2,
            'explanation': 'API (Application Programming Interface) defines how software components interact with each other'
        },
        {
            'question': 'Which HTTP method is typically used to retrieve data from a server?',
            'options': ['POST', 'PUT', 'DELETE', 'GET'],
            'answer': 3,
            'explanation': 'GET requests retrieve data from a server without modifying any resources'
        },
        {
            'question': 'What is the purpose of caching in software systems?',
            'options': [
                'To encrypt data',
                'To store frequently accessed data in fast-access storage for better performance',
                'To back up data',
                'To compress files'
            ],
            'answer': 1,
            'explanation': 'Caching reduces latency and server load by storing frequently accessed data closer to the consumer'
        }
    ]
}


# ─────────────────────────────────────────────
# Learning Path Templates
# ─────────────────────────────────────────────

LEARNING_PATHS = {
    'ai': {
        'title': 'AI Engineer Learning Path',
        'total_duration': '6-9 months',
        'steps': [
            {
                'step': 1,
                'skill': 'Python for AI',
                'duration': '3-4 weeks',
                'topics': ['Advanced Python', 'OOP Concepts', 'NumPy & Pandas', 'Data Manipulation'],
                'resources': [
                    {'name': 'Python for Data Science (Coursera)', 'url': 'https://coursera.org/specializations/python'},
                    {'name': 'Real Python Tutorials', 'url': 'https://realpython.com'}
                ]
            },
            {
                'step': 2,
                'skill': 'Machine Learning Fundamentals',
                'duration': '4-6 weeks',
                'topics': ['Supervised Learning', 'Unsupervised Learning', 'Model Evaluation', 'Feature Engineering'],
                'resources': [
                    {'name': 'Andrew Ng ML Course (Coursera)', 'url': 'https://coursera.org/specializations/machine-learning-introduction'},
                    {'name': 'Hands-On ML with Scikit-Learn (Book)', 'url': 'https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032632/'}
                ]
            },
            {
                'step': 3,
                'skill': 'Deep Learning & Neural Networks',
                'duration': '5-7 weeks',
                'topics': ['Neural Network Architecture', 'CNNs', 'RNNs/LSTMs', 'PyTorch/TensorFlow'],
                'resources': [
                    {'name': 'Deep Learning Specialization (Coursera)', 'url': 'https://coursera.org/specializations/deep-learning'},
                    {'name': 'fast.ai Practical Deep Learning', 'url': 'https://fast.ai'}
                ]
            },
            {
                'step': 4,
                'skill': 'Large Language Models & NLP',
                'duration': '4-5 weeks',
                'topics': ['Transformers', 'BERT/GPT Architecture', 'Fine-tuning LLMs', 'RAG Systems', 'Prompt Engineering'],
                'resources': [
                    {'name': 'HuggingFace NLP Course', 'url': 'https://huggingface.co/course'},
                    {'name': 'LangChain Documentation', 'url': 'https://python.langchain.com'}
                ]
            },
            {
                'step': 5,
                'skill': 'MLOps & Model Deployment',
                'duration': '3-4 weeks',
                'topics': ['MLflow', 'Model Serving', 'Docker for ML', 'CI/CD for ML', 'Monitoring'],
                'resources': [
                    {'name': 'MLOps Specialization (Coursera)', 'url': 'https://coursera.org/specializations/machine-learning-engineering-for-production-mlops'},
                    {'name': 'Made With ML MLOps Guide', 'url': 'https://madewithml.com'}
                ]
            },
            {
                'step': 6,
                'skill': 'Cloud AI Services',
                'duration': '2-3 weeks',
                'topics': ['AWS SageMaker', 'Azure ML', 'GCP Vertex AI', 'Cloud Deployment Patterns'],
                'resources': [
                    {'name': 'AWS ML Learning Path', 'url': 'https://aws.amazon.com/training/learn-about/machine-learning/'},
                    {'name': 'Google Cloud AI Documentation', 'url': 'https://cloud.google.com/ai-platform/docs'}
                ]
            }
        ]
    },
    'data_analyst': {
        'title': 'Data Analyst Learning Path',
        'total_duration': '4-6 months',
        'steps': [
            {
                'step': 1,
                'skill': 'SQL Mastery',
                'duration': '3-4 weeks',
                'topics': ['Advanced JOINs', 'Window Functions', 'CTEs', 'Query Optimization'],
                'resources': [
                    {'name': 'Mode SQL Tutorial', 'url': 'https://mode.com/sql-tutorial/'},
                    {'name': 'SQLZoo Interactive', 'url': 'https://sqlzoo.net'}
                ]
            },
            {
                'step': 2,
                'skill': 'Python for Data Analysis',
                'duration': '3-4 weeks',
                'topics': ['Pandas', 'NumPy', 'Data Cleaning', 'Exploratory Data Analysis'],
                'resources': [
                    {'name': 'Kaggle Python Course', 'url': 'https://kaggle.com/learn/python'},
                    {'name': 'Pandas Documentation', 'url': 'https://pandas.pydata.org/docs/'}
                ]
            },
            {
                'step': 3,
                'skill': 'Data Visualization',
                'duration': '2-3 weeks',
                'topics': ['Matplotlib', 'Seaborn', 'Plotly', 'Tableau/Power BI', 'Storytelling with Data'],
                'resources': [
                    {'name': 'Tableau Public Learning', 'url': 'https://public.tableau.com/en-us/s/resources'},
                    {'name': 'Data Visualization Course (Coursera)', 'url': 'https://coursera.org/learn/data-visualization'}
                ]
            },
            {
                'step': 4,
                'skill': 'Statistics & Analytics',
                'duration': '3-4 weeks',
                'topics': ['Descriptive Statistics', 'Probability', 'Hypothesis Testing', 'A/B Testing', 'Regression Analysis'],
                'resources': [
                    {'name': 'Statistics with Python (Coursera)', 'url': 'https://coursera.org/specializations/statistics-with-python'},
                    {'name': 'Khan Academy Statistics', 'url': 'https://khanacademy.org/math/statistics-probability'}
                ]
            },
            {
                'step': 5,
                'skill': 'Business Intelligence & Reporting',
                'duration': '2-3 weeks',
                'topics': ['Dashboard Design', 'KPI Frameworks', 'Business Metrics', 'Stakeholder Communication'],
                'resources': [
                    {'name': 'Google Data Analytics Certificate', 'url': 'https://coursera.org/professional-certificates/google-data-analytics'},
                    {'name': 'Power BI Learning Path', 'url': 'https://learn.microsoft.com/en-us/training/powerplatform/power-bi'}
                ]
            }
        ]
    },
    'web_developer': {
        'title': 'Web Developer Learning Path',
        'total_duration': '5-7 months',
        'steps': [
            {
                'step': 1,
                'skill': 'HTML & CSS Fundamentals',
                'duration': '2-3 weeks',
                'topics': ['Semantic HTML', 'CSS Grid', 'Flexbox', 'Responsive Design', 'CSS Variables'],
                'resources': [
                    {'name': 'MDN Web Docs', 'url': 'https://developer.mozilla.org/en-US/docs/Learn'},
                    {'name': 'CSS-Tricks', 'url': 'https://css-tricks.com'}
                ]
            },
            {
                'step': 2,
                'skill': 'JavaScript & TypeScript',
                'duration': '4-5 weeks',
                'topics': ['ES6+ Features', 'Async/Await', 'DOM Manipulation', 'TypeScript Basics', 'Modules'],
                'resources': [
                    {'name': 'JavaScript.info', 'url': 'https://javascript.info'},
                    {'name': 'TypeScript Handbook', 'url': 'https://typescriptlang.org/docs/handbook/intro.html'}
                ]
            },
            {
                'step': 3,
                'skill': 'React Framework',
                'duration': '4-5 weeks',
                'topics': ['Components & Props', 'State Management', 'Hooks', 'Next.js', 'Testing'],
                'resources': [
                    {'name': 'React Official Docs', 'url': 'https://react.dev'},
                    {'name': 'Next.js Documentation', 'url': 'https://nextjs.org/docs'}
                ]
            },
            {
                'step': 4,
                'skill': 'Backend Development',
                'duration': '4-5 weeks',
                'topics': ['Node.js', 'Express', 'REST APIs', 'Authentication', 'Database Integration'],
                'resources': [
                    {'name': 'Node.js Learning Path', 'url': 'https://nodejs.dev/learn'},
                    {'name': 'The Odin Project', 'url': 'https://theodinproject.com'}
                ]
            },
            {
                'step': 5,
                'skill': 'DevOps for Web',
                'duration': '2-3 weeks',
                'topics': ['Git Workflows', 'Docker Basics', 'CI/CD', 'Cloud Deployment (Vercel/AWS)'],
                'resources': [
                    {'name': 'Vercel Deployment Guides', 'url': 'https://vercel.com/docs'},
                    {'name': 'GitHub Actions Documentation', 'url': 'https://docs.github.com/en/actions'}
                ]
            }
        ]
    },
    'ml_engineer': {
        'title': 'ML Engineer Learning Path',
        'total_duration': '6-8 months',
        'steps': [
            {
                'step': 1,
                'skill': 'Python & Software Engineering',
                'duration': '3-4 weeks',
                'topics': ['Clean Code', 'Design Patterns', 'Testing', 'Profiling & Optimization'],
                'resources': [
                    {'name': 'Clean Code (Book)', 'url': 'https://www.oreilly.com/library/view/clean-code-a/9780136083238/'},
                    {'name': 'Python Testing with pytest', 'url': 'https://pytest.org'}
                ]
            },
            {
                'step': 2,
                'skill': 'Machine Learning & Deep Learning',
                'duration': '5-6 weeks',
                'topics': ['ML Algorithms', 'Neural Networks', 'Model Evaluation', 'Experiment Tracking'],
                'resources': [
                    {'name': 'Fast.ai Course', 'url': 'https://fast.ai'},
                    {'name': 'MLflow Documentation', 'url': 'https://mlflow.org/docs/latest/index.html'}
                ]
            },
            {
                'step': 3,
                'skill': 'Data Engineering & Pipelines',
                'duration': '3-4 weeks',
                'topics': ['Apache Spark', 'Airflow', 'Kafka', 'Data Pipelines', 'Feature Stores'],
                'resources': [
                    {'name': 'Apache Spark Documentation', 'url': 'https://spark.apache.org/docs/latest/'},
                    {'name': 'Airflow Tutorials', 'url': 'https://airflow.apache.org/docs/'}
                ]
            },
            {
                'step': 4,
                'skill': 'Model Deployment & Serving',
                'duration': '3-4 weeks',
                'topics': ['FastAPI for ML', 'Model Serving Patterns', 'A/B Testing', 'Monitoring & Drift'],
                'resources': [
                    {'name': 'Chip Huyen ML Systems Design', 'url': 'https://huyenchip.com/machine-learning-systems-design/toc.html'},
                    {'name': 'BentoML Documentation', 'url': 'https://docs.bentoml.org'}
                ]
            },
            {
                'step': 5,
                'skill': 'MLOps & Infrastructure',
                'duration': '3-4 weeks',
                'topics': ['Kubernetes for ML', 'KubeFlow', 'CI/CD for ML', 'Cost Optimization'],
                'resources': [
                    {'name': 'MLOps Specialization (Coursera)', 'url': 'https://coursera.org/specializations/machine-learning-engineering-for-production-mlops'},
                    {'name': 'Made With ML', 'url': 'https://madewithml.com'}
                ]
            }
        ]
    },
    'devops': {
        'title': 'DevOps Engineer Learning Path',
        'total_duration': '5-7 months',
        'steps': [
            {
                'step': 1,
                'skill': 'Linux & Scripting',
                'duration': '3-4 weeks',
                'topics': ['Linux Command Line', 'Bash Scripting', 'File Systems', 'Networking Basics'],
                'resources': [
                    {'name': 'Linux Journey', 'url': 'https://linuxjourney.com'},
                    {'name': 'Bash Academy', 'url': 'https://guide.bash.academy'}
                ]
            },
            {
                'step': 2,
                'skill': 'Containers & Docker',
                'duration': '2-3 weeks',
                'topics': ['Docker Architecture', 'Dockerfile Best Practices', 'Docker Compose', 'Container Security'],
                'resources': [
                    {'name': 'Docker Official Get Started', 'url': 'https://docs.docker.com/get-started/'},
                    {'name': 'Play with Docker', 'url': 'https://labs.play-with-docker.com'}
                ]
            },
            {
                'step': 3,
                'skill': 'Kubernetes & Orchestration',
                'duration': '4-5 weeks',
                'topics': ['Pods, Services, Deployments', 'Helm Charts', 'Ingress', 'RBAC', 'Storage'],
                'resources': [
                    {'name': 'Kubernetes Documentation', 'url': 'https://kubernetes.io/docs/home/'},
                    {'name': 'Kelsey Hightower K8s The Hard Way', 'url': 'https://github.com/kelseyhightower/kubernetes-the-hard-way'}
                ]
            },
            {
                'step': 4,
                'skill': 'Infrastructure as Code',
                'duration': '3-4 weeks',
                'topics': ['Terraform', 'Ansible', 'CloudFormation', 'State Management'],
                'resources': [
                    {'name': 'HashiCorp Terraform Learn', 'url': 'https://developer.hashicorp.com/terraform/tutorials'},
                    {'name': 'Ansible Documentation', 'url': 'https://docs.ansible.com'}
                ]
            },
            {
                'step': 5,
                'skill': 'CI/CD Pipelines',
                'duration': '2-3 weeks',
                'topics': ['Jenkins Pipelines', 'GitHub Actions', 'GitLab CI', 'ArgoCD'],
                'resources': [
                    {'name': 'GitHub Actions Documentation', 'url': 'https://docs.github.com/en/actions'},
                    {'name': 'Jenkins User Documentation', 'url': 'https://www.jenkins.io/doc/'}
                ]
            },
            {
                'step': 6,
                'skill': 'Monitoring & Observability',
                'duration': '2-3 weeks',
                'topics': ['Prometheus', 'Grafana', 'ELK Stack', 'Alerting', 'SLOs/SLAs'],
                'resources': [
                    {'name': 'Prometheus Documentation', 'url': 'https://prometheus.io/docs/introduction/overview/'},
                    {'name': 'Grafana Labs Tutorials', 'url': 'https://grafana.com/tutorials/'}
                ]
            }
        ]
    }
}


# ─────────────────────────────────────────────
# Interview Questions per Role
# ─────────────────────────────────────────────

INTERVIEW_QUESTIONS = {
    'ai': [
        'Explain the difference between supervised, unsupervised, and reinforcement learning. Give a real-world example of each.',
        'What is the vanishing gradient problem in deep learning, and how can it be mitigated?',
        'Describe the Transformer architecture and explain why it revolutionized NLP.',
        'How would you approach building a Retrieval-Augmented Generation (RAG) system? What components are involved?',
        'Explain the concept of fine-tuning a large language model. When would you choose this over prompt engineering?',
        'What metrics would you use to evaluate a classification model, and which would you prioritize for an imbalanced dataset?',
        'How do you handle data drift in production ML systems? Describe a monitoring strategy.',
        'Walk me through how you would design an ML pipeline from data ingestion to model serving.',
    ],
    'data_analyst': [
        'How would you approach an A/B test to evaluate the impact of a new product feature?',
        'Explain the difference between correlation and causation. Give an example where confusing them could lead to bad business decisions.',
        'You have a dataset with 20% missing values in a key column. How would you handle this?',
        'Describe the process of building a dashboard for a business stakeholder. What questions do you ask first?',
        'How would you detect and handle outliers in a dataset?',
        'Explain window functions in SQL and provide a use case for ROW_NUMBER() vs RANK().',
        'What is cohort analysis, and how is it useful for understanding user behavior?',
        'Walk me through how you would analyze why a key business metric dropped last week.',
    ],
    'web_developer': [
        'Explain the concept of the Virtual DOM in React and why it improves performance.',
        'What is the difference between server-side rendering (SSR) and client-side rendering (CSR)?',
        'How do you optimize the performance of a web application? List at least 5 techniques.',
        'Explain REST principles and the difference between PUT and PATCH methods.',
        'What is CORS and how do you handle it in a web application?',
        'Describe how you would implement authentication and authorization in a web app.',
        'What is the event loop in JavaScript? Explain how async/await works under the hood.',
        'How would you approach making a web application accessible (WCAG compliance)?',
    ],
    'ml_engineer': [
        'What is the difference between batch inference and real-time inference? When would you choose each?',
        'Describe the components of an MLOps pipeline. What tools would you use for each stage?',
        'How do you version control ML models and datasets? What tools and best practices do you use?',
        'Explain the concept of feature stores. What problems do they solve?',
        'How would you design a system to retrain ML models automatically when performance degrades?',
        'What strategies do you use to reduce latency in model serving?',
        'Describe the challenges of deploying ML models in a distributed system.',
        'How would you approach shadow deployment and canary releases for ML models?',
    ],
    'devops': [
        'Explain the difference between Docker and a virtual machine. When would you choose one over the other?',
        'How would you design a CI/CD pipeline for a microservices application?',
        'Describe how Kubernetes handles pod scheduling and what factors influence it.',
        'What is infrastructure as code? What are the benefits of using Terraform?',
        'How do you implement a blue-green deployment strategy? What are the trade-offs?',
        'Explain the 12-factor app methodology and its relevance to DevOps practices.',
        'How would you design a monitoring and alerting system for a production application?',
        'Describe how you would handle a production outage. Walk me through your incident response process.',
    ]
}


# ─────────────────────────────────────────────
# Public Functions
# ─────────────────────────────────────────────

def get_diagnostic_questions(skill):
    """Get diagnostic questions for a given skill."""
    skill_lower = skill.lower()

    # Direct match
    if skill_lower in DIAGNOSTIC_QUESTIONS:
        questions = DIAGNOSTIC_QUESTIONS[skill_lower]
    else:
        # Partial match
        matched = None
        for key in DIAGNOSTIC_QUESTIONS:
            if key != 'default' and (key in skill_lower or skill_lower in key):
                matched = key
                break
        questions = DIAGNOSTIC_QUESTIONS.get(matched, DIAGNOSTIC_QUESTIONS['default'])

    # Return a random selection of 4 questions
    sample = random.sample(questions, min(4, len(questions)))
    return [
        {
            'question': q['question'],
            'options': q['options'],
            'correct': q['answer'],
            'explanation': q['explanation']
        }
        for q in sample
    ]


def get_learning_path(role_key, missing_skills=None):
    """Get the learning path for a given role, filtered by missing skills."""
    if role_key not in LEARNING_PATHS:
        role_key = 'ai'

    path = LEARNING_PATHS[role_key]

    if missing_skills:
        missing_lower = [s.lower() for s in missing_skills]
        # Filter steps to only include relevant missing skills
        filtered_steps = []
        for step in path['steps']:
            skill_lower = step['skill'].lower()
            relevant = any(
                m in skill_lower or skill_lower in m
                for m in missing_lower
            )
            if relevant or len(filtered_steps) < 3:
                filtered_steps.append(step)
        if filtered_steps:
            return {**path, 'steps': filtered_steps}

    return path


def get_interview_questions(role_key, count=5):
    """Get interview questions for a given role."""
    if role_key not in INTERVIEW_QUESTIONS:
        role_key = 'ai'

    questions = INTERVIEW_QUESTIONS[role_key]
    selected = random.sample(questions, min(count, len(questions)))
    return [
        {'index': i + 1, 'question': q, 'role': role_key}
        for i, q in enumerate(selected)
    ]


def evaluate_answer(question, answer, role_key='ai'):
    """
    Generate AI feedback for an interview answer.
    Uses template-based scoring and feedback generation.
    """
    if not answer or len(answer.strip()) < 10:
        return {
            'score': 0,
            'rating': 'No Answer',
            'feedback': 'No meaningful answer was provided.',
            'strengths': [],
            'improvements': ['Please provide a detailed answer to demonstrate your knowledge'],
            'keywords_mentioned': []
        }

    answer_lower = answer.lower()
    word_count = len(answer.split())

    # Role-specific technical keywords
    role_keywords = {
        'ai': ['model', 'training', 'data', 'neural', 'learning', 'algorithm', 'feature', 'accuracy',
               'gradient', 'loss', 'inference', 'deployment', 'pipeline', 'transformer', 'embedding'],
        'data_analyst': ['data', 'analysis', 'query', 'metric', 'dashboard', 'visualization', 'sql',
                         'insight', 'trend', 'hypothesis', 'correlation', 'distribution', 'outlier'],
        'web_developer': ['component', 'api', 'render', 'state', 'dom', 'async', 'http', 'request',
                          'response', 'authentication', 'endpoint', 'database', 'performance'],
        'ml_engineer': ['pipeline', 'deployment', 'serving', 'monitoring', 'drift', 'versioning',
                        'container', 'orchestration', 'feature', 'latency', 'throughput', 'scaling'],
        'devops': ['container', 'deployment', 'pipeline', 'infrastructure', 'monitoring', 'scaling',
                   'automation', 'configuration', 'orchestration', 'availability', 'rollback']
    }

    keywords = role_keywords.get(role_key, role_keywords['ai'])
    mentioned = [kw for kw in keywords if kw in answer_lower]
    keyword_score = min(len(mentioned) / max(len(keywords) * 0.4, 1), 1.0)

    # Length score (ideal: 100-300 words)
    if word_count < 20:
        length_score = 0.2
    elif word_count < 50:
        length_score = 0.5
    elif word_count <= 300:
        length_score = 1.0
    elif word_count <= 500:
        length_score = 0.8
    else:
        length_score = 0.6

    # Structure score (has examples, explanations)
    structure_indicators = ['because', 'for example', 'such as', 'first', 'second', 'finally',
                            'in addition', 'however', 'therefore', 'e.g.', 'i.e.', 'specifically']
    structure_score = min(sum(1 for s in structure_indicators if s in answer_lower) / 3, 1.0)

    # Overall score (weighted)
    raw_score = (keyword_score * 0.4 + length_score * 0.3 + structure_score * 0.3)
    score = round(raw_score * 10, 1)  # Scale to 10

    # Rating
    if score >= 8:
        rating = 'Excellent'
    elif score >= 6.5:
        rating = 'Good'
    elif score >= 5:
        rating = 'Average'
    elif score >= 3:
        rating = 'Below Average'
    else:
        rating = 'Needs Improvement'

    # Generate contextual feedback
    strengths = []
    improvements = []

    if keyword_score >= 0.5:
        strengths.append(f'Good use of technical terminology ({len(mentioned)} relevant keywords)')
    else:
        improvements.append('Include more domain-specific technical terms and concepts')

    if length_score >= 0.8:
        strengths.append('Answer has appropriate depth and detail')
    elif word_count < 50:
        improvements.append('Expand your answer with more detail and examples (aim for 100-200 words)')
    else:
        improvements.append('Be more concise — focus on the most impactful points')

    if structure_score >= 0.5:
        strengths.append('Well-structured response with clear explanations')
    else:
        improvements.append('Structure your answer with a clear introduction, main points, and conclusion')

    if 'example' in answer_lower or 'for instance' in answer_lower:
        strengths.append('Good use of concrete examples to support your points')
    else:
        improvements.append('Add real-world examples to demonstrate practical experience')

    if not strengths:
        strengths.append('Attempted to address the question')

    general_feedback = (
        f'Your answer scored {score}/10 ({rating}). '
        f'You demonstrated knowledge of {len(mentioned)} key concepts. '
        f'{"Strong technical foundation shown." if score >= 7 else "Focus on deepening your technical explanations."}'
    )

    return {
        'score': score,
        'rating': rating,
        'feedback': general_feedback,
        'strengths': strengths[:3],
        'improvements': improvements[:3],
        'keywords_mentioned': mentioned[:8],
        'word_count': word_count
    }
