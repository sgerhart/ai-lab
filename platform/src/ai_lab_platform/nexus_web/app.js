/**
 * Knowledge Nexus - Learning Journey & Resource Hub Application
 * Author: Steven Gerhart Study Assistant
 */

// Portable relative path resolution: works seamlessly on local file:// or http:// on any machine
function getFileUrl(relPath) {
  return encodeURI(relPath);
}

// ==========================================================================
// 1. Core Journey Tracks Data
// ==========================================================================
const JOURNEY_TRACKS = {
  'ai-agent': {
    id: 'ai-agent',
    title: 'AI Agent & LLM Engineer',
    subtitle: 'From prompt engineering and vibe coding to autonomous multi-agent systems and MCP interoperability.',
    icon: '🤖',
    stages: [
      {
        id: 'stage-1',
        title: 'Stage 1: LLM Foundations & Prompt Engineering',
        desc: 'Understand large language model pretraining, architecture, and prompt engineering.',
        milestones: [
          {
            id: 'm-llm-foundations',
            title: 'Foundations of LLMs & Pretraining',
            time: '45 mins',
            type: 'Reading',
            filePath: '01_AI_and_GenAI/01_Foundations_and_LLMs/Foundation of LLM.pdf',
            desc: 'Core architectures, tokenization, pretraining pipelines, and parameter scaling.',
            keyPoints: [
              'Understand attention mechanisms and transformer decoder architectures',
              'Learn pretraining vs fine-tuning tradeoffs',
              'Review inference optimization and model latency parameters'
            ],
            related: [
              { title: 'Pretraining LLMs Guide', path: '01_AI_and_GenAI/01_Foundations_and_LLMs/pretraining_llm.pdf' },
              { title: 'How to Select the Right LLM', path: '01_AI_and_GenAI/01_Foundations_and_LLMs/How_to_select_the_right_LLM_Model_for_use_case__1725717140.pdf' }
            ]
          },
          {
            id: 'm-prompt-eng',
            title: 'Kaggle Whitepaper: Prompt Engineering Mastery',
            time: '35 mins',
            type: 'Whitepaper',
            filePath: '03_Courses_and_Bootcamps/Kaggle_5_Day_GenAI_Intensive/whitepaper_Prompt Engineering_v4.pdf',
            desc: 'Systematic prompt design: few-shot learning, chain-of-thought, persona steering, and delimiters.',
            keyPoints: [
              'Zero-shot vs Few-shot in-context demonstration techniques',
              'Chain-of-Thought (CoT) and Least-to-Most reasoning prompting',
              'Structuring deterministic JSON / schema outputs'
            ],
            related: [
              { title: 'Foundational LLMs & Text Generation', path: '03_Courses_and_Bootcamps/Kaggle_5_Day_GenAI_Intensive/whitepaper_Foundational Large Language models & text generation.pdf' }
            ]
          }
        ]
      },
      {
        id: 'stage-2',
        title: 'Stage 2: Kaggle 5-Day Agent Intensive',
        desc: 'The official fast-paced 5-day agent development boot-camp.',
        milestones: [
          {
            id: 'm-agent-day1',
            title: 'Day 1: Intro to Agents & The New SDLC with Vibe Coding',
            time: '40 mins',
            type: 'Course',
            filePath: '03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/2025_Day_1_Rewrite_v1_IntroductionToAgents.pdf',
            desc: 'How autonomous agents rethink software development lifecycles and modern human-in-the-loop workflows.',
            keyPoints: [
              'Agent autonomy spectrum: Chatbots vs ReAct vs Fully Autonomous loops',
              'Vibe coding best practices and rapid prototyping',
              'Deconstructing agent goal orientation and feedback loops'
            ],
            related: [
              { title: 'The New SDLC With Vibe Coding (Day 1)', path: '03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/The New SDLC With Vibe Coding_Day_1.pdf' }
            ]
          },
          {
            id: 'm-agent-day2',
            title: 'Day 2: Agent Tools & Interoperability (MCP)',
            time: '45 mins',
            type: 'Course',
            filePath: '03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/2025_Day_2_Rewrite_v1_AgentTools.pdf',
            desc: 'Empowering LLMs with deterministic tools, APIs, and the Model Context Protocol (MCP).',
            keyPoints: [
              'Tool definitions, schemas, and parameter validation',
              'Understanding Model Context Protocol (MCP) server & client paradigms',
              'Handling tool execution errors and reflection'
            ],
            related: [
              { title: 'Agent Tools & Interoperability with MCP', path: '01_AI_and_GenAI/02_Agents_and_Workflows/Agent Tools & Interoperability with Model Context Protocol (MCP).pdf' }
            ]
          },
          {
            id: 'm-agent-day3',
            title: 'Day 3: Context Engineering, Sessions & Memory',
            time: '45 mins',
            type: 'Course',
            filePath: '03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/2025_Day_3_Rewrite_v1_ContextEngineering.pdf',
            desc: 'Managing stateful agent interactions, short-term vs long-term memory, and context window compression.',
            keyPoints: [
              'Context compaction, summarization, and sliding window buffers',
              'Persistent episodic and semantic memory architectures',
              'Designing resilient agent session storage'
            ],
            related: [
              { title: 'Context Engineering: Sessions & Memory', path: '01_AI_and_GenAI/02_Agents_and_Workflows/Context Engineering_ Sessions & Memory.pdf' },
              { title: 'Agent Skills (Day 3)', path: '03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/Agent Skills_Day_3.pdf' }
            ]
          },
          {
            id: 'm-agent-day4',
            title: 'Day 4: Agent Quality, Security & Evaluation',
            time: '50 mins',
            type: 'Course',
            filePath: '03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/2025_Day_4_Rewrite_v1_AgentQuality.pdf',
            desc: 'Benchmarking agent reliability, tool hallucinations, guardrails, and red teaming.',
            keyPoints: [
              'LLM-as-a-judge evaluation frameworks and regression testing',
              'Defending against prompt injections and indirect tool hijacking',
              'Establishing SLAs for multi-step agent trajectories'
            ],
            related: [
              { title: 'Agent Quality Master Guide', path: '01_AI_and_GenAI/02_Agents_and_Workflows/Agent Quality.pdf' },
              { title: 'Vibe Coding Agent Security & Eval', path: '03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/Vibe Coding Agent Security and Evaluation_Day_4.pdf' }
            ]
          },
          {
            id: 'm-agent-day5',
            title: 'Day 5: Prototype to Production Deployment',
            time: '60 mins',
            type: 'Course',
            filePath: '03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/2025_Day_5_Rewrite_v1_Prototype.pdf',
            desc: 'Taking an agent from notebook code to scalable production microservices with observability.',
            keyPoints: [
              'Async task scheduling and queueing for long-running agents',
              'Tracing with OpenTelemetry and agent debuggers',
              'Cost management and rate limit fallback mechanisms'
            ],
            related: [
              { title: 'Prototype to Production Guide', path: '03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/Prototype to Production.pdf' }
            ]
          }
        ]
      },
      {
        id: 'stage-3',
        title: 'Stage 3: Advanced Agent Patterns & Workflows',
        desc: 'Deepen knowledge in architectural patterns: ReAct, Plan-and-Solve, and Multi-Agent Orchestration.',
        milestones: [
          {
            id: 'm-react-prompting',
            title: 'What is ReAct Prompting? (Reasoning + Acting)',
            time: '30 mins',
            type: 'Guide',
            filePath: '01_AI_and_GenAI/02_Agents_and_Workflows/What_is_ReAct_Prompting__1727696866.pdf',
            desc: 'How interleaving thought reasoning and external actions dramatically cuts tool errors.',
            keyPoints: [
              'Thought $\\to$ Action $\\to$ Observation $\\to$ Reflection loop',
              'Comparing ReAct against pure function calling and plan-and-solve',
              'Implementing ReAct in Python from scratch'
            ],
            related: [
              { title: 'Common Agentic Workflow Patterns', path: '01_AI_and_GenAI/02_Agents_and_Workflows/Common_Agentic_Workflow_Patterns_1727439222.pdf' }
            ]
          },
          {
            id: 'm-google-agents',
            title: 'Google AI Agents Architecture Whitepaper',
            time: '45 mins',
            type: 'Architecture Guide',
            filePath: '01_AI_and_GenAI/02_Agents_and_Workflows/Google_AI Agents.pdf',
            desc: 'Enterprise patterns for autonomous agents, memory topologies, and ground truth grounding.',
            keyPoints: [
              'Cognitive architectures: Perception, Planning, Memory, Action',
              'Grounding techniques to eliminate hallucinations',
              'Multi-agent collaboration and sub-agent delegation'
            ],
            related: [
              { title: 'Kaggle Agents Whitepaper', path: '03_Courses_and_Bootcamps/Kaggle_5_Day_GenAI_Intensive/Newwhitepaper_Agents.pdf' }
            ]
          }
        ]
      },
      {
        id: 'stage-4',
        title: 'Stage 4: RAG, Vector Search & Embeddings',
        desc: 'Grounding agents with enterprise data using modern retrieval architectures.',
        milestones: [
          {
            id: 'm-rag-techniques',
            title: '6 Different RAG Techniques Explained',
            time: '35 mins',
            type: 'Cheat Sheet',
            filePath: '01_AI_and_GenAI/03_RAG_and_Vector_Search/6_different_RAG_techniques_1726533237.pdf',
            desc: 'Naive RAG, Sentence-Window, Parent-Child Chunking, HyDE, Multi-Query, and Graph RAG.',
            keyPoints: [
              'Evaluating chunking strategies and overlap sizing',
              'Hypothetical Document Embeddings (HyDE) and query expansion',
              'Rerankers: Cross-encoders vs bi-encoders'
            ],
            related: [
              { title: 'RAG vs Long-Context LLMs', path: '01_AI_and_GenAI/03_RAG_and_Vector_Search/RAG_vs_Long_Context_LLMs_1728404797.pdf' },
              { title: 'Embeddings & Vector Stores Whitepaper', path: '03_Courses_and_Bootcamps/Kaggle_5_Day_GenAI_Intensive/Newwhitepaper_Embeddings & vector stores.pdf' }
            ]
          },
          {
            id: 'm-book-ai-search',
            title: 'Book: AI-Powered Search (Semantic Search & Vector Engines)',
            time: '2 hours',
            type: 'Book',
            filePath: '04_Books_Library/AI_and_Machine_Learning/AI-Powered_Search.pdf',
            desc: 'Comprehensive Manning guide on dense retrieval, hybrid search (BM25 + Dense), and learned ranking.',
            keyPoints: [
              'Vector indexing: HNSW, IVF, Product Quantization',
              'Hybrid search merging lexical and dense results',
              'Evaluation of search recall @ K and NDCG'
            ],
            related: [
              { title: 'AI-Powered Search (EPUB)', path: '04_Books_Library/AI_and_Machine_Learning/AI-Powered_Search.epub' }
            ]
          }
        ]
      },
      {
        id: 'stage-5',
        title: 'Stage 5: Production Agent Systems & Full Books',
        desc: 'Read the definitive guidebooks on production deployment, evaluation, and reliability.',
        milestones: [
          {
            id: 'm-book-agents-action',
            title: 'Book: AI Agents in Action',
            time: '2.5 hours',
            type: 'Book',
            filePath: '04_Books_Library/AI_and_Machine_Learning/AI_Agents_in_Action.pdf',
            desc: 'End-to-end blueprint for building multi-modal, tool-calling agents in production environments.',
            keyPoints: [
              'Agent runtime architecture and environment abstraction',
              'State machines vs autonomous loop controllers',
              'Real-world case studies in automated coding and data analytics'
            ],
            related: [
              { title: 'Building Reliable AI Systems', path: '04_Books_Library/AI_and_Machine_Learning/Building_Reliable_AI_Systems.pdf' }
            ]
          },
          {
            id: 'm-book-llms-prod',
            title: 'Book: LLMs in Production',
            time: '2.5 hours',
            type: 'Book',
            filePath: '04_Books_Library/AI_and_Machine_Learning/LLMs_in_Production.pdf',
            desc: 'Serving, latency tuning, KV caching, quantization, and real-time monitoring of LLM pipelines.',
            keyPoints: [
              'Serving engines: vLLM, TensorRT-LLM, and continuous batching',
              'Quantization methods (AWQ, GPTQ, GGUF) and memory footprint math',
              'Production telemetry and continuous alignment monitoring'
            ],
            related: [
              { title: 'LLM Evaluation & Alignment', path: '04_Books_Library/AI_and_Machine_Learning/LLM_Evaluation_and_Alignment_The_Founda_v4_MEAP.pdf' }
            ]
          }
        ]
      },
      {
        id: 'stage-6',
        title: 'Stage 6: Certifications & Industry Mastery',
        desc: 'Prepare for official enterprise certifications and technical AI architecture interviews.',
        milestones: [
          {
            id: 'm-claude-cert',
            title: 'Anthropic Claude Certified Architect – Foundations',
            time: '1.5 hours',
            type: 'Certification Guide',
            filePath: '01_AI_and_GenAI/08_Certifications_and_Prep/Claude Certified Architect – Foundations.pdf',
            desc: 'Official Anthropic blueprint for Claude 3.5 Sonnet / Opus prompt optimization, tool usage, and vision.',
            keyPoints: [
              'XML tag structuring for prompt parsing and context boundaries',
              'System prompt crafting and prefilling assistant responses',
              'Tool use formatting and multi-turn Claude conversation tuning'
            ],
            related: [
              { title: 'Top 40 LLM Interview Questions & Answers', path: '01_AI_and_GenAI/08_Certifications_and_Prep/Top_40_LLM_Interview_Questions_Answers_1726484618.pdf' }
            ]
          },
          {
            id: 'm-deepseek-paper',
            title: 'Research Paper: DeepSeek-R1 (2501.12948)',
            time: '1 hour',
            type: 'Research Paper',
            filePath: '01_AI_and_GenAI/05_Research_Papers/2501.12948v1.pdf',
            desc: 'Incentivizing reasoning capability in LLMs via pure reinforcement learning.',
            keyPoints: [
              'Pure RL without supervised fine-tuning warm start (R1-Zero)',
              'Multi-stage training pipeline and cold-start data bootstrapping',
              'Distillation of reasoning capabilities to smaller dense models'
            ],
            related: [
              { title: 'The Illusion of Thinking Paper', path: '01_AI_and_GenAI/01_Foundations_and_LLMs/the-illusion-of-thinking.pdf' }
            ]
          }
        ]
      }
    ]
  },

  'python-ds': {
    id: 'python-ds',
    title: 'Python, Math & Data Science',
    subtitle: 'From core Python and object-oriented design to numerical math, Pandas data cleaning, and PyTorch deep learning.',
    icon: '🐍',
    stages: [
      {
        id: 'p-stage-1',
        title: 'Stage 1: Core Python & Object-Oriented Mastery',
        desc: 'Solidify your foundations in advanced Python features, OOP, and multiprocessing.',
        milestones: [
          {
            id: 'pm-mastering-python',
            title: 'Mastering Python & Advanced Syntax',
            time: '1 hour',
            type: 'Guide',
            filePath: '02_Python_and_Data_Science/01_Core_Python/mastering_python.pdf',
            desc: 'Decorators, generators, context managers, type hints, and memory optimization.',
            keyPoints: [
              'Generators & iterators for memory-efficient data streaming',
              'Function decorators and class decorators',
              'Type hinting and static type checking with Mypy'
            ],
            related: [
              { title: 'Advanced Programming with Python', path: '02_Python_and_Data_Science/01_Core_Python/Advanced_Programming_with_Python__1747243259.pdf' },
              { title: 'Python Cheatsheet', path: '02_Python_and_Data_Science/01_Core_Python/python_cheatsheet.pdf' }
            ]
          },
          {
            id: 'pm-oop-concepts',
            title: 'OOP Concepts & Design Patterns in Python',
            time: '45 mins',
            type: 'Guide',
            filePath: '02_Python_and_Data_Science/01_Core_Python/OOP_CONCEPTS_IN_PYTHON_1735831777.pdf',
            desc: 'Encapsulation, inheritance, polymorphism, abstract base classes, and dataclasses.',
            keyPoints: [
              'Building modular classes and abstract interfaces with abc module',
              'Magic/dunder methods (__init__, __call__, __repr__, __enter__)',
              'Python dataclasses and Pydantic validation'
            ],
            related: [
              { title: 'Multiprocessing in Python', path: '02_Python_and_Data_Science/01_Core_Python/multiprocessing_in_python.pdf' }
            ]
          }
        ]
      },
      {
        id: 'p-stage-2',
        title: 'Stage 2: NumPy & Scientific Computing',
        desc: 'Vectorized computing, n-dimensional arrays, broadcasting, and linear algebra operations.',
        milestones: [
          {
            id: 'pm-numpy-beginners',
            title: 'NumPy Guide for Beginners & Array Ops',
            time: '45 mins',
            type: 'Guide',
            filePath: '02_Python_and_Data_Science/02_NumPy_and_Math/NumPy_guide_for_beginners__1734359174.pdf',
            desc: 'Creating ndarrays, slicing, masking, reshaping, and vectorized arithmetic.',
            keyPoints: [
              'Array creation and shape manipulation (.reshape, .squeeze, .transpose)',
              'Broadcasting rules across differing dimensions',
              'Matrix dot products, inversions, and eigenvalues with np.linalg'
            ],
            related: [
              { title: 'NumPy Cheatsheet', path: '02_Python_and_Data_Science/02_NumPy_and_Math/numpy_cheatsheet.pdf' },
              { title: 'NumPy Coding Practice', path: '02_Python_and_Data_Science/02_NumPy_and_Math/numpy_coding.pdf' }
            ]
          }
        ]
      },
      {
        id: 'p-stage-3',
        title: 'Stage 3: Pandas & Exploratory Data Analysis (EDA)',
        desc: 'Tabular data manipulation, missing value imputation, grouping, merging, and SQL querying.',
        milestones: [
          {
            id: 'pm-pandas-cleaning',
            title: 'Pandas Data Cleaning & Transformation Guide',
            time: '50 mins',
            type: 'Guide',
            filePath: '02_Python_and_Data_Science/03_Pandas_and_Data_Analysis/pandas_data_cleaning.pdf',
            desc: 'Handling nulls, duplicates, string parsing, datetime conversions, and groupby aggregations.',
            keyPoints: [
              'Vectorized string and datetime accessors (.str, .dt)',
              'Groupby, pivot tables, and multi-index slicing',
              'Optimizing memory with categorical data types'
            ],
            related: [
              { title: 'Pandas Cheat Sheet', path: '02_Python_and_Data_Science/03_Pandas_and_Data_Analysis/pandas_cheat_sheet.pdf' },
              { title: 'Nikita Prasad EDA CheatCode', path: '01_AI_and_GenAI/06_CheatSheets_and_Guides/Nikita_Prasad_EDA_CheatCode_1725965285.pdf' }
            ]
          },
          {
            id: 'pm-sql-guide',
            title: 'SQL Guide & Data Querying for Data Science',
            time: '40 mins',
            type: 'Cheat Sheet',
            filePath: '01_AI_and_GenAI/06_CheatSheets_and_Guides/SQL_Guide_1736770305.pdf',
            desc: 'Window functions, joins, CTEs (Common Table Expressions), and aggregation for data prep.',
            keyPoints: [
              'Window functions: ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), LEAD()',
              'CTEs and subqueries for complex data transformations',
              'Integrating SQL with pandas via read_sql and SQLAlchemy'
            ],
            related: [
              { title: 'Feature Engineering Basics Cheat Sheet', path: '01_AI_and_GenAI/06_CheatSheets_and_Guides/Nikita_Prasad_Feature_Engineering_Basics_1726842130.pdf' }
            ]
          }
        ]
      },
      {
        id: 'p-stage-4',
        title: 'Stage 4: Mathematics for Machine Learning',
        desc: 'Linear algebra, multivariate calculus, gradient descent, and probability foundations.',
        milestones: [
          {
            id: 'pm-math-c1',
            title: 'Math for ML: Course 1 (Linear Algebra Weeks 1–4)',
            time: '1.5 hours',
            type: 'Course Notes',
            filePath: '03_Courses_and_Bootcamps/Math_for_Machine_Learning/C1_Linear_Algebra/C1_W1.pdf',
            desc: 'Vectors, linear transformations, matrices, determinants, and dot products.',
            keyPoints: [
              'Week 1 & 2: Vectors, linear combinations, and vector spaces',
              'Week 3: Matrices as linear transformations and inverse matrices',
              'Week 4: Determinants, eigenvalues, and eigenvectors'
            ],
            related: [
              { title: 'Maths for ML Linear Algebra Formulas', path: '01_AI_and_GenAI/06_CheatSheets_and_Guides/maths4ml-linearalgebra-formula.pdf' },
              { title: 'C1 Week 2 Notes', path: '03_Courses_and_Bootcamps/Math_for_Machine_Learning/C1_Linear_Algebra/C1_W2.pdf' }
            ]
          },
          {
            id: 'pm-math-c2',
            title: 'Math for ML: Course 2 (Calculus & Stats Weeks 1–3)',
            time: '1.5 hours',
            type: 'Course Notes',
            filePath: '03_Courses_and_Bootcamps/Math_for_Machine_Learning/C2_Calculus_and_Stats/C2_W1.pdf',
            desc: 'Partial derivatives, Jacobians, Hessians, gradient descent optimization, and loss surfaces.',
            keyPoints: [
              'Multivariate differentiation and chain rule',
              'Gradients, directional derivatives, and steepest descent',
              'Hessian matrices and convexity in neural network loss landscapes'
            ],
            related: [
              { title: 'Optimization Algorithms Book', path: '04_Books_Library/AI_and_Machine_Learning/Optimization_Algorithms.pdf' }
            ]
          }
        ]
      },
      {
        id: 'p-stage-5',
        title: 'Stage 5: Deep Learning, PyTorch & Transformers',
        desc: 'Build, train, and evaluate deep neural networks and transformer models in Python.',
        milestones: [
          {
            id: 'pm-pytorch-guide',
            title: 'PyTorch Deep Learning & Tensor Ops',
            time: '1 hour',
            type: 'Guide',
            filePath: '02_Python_and_Data_Science/04_Machine_Learning_and_DL/pytorch.pdf',
            desc: 'Autograd engine, nn.Module, custom Datasets & DataLoaders, and training loops.',
            keyPoints: [
              'Tensor operations on GPU/MPS acceleration',
              'Building custom modules with forward pass and loss backward',
              'Optimizers (AdamW, SGD) and learning rate schedulers'
            ],
            related: [
              { title: 'TensorFlow vs PyTorch Comparison', path: '02_Python_and_Data_Science/04_Machine_Learning_and_DL/TensorFlow_vs_PyTorch.pdf' },
              { title: 'Book: Deep Learning with Python', path: '04_Books_Library/AI_and_Machine_Learning/Deep_Learning_with_Python.pdf' }
            ]
          },
          {
            id: 'pm-transformers-nlp',
            title: 'NLP & Transformer-Based Models in Python',
            time: '1 hour',
            type: 'Guide',
            filePath: '02_Python_and_Data_Science/04_Machine_Learning_and_DL/NLP_Transformer_based_Models.pdf',
            desc: 'Hugging Face transformers, tokenizers, sequence classification, and causal LM generation.',
            keyPoints: [
              'Self-attention and multi-head attention math in Python',
              'Fine-tuning pre-trained transformer checkpoints',
              'PEFT / LoRA parameter-efficient fine-tuning methods'
            ],
            related: [
              { title: 'Book: Transformers in Action', path: '04_Books_Library/AI_and_Machine_Learning/Transformers_in_Action.pdf' }
            ]
          }
        ]
      }
    ]
  },

  'ai-safety': {
    id: 'ai-safety',
    title: 'AI Safety, Red Teaming & Risk',
    subtitle: 'OWASP Top 10 for GenAI, US AI Safety Institute standards, adversarial prompt testing, and governance.',
    icon: '🛡️',
    stages: [
      {
        id: 's-stage-1',
        title: 'Stage 1: AI Safety & Governance Frameworks',
        desc: 'Understand international AI standards, NIST AI RMF, and US AISI strategic directives.',
        milestones: [
          {
            id: 'sm-us-aisi',
            title: 'US AI Safety Institute: Vision, Mission & Strategic Goals',
            time: '40 mins',
            type: 'Government Paper',
            filePath: '01_AI_and_GenAI/04_Safety_Governance_Security/U_S_AI_Safety_Institute_Vision_Mission_Strategic_Goals_1716603441.pdf',
            desc: 'NIST AISI guidelines on evaluation, red-teaming standards, and safety assurance for frontier models.',
            keyPoints: [
              'Core pillars of safety evaluations and capability thresholds',
              'Pre-deployment testing for cyber and chemical/biological risks',
              'Standardized reporting frameworks for AI model developers'
            ],
            related: [
              { title: 'Plan for Global Engagement on AI Standards', path: '01_AI_and_GenAI/04_Safety_Governance_Security/A_Plan_for_Global_Engagement_on_AI_Standards_1724635314.pdf' },
              { title: 'Book: AI Governance', path: '04_Books_Library/AI_and_Machine_Learning/AI_Governance_v2_MEAP.pdf' }
            ]
          }
        ]
      },
      {
        id: 's-stage-2',
        title: 'Stage 2: OWASP GenAI Red Teaming & Attack Vectors',
        desc: 'Adversarial prompt injection, data exfiltration, jailbreaking, and insecure plugin design.',
        milestones: [
          {
            id: 'sm-owasp-redteam',
            title: 'OWASP GenAI Red Teaming Guide',
            time: '1 hour',
            type: 'Security Standard',
            filePath: '01_AI_and_GenAI/04_Safety_Governance_Security/OWASP-GenAI Red Teaming Guide.pdf',
            desc: 'Comprehensive methodologies for planning, executing, and documenting GenAI red team engagements.',
            keyPoints: [
              'Direct vs indirect prompt injection attacks',
              'Training data poisoning and supply chain package hallucination',
              'Automated adversarial benchmarking with prompt fuzzers'
            ],
            related: [
              { title: 'Security of AI Agents Guide', path: '01_AI_and_GenAI/04_Safety_Governance_Security/Security of AI Agents.pdf' }
            ]
          }
        ]
      },
      {
        id: 's-stage-3',
        title: 'Stage 3: LLM Privacy & Defense Engineering',
        desc: 'Implementing runtime guardrails, output filtering, and differential privacy.',
        milestones: [
          {
            id: 'sm-book-privacy-llm',
            title: 'Book: Privacy & Security for Large Language Models',
            time: '2 hours',
            type: 'Book',
            filePath: '04_Books_Library/Cybersecurity/privacyandsecurityforlargelanguagemodels.pdf',
            desc: 'Defending against data extraction, membership inference, and building compliant LLM apps.',
            keyPoints: [
              'PII masking and anonymization pipelines before LLM ingestion',
              'Differential privacy techniques in fine-tuning datasets',
              'Implementing NeMo Guardrails and Llama-Guard filters'
            ],
            related: [
              { title: 'Developers Playbook for LLM Security', path: '04_Books_Library/Cybersecurity/developersplaybookforlargelanguagemodelsecurity.pdf' }
            ]
          }
        ]
      }
    ]
  },

  'infra-security': {
    id: 'infra-security',
    title: 'Cloud, Platform & Cyber Ops',
    subtitle: 'Modern platform engineering, Kubernetes security, eBPF kernel observability, and CISSP/CISO executive strategy.',
    icon: '☁️',
    stages: [
      {
        id: 'i-stage-1',
        title: 'Stage 1: Platform Engineering & Kubernetes Observability',
        desc: 'Building developer platforms, GitOps workflows, and secure container infrastructure.',
        milestones: [
          {
            id: 'im-effective-platform',
            title: 'Book: Effective Platform Engineering',
            time: '2 hours',
            type: 'Book',
            filePath: '04_Books_Library/Cloud_Platform_and_eBPF/Effective_Platform_Engineering.pdf',
            desc: 'Designing Internal Developer Platforms (IDPs), self-service APIs, and platform metrics.',
            keyPoints: [
              'Platform as a Product: Developer experience and cognitive load reduction',
              'Self-service provisioning and golden paths',
              'Measuring platform ROI with DORA and SPACE metrics'
            ],
            related: [
              { title: 'Kubernetes Security & Observability', path: '04_Books_Library/Cloud_Platform_and_eBPF/kubernetessecurityandobservability.pdf' }
            ]
          }
        ]
      },
      {
        id: 'i-stage-2',
        title: 'Stage 2: eBPF Deep Dive & Kernel Observability',
        desc: 'Unlock programmable Linux kernel tracing, packet filtering, and runtime security with eBPF.',
        milestones: [
          {
            id: 'im-learning-ebpf',
            title: 'Book: Learning eBPF (Liz Rice)',
            time: '2 hours',
            type: 'Book',
            filePath: '04_Books_Library/Cloud_Platform_and_eBPF/Learning-eBPF - Full book.pdf',
            desc: 'Writing eBPF programs in C and Go, kprobes, tracepoints, XDP, and Cilium networking.',
            keyPoints: [
              'eBPF virtual machine, verifier, and map data structures',
              'Attaching to kprobes, uprobes, and socket filters',
              'High-speed packet inspection and DDoS defense with XDP'
            ],
            related: [
              { title: 'Buzzing Across Space: Illustrated eBPF Guide', path: '04_Books_Library/Cloud_Platform_and_eBPF/buzzing-across-space-illustrated-childrens-guide-to-ebpf.pdf' }
            ]
          }
        ]
      },
      {
        id: 'i-stage-3',
        title: 'Stage 3: Executive Security, CISSP & Incident Response',
        desc: 'CISO leadership, incident response runbooks, CISSP certification domains, and network segmentation.',
        milestones: [
          {
            id: 'im-cissp-guide',
            title: 'CISSP Exam Study Guide & Domains',
            time: '2 hours',
            type: 'Study Guide',
            filePath: '05_Cybersecurity/01_CISSP_and_CISO/CISSP_Exam_Study_Guide_1733077547.pdf',
            desc: 'Comprehensive review across all 8 CISSP security domains for certification readiness.',
            keyPoints: [
              'Security & Risk Management, Asset Security, Security Architecture',
              'Communication & Network Security, Identity & Access Management (IAM)',
              'Security Assessment, Testing, Operations, and Software Development Security'
            ],
            related: [
              { title: 'CISO Handbook 2024', path: '05_Cybersecurity/01_CISSP_and_CISO/CHIEF_INFORMATION_SECURITY_OFFICER_HANDBOOK_1729696878.pdf' },
              { title: 'Blue Team Incident Response Handbook', path: '04_Books_Library/Cybersecurity/blueteamhandbook_incidentresponse.pdf' }
            ]
          }
        ]
      }
    ]
  }
};

