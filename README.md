# AutoLlama 🦙

*An intelligent, end-to-end knowledge automation system that transforms spontaneous ideas into searchable AI knowledge bases*

AutoLlama is a comprehensive automation pipeline that captures your ideas through voice or text, researches them using Perplexity AI, and automatically builds searchable knowledge bases in OpenWebUI. Inspired by Matt Williams's innovative work on MPC servers and automated research workflows, AutoLlama creates a seamless bridge from thought to searchable knowledge.

## 🌟 The Complete Workflow

AutoLlama implements a sophisticated automation chain that transforms fleeting ideas into persistent, searchable knowledge:

### 1. **Idea Capture** 📱
- Speak or type a short phrase into your iOS device
- Custom iOS Shortcut triggers the automation pipeline
- No need to open apps or navigate interfaces

### 2. **Intelligent Research** 🔍
- iOS Shortcut calls a webhook to Perplexity AI
- Carefully crafted prompts guide comprehensive research
- Perplexity generates detailed analysis with citations and source links

### 3. **Knowledge Documentation** 📝
- Perplexity automatically calls webhook to Obsidian
- Creates new note with research findings and citations
- Includes curated list of source URLs for further processing

### 4. **Content Acquisition** 🕷️
- Source URLs automatically sent to AutoLlama API
- Advanced web scraping extracts clean, structured text
- PDF documents automatically converted and processed
- Content optimized for RAG (Retrieval-Augmented Generation) systems

### 5. **Knowledge Base Integration** 🧠
- Processed content automatically loaded into OpenWebUI
- Creates searchable knowledge collections using OpenWebUI's built-in vector database
- Embeddings generated for semantic search capabilities

### 6. **Intelligent Retrieval** 💬
- Use `#` command in OpenWebUI to access knowledge collections
- Natural language queries across all processed research
- Contextual answers drawn from your curated knowledge base

## ✨ Key Features

### **Seamless Automation**
- **Voice-to-Knowledge Pipeline**: From spoken idea to searchable knowledge base
- **Zero Manual Intervention**: Fully automated research and processing
- **iOS Integration**: Native Shortcuts app integration for mobile convenience
- **n8n Workflow Orchestration**: Professional automation with visual workflow editor

### **Intelligent Processing**
- **Advanced Web Scraping**: Clean text extraction with boilerplate removal
- **PDF Processing**: Intelligent conversion and text extraction
- **Quality Filtering**: Automatic content validation and duplicate prevention
- **Citation Preservation**: Maintains research provenance and source tracking

### **Professional Infrastructure**
- **Docker Orchestration**: Production-ready containerized deployment
- **OpenWebUI Integration**: Seamless RAG knowledge base creation
- **Built-in Vector Database**: Uses OpenWebUI's native vector storage
- **Webhook Architecture**: Real-time automation triggers

### **Research-Grade Output**
- **Perplexity AI Research**: Professional-quality research with citations
- **Obsidian Documentation**: Structured note creation with source links
- **Knowledge Graphs**: Interconnected information discovery
- **Natural Language Querying**: Conversational access to research

## 🏗️ System Architecture

```
[iOS Device] → [Shortcut] → [Perplexity Webhook] → [Research]
                                    ↓
[Obsidian Notes] ← [Webhook] ← [Citations & URLs]
                                    ↓
[AutoLlama API] ← [Source URLs] → [Web Scraping]
                                    ↓
[PDF Processing] → [Content Cleaning] → [OpenWebUI]
                                    ↓
[OpenWebUI Vector DB] ← [Knowledge Base] ← [Vector Embeddings]
                                    ↓
[# Search] → [Natural Language Queries] → [Contextual Answers]
```

> **⚠️ Important Database Note**: AutoLlama uses OpenWebUI's built-in vector database. You do NOT need to set up ChromaDB or any external vector database. OpenWebUI handles all vector storage and semantic search internally.

## 🛠️ Technology Stack

- **Backend**: Python Flask API with advanced web scraping
- **Vector Database**: OpenWebUI's built-in vector storage (no external DB required)
- **RAG Interface**: OpenWebUI for natural language interactions
- **Automation**: n8n workflow orchestration
- **Research Engine**: Perplexity AI for intelligent research
- **Documentation**: Obsidian for structured knowledge management
- **Mobile Integration**: iOS Shortcuts for voice/text capture
- **Infrastructure**: Docker Compose with SSL/TLS termination

## 📋 Prerequisites

- **iOS Device**: For Shortcuts app integration
- **Perplexity AI Account**: For research automation
- **Obsidian**: For research documentation
- **n8n Instance**: For workflow orchestration (see included workflow)
- **Linux System**: Tested on Debian/Ubuntu
- **Docker & Docker Compose**: For container orchestration
- **Minimum 4GB RAM**: For optimal performance

