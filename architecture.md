# Architecture Technique - EpiChat

Voici le schéma d'architecture de l'application EpiChat, généré en format Mermaid.

```mermaid
graph TD
    %% Définition des Styles
    classDef client fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef frontend fill:#e0f2f1,stroke:#00695c,stroke-width:2px;
    classDef backend fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef ai fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef external fill:#eceff1,stroke:#455a64,stroke-width:2px,stroke-dasharray: 5 5;

    %% Nœud Utilisateur
    User((Utilisateur)):::client
    
    %% Frontend
    subgraph Client_Side [Côté Client]
        Browser[Navigateur Web]:::client
        FE[Frontend (React + Vite + Tailwind)\nPort: 5173]:::frontend
    end

    %% Backend
    subgraph Server_Side [Serveur Backend]
        BE[Backend API (FastAPI + Python)\nPort: 8000]:::backend
        Logic[Logique Métier\n(Regex, Parsing, Gestion Context)]:::backend
        Scraper[Script Scrapy (Subprocess)\n/MCP_Server/epitech_scraper]:::backend
    end

    %% AI / LLM
    subgraph AI_Engine [Moteur IA Local]
        Ollama[Ollama (Llama 3.1)\nPort: 11434]:::ai
    end

    %% Services Externes
    subgraph External_Services [Services Externes]
        EpitechWeb[Site Web Epitech\n(Actualités)]:::external
        GeoGouv[API Gouv France\n(Géocodage)]:::external
        OSM[OpenStreetMap Nominatim\n(Géocodage Monde)]:::external
    end

    %% Relations
    User -->|Interaction| Browser
    Browser -->|Rendu| FE
    FE -->|HTTP POST /chat| BE
    
    BE --> Logic
    
    %% Flux Logic
    Logic -->|Si besoins Actus| Scraper
    Logic -->|Si besoins Localisation| GeoGouv
    Logic -->|Si besoins Localisation (Monde)| OSM
    
    %% Flux Scraper
    Scraper -->|HTTP GET| EpitechWeb
    Scraper -.->|Retourne JSON| Logic

    %% Flux LLM
    Logic -->|Prompt + Contexte Enrichi| Ollama
    Ollama -.->|Réponse Générée| Logic

    %% Retour
    Logic -.->|Réponse JSON| FE
```