// ==========================================================================
// 2. Resource Library Data (All 100+ Books, Papers, Courses)
// ==========================================================================
const RESOURCE_LIBRARY = [
  {
    "id": "lib-1",
    "title": "Looks Good to Me",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/Software_Engineering/Looks_Good_to_Me_.epub",
    "desc": "E-Reader publication format for Looks Good to Me."
  },
  {
    "id": "lib-2",
    "title": "Looks Good to Me",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/Software_Engineering/Looks_Good_to_Me_.pdf",
    "desc": "General Resource in PDF format."
  },
  {
    "id": "lib-3",
    "title": "Software Testing with Generative AI",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/Software_Engineering/Software_Testing_with_Generative_AI.epub",
    "desc": "E-Reader publication format for Software Testing with Generative AI."
  },
  {
    "id": "lib-4",
    "title": "Software Testing with Generative AI",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/Software_Engineering/Software_Testing_with_Generative_AI.pdf",
    "desc": "General Resource in PDF format."
  },
  {
    "id": "lib-5",
    "title": "Zero Trust Arch",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/Zero Trust Arch.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-6",
    "title": "blueteamhandbook incidentresponse",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/blueteamhandbook_incidentresponse.epub",
    "desc": "E-Reader publication format for blueteamhandbook incidentresponse."
  },
  {
    "id": "lib-7",
    "title": "blueteamhandbook incidentresponse",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/blueteamhandbook_incidentresponse.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-8",
    "title": "buildingacyberriskmanagementprogram",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/buildingacyberriskmanagementprogram.epub",
    "desc": "E-Reader publication format for buildingacyberriskmanagementprogram."
  },
  {
    "id": "lib-9",
    "title": "buildingacyberriskmanagementprogram",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/buildingacyberriskmanagementprogram.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-10",
    "title": "cybersecuritymanagersguide",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/cybersecuritymanagersguide.epub",
    "desc": "E-Reader publication format for cybersecuritymanagersguide."
  },
  {
    "id": "lib-11",
    "title": "cybersecuritymanagersguide",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/cybersecuritymanagersguide.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-12",
    "title": "cybersecurityopswithbash",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/cybersecurityopswithbash.epub",
    "desc": "E-Reader publication format for cybersecurityopswithbash."
  },
  {
    "id": "lib-13",
    "title": "cybersecurityopswithbash",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/cybersecurityopswithbash.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-14",
    "title": "defensivesecurityhandbook2ndedition",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/defensivesecurityhandbook2ndedition.epub",
    "desc": "E-Reader publication format for defensivesecurityhandbook2ndedition."
  },
  {
    "id": "lib-15",
    "title": "defensivesecurityhandbook2ndedition",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/defensivesecurityhandbook2ndedition.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-16",
    "title": "developersplaybookforlargelanguagemodelsecurity",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/developersplaybookforlargelanguagemodelsecurity.epub",
    "desc": "E-Reader publication format for developersplaybookforlargelanguagemodelsecurity."
  },
  {
    "id": "lib-17",
    "title": "developersplaybookforlargelanguagemodelsecurity",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/developersplaybookforlargelanguagemodelsecurity.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-18",
    "title": "identitysecurityforsoftwaredevelopment",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/identitysecurityforsoftwaredevelopment.epub",
    "desc": "E-Reader publication format for identitysecurityforsoftwaredevelopment."
  },
  {
    "id": "lib-19",
    "title": "identitysecurityforsoftwaredevelopment",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/identitysecurityforsoftwaredevelopment.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-20",
    "title": "insidecyberwarfare3rdedition",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/insidecyberwarfare3rdedition.epub",
    "desc": "E-Reader publication format for insidecyberwarfare3rdedition."
  },
  {
    "id": "lib-21",
    "title": "insidecyberwarfare3rdedition",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/insidecyberwarfare3rdedition.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-22",
    "title": "intelligentcontinuoussecurity",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/intelligentcontinuoussecurity.epub",
    "desc": "E-Reader publication format for intelligentcontinuoussecurity."
  },
  {
    "id": "lib-23",
    "title": "intelligentcontinuoussecurity",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/intelligentcontinuoussecurity.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-24",
    "title": "privacyandsecurityforlargelanguagemodels",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/privacyandsecurityforlargelanguagemodels.epub",
    "desc": "E-Reader publication format for privacyandsecurityforlargelanguagemodels."
  },
  {
    "id": "lib-25",
    "title": "privacyandsecurityforlargelanguagemodels",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/privacyandsecurityforlargelanguagemodels.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-26",
    "title": "securityascode",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/securityascode.epub",
    "desc": "E-Reader publication format for securityascode."
  },
  {
    "id": "lib-27",
    "title": "securityascode",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/securityascode.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-28",
    "title": "softwaresupplychainsecurity",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/softwaresupplychainsecurity.epub",
    "desc": "E-Reader publication format for softwaresupplychainsecurity."
  },
  {
    "id": "lib-29",
    "title": "softwaresupplychainsecurity",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/softwaresupplychainsecurity.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-30",
    "title": "webapplicationsecurity2ndedition",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/webapplicationsecurity2ndedition.epub",
    "desc": "E-Reader publication format for webapplicationsecurity2ndedition."
  },
  {
    "id": "lib-31",
    "title": "webapplicationsecurity2ndedition",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/webapplicationsecurity2ndedition.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-32",
    "title": "zerotrustnetworks2ndedition",
    "category": "cyber-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cybersecurity/zerotrustnetworks2ndedition.epub",
    "desc": "E-Reader publication format for zerotrustnetworks2ndedition."
  },
  {
    "id": "lib-33",
    "title": "zerotrustnetworks2ndedition",
    "category": "cyber-books",
    "format": "PDF",
    "path": "04_Books_Library/Cybersecurity/zerotrustnetworks2ndedition.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-34",
    "title": "AI Powered Search",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/AI-Powered_Search.epub",
    "desc": "E-Reader publication format for AI Powered Search."
  },
  {
    "id": "lib-35",
    "title": "AI Powered Search",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/AI-Powered_Search.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-36",
    "title": "AI Agents in Action",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/AI_Agents_in_Action.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-37",
    "title": "AI Governance (MEAP)",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/AI_Governance_v2_MEAP.epub",
    "desc": "Manning Early Access Edition on AI Governance (MEAP)."
  },
  {
    "id": "lib-38",
    "title": "AI Governance (MEAP)",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/AI_Governance_v2_MEAP.pdf",
    "desc": "Manning Early Access Edition on AI Governance (MEAP)."
  },
  {
    "id": "lib-39",
    "title": "AI Model Evaluation (MEAP)",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/AI_Model_Evaluation_v5_MEAP.epub",
    "desc": "Manning Early Access Edition on AI Model Evaluation (MEAP)."
  },
  {
    "id": "lib-40",
    "title": "AI Model Evaluation (MEAP)",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/AI_Model_Evaluation_v5_MEAP.pdf",
    "desc": "Manning Early Access Edition on AI Model Evaluation (MEAP)."
  },
  {
    "id": "lib-41",
    "title": "AI for Everyday IT",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/AI_for_Everyday_IT.epub",
    "desc": "E-Reader publication format for AI for Everyday IT."
  },
  {
    "id": "lib-42",
    "title": "AI for Everyday IT",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/AI_for_Everyday_IT.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-43",
    "title": "Build AI Drug Discovery Pipelines (MEAP)",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Build_AI_Drug_Discovery_Pipelines_v12_MEAP.epub",
    "desc": "Manning Early Access Edition on Build AI Drug Discovery Pipelines (MEAP)."
  },
  {
    "id": "lib-44",
    "title": "Build AI Drug Discovery Pipelines (MEAP)",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Build_AI_Drug_Discovery_Pipelines_v12_MEAP.pdf",
    "desc": "Manning Early Access Edition on Build AI Drug Discovery Pipelines (MEAP)."
  },
  {
    "id": "lib-45",
    "title": "Build Financial Software with Generative",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Build_Financial_Software_with_Generative.epub",
    "desc": "E-Reader publication format for Build Financial Software with Generative."
  },
  {
    "id": "lib-46",
    "title": "Build Financial Software with Generative",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Build_Financial_Software_with_Generative.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-47",
    "title": "Build a Large Language Model (From Scrat",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Build_a_Large_Language_Model_(From_Scrat.epub",
    "desc": "E-Reader publication format for Build a Large Language Model (From Scrat."
  },
  {
    "id": "lib-48",
    "title": "Building Reliable AI Systems",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Building_Reliable_AI_Systems.epub",
    "desc": "E-Reader publication format for Building Reliable AI Systems."
  },
  {
    "id": "lib-49",
    "title": "Building Reliable AI Systems",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Building_Reliable_AI_Systems.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-50",
    "title": "Coding with AI",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Coding_with_AI.epub",
    "desc": "E-Reader publication format for Coding with AI."
  },
  {
    "id": "lib-51",
    "title": "Coding with AI",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Coding_with_AI.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-52",
    "title": "Deep Learning with Python",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Deep_Learning_with_Python.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-53",
    "title": "Effective Conversational AI",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Effective_Conversational_AI.epub",
    "desc": "E-Reader publication format for Effective Conversational AI."
  },
  {
    "id": "lib-54",
    "title": "Effective Conversational AI",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Effective_Conversational_AI.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-55",
    "title": "Financial AI in Practice (MEAP)",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Financial_AI_in_Practice_v8_MEAP.epub",
    "desc": "Manning Early Access Edition on Financial AI in Practice (MEAP)."
  },
  {
    "id": "lib-56",
    "title": "Financial AI in Practice (MEAP)",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Financial_AI_in_Practice_v8_MEAP.pdf",
    "desc": "Manning Early Access Edition on Financial AI in Practice (MEAP)."
  },
  {
    "id": "lib-57",
    "title": "Generative AI in Action",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Generative_AI_in_Action.epub",
    "desc": "E-Reader publication format for Generative AI in Action."
  },
  {
    "id": "lib-58",
    "title": "Generative AI in Action",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Generative_AI_in_Action.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-59",
    "title": "Human in the Loop Machine Learning",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Human-in-the-Loop_Machine_Learning.epub",
    "desc": "E-Reader publication format for Human in the Loop Machine Learning."
  },
  {
    "id": "lib-60",
    "title": "Human in the Loop Machine Learning",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Human-in-the-Loop_Machine_Learning.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-61",
    "title": "Inside AI",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Inside_AI.epub",
    "desc": "E-Reader publication format for Inside AI."
  },
  {
    "id": "lib-62",
    "title": "Inside AI",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Inside_AI.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-63",
    "title": "Interpretable AI",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Interpretable_AI.epub",
    "desc": "E-Reader publication format for Interpretable AI."
  },
  {
    "id": "lib-64",
    "title": "Interpretable AI",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Interpretable_AI.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-65",
    "title": "LLM Evaluation and Alignment The Founda (MEAP)",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/LLM_Evaluation_and_Alignment_The_Founda_v4_MEAP.epub",
    "desc": "Manning Early Access Edition on LLM Evaluation and Alignment The Founda (MEAP)."
  },
  {
    "id": "lib-66",
    "title": "LLM Evaluation and Alignment The Founda (MEAP)",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/LLM_Evaluation_and_Alignment_The_Founda_v4_MEAP.pdf",
    "desc": "Manning Early Access Edition on LLM Evaluation and Alignment The Founda (MEAP)."
  },
  {
    "id": "lib-67",
    "title": "LLMs in Production",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/LLMs_in_Production.epub",
    "desc": "E-Reader publication format for LLMs in Production."
  },
  {
    "id": "lib-68",
    "title": "LLMs in Production",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/LLMs_in_Production.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-69",
    "title": "Learn AI Data Engineering (MEAP)",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Learn_AI_Data_Engineering_v8_MEAP.epub",
    "desc": "Manning Early Access Edition on Learn AI Data Engineering (MEAP)."
  },
  {
    "id": "lib-70",
    "title": "Learn AI Data Engineering (MEAP)",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Learn_AI_Data_Engineering_v8_MEAP.pdf",
    "desc": "Manning Early Access Edition on Learn AI Data Engineering (MEAP)."
  },
  {
    "id": "lib-71",
    "title": "Machine Learning Platform Engineering",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Machine_Learning_Platform_Engineering.epub",
    "desc": "E-Reader publication format for Machine Learning Platform Engineering."
  },
  {
    "id": "lib-72",
    "title": "Machine Learning Platform Engineering",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Machine_Learning_Platform_Engineering.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-73",
    "title": "Optimization Algorithms",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Optimization_Algorithms.epub",
    "desc": "E-Reader publication format for Optimization Algorithms."
  },
  {
    "id": "lib-74",
    "title": "Optimization Algorithms",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Optimization_Algorithms.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-75",
    "title": "Spring AI in Action",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Spring_AI_in_Action.epub",
    "desc": "E-Reader publication format for Spring AI in Action."
  },
  {
    "id": "lib-76",
    "title": "Spring AI in Action",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Spring_AI_in_Action.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-77",
    "title": "Succeeding with AI",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Succeeding_with_AI.epub",
    "desc": "E-Reader publication format for Succeeding with AI."
  },
  {
    "id": "lib-78",
    "title": "Succeeding with AI",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Succeeding_with_AI.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-79",
    "title": "Swarm intelligence James Kennedy",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Swarm intelligence - James Kennedy.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-80",
    "title": "The AI Pocket Book",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/The_AI_Pocket_Book.epub",
    "desc": "E-Reader publication format for The AI Pocket Book."
  },
  {
    "id": "lib-81",
    "title": "The AI Pocket Book",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/The_AI_Pocket_Book.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-82",
    "title": "The Art of AI Product Development",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/The_Art_of_AI_Product_Development.epub",
    "desc": "E-Reader publication format for The Art of AI Product Development."
  },
  {
    "id": "lib-83",
    "title": "The Art of AI Product Development",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/The_Art_of_AI_Product_Development.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-84",
    "title": "Transformers in Action",
    "category": "ai-books",
    "format": "EPUB",
    "path": "04_Books_Library/AI_and_Machine_Learning/Transformers_in_Action.epub",
    "desc": "E-Reader publication format for Transformers in Action."
  },
  {
    "id": "lib-85",
    "title": "Transformers in Action",
    "category": "ai-books",
    "format": "PDF",
    "path": "04_Books_Library/AI_and_Machine_Learning/Transformers_in_Action.pdf",
    "desc": "AI & ML Book in PDF format."
  },
  {
    "id": "lib-86",
    "title": "Effective Platform Engineering",
    "category": "cloud-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/Effective_Platform_Engineering.epub",
    "desc": "E-Reader publication format for Effective Platform Engineering."
  },
  {
    "id": "lib-87",
    "title": "Effective Platform Engineering",
    "category": "cloud-books",
    "format": "PDF",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/Effective_Platform_Engineering.pdf",
    "desc": "Cloud & Platform in PDF format."
  },
  {
    "id": "lib-88",
    "title": "Learning eBPF Full book",
    "category": "cloud-books",
    "format": "PDF",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/Learning-eBPF - Full book.pdf",
    "desc": "Cloud & Platform in PDF format."
  },
  {
    "id": "lib-89",
    "title": "buzzing across space illustrated childrens guide to ebpf",
    "category": "cloud-books",
    "format": "PDF",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/buzzing-across-space-illustrated-childrens-guide-to-ebpf.pdf",
    "desc": "Cloud & Platform in PDF format."
  },
  {
    "id": "lib-90",
    "title": "cloudnativesecuritycookbook",
    "category": "cloud-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/cloudnativesecuritycookbook.epub",
    "desc": "E-Reader publication format for cloudnativesecuritycookbook."
  },
  {
    "id": "lib-91",
    "title": "cloudnativesecuritycookbook",
    "category": "cloud-books",
    "format": "PDF",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/cloudnativesecuritycookbook.pdf",
    "desc": "Cloud & Platform in PDF format."
  },
  {
    "id": "lib-92",
    "title": "kubernetessecurityandobservability",
    "category": "cloud-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/kubernetessecurityandobservability.epub",
    "desc": "E-Reader publication format for kubernetessecurityandobservability."
  },
  {
    "id": "lib-93",
    "title": "kubernetessecurityandobservability",
    "category": "cloud-books",
    "format": "PDF",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/kubernetessecurityandobservability.pdf",
    "desc": "Cloud & Platform in PDF format."
  },
  {
    "id": "lib-94",
    "title": "learningcloudsecurity",
    "category": "cloud-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/learningcloudsecurity.epub",
    "desc": "E-Reader publication format for learningcloudsecurity."
  },
  {
    "id": "lib-95",
    "title": "learningcloudsecurity",
    "category": "cloud-books",
    "format": "PDF",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/learningcloudsecurity.pdf",
    "desc": "Cloud & Platform in PDF format."
  },
  {
    "id": "lib-96",
    "title": "learningserverlesssecurity",
    "category": "cloud-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/learningserverlesssecurity.epub",
    "desc": "E-Reader publication format for learningserverlesssecurity."
  },
  {
    "id": "lib-97",
    "title": "learningserverlesssecurity",
    "category": "cloud-books",
    "format": "PDF",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/learningserverlesssecurity.pdf",
    "desc": "Cloud & Platform in PDF format."
  },
  {
    "id": "lib-98",
    "title": "practicalcloudsecurity2ndedition",
    "category": "cloud-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/practicalcloudsecurity2ndedition.epub",
    "desc": "E-Reader publication format for practicalcloudsecurity2ndedition."
  },
  {
    "id": "lib-99",
    "title": "practicalcloudsecurity2ndedition",
    "category": "cloud-books",
    "format": "PDF",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/practicalcloudsecurity2ndedition.pdf",
    "desc": "Cloud & Platform in PDF format."
  },
  {
    "id": "lib-100",
    "title": "securityarchitectureforhybridcloud",
    "category": "cloud-books",
    "format": "EPUB",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/securityarchitectureforhybridcloud.epub",
    "desc": "E-Reader publication format for securityarchitectureforhybridcloud."
  },
  {
    "id": "lib-101",
    "title": "securityarchitectureforhybridcloud",
    "category": "cloud-books",
    "format": "PDF",
    "path": "04_Books_Library/Cloud_Platform_and_eBPF/securityarchitectureforhybridcloud.pdf",
    "desc": "Cloud & Platform in PDF format."
  },
  {
    "id": "lib-102",
    "title": "NumPy guide for beginners",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/02_NumPy_and_Math/NumPy_guide_for_beginners__1734359174.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-103",
    "title": "numpy cheatsheet",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/02_NumPy_and_Math/numpy_cheatsheet.pdf",
    "desc": "Quick reference cheat sheet for rapid developer lookup."
  },
  {
    "id": "lib-104",
    "title": "numpy coding",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/02_NumPy_and_Math/numpy_coding.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-105",
    "title": "algorithms python",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/05_Algorithms_and_DS/algorithms_python.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-106",
    "title": "data science python",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/03_Pandas_and_Data_Analysis/data_science_python.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-107",
    "title": "pandas cheat sheet",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/03_Pandas_and_Data_Analysis/pandas_cheat_sheet.pdf",
    "desc": "Quick reference cheat sheet for rapid developer lookup."
  },
  {
    "id": "lib-108",
    "title": "pandas data cleaning",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/03_Pandas_and_Data_Analysis/pandas_data_cleaning.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-109",
    "title": "Advanced Programming with Python",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/01_Core_Python/Advanced_Programming_with_Python__1747243259.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-110",
    "title": "OOP CONCEPTS IN PYTHON",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/01_Core_Python/OOP_CONCEPTS_IN_PYTHON_1735831777.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-111",
    "title": "mastering python",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/01_Core_Python/mastering_python.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-112",
    "title": "multiprocessing in python",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/01_Core_Python/multiprocessing_in_python.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-113",
    "title": "python cheatsheet",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/01_Core_Python/python_cheatsheet.pdf",
    "desc": "Quick reference cheat sheet for rapid developer lookup."
  },
  {
    "id": "lib-114",
    "title": "python tutorial",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/01_Core_Python/python_tutorial.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-115",
    "title": "NLP Transformer based Models",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/04_Machine_Learning_and_DL/NLP_Transformer_based_Models.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-116",
    "title": "Python for Machine Learning Visualization",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/04_Machine_Learning_and_DL/Python_for_Machine_Learning_Visualization_1735220967.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-117",
    "title": "TensorFlow vs PyTorch",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/04_Machine_Learning_and_DL/TensorFlow_vs_PyTorch.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-118",
    "title": "python in gen ai",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/04_Machine_Learning_and_DL/python_in_gen_ai.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-119",
    "title": "pytorch",
    "category": "python-ds",
    "format": "PDF",
    "path": "02_Python_and_Data_Science/04_Machine_Learning_and_DL/pytorch.pdf",
    "desc": "Python & Data Science in PDF format."
  },
  {
    "id": "lib-120",
    "title": "2025 Day 1 Rewrite v1 IntroductionToAgents",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/2025_Day_1_Rewrite_v1_IntroductionToAgents.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-121",
    "title": "2025 Day 2 Rewrite v1 AgentTools",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/2025_Day_2_Rewrite_v1_AgentTools.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-122",
    "title": "2025 Day 3 Rewrite v1 ContextEngineering",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/2025_Day_3_Rewrite_v1_ContextEngineering.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-123",
    "title": "2025 Day 4 Rewrite v1 AgentQuality",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/2025_Day_4_Rewrite_v1_AgentQuality.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-124",
    "title": "2025 Day 5 Rewrite v1 Prototype",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/2025_Day_5_Rewrite_v1_Prototype.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-125",
    "title": "Agent Skills Day 3",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/Agent Skills_Day_3.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-126",
    "title": "Agent Tools & Interoperability Day 2",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/Agent Tools & Interoperability_Day_2.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-127",
    "title": "Day 5 v3",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/Day_5_v3.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-128",
    "title": "Prototype to Production copy",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/Prototype to Production copy.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-129",
    "title": "Prototype to Production",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/Prototype to Production.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-130",
    "title": "The New SDLC With Vibe Coding Day 1",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/The New SDLC With Vibe Coding_Day_1.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-131",
    "title": "Vibe Coding Agent Security and Evaluation Day 4",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_AI_Agents/Vibe Coding Agent Security and Evaluation_Day_4.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-132",
    "title": "Newwhitepaper Agents",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_GenAI_Intensive/Newwhitepaper_Agents.pdf",
    "desc": "Technical whitepaper exploring Newwhitepaper Agents."
  },
  {
    "id": "lib-133",
    "title": "Newwhitepaper Embeddings & vector stores",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_GenAI_Intensive/Newwhitepaper_Embeddings & vector stores.pdf",
    "desc": "Technical whitepaper exploring Newwhitepaper Embeddings & vector stores."
  },
  {
    "id": "lib-134",
    "title": "Newwhitepaper Operationalizing Generative AI on Vertex AI",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_GenAI_Intensive/Newwhitepaper_Operationalizing Generative AI on Vertex AI.pdf",
    "desc": "Technical whitepaper exploring Newwhitepaper Operationalizing Generative AI on Vertex AI."
  },
  {
    "id": "lib-135",
    "title": "Newwhitepaper Solving Domain Specific problems using LLMs",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_GenAI_Intensive/Newwhitepaper_Solving Domain-Specific problems using LLMs.pdf",
    "desc": "Technical whitepaper exploring Newwhitepaper Solving Domain Specific problems using LLMs."
  },
  {
    "id": "lib-136",
    "title": "whitepaper Foundational Large Language models & text generation",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_GenAI_Intensive/whitepaper_Foundational Large Language models & text generation.pdf",
    "desc": "Technical whitepaper exploring whitepaper Foundational Large Language models & text generation."
  },
  {
    "id": "lib-137",
    "title": "whitepaper Prompt Engineering v4",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Kaggle_5_Day_GenAI_Intensive/whitepaper_Prompt Engineering_v4.pdf",
    "desc": "Technical whitepaper exploring whitepaper Prompt Engineering v4."
  },
  {
    "id": "lib-138",
    "title": "365 DataScience",
    "category": "courses",
    "format": "PNG",
    "path": "03_Courses_and_Bootcamps/Udemy_365_Data_Science/365_DataScience.png",
    "desc": "Course & Bootcamp in PNG format."
  },
  {
    "id": "lib-139",
    "title": "365 DataScience Diagram",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Udemy_365_Data_Science/365_DataScience_Diagram.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-140",
    "title": "Intro+to+AI+ +Course+notes",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Udemy_365_Data_Science/Intro+to+AI+-+Course+notes.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-141",
    "title": "C2 W1",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Math_for_Machine_Learning/C2_Calculus_and_Stats/C2_W1.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-142",
    "title": "C2 W2",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Math_for_Machine_Learning/C2_Calculus_and_Stats/C2_W2.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-143",
    "title": "C2 W3",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Math_for_Machine_Learning/C2_Calculus_and_Stats/C2_W3.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-144",
    "title": "C1 W1",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Math_for_Machine_Learning/C1_Linear_Algebra/C1_W1.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-145",
    "title": "C1 W2",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Math_for_Machine_Learning/C1_Linear_Algebra/C1_W2.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-146",
    "title": "C1 W3",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Math_for_Machine_Learning/C1_Linear_Algebra/C1_W3.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-147",
    "title": "C1 W4",
    "category": "courses",
    "format": "PDF",
    "path": "03_Courses_and_Bootcamps/Math_for_Machine_Learning/C1_Linear_Algebra/C1_W4.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-148",
    "title": "CiscoSegmentationSolution",
    "category": "cyber-books",
    "format": "DOCX",
    "path": "05_Cybersecurity/03_Segmentation_and_Network/CiscoSegmentationSolution.docx",
    "desc": "Cybersecurity in DOCX format."
  },
  {
    "id": "lib-149",
    "title": "Cisco HIPAA 2026 Segmentation NISP",
    "category": "cyber-books",
    "format": "PPTX",
    "path": "05_Cybersecurity/03_Segmentation_and_Network/Cisco_HIPAA_2026_Segmentation-NISP.pptx",
    "desc": "Cybersecurity in PPTX format."
  },
  {
    "id": "lib-150",
    "title": "Hybrid Mesh Firewall Study Guide",
    "category": "cyber-books",
    "format": "PDF",
    "path": "05_Cybersecurity/03_Segmentation_and_Network/Hybrid Mesh Firewall Study Guide.PDF",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-151",
    "title": "SegmentationArch BGWhite",
    "category": "cyber-books",
    "format": "PPTX",
    "path": "05_Cybersecurity/03_Segmentation_and_Network/SegmentationArch-BGWhite.pptx",
    "desc": "Cybersecurity in PPTX format."
  },
  {
    "id": "lib-152",
    "title": "SegmentationPlan",
    "category": "cyber-books",
    "format": "DOCX",
    "path": "05_Cybersecurity/03_Segmentation_and_Network/SegmentationPlan.docx",
    "desc": "Cybersecurity in DOCX format."
  },
  {
    "id": "lib-153",
    "title": "SegmentationPlan",
    "category": "cyber-books",
    "format": "PDF",
    "path": "05_Cybersecurity/03_Segmentation_and_Network/SegmentationPlan.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-154",
    "title": "Memory Forensics A Comprehensive Technical Guide",
    "category": "cyber-books",
    "format": "PDF",
    "path": "05_Cybersecurity/02_Forensics_and_Offensive/Memory_Forensics_A_Comprehensive_Technical_Guide_1735430479.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-155",
    "title": "Using AI for Offensive Security",
    "category": "cyber-books",
    "format": "PDF",
    "path": "05_Cybersecurity/02_Forensics_and_Offensive/Using_AI_for_Offensive_Security_1724803512.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-156",
    "title": "Windows forensic Commands",
    "category": "cyber-books",
    "format": "PDF",
    "path": "05_Cybersecurity/02_Forensics_and_Offensive/Windows_forensic_Commands_1728089461.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-157",
    "title": "CHIEF INFORMATION SECURITY OFFICER HANDBOOK",
    "category": "cyber-books",
    "format": "PDF",
    "path": "05_Cybersecurity/01_CISSP_and_CISO/CHIEF_INFORMATION_SECURITY_OFFICER_HANDBOOK_1729696878.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-158",
    "title": "CISSP Exam Study Guide",
    "category": "cyber-books",
    "format": "PDF",
    "path": "05_Cybersecurity/01_CISSP_and_CISO/CISSP_Exam_Study_Guide_1733077547.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-159",
    "title": "INSIDE THE MIND OF A CISO 2024",
    "category": "cyber-books",
    "format": "PDF",
    "path": "05_Cybersecurity/01_CISSP_and_CISO/INSIDE_THE_MIND_OF_A_CISO_2024_1725881040.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-160",
    "title": "CYBERSECURITY ECONOMICS FOR EMERGING MARKETS",
    "category": "cyber-books",
    "format": "PDF",
    "path": "05_Cybersecurity/04_Cloud_and_Economics/CYBERSECURITY_ECONOMICS_FOR_EMERGING_MARKETS_1735357437.pdf",
    "desc": "Cybersecurity in PDF format."
  },
  {
    "id": "lib-161",
    "title": "Journey to Cloud JS",
    "category": "cyber-books",
    "format": "PPTX",
    "path": "05_Cybersecurity/04_Cloud_and_Economics/Journey to Cloud-JS.pptx",
    "desc": "Cybersecurity in PPTX format."
  },
  {
    "id": "lib-162",
    "title": "A Plan for Global Engagement on AI Standards",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/04_Safety_Governance_Security/A_Plan_for_Global_Engagement_on_AI_Standards_1724635314.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-163",
    "title": "OWASP GenAI Red Teaming Guide",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/04_Safety_Governance_Security/OWASP-GenAI Red Teaming Guide.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-164",
    "title": "Security of AI Agents",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/04_Safety_Governance_Security/Security of AI Agents.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-165",
    "title": "U S AI Safety Institute Vision Mission Strategic Goals 1716603441 copy",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/04_Safety_Governance_Security/U_S_AI_Safety_Institute_Vision_Mission_Strategic_Goals_1716603441 copy.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-166",
    "title": "U S AI Safety Institute Vision Mission Strategic Goals",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/04_Safety_Governance_Security/U_S_AI_Safety_Institute_Vision_Mission_Strategic_Goals_1716603441.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-167",
    "title": "Claude Certified Architect \u2013 Foundations",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/08_Certifications_and_Prep/Claude Certified Architect \u2013 Foundations.pdf",
    "desc": "Certification study and exam preparation reference."
  },
  {
    "id": "lib-168",
    "title": "Top 40 LLM Interview Questions Answers",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/08_Certifications_and_Prep/Top_40_LLM_Interview_Questions_Answers_1726484618.pdf",
    "desc": "Certification study and exam preparation reference."
  },
  {
    "id": "lib-169",
    "title": "Agent Quality",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/02_Agents_and_Workflows/Agent Quality.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-170",
    "title": "Agent Tools & Interoperability with Model Context Protocol (MCP)",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/02_Agents_and_Workflows/Agent Tools & Interoperability with Model Context Protocol (MCP).pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-171",
    "title": "Common Agentic Workflow Patterns",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/02_Agents_and_Workflows/Common_Agentic_Workflow_Patterns_1727439222.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-172",
    "title": "Context Engineering Sessions & Memory",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/02_Agents_and_Workflows/Context Engineering_ Sessions & Memory.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-173",
    "title": "Google AI Agents",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/02_Agents_and_Workflows/Google_AI Agents.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-174",
    "title": "What is ReAct Prompting",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/02_Agents_and_Workflows/What_is_ReAct_Prompting__1727696866.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-175",
    "title": "10 UBS CIO Views on AI",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/07_Industry_and_Strategy/10_UBS_CIO_Views_on_AI_1727703250.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-176",
    "title": "AI For Good",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/07_Industry_and_Strategy/AI_For_Good__1726095342.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-177",
    "title": "Key NVIDIA Industry Use Cases for Partners",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/07_Industry_and_Strategy/Key NVIDIA Industry Use Cases for Partners.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-178",
    "title": "Operationalizing Generative AI on Vertex AI using MLOps",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/07_Industry_and_Strategy/Operationalizing Generative AI on Vertex AI using MLOps.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-179",
    "title": "Trends Artificial Intelligence",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/07_Industry_and_Strategy/Trends_Artificial_Intelligence.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-180",
    "title": "2501.12948v1",
    "category": "papers",
    "format": "PDF",
    "path": "01_AI_and_GenAI/05_Research_Papers/2501.12948v1.pdf",
    "desc": "Research Paper in PDF format."
  },
  {
    "id": "lib-181",
    "title": "2506.02153v2",
    "category": "papers",
    "format": "PDF",
    "path": "01_AI_and_GenAI/05_Research_Papers/2506.02153v2.pdf",
    "desc": "Research Paper in PDF format."
  },
  {
    "id": "lib-182",
    "title": "978 3 319 10590 1 53",
    "category": "papers",
    "format": "PDF",
    "path": "01_AI_and_GenAI/05_Research_Papers/978-3-319-10590-1_53.pdf",
    "desc": "Research Paper in PDF format."
  },
  {
    "id": "lib-183",
    "title": "RLCD Jev",
    "category": "papers",
    "format": "PDF",
    "path": "01_AI_and_GenAI/05_Research_Papers/RLCD-Jev.pdf",
    "desc": "Research Paper in PDF format."
  },
  {
    "id": "lib-184",
    "title": "Visualizing and understanding convolutional networks",
    "category": "papers",
    "format": "PDF",
    "path": "01_AI_and_GenAI/05_Research_Papers/Visualizing_and_understanding_convolutional_networks.pdf",
    "desc": "Research Paper in PDF format."
  },
  {
    "id": "lib-185",
    "title": "6 different RAG techniques",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/03_RAG_and_Vector_Search/6_different_RAG_techniques_1726533237.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-186",
    "title": "Leiden HDBScan",
    "category": "ai-books",
    "format": "DOCX",
    "path": "01_AI_and_GenAI/03_RAG_and_Vector_Search/Leiden-HDBScan.docx",
    "desc": "AI & GenAI Guide in DOCX format."
  },
  {
    "id": "lib-187",
    "title": "Leiden HDBScan",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/03_RAG_and_Vector_Search/Leiden-HDBScan.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-188",
    "title": "RAG vs Long Context LLMs",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/03_RAG_and_Vector_Search/RAG_vs_Long_Context_LLMs_1728404797.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-189",
    "title": "AI Intro",
    "category": "ai-books",
    "format": "PPTX",
    "path": "01_AI_and_GenAI/01_Foundations_and_LLMs/AI-Intro.pptx",
    "desc": "AI & GenAI Guide in PPTX format."
  },
  {
    "id": "lib-190",
    "title": "Foundation of LLM",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/01_Foundations_and_LLMs/Foundation of LLM.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-191",
    "title": "How to select the right LLM Model for use case",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/01_Foundations_and_LLMs/How_to_select_the_right_LLM_Model_for_use_case__1725717140.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-192",
    "title": "NLTK Chapter1 2",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/01_Foundations_and_LLMs/NLTK-Chapter1 2.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-193",
    "title": "inference optimization matters",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/01_Foundations_and_LLMs/inference_optimization_matters_1726858492.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-194",
    "title": "pretraining llm",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/01_Foundations_and_LLMs/pretraining_llm.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-195",
    "title": "the illusion of thinking",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/01_Foundations_and_LLMs/the-illusion-of-thinking.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-196",
    "title": "Nikita Prasad EDA CheatCode",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/06_CheatSheets_and_Guides/Nikita_Prasad_EDA_CheatCode_1725965285.pdf",
    "desc": "Quick reference cheat sheet for rapid developer lookup."
  },
  {
    "id": "lib-197",
    "title": "Nikita Prasad Feature Engineering Basics",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/06_CheatSheets_and_Guides/Nikita_Prasad_Feature_Engineering_Basics_1726842130.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-198",
    "title": "SQL Guide",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/06_CheatSheets_and_Guides/SQL_Guide_1736770305.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-199",
    "title": "learneverythingai",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/06_CheatSheets_and_Guides/learneverythingai__1714435215.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-200",
    "title": "maths4ml linearalgebra formula",
    "category": "ai-books",
    "format": "PDF",
    "path": "01_AI_and_GenAI/06_CheatSheets_and_Guides/maths4ml-linearalgebra-formula.pdf",
    "desc": "AI & GenAI Guide in PDF format."
  },
  {
    "id": "lib-201",
    "title": "SwiftUI Views Mastery",
    "category": "courses",
    "format": "EPUB",
    "path": "06_Apple_and_Swift/SwiftUI_Views_Mastery/SwiftUI Views Mastery.epub",
    "desc": "E-Reader publication format for SwiftUI Views Mastery."
  },
  {
    "id": "lib-202",
    "title": "Xcode Project (1)",
    "category": "courses",
    "format": "ZIP",
    "path": "06_Apple_and_Swift/SwiftUI_Views_Mastery/Xcode Project (1).zip",
    "desc": "Course & Bootcamp in ZIP format."
  },
  {
    "id": "lib-203",
    "title": "SwiftUI Essentials",
    "category": "courses",
    "format": "EPUB",
    "path": "06_Apple_and_Swift/SwiftUI_Essentials/SwiftUI Essentials.epub",
    "desc": "E-Reader publication format for SwiftUI Essentials."
  },
  {
    "id": "lib-204",
    "title": "SwiftUI Essentials",
    "category": "courses",
    "format": "PDF",
    "path": "06_Apple_and_Swift/SwiftUI_Essentials/SwiftUI Essentials.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-205",
    "title": "Xcode Project",
    "category": "courses",
    "format": "ZIP",
    "path": "06_Apple_and_Swift/SwiftUI_Essentials/Xcode Project.zip",
    "desc": "Course & Bootcamp in ZIP format."
  },
  {
    "id": "lib-206",
    "title": "SwiftUI Views Quick Start",
    "category": "courses",
    "format": "EPUB",
    "path": "06_Apple_and_Swift/SwiftUI_Views_QuickStart/SwiftUI Views Quick Start.epub",
    "desc": "E-Reader publication format for SwiftUI Views Quick Start."
  },
  {
    "id": "lib-207",
    "title": "SwiftUI Views Quick Start",
    "category": "courses",
    "format": "PDF",
    "path": "06_Apple_and_Swift/SwiftUI_Views_QuickStart/SwiftUI Views Quick Start.pdf",
    "desc": "Course & Bootcamp in PDF format."
  },
  {
    "id": "lib-208",
    "title": "coupon",
    "category": "courses",
    "format": "PNG",
    "path": "06_Apple_and_Swift/SwiftUI_Views_QuickStart/coupon.png",
    "desc": "Course & Bootcamp in PNG format."
  },
  {
    "id": "lib-209",
    "title": "save.10.percent",
    "category": "courses",
    "format": "PNG",
    "path": "06_Apple_and_Swift/SwiftUI_Views_QuickStart/save.10.percent.png",
    "desc": "Course & Bootcamp in PNG format."
  }
];


// Readable book titles from library filenames.
// Keep this in step with format_book_title in nexus_study.py.
const TITLE_WORDS = new Set(["a", "about", "across", "action", "advanced", "agent", "agentic", "agents", "algebra", "algorithms", "alignment", "also", "an", "and", "answers", "any", "application", "arch", "architect", "architecture", "art", "artificial", "as", "at", "based", "bash", "basics", "been", "beginner", "beginners", "being", "blue", "book", "both", "build", "building", "but", "buzzing", "by", "case", "cases", "certified", "chain", "chapter", "cheat", "cheatsheet", "chief", "children", "childrens", "cisco", "claude", "cleaning", "cloud", "code", "coding", "commands", "common", "comparison", "comprehensive", "concepts", "context", "continuous", "conversational", "convolutional", "cookbook", "coupon", "course", "cyber", "cybersecurity", "data", "day", "deep", "defensive", "developer", "developers", "development", "diagram", "did", "different", "discovery", "do", "does", "domain", "down", "drug", "each", "economics", "edition", "effective", "eight", "embeddings", "emerging", "engagement", "engineer", "engineering", "engineers", "essentials", "evaluation", "everyday", "everything", "exam", "feature", "few", "financial", "firewall", "first", "five", "for", "forensics", "formula", "foundation", "foundational", "foundations", "four", "fourth", "from", "full", "gen", "generation", "generative", "global", "goals", "good", "google", "governance", "guide", "guides", "had", "handbook", "has", "have", "how", "human", "hybrid", "identity", "if", "illusion", "illustrated", "in", "incident", "industry", "inference", "information", "inside", "intelligence", "intelligent", "interoperability", "interpretable", "interview", "into", "intro", "introduction", "its", "james", "journey", "kennedy", "key", "kubernetes", "language", "large", "learn", "learning", "leiden", "linear", "long", "looks", "loop", "machine", "management", "manager", "managers", "many", "markets", "mastering", "mastery", "math", "maths", "matters", "me", "memory", "mind", "mission", "model", "models", "more", "most", "much", "multiprocessing", "my", "native", "network", "networks", "new", "nikita", "nine", "no", "nor", "notes", "observability", "of", "off", "offensive", "officer", "on", "one", "only", "operation", "operationalizing", "operations", "ops", "optimization", "or", "other", "our", "out", "over", "own", "paper", "papers", "partners", "patterns", "per", "percent", "pipelines", "plan", "platform", "platforms", "playbook", "pocket", "powered", "practical", "practice", "prasad", "pretraining", "privacy", "problems", "product", "production", "program", "programming", "prompt", "prompting", "prototype", "python", "quality", "questions", "quick", "red", "reliable", "response", "rewrite", "right", "risk", "same", "save", "science", "search", "second", "security", "segmentation", "select", "serverless", "sessions", "seven", "sheet", "six", "skills", "so", "software", "solution", "solving", "some", "space", "specific", "standards", "start", "stores", "strategic", "study", "succeeding", "such", "supply", "swarm", "system", "systems", "team", "teaming", "technical", "techniques", "ten", "testing", "text", "than", "the", "their", "then", "these", "they", "thinking", "third", "those", "three", "through", "to", "too", "tools", "top", "transformers", "trends", "trust", "tutorial", "two", "understanding", "up", "use", "using", "vector", "vertex", "very", "via", "vibe", "views", "vision", "visualization", "visualizing", "vs", "warfare", "was", "we", "web", "week", "were", "what", "when", "where", "which", "whitepaper", "who", "why", "windows", "with", "within", "without", "workflow", "yes", "you", "your", "zero"]);
const TITLE_ACRONYMS = {"ai": "AI", "api": "API", "bg": "BG", "cio": "CIO", "ciso": "CISO", "cissp": "CISSP", "cpu": "CPU", "css": "CSS", "dl": "DL", "eda": "EDA", "epub": "EPUB", "gpu": "GPU", "hipaa": "HIPAA", "html": "HTML", "it": "IT", "js": "JS", "json": "JSON", "llm": "LLM", "llms": "LLMs", "mcp": "MCP", "meap": "MEAP", "ml": "ML", "mlops": "MLOps", "nisp": "NISP", "nlp": "NLP", "nltk": "NLTK", "nvidia": "NVIDIA", "oop": "OOP", "owasp": "OWASP", "pdf": "PDF", "rag": "RAG", "rlcd": "RLCD", "sdlc": "SDLC", "sql": "SQL", "ubs": "UBS"};
const TITLE_SPECIAL = {"ebpf": "eBPF", "genai": "GenAI", "github": "GitHub", "hdbscan": "HDBScan", "javascript": "JavaScript", "numpy": "NumPy", "openai": "OpenAI", "pandas": "Pandas", "pytorch": "PyTorch", "react": "ReAct", "swiftui": "SwiftUI", "tensorflow": "TensorFlow", "xcode": "Xcode"};
const TITLE_SMALL = new Set(["a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "nor", "of", "on", "or", "the", "to", "vs", "with"]);
const HYPHEN_TAILS = new Set(["assisted", "based", "driven", "enabled", "native", "powered"]);
const TITLE_EXTENSIONS = [".epub", ".pdf", ".png", ".pptx", ".docx", ".zip", ".html", ".ppt"];


function segmentTitleToken(token) {
  const text = token.toLowerCase();
  if (TITLE_WORDS.has(text) || TITLE_ACRONYMS[text] || TITLE_SPECIAL[text] || /^\d+(?:st|nd|rd|th)$/i.test(text) || /^\d+$/.test(text)) {
    return [text];
  }
  const length = text.length;
  if (length < 8) return [token];
  const best = Array(length + 1).fill(1e9);
  const prev = Array(length + 1).fill(-1);
  best[0] = 0;
  for (let start = 0; start < length; start++) {
    if (best[start] >= 1e9) continue;
    for (let end = start + 1; end <= Math.min(length, start + 28); end++) {
      const piece = text.slice(start, end);
      const known = TITLE_WORDS.has(piece) || TITLE_ACRONYMS[piece] || TITLE_SPECIAL[piece] || /^\d+(?:st|nd|rd|th)$/i.test(piece) || (/^\d+$/.test(piece) && piece.length <= 4);
      if (!known) continue;
      const cost = 1 / (piece.length ** 2);
      if (best[start] + cost < best[end]) {
        best[end] = best[start] + cost;
        prev[end] = start;
      }
    }
  }
  if (prev[length] < 0) return [token];
  const parts = [];
  let cursor = length;
  while (cursor > 0) {
    const cut = prev[cursor];
    parts.push(text.slice(cut, cursor));
    cursor = cut;
  }
  parts.reverse();
  return parts.length > 1 ? parts : [token];
}

function splitCamel(token) {
  const key = token.toLowerCase();
  if (TITLE_SPECIAL[key] || TITLE_ACRONYMS[key]) return [token];
  if (/^v\d+$/i.test(token) || /^[CW]\d+$/.test(token) || /^\d+(?:st|nd|rd|th)$/i.test(token)) return [token];
  const parts = token.replace(/(?<=[a-z])(?=[A-Z])/g, " ").split(" ");
  const out = [];
  for (const part of parts) {
    const match = part.match(/^([A-Z]{2,})([A-Z][a-z].+)$/);
    if (match && (TITLE_ACRONYMS[match[1].toLowerCase()] || TITLE_WORDS.has(match[2].toLowerCase()))) {
      out.push(match[1], match[2]);
    } else {
      out.push(part);
    }
  }
  return out.length ? out : [token];
}

function keepTitleHyphen(left, right) {
  if (/^\d+$/.test(left) && /^\d+$/.test(right)) return true;
  const small = new Set(["a", "an", "the", "of", "in", "on", "to", "for", "and", "with", "by"]);
  if ((small.has(left.toLowerCase()) || small.has(right.toLowerCase())) && (/^[A-Z]/.test(left) || /^[A-Z]/.test(right))) return true;
  const rightKey = right.toLowerCase();
  if (TITLE_ACRONYMS[left.toLowerCase()] && (TITLE_ACRONYMS[rightKey] || TITLE_SPECIAL[rightKey] || HYPHEN_TAILS.has(rightKey))) return true;
  if (/^[A-Z][a-z]{2,}$/.test(left) && /^[A-Z][a-z]{2,}$/.test(right)) return true;
  return false;
}

function splitTitleHyphens(text) {
  let previous = null;
  while (previous !== text) {
    previous = text;
    text = text.replace(/([A-Za-z0-9]+)-([A-Za-z0-9]+)/, (all, left, right) => keepTitleHyphen(left, right) ? `${left}-${right}` : `${left} ${right}`);
  }
  return text;
}

function knownTitleWord(word) {
  const key = word.replace(/[()]/g, "").toLowerCase().replace(/'s/g, "").replace(/'/g, "");
  return TITLE_WORDS.has(key) || !!TITLE_ACRONYMS[key] || !!TITLE_SPECIAL[key] || /^\d+(?:st|nd|rd|th)$/i.test(key) || /^v\d+$/i.test(key) || /^[CW]\d+$/.test(key) || /^\d+$/.test(key);
}

function polishTitleWord(word, first, last, nextKnown) {
  if (word === ":") return word;
  const bare = word.replace(/[()]/g, "");
  const key = bare.toLowerCase();
  const startsParen = word.startsWith("(");
  let cased;
  if (TITLE_SPECIAL[key]) cased = TITLE_SPECIAL[key];
  else if (TITLE_ACRONYMS[key]) cased = TITLE_ACRONYMS[key];
  else if (/^\d+(?:st|nd|rd|th)$/i.test(key) || /^\d+$/.test(key)) cased = key;
  else if (/^v\d+$/i.test(key)) cased = key.toLowerCase();
  else if (/^[CW]\d+$/.test(bare)) cased = bare[0].toUpperCase() + bare.slice(1);
  else if ([...bare.slice(1)].some((ch) => ch >= "A" && ch <= "Z") && bare !== bare.toUpperCase()) cased = bare;
  else if (TITLE_SMALL.has(key) && !first && !last && !startsParen && nextKnown) cased = key;
  else if (/^[A-Za-z']+$/.test(key.replace(/'/g, "x"))) cased = key.charAt(0).toUpperCase() + key.slice(1);
  else cased = bare;
  if (startsParen) cased = "(" + cased;
  if (word.endsWith(")") && !cased.endsWith(")")) cased += ")";
  return cased;
}

function formatBookTitle(name) {
  let raw = String(name || "").trim();
  raw = raw.replace(/\\u([0-9a-fA-F]{4})/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)));
  raw = raw.replace(/\\(?!u)/g, "/");
  let text = raw.split("/").pop();
  const lowered = text.toLowerCase();
  for (const ext of TITLE_EXTENSIONS) {
    if (lowered.endsWith(ext)) {
      text = text.slice(0, -ext.length);
      break;
    }
  }
  if (/^\d{4}\.\d{4,5}(?:v\d+)?$/i.test(text)) return text;
  text = text.replace(/\s+copy$/i, "").trim();
  text = text.replace(/\./g, " ");
  text = text.replace(/(?:^|[_\s])1[6-9]\d{8}(?=$|[_\s])/g, " ");
  text = text.replace(/[_\s]+v\d+[_\s]+MEAP\b/gi, " (MEAP)");
  text = text.replace(/\s+full book$/i, "").trim();
  text = text.replace(/\u2013/g, " - ").replace(/\u2014/g, " - ");
  text = text.replace(/\+/g, " ").replace(/_/g, " ");
  text = text.replace(/(\d+)(st|nd|rd|th)/gi, " $1$2 ");
  text = text.replace(/\(From Scrat\b\)?/i, "(From Scratch)");
  text = text.replace(/\s+-\s+/g, " : ");
  text = text.replace(/\s+/g, " ").trim();
  let parts = text.split(/\s+/).filter(Boolean);
  if (parts.length === 2 && parts.every((part) => /^[a-z0-9]{10,}$/.test(part))) {
    text = `${parts[0]} : ${parts[1]}`;
  }
  text = splitTitleHyphens(text);
  text = text.replace(/\s+/g, " ").replace(/^[\s-]+|[\s-]+$/g, "");
  const tokens = [];
  for (const tok of text.split(/\s+/)) {
    if (!tok) continue;
    if (tok === ":") { tokens.push(":"); continue; }
    if (/^\d{4}\.\d{4,5}(?:v\d+)?$/i.test(tok)) { tokens.push(tok); continue; }
    let bits = [tok];
    if (/[A-Za-z]{3,}\d|\d[A-Za-z]{2,}/.test(tok) && !/^v\d+$/i.test(tok) && !/^[CW]\d+$/.test(tok) && !/^\d+(?:st|nd|rd|th)$/i.test(tok)) {
      bits = tok.match(/[A-Za-z]+|\d+(?:st|nd|rd|th)|\d+|[()]/gi) || [tok];
    }
    for (const bit of bits) {
      if (bit === ")" && tokens.length) { tokens[tokens.length - 1] += ")"; continue; }
      if (bit === "(") { tokens.push("("); continue; }
      const sides = bit.includes("-") ? bit.split("-") : [bit];
      const keepHyphen = bit.includes("-");
      const pieces = [];
      for (const side of sides) {
        for (const camel of splitCamel(side)) {
          if (camel === camel.toLowerCase() || (camel.length > 10 && camel.slice(1) === camel.slice(1).toLowerCase())) {
            pieces.push(...segmentTitleToken(camel.toLowerCase()));
          } else {
            pieces.push(camel);
          }
        }
      }
      if (keepHyphen && pieces.length === sides.length) tokens.push(pieces.join("-"));
      else tokens.push(...pieces);
    }
  }
  const cleaned = [];
  for (const tok of tokens) {
    if (cleaned.length && cleaned[cleaned.length - 1] === "(") cleaned[cleaned.length - 1] += tok;
    else cleaned.push(tok);
  }
  const rewritten = [];
  for (let index = 0; index < cleaned.length; index++) {
    const tok = cleaned[index];
    const nxt = cleaned[index + 1] ? cleaned[index + 1].toLowerCase() : "";
    if (tok.toLowerCase() === "maths" && cleaned[index + 1] === "4" && nxt === "ml" || (cleaned[index + 2] && cleaned[index + 2].toLowerCase() === "ml" && tok.toLowerCase() === "maths" && cleaned[index + 1] === "4")) {
      rewritten.push("Maths", "for", "ML");
      index += 2;
      continue;
    }
    if ((tok.toLowerCase() === "developers" || tok.toLowerCase() === "managers") && ["guide", "playbook", "handbook"].includes(nxt)) {
      rewritten.push((tok.toLowerCase().startsWith("developer") ? "developer" : "manager") + "'s");
    } else if (tok.toLowerCase() === "childrens" && (nxt === "guide" || nxt === "book")) {
      rewritten.push("children's");
    } else {
      rewritten.push(tok);
    }
  }
  const joined = [];
  for (let index = 0; index < rewritten.length; index++) {
    const piece = rewritten[index];
    if (/^[A-Za-z]$/.test(piece) && !["a", "i"].includes(piece.toLowerCase()) && rewritten[index + 1] && /^[A-Za-z]$/.test(rewritten[index + 1]) && !["a", "i"].includes(rewritten[index + 1].toLowerCase())) {
      const letters = [piece, rewritten[index + 1]];
      index += 2;
      while (rewritten[index] && /^[A-Za-z]$/.test(rewritten[index]) && !["a", "i"].includes(rewritten[index].toLowerCase())) {
        letters.push(rewritten[index]);
        index++;
      }
      index--;
      joined.push(letters.map((ch) => ch.toUpperCase()).join(".") + ".");
      continue;
    }
    joined.push(piece);
  }
  const polished = joined.map((tok, index) => {
    const following = joined[index + 1] || "";
    if (tok.includes("-") && tok !== "-") {
      const bits = tok.split("-");
      return bits.map((bit, bitIndex) => polishTitleWord(
        bit,
        index === 0 && bitIndex === 0,
        index === joined.length - 1 && bitIndex === bits.length - 1,
        bitIndex + 1 < bits.length ? knownTitleWord(bits[bitIndex + 1]) : knownTitleWord(following)
      )).join("-");
    }
    return polishTitleWord(tok, index === 0 || tok.startsWith("("), index === joined.length - 1, knownTitleWord(following));
  });
  let title = polished.join(" ");
  title = title.replace(/\s+:\s+/g, ": ");
  title = title.replace(/\s+([,.;)])/g, "$1");
  title = title.replace(/\(\s+/g, "(");
  title = title.replace(/\s+/g, " ").trim();
  title = title.replace(/\s+(\d+(?:st|nd|rd|th) Edition)$/i, ", $1");
  title = title.replace(/^(New Whitepaper|Whitepaper)\s+(?!:)/, "$1: ");
  return title;
}