> **💡 Database Setup**: No external vector database setup required! OpenWebUI includes its own vector storage system.

## 🚀 Quick Start

### 1. **Clone Repository**
```bash
git clone https://github.com/snedea/autollama.git
cd autollama
```

### 2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your settings:
# - PERPLEXITY_API_KEY
# - OBSIDIAN_WEBHOOK_URL
# - OPEN_WEBUI_API_KEY
```

### 3. **Deploy Infrastructure**
```bash
docker compose up -d
```

### 4. **Setup n8n Workflow**
- Import the included `autollama-workflow.json` into your n8n instance
- Configure webhook endpoints and API credentials
- Test the complete automation pipeline

### 5. **Configure iOS Shortcut**
- Install the provided iOS Shortcut
- Configure webhook URL to your n8n instance
- Test voice/text idea capture

## 📱 iOS Shortcut Configuration

The included iOS Shortcut enables seamless idea capture:

1. **Voice Input**: Speak your idea naturally
2. **Text Input**: Type concepts quickly
3. **Webhook Trigger**: Automatically calls your automation pipeline
4. **Background Processing**: Continue using your device while research happens

*Download the pre-configured shortcut from the `/shortcuts` directory*

## 🔄 n8n Workflow Integration

AutoLlama includes a comprehensive n8n workflow that orchestrates the complete automation pipeline:

![AutoLlama n8n Workflow](https://raw.githubusercontent.com/snedea/autollama/refs/heads/main/Idea%20to%20Research%20Workflow.png)

### Workflow Components:
- **Webhook Reception**: Receives ideas from iOS Shortcut
- **HTTP Request to Perplexity**: Triggers AI research with optimized prompts  
- **Code Processing**: Parses research results and extracts source URLs
- **Send to Obsidian**: Creates structured research notes with citations
- **Parse and Extract URLs**: Processes source links for content scraping
- **Send to RAG**: Forwards URLs to AutoLlama for knowledge base creation

### Installation:
1. **Download the workflow**: [Idea_to_Research.json](https://github.com/snedea/autollama/blob/d06f815c91121950075eff875d18967b127408fe/Idea_to_Research.json)
2. Import into your n8n instance: `Settings → Import from file`
3. Configure all credential nodes with your API keys
4. Test webhook endpoints and activate the workflow

**[📥 Download n8n Workflow](https://github.com/snedea/autollama/blob/d06f815c91121950075eff875d18967b127408fe/Idea_to_Research.json)**

## 🔧 Configuration

### **Environment Variables**
```bash
# Research Integration
PERPLEXITY_API_KEY=your_perplexity_key
OBSIDIAN_WEBHOOK_URL=your_obsidian_webhook

# AutoLlama Core
OPEN_WEBUI_API_KEY=your_openwebui_key
WEBHOOK_SECRET=your_security_secret

# Optional: Custom Domain
DOMAIN=your-domain.com
CLOUDFLARE_API_TOKEN=your_cloudflare_token
```

### **Customization Options**
- **Research Prompts**: Modify Perplexity prompts in n8n workflow
- **Content Filtering**: Adjust quality thresholds in `daily_ingest.py`
- **Processing Schedule**: Configure automation timing
- **Knowledge Collections**: Customize organization and naming

## 📊 Usage Examples

### **Voice Research Command**
*"Research the latest developments in quantum computing applications"*

**Result**: Complete research report in Obsidian + searchable knowledge base in OpenWebUI

### **Quick Concept Exploration**
*"Social impact of remote work trends"*

**Result**: Curated research with citations + conversational access via `#` search

### **Technical Deep-Dive**
*"Best practices for microservices architecture in 2024"*

**Result**: Technical documentation + expert-level Q&A capability

## 🔍 Querying Your Knowledge

Access your research through OpenWebUI's natural language interface:

```
# Activate knowledge search
Type: #

# Example queries
"What did my research find about quantum computing applications?"
"Summarize the key points about remote work social impact"
"What are the main microservices best practices from my research?"
```

## 🎯 Inspiration & Acknowledgments

AutoLlama was inspired by **Matt Williams's** groundbreaking work on:
- MPC (Multi-Protocol Chat) server implementations
- Automated research workflows
- Perplexity-to-Obsidian automation pipelines

This project extends those concepts into a production-ready, end-to-end knowledge automation system.

**Special Thanks**:
- **Matt Williams** for the original automation concepts
- **OpenWebUI** team for the excellent RAG interface
- **Perplexity AI** for research capabilities
- **n8n** community for workflow automation tools

## 🤝 Contributing

We welcome contributions to AutoLlama:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/snedea/autollama/issues)
- **Documentation**: See included guides and workflow files
- **Community**: Join discussions for questions and feature requests

---

**Transform your ideas into intelligent, searchable knowledge with AutoLlama** 🦙✨