// ==========================================================================
// 2b. Consolidated Resource Library (Deduplicating EPUB + PDF Titles)
// ==========================================================================
const CONSOLIDATED_LIBRARY = (() => {
  const map = new Map();
  RESOURCE_LIBRARY.forEach(item => {
    const pretty = formatBookTitle(item.path || item.title);
    const normTitle = pretty.trim().toLowerCase().replace(/\s+/g, " ");
    const key = `${item.category}:::${normTitle}`;

    if (!map.has(key)) {
      let desc = item.desc || "";
      if (item.title && pretty && item.title !== pretty && desc.includes(item.title)) {
        desc = desc.split(item.title).join(pretty);
      }
      map.set(key, {
        id: item.id,
        title: pretty,
        category: item.category,
        desc,
        formats: []
      });
    }
    const entry = map.get(key);
    entry.formats.push({
      format: (item.format || 'FILE').toUpperCase(),
      path: item.path,
      desc: item.desc
    });

    if (entry.formats.length > 1) {
      if (entry.desc.includes('E-Reader') || entry.desc.includes('in PDF format') || entry.desc.includes('General Resource')) {
        entry.desc = 'Complete edition available in both PDF and EPUB e-reader formats.';
      }
    }
  });
  return Array.from(map.values());
})();

function updateLibraryFilterCounts() {
  const pills = document.querySelectorAll('#libraryFilters .filter-pill');
  if (!pills.length) return;
  pills.forEach(pill => {
    const filter = pill.getAttribute('data-filter');
    const count = (filter === 'all')
      ? CONSOLIDATED_LIBRARY.length
      : CONSOLIDATED_LIBRARY.filter(i => i.category === filter).length;
    const baseLabel = pill.textContent.split('(')[0].trim();
    pill.textContent = `${baseLabel} (${count})`;
  });
}

// ==========================================================================
// 3. Quick Cheat Sheets Data
// ==========================================================================
const QUICK_CHEATSHEETS = [
  {
    icon: '📊',
    title: 'EDA CheatCode (Exploratory Data Analysis)',
    desc: 'Quick reference for summary statistics, outlier detection, distribution checks, and missing value imputation in pandas.',
    path: '01_AI_and_GenAI/06_CheatSheets_and_Guides/Nikita_Prasad_EDA_CheatCode_1725965285.pdf'
  },
  {
    icon: '⚙️',
    title: 'Feature Engineering Basics',
    desc: 'Encoding categorical variables, binning, polynomial features, log transforms, and scaling strategies.',
    path: '01_AI_and_GenAI/06_CheatSheets_and_Guides/Nikita_Prasad_Feature_Engineering_Basics_1726842130.pdf'
  },
  {
    icon: '🔍',
    title: '6 Different RAG Techniques Cheat Sheet',
    desc: 'Visual summary of Naive RAG, Sentence-Window, Parent-Document, HyDE, Multi-Query, and Graph RAG.',
    path: '01_AI_and_GenAI/03_RAG_and_Vector_Search/6_different_RAG_techniques_1726533237.pdf'
  },
  {
    icon: '🗄️',
    title: 'SQL Guide for Data Science & Analytics',
    desc: 'Essential window functions, CTEs, Joins, subqueries, and analytical queries for preparing datasets.',
    path: '01_AI_and_GenAI/06_CheatSheets_and_Guides/SQL_Guide_1736770305.pdf'
  },
  {
    icon: '📐',
    title: 'Linear Algebra & Math for ML Formulas',
    desc: 'Matrix dot product rules, determinants, eigenvalues, SVD, and gradient descent update formulas.',
    path: '01_AI_and_GenAI/06_CheatSheets_and_Guides/maths4ml-linearalgebra-formula.pdf'
  },
  {
    icon: '🐼',
    title: 'Pandas Data Cleaning & Cheatsheet',
    desc: 'Rapid lookup for dataframe indexing, apply functions, groupby aggregations, and datetime manipulation.',
    path: '02_Python_and_Data_Science/03_Pandas_and_Data_Analysis/pandas_cheat_sheet.pdf'
  },
  {
    icon: '🔢',
    title: 'NumPy Array Cheatsheet & Coding Guide',
    desc: 'Array indexing, slicing syntax, broadcasting tricks, boolean masks, and matrix math operations.',
    path: '02_Python_and_Data_Science/02_NumPy_and_Math/numpy_cheatsheet.pdf'
  },
  {
    icon: '💼',
    title: 'Top 40 LLM Interview Questions & Answers',
    desc: 'Curated technical interview questions covering transformers, temperature, attention, fine-tuning, and RAG.',
    path: '01_AI_and_GenAI/08_Certifications_and_Prep/Top_40_LLM_Interview_Questions_Answers_1726484618.pdf'
  }
];

// ==========================================================================
// 4. State Management (localStorage)
// ==========================================================================
const STORAGE_KEY = 'nexus_learning_progress_v1';
let appState = {
  activeTab: 'journey',
  activeTrack: 'ai-agent',
  completedMilestones: {}
};

function loadState() {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        appState.completedMilestones = parsed.completedMilestones || {};
      }
    }
  } catch (e) {
    console.warn('LocalStorage not available, continuing with session state:', e);
    appState.completedMilestones = {};
  }
}

function saveState() {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
        completedMilestones: appState.completedMilestones
      }));
    }
  } catch (e) {
    console.warn('Could not save state to localStorage:', e);
  }
}

function toggleMilestone(milestoneId) {
  if (appState.completedMilestones[milestoneId]) {
    delete appState.completedMilestones[milestoneId];
  } else {
    appState.completedMilestones[milestoneId] = true;
  }
  saveState();
  updateUI();
}

function resetProgress() {
  if (confirm('Are you sure you want to reset all completed study progress?')) {
    appState.completedMilestones = {};
    saveState();
    updateUI();
  }
}

// ==========================================================================
// 5. UI Rendering & Updates
// ==========================================================================
function getAllMilestones() {
  const all = [];
  Object.values(JOURNEY_TRACKS).forEach(track => {
    track.stages.forEach(stage => {
      stage.milestones.forEach(m => {
        all.push({ ...m, trackId: track.id, trackTitle: track.title });
      });
    });
  });
  return all;
}

function getTrackProgress(trackId) {
  const track = JOURNEY_TRACKS[trackId];
  if (!track) return { total: 0, completed: 0, percent: 0 };
  let total = 0;
  let completed = 0;
  track.stages.forEach(stage => {
    stage.milestones.forEach(m => {
      total++;
      if (appState.completedMilestones[m.id]) completed++;
    });
  });
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
  return { total, completed, percent };
}

function getOverallStats() {
  const all = getAllMilestones();
  const total = all.length;
  let completed = 0;
  all.forEach(m => {
    if (appState.completedMilestones[m.id]) completed++;
  });
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0;

  // Rank determination
  let rank = 'AI Novice';
  if (completed >= 30) rank = 'Autonomous Architect';
  else if (completed >= 20) rank = 'AI System Engineer';
  else if (completed >= 10) rank = 'ML Practitioner';
  else if (completed >= 4) rank = 'Active Apprentice';

  return { total, completed, percent, rank };
}

function getNextRecommendedMilestone() {
  // First check in the currently active track
  const currentTrack = JOURNEY_TRACKS[appState.activeTrack];
  if (currentTrack) {
    for (const stage of currentTrack.stages) {
      for (const m of stage.milestones) {
        if (!appState.completedMilestones[m.id]) {
          return { ...m, trackTitle: currentTrack.title, trackId: currentTrack.id };
        }
      }
    }
  }

  // If active track is 100% completed, check all other tracks
  const all = getAllMilestones();
  for (const m of all) {
    if (!appState.completedMilestones[m.id]) {
      return m;
    }
  }

  // All completed!
  return null;
}

function renderNextStepBanner() {
  const next = getNextRecommendedMilestone();
  const banner = document.getElementById('nextStepBanner');
  const title = document.getElementById('nextStepTitle');
  const desc = document.getElementById('nextStepDesc');
  const trackTag = document.getElementById('nextStepTrack');
  const timeTag = document.getElementById('nextStepTime');
  const typeTag = document.getElementById('nextStepType');
  const actionBtn = document.getElementById('nextStepActionBtn');
  const markDoneBtn = document.getElementById('nextStepMarkDoneBtn');

  if (!next) {
    title.textContent = '🎉 Congratulations! You have completed all milestones!';
    desc.textContent = 'You have worked through the complete curriculum across AI Agents, Python, Data Science, and Security.';
    trackTag.textContent = 'Mastery Achieved';
    timeTag.textContent = '100%';
    typeTag.textContent = 'Complete';
    actionBtn.style.display = 'none';
    markDoneBtn.style.display = 'none';
    return;
  }

  actionBtn.style.display = 'inline-flex';
  markDoneBtn.style.display = 'inline-flex';

  title.textContent = next.title;
  desc.textContent = next.desc;
  trackTag.textContent = next.trackTitle;
  timeTag.textContent = `⏱ ${next.time}`;
  typeTag.textContent = next.type;

  const fullUrl = getFileUrl(next.filePath);
  actionBtn.href = fullUrl;
  actionBtn.onclick = (e) => {
    // Also open details modal if desired
  };

  markDoneBtn.onclick = () => {
    toggleMilestone(next.id);
  };
}

function renderTrackPills() {
  const t1 = getTrackProgress('ai-agent');
  const t2 = getTrackProgress('python-ds');
  const t3 = getTrackProgress('ai-safety');
  const t4 = getTrackProgress('infra-security');

  const p1 = document.getElementById('track1Pill');
  const p2 = document.getElementById('track2Pill');
  const p3 = document.getElementById('track3Pill');
  const p4 = document.getElementById('track4Pill');

  if (p1) p1.textContent = `${t1.percent}%`;
  if (p2) p2.textContent = `${t2.percent}%`;
  if (p3) p3.textContent = `${t3.percent}%`;
  if (p4) p4.textContent = `${t4.percent}%`;
}

function renderActiveTrack() {
  const container = document.getElementById('journeyTrackDisplay');
  const track = JOURNEY_TRACKS[appState.activeTrack];
  if (!container || !track) return;

  const progress = getTrackProgress(track.id);

  let html = `
    <div class="journey-track-header">
      <div class="journey-track-title">
        <h2>${track.icon} ${track.title}</h2>
        <p>${track.subtitle}</p>
      </div>
      <div class="journey-progress-container">
        <div style="display:flex; justify-content:space-between; font-size:0.82rem; font-weight:700;">
          <span style="color:var(--text-secondary);">Track Progress</span>
          <span style="color:#818cf8;">${progress.completed}/${progress.total} (${progress.percent}%)</span>
        </div>
        <div class="journey-progress-bar-bg">
          <div class="journey-progress-bar-fill" style="width: ${progress.percent}%;"></div>
        </div>
      </div>
    </div>

    <div class="stages-list">
  `;

  track.stages.forEach((stage, sIdx) => {
    let stageCompleted = 0;
    stage.milestones.forEach(m => {
      if (appState.completedMilestones[m.id]) stageCompleted++;
    });

    html += `
      <div class="stage-card">
        <div class="stage-header">
          <div class="stage-title-wrap">
            <div class="stage-number">${sIdx + 1}</div>
            <div>
              <h3>${stage.title}</h3>
              <p>${stage.desc}</p>
            </div>
          </div>
          <div class="stage-stats">${stageCompleted}/${stage.milestones.length} Completed</div>
        </div>
        <div class="milestones-list">
    `;

    stage.milestones.forEach(m => {
      const isDone = !!appState.completedMilestones[m.id];
      html += `
        <div class="milestone-item ${isDone ? 'completed' : ''}" data-milestone-id="${m.id}">
          <div class="milestone-left">
            <div class="custom-checkbox" data-checkbox-id="${m.id}" title="Toggle Complete">
              ${isDone ? '✓' : ''}
            </div>
            <div class="milestone-info" data-open-modal="${m.id}">
              <h4>${m.title}</h4>
              <p>${m.desc}</p>
            </div>
          </div>
          <div class="milestone-right">
            <span class="badge badge-time">⏱ ${m.time}</span>
            <span class="badge badge-type">${m.type}</span>
            <a href="${getFileUrl(m.filePath)}" class="btn btn-sm" target="_blank" onclick="event.stopPropagation();" title="Open Material Directly">
              Open ↗
            </a>
          </div>
        </div>
      `;
    });

    html += `
        </div>
      </div>
    `;
  });

  html += `</div>`;
  container.innerHTML = html;

  // Bind checkbox events
  container.querySelectorAll('.custom-checkbox').forEach(box => {
    box.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = box.getAttribute('data-checkbox-id');
      toggleMilestone(id);
    });
  });

  // Bind item modal open events
  container.querySelectorAll('.milestone-info, .milestone-item').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target.closest('.custom-checkbox') || e.target.closest('a')) return;
      const id = el.closest('.milestone-item').getAttribute('data-milestone-id');
      openMilestoneModal(id);
    });
  });
}

function escapeHtml(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;"
  }[ch]));
}

function renderLibrary(filter = 'all', search = '') {
  const grid = document.getElementById('libraryGrid');
  if (!grid) return;
  grid.classList.remove('is-shelves');
  grid.classList.add('is-grid');

  const s = search.toLowerCase().trim();
  const filtered = CONSOLIDATED_LIBRARY.filter(item => {
    const matchFilter = filter === 'all' || item.category === filter;
    const matchTitle = item.title.toLowerCase().includes(s);
    const matchDesc = item.desc.toLowerCase().includes(s);
    const matchPath = item.formats.some(f => f.path.toLowerCase().includes(s));
    const matchSearch = !s || matchTitle || matchDesc || matchPath;
    return matchFilter && matchSearch;
  });

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align:center; padding: 4rem 1rem; color:var(--text-muted);">
        <p style="font-size:1.1rem; margin-bottom:0.5rem;">No resources found matching "${search}"</p>
        <span style="font-size:0.85rem;">Try searching for keywords like "transformers", "agent", "ebpf", or "pandas".</span>
      </div>
    `;
    return;
  }

  let html = '';
  filtered.forEach(item => {
    const pdfFmt = item.formats.find(f => f.format === 'PDF');
    const epubFmt = item.formats.find(f => f.format === 'EPUB');

    let formatBadge = '';
    if (pdfFmt && epubFmt) {
      formatBadge = `<span class="badge badge-format-dual">PDF + EPUB</span>`;
    } else if (pdfFmt) {
      formatBadge = `<span class="badge badge-format-pdf">PDF</span>`;
    } else if (epubFmt) {
      formatBadge = `<span class="badge badge-format-epub">EPUB</span>`;
    } else {
      formatBadge = `<span class="badge badge-format">${escapeHtml(item.formats[0]?.format || 'FILE')}</span>`;
    }

    const primaryObj = pdfFmt || epubFmt || item.formats[0] || {};
    const primaryPath = primaryObj.path || '';
    const primaryFilename = primaryPath.split('/').pop() || '';
    const coverUrl = primaryPath ? `/v1/nexus/cover?path=${encodeURIComponent(primaryPath)}` : '';

    let actionButtons = '';
    if (pdfFmt) {
      actionButtons += `<button type="button" class="btn-study-copilot" data-title="${escapeHtml(item.title)}" data-category="${escapeHtml(item.category)}" data-path="${escapeHtml(pdfFmt.path)}" title="Open in Split-Screen AI Study Copilot">🎓 Study</button>`;
    }
    if (pdfFmt && epubFmt) {
      actionButtons += `
        <a href="${getFileUrl(pdfFmt.path)}" class="btn-format btn-format-pdf" target="_blank" title="Open PDF">PDF ↗</a>
        <a href="${getFileUrl(epubFmt.path)}" class="btn-format btn-format-epub" target="_blank" title="Download / Open EPUB">EPUB ↗</a>
      `;
    } else if (pdfFmt) {
      actionButtons += `<a href="${getFileUrl(pdfFmt.path)}" class="btn-format btn-format-single" target="_blank">PDF ↗</a>`;
    } else if (epubFmt) {
      actionButtons += `<a href="${getFileUrl(epubFmt.path)}" class="btn-format btn-format-epub" target="_blank">EPUB ↗</a>`;
    } else if (item.formats[0]) {
      actionButtons += `<a href="${getFileUrl(item.formats[0].path)}" class="btn-format btn-format-single" target="_blank">Open ↗</a>`;
    }

    const category = (item.category || '').replace(/-/g, ' ');

    html += `
      <article class="library-card has-cover" data-id="${escapeHtml(item.id || '')}">
        <div class="library-card-cover-col">
          <div class="library-cover-wrap">
            ${coverUrl ? `<img class="library-cover-img" src="${coverUrl}" alt="${escapeHtml(item.title)}" loading="lazy" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='flex';" />` : ''}
            <div class="library-cover-fallback" style="${coverUrl ? 'display:none;' : 'display:flex;'}">
              <span class="library-cover-fallback-icon">📚</span>
              <div class="library-cover-fallback-title">${escapeHtml(item.title)}</div>
              <span class="library-cover-fallback-cat">${escapeHtml(category)}</span>
            </div>
          </div>
        </div>
        <div class="library-card-content">
          <div class="library-card-top">
            <div class="library-card-meta">
              <span class="library-card-category">${escapeHtml(category)}</span>
              ${formatBadge}
            </div>
            <h3 class="library-card-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</h3>
            <p class="library-card-desc">${escapeHtml(item.desc || '')}</p>
          </div>
          <div class="library-card-bottom">
            <code class="library-card-filename" title="${escapeHtml(primaryFilename)}">${escapeHtml(primaryFilename)}</code>
            <div class="library-card-actions">
              ${actionButtons}
            </div>
          </div>
        </div>
      </article>
    `;
  });

  grid.innerHTML = html;
}

function renderQuickstart() {
  const grid = document.getElementById('quickstartGrid');
  if (!grid) return;

  let html = '';
  QUICK_CHEATSHEETS.forEach(sheet => {
    const fullUrl = getFileUrl(sheet.path);
    html += `
      <div class="quickstart-card">
        <div class="quickstart-icon">${sheet.icon}</div>
        <div>
          <h3>${sheet.title}</h3>
        </div>
        <p>${sheet.desc}</p>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.5rem;">
          <code style="font-size:0.7rem; color:var(--text-muted); font-family:var(--font-mono);">${sheet.path.split('/').pop()}</code>
          <a href="${fullUrl}" class="btn btn-sm btn-primary" target="_blank">View Sheet ↗</a>
        </div>
      </div>
    `;
  });
  grid.innerHTML = html;
}

function updateUI() {
  try {
    const stats = getOverallStats();
    const pEl = document.getElementById('overallProgressPercent');
    const cEl = document.getElementById('completedCount');
    const rEl = document.getElementById('userRank');

    if (pEl) pEl.textContent = `${stats.percent}%`;
    if (cEl) cEl.textContent = `${stats.completed}/${stats.total}`;
    if (rEl) rEl.textContent = stats.rank;

    renderTrackPills();
    renderNextStepBanner();
    renderActiveTrack();
  } catch (err) {
    console.error('Error in updateUI:', err);
  }
}

// ==========================================================================
// 6. Modal Logic
// ==========================================================================
let currentModalMilestone = null;

function openMilestoneModal(milestoneId) {
  const all = getAllMilestones();
  const m = all.find(x => x.id === milestoneId);
  if (!m) return;

  currentModalMilestone = m;
  const isDone = !!appState.completedMilestones[m.id];

  document.getElementById('modalTitle').textContent = m.title;
  document.getElementById('modalSubtitle').textContent = m.desc;

  // Badges
  const badgesContainer = document.getElementById('modalBadges');
  badgesContainer.innerHTML = `
    <span class="badge badge-track">${m.trackTitle}</span>
    <span class="badge badge-time">⏱ ${m.time}</span>
    <span class="badge badge-type">${m.type}</span>
  `;

  // Key points
  const pointsList = document.getElementById('modalKeyPoints');
  pointsList.innerHTML = m.keyPoints.map(p => `<li>${p}</li>`).join('');

  // Primary file path
  const fullUrl = getFileUrl(m.filePath);
  document.getElementById('modalFilePath').textContent = m.filePath;

  const openBtn = document.getElementById('modalOpenFileBtn');
  openBtn.href = fullUrl;

  const copyBtn = document.getElementById('modalCopyPathBtn');
  copyBtn.onclick = () => {
    navigator.clipboard.writeText(m.filePath);
    copyBtn.textContent = 'Copied!';
    setTimeout(() => { copyBtn.textContent = 'Copy Path'; }, 2000);
  };

  // Related files
  const relatedSec = document.getElementById('modalSecondarySection');
  const relatedList = document.getElementById('modalRelatedFiles');
  if (m.related && m.related.length > 0) {
    relatedSec.style.display = 'block';
    relatedList.innerHTML = m.related.map(r => `
      <a href="${getFileUrl(r.path)}" class="related-file-pill" target="_blank">
        <span>📖 ${r.title}</span>
        <span class="badge badge-format">Open ↗</span>
      </a>
    `).join('');
  } else {
    relatedSec.style.display = 'none';
  }

  // Toggle button
  const toggleBtn = document.getElementById('modalToggleDoneBtn');
  toggleBtn.textContent = isDone ? '✕ Mark as Incomplete' : '✓ Mark as Completed';
  toggleBtn.className = isDone ? 'btn btn-secondary' : 'btn btn-primary';
  toggleBtn.onclick = () => {
    toggleMilestone(m.id);
    openMilestoneModal(m.id); // refresh modal view
  };

  document.getElementById('modalBackdrop').classList.add('open');
}

function closeModal() {
  document.getElementById('modalBackdrop').classList.remove('open');
  currentModalMilestone = null;
}

// ==========================================================================
// 7. Event Handlers & Initialization
// ==========================================================================

// ==========================================================================
// Phase 2: Active Study Mode Controller (PDF Viewer + AI Study Assistant)
// ==========================================================================
const studyState = {
  active: false,
  bookTitle: '',
  bookCategory: '',
  pdfPath: '',
  conversationId: null,
  sending: false
};

function formatStudyMarkdown(text) {
  if (!text) return '';
  let escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks: ```lang ... ```
  escaped = escaped.replace(/```([a-zA-Z0-9_-]*)\n?([\s\S]*?)```/g, (m, lang, code) => {
    const l = lang ? lang.trim() : 'code';
    return `<div class="study-code-wrapper"><div class="study-code-header"><span>${l}</span><button type="button" class="copy-code-btn" onclick="navigator.clipboard.writeText(this.closest('.study-code-wrapper').querySelector('code').innerText); this.textContent='Copied!'; setTimeout(()=>this.textContent='Copy', 1500);">Copy</button></div><pre><code>${code.trim()}</code></pre></div>`;
  });

  // Headers
  escaped = escaped.replace(/^### (.*$)/gim, '<h4>$1</h4>');
  escaped = escaped.replace(/^## (.*$)/gim, '<h3>$1</h3>');
  escaped = escaped.replace(/^# (.*$)/gim, '<h2>$1</h2>');

  // Blockquotes
  escaped = escaped.replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>');

  // Inline code: `code`
  escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Bold: **text**
  escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Italics: *text*
  escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Bullet points
  escaped = escaped.replace(/(?:^|\n)[*-] (.*?)(?=(?:\n[*-] )|\n\n|$)/g, '<li>$1</li>');
  escaped = escaped.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');

  // Line breaks
  escaped = escaped.replace(/\n\n+/g, '<br><br>');
  escaped = escaped.replace(/\n/g, '<br>');
  return escaped;
}

async function getOrCreateStudyConversation() {
  if (studyState.conversationId) return studyState.conversationId;
  try {
    let authHeader = { 'Content-Type': 'application/json' };
    if (typeof labAuthHeaders === 'function') {
      authHeader = labAuthHeaders();
    }
    const res = await fetch('/v1/conversations', {
      method: 'POST',
      headers: authHeader,
      body: JSON.stringify({
        agent: 'study',
        title: `Study: ${studyState.bookTitle}`
      })
    });
    if (!res.ok) throw new Error('Failed to create study session');
    const data = await res.json();
    studyState.conversationId = data.id;
    return data.id;
  } catch (err) {
    console.error('Study conversation init error:', err);
    return null;
  }
}

function openStudyMode(title, category, rawPath) {
  let cleanRelPath = decodeURIComponent(rawPath || '');
  cleanRelPath = cleanRelPath.replace(/^[a-z]+:\/\/[^\/]+/i, '');
  cleanRelPath = cleanRelPath.replace(/^\/?nexus\//i, '');
  cleanRelPath = cleanRelPath.replace(/^\//, '');

  studyState.active = true;
  studyState.bookTitle = title || 'Reference Material';
  studyState.bookCategory = category || 'AI';
  studyState.relPath = cleanRelPath;
  studyState.pdfPath = cleanRelPath;
  studyState.conversationId = null;

  const workspace = document.getElementById('studyWorkspace');
  const titleEl = document.getElementById('studyBookTitle');
  const badgeEl = document.getElementById('studyBadgeCategory');
  const extLink = document.getElementById('studyExternalLink');
  const pdfFrame = document.getElementById('studyPdfFrame');
  const welcomeBook = document.getElementById('studyWelcomeBook');
  const msgs = document.getElementById('studyMessages');

  if (titleEl) titleEl.textContent = title;
  if (badgeEl) badgeEl.textContent = (category || 'AI').replace(/-/g, ' ');
  if (extLink) extLink.href = getFileUrl(cleanRelPath);
  if (welcomeBook) welcomeBook.textContent = title;

  // Reset thread to welcome message
  if (msgs) {
    msgs.innerHTML = `
      <div class="study-welcome-msg" id="studyWelcomeMsg">
        <div class="study-welcome-avatar">🎓</div>
        <h4>Welcome to Active Study Mode</h4>
        <p>I'm your AI study partner for <strong>${escapeHtml(title)}</strong>. Read through the document on the left, and use the quick buttons above or ask me anything below.</p>
      </div>
    `;
  }

  // Load PDF into frame
  if (pdfFrame) {
    pdfFrame.src = getFileUrl(pdfPath);
  }

  if (workspace) {
    workspace.classList.add('active');
  }

  // Pre-initialize conversation in background
  getOrCreateStudyConversation();

  setTimeout(() => {
    const input = document.getElementById('studyInput');
    if (input) input.focus();
  }, 200);
}

function closeStudyMode() {
  const workspace = document.getElementById('studyWorkspace');
  const pdfFrame = document.getElementById('studyPdfFrame');
  if (workspace) workspace.classList.remove('active');
  if (pdfFrame) pdfFrame.src = 'about:blank';
  studyState.active = false;
}

async function sendStudyMessage(text) {
  const cleanText = (text || '').trim();
  if (!cleanText || studyState.sending) return;

  const msgs = document.getElementById('studyMessages');
  const input = document.getElementById('studyInput');
  const sendBtn = document.getElementById('studySendBtn');
  const modelSelect = document.getElementById('studyModelSelect');

  // Parse model choice
  let backend = 'ollama';
  let model = 'qwen3.6:35b-a3b';
  if (modelSelect && modelSelect.value) {
    const parts = modelSelect.value.split('::');
    backend = parts[0] || 'openai';
    model = parts[1] || 'gpt-4o-mini';
  }

  studyState.sending = true;
  if (sendBtn) sendBtn.disabled = true;
  if (input) input.value = '';

  // Append user bubble
  const userEl = document.createElement('div');
  userEl.className = 'study-bubble user';
  userEl.textContent = cleanText;
  msgs.appendChild(userEl);

  // Append assistant placeholder bubble
  const asstEl = document.createElement('div');
  asstEl.className = 'study-bubble assistant';
  asstEl.innerHTML = '<span style="color:var(--text-muted)">Thinking…</span>';
  msgs.appendChild(asstEl);
  msgs.scrollTop = msgs.scrollHeight;

  try {
    const convId = await getOrCreateStudyConversation();
    if (!convId) throw new Error('Could not establish study conversation');

    // Contextualized study prompt including book name and file path for Qdrant RAG extraction
    const promptPayload = `[Study Context: Book: "${studyState.bookTitle}", Path: "${studyState.relPath}"]\n\n${cleanText}`;

    let authHeader = { 'Content-Type': 'application/json' };
    if (typeof labAuthHeaders === 'function') {
      authHeader = labAuthHeaders();
    }

    const res = await fetch(`/v1/conversations/${convId}/messages/stream`, {
      method: 'POST',
      headers: authHeader,
      body: JSON.stringify({
        content: promptPayload,
        role: 'user',
        reply: true,
        backend: backend,
        model: model
      })
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `Server responded with ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    let accumulated = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const parts = buf.split('\n\n');
      buf = parts.pop() || '';

      for (const block of parts) {
        const line = block.split('\n').find(l => l.startsWith('data: '));
        if (!line) continue;
        let ev;
        try { ev = JSON.parse(line.slice(6)); } catch { continue; }

        if (ev.event === 'token') {
          accumulated += (ev.text || '');
          asstEl.innerHTML = formatStudyMarkdown(accumulated);
          msgs.scrollTop = msgs.scrollHeight;
        } else if (ev.event === 'replace') {
          accumulated = (ev.text || '');
          asstEl.innerHTML = formatStudyMarkdown(accumulated);
          msgs.scrollTop = msgs.scrollHeight;
        } else if (ev.event === 'error') {
          asstEl.innerHTML = `<span style="color:#f87171">Error: ${ev.error || 'Request failed'}</span>`;
        }
      }
    }

    if (!accumulated) {
      asstEl.innerHTML = '<span style="color:var(--text-muted)">Response complete.</span>';
    }
  } catch (err) {
    console.error('Study chat error:', err);
    asstEl.innerHTML = `<span style="color:#f87171">Study Copilot error: ${err.message || 'Could not connect to model'}</span>`;
  } finally {
    studyState.sending = false;
    if (sendBtn) sendBtn.disabled = false;
    if (input) input.focus();
  }
}

function initStudyWorkspace() {
  const closeBtn = document.getElementById('studyCloseBtn');
  if (closeBtn) closeBtn.addEventListener('click', closeStudyMode);

  const clearBtn = document.getElementById('studyClearChatBtn');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      studyState.conversationId = null;
      const msgs = document.getElementById('studyMessages');
      if (msgs) {
        msgs.innerHTML = `
          <div class="study-welcome-msg" id="studyWelcomeMsg">
            <div class="study-welcome-avatar">🎓</div>
            <h4>Chat Cleared</h4>
            <p>Ready for a fresh topic on <strong>${studyState.bookTitle || 'this book'}</strong>. Ask a question or use a chip above.</p>
          </div>
        `;
      }
    });
  }

  // Quick Chips
  document.querySelectorAll('.study-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      if (prompt) sendStudyMessage(prompt);
    });
  });

  // Composer
  const sendBtn = document.getElementById('studySendBtn');
  const input = document.getElementById('studyInput');

  if (sendBtn && input) {
    sendBtn.addEventListener('click', () => {
      sendStudyMessage(input.value);
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendStudyMessage(input.value);
      }
    });
  }

  // Escape key closes study mode
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && studyState.active) {
      closeStudyMode();
    }
  });

  // Bind study mode to study button and covers in Library
  const grid = document.getElementById('libraryGrid');
  if (grid) {
    grid.addEventListener('click', (e) => {
      const studyBtn = e.target.closest('.btn-study-copilot');
      if (studyBtn) {
        e.preventDefault();
        const title = studyBtn.getAttribute('data-title') || 'Reference Book';
        const cat = studyBtn.getAttribute('data-category') || 'AI';
        const path = studyBtn.getAttribute('data-path') || '';
        openStudyMode(title, cat, path);
        return;
      }
      const coverWrap = e.target.closest('.library-cover-wrap');
      if (coverWrap) {
        const card = coverWrap.closest('.library-card');
        const sBtn = card ? card.querySelector('.btn-study-copilot') : null;
        if (sBtn) {
          e.preventDefault();
          const title = sBtn.getAttribute('data-title') || 'Reference Book';
          const cat = sBtn.getAttribute('data-category') || 'AI';
          const path = sBtn.getAttribute('data-path') || '';
          openStudyMode(title, cat, path);
          return;
        }
      }
    });
  }
}


function initApp() {
  try {
    loadState();

    // Tab switching
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-view').forEach(v => v.classList.remove('active'));

        tab.classList.add('active');
        const tabName = tab.getAttribute('data-tab');
        appState.activeTab = tabName;

        if (tabName === 'journey') {
          const v = document.getElementById('viewJourney');
          if (v) v.classList.add('active');
          renderActiveTrack();
        } else if (tabName === 'library') {
          const v = document.getElementById('viewLibrary');
          if (v) v.classList.add('active');
          renderLibrary();
        } else if (tabName === 'quickstart') {
          const v = document.getElementById('viewQuickstart');
          if (v) v.classList.add('active');
          renderQuickstart();
    initStudyWorkspace();
        }
      });
    });

    // Track switching
    document.querySelectorAll('.track-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.track-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        appState.activeTrack = btn.getAttribute('data-track');
        renderActiveTrack();
        renderNextStepBanner();
      });
    });

    // Library search and filter
    const searchInput = document.getElementById('librarySearchInput');
    const clearBtn = document.getElementById('clearSearchBtn');
    let currentFilter = 'all';

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const val = e.target.value;
        if (clearBtn) clearBtn.style.display = val ? 'block' : 'none';
        renderLibrary(currentFilter, val);
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (searchInput) searchInput.value = '';
        clearBtn.style.display = 'none';
        renderLibrary(currentFilter, '');
      });
    }

    document.querySelectorAll('.filter-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        currentFilter = pill.getAttribute('data-filter');
        const sVal = searchInput ? searchInput.value : '';
        renderLibrary(currentFilter, sVal);
      });
    });

    // Modal close events
    const closeBtn = document.getElementById('modalCloseBtn');
    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    const backdrop = document.getElementById('modalBackdrop');
    if (backdrop) {
      backdrop.addEventListener('click', (e) => {
        if (e.target.id === 'modalBackdrop') closeModal();
      });
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModal();
    });

    // Reset button
    const resetBtn = document.getElementById('resetProgressBtn');
    if (resetBtn) resetBtn.addEventListener('click', resetProgress);

    // Initial render
    updateUI();
    renderQuickstart();
    initStudyWorkspace();
    console.log('Nexus App Initialized Successfully!');
  } catch (err) {
    console.error('Initialization error:', err);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
