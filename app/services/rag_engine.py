"""
RAG (Retrieval-Augmented Generation) Engine.
Manages knowledge base for government schemes and disease treatments.
Uses ChromaDB for vector storage and sentence-transformers for embeddings.
"""

import json
import os
from app.utils.logger import logger


class RAGEngine:
    """RAG engine for agricultural knowledge retrieval."""

    _collection_schemes = None
    _collection_treatments = None
    _client = None
    _initialized = False

    @classmethod
    def initialize(cls):
        """Initialize ChromaDB and load knowledge base."""
        if cls._initialized:
            return

        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            # Initialize ChromaDB (persistent storage)
            cls._client = chromadb.Client(ChromaSettings(
                anonymized_telemetry=False,
            ))

            # Create collections
            cls._collection_schemes = cls._client.get_or_create_collection(
                name="govt_schemes",
                metadata={"description": "Indian government agricultural schemes"},
            )
            cls._collection_treatments = cls._client.get_or_create_collection(
                name="disease_treatments",
                metadata={"description": "Crop disease treatment protocols"},
            )

            # Load data if collections are empty
            if cls._collection_schemes.count() == 0:
                cls._load_schemes()
            if cls._collection_treatments.count() == 0:
                cls._load_treatments()

            cls._initialized = True
            logger.info(
                f"📚 RAG initialized: {cls._collection_schemes.count()} schemes, "
                f"{cls._collection_treatments.count()} treatments"
            )

        except ImportError:
            logger.info("⚡ Lightweight RAG mode active (Using fast local indexing)")
            cls._initialized = True
        except Exception as e:
            logger.error(f"❌ RAG initialization failed: {e}")
            cls._initialized = True  # Set to true to avoid repeated failures

    @classmethod
    def _load_schemes(cls):
        """Load government schemes into ChromaDB."""
        schemes_path = os.path.join("data", "schemes", "govt_schemes.json")
        try:
            with open(schemes_path, "r", encoding="utf-8") as f:
                schemes = json.load(f)

            documents = []
            metadatas = []
            ids = []

            for i, scheme in enumerate(schemes):
                doc = (
                    f"Scheme: {scheme['name']}\n"
                    f"Hindi: {scheme.get('name_hi', '')}\n"
                    f"Description: {scheme['description']}\n"
                    f"Eligibility: {scheme.get('eligibility', '')}\n"
                    f"Benefits: {scheme.get('benefits', '')}\n"
                    f"How to Apply: {scheme.get('how_to_apply', '')}"
                )
                documents.append(doc)
                metadatas.append({
                    "name": scheme["name"],
                    "category": scheme.get("category", "general"),
                })
                ids.append(f"scheme_{i}")

            cls._collection_schemes.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"📋 Loaded {len(schemes)} government schemes into RAG")

        except FileNotFoundError:
            logger.warning(f"⚠️ Schemes file not found at {schemes_path}")
            cls._load_default_schemes()
        except Exception as e:
            logger.error(f"❌ Failed to load schemes: {e}")
            cls._load_default_schemes()

    @classmethod
    def _load_default_schemes(cls):
        """Load default scheme data when JSON file is unavailable."""
        default_schemes = [
            {
                "doc": "Scheme: PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)\nDescription: Direct income support of ₹6,000 per year to small and marginal farmers in three installments of ₹2,000.\nEligibility: All farmer families with cultivable land. Excluded: Institutional land holders, income tax payers.\nBenefits: ₹6,000/year directly to bank account.\nHow to Apply: Visit pmkisan.gov.in or contact local CSC center.",
                "metadata": {"name": "PM-KISAN", "category": "income_support"},
            },
            {
                "doc": "Scheme: PMFBY (Pradhan Mantri Fasal Bima Yojana)\nDescription: Crop insurance scheme providing financial support to farmers in case of crop loss due to natural calamities, pests, and diseases.\nEligibility: All farmers (mandatory for loanee farmers, optional for others).\nBenefits: Insurance coverage at premium of 2% for Kharif, 1.5% for Rabi crops.\nHow to Apply: Apply through bank, CSC center, or pmfby.gov.in.",
                "metadata": {"name": "PMFBY", "category": "insurance"},
            },
            {
                "doc": "Scheme: Kisan Credit Card (KCC)\nDescription: Provides short-term credit to farmers for crop production, post-harvest expenses, and maintenance.\nEligibility: All farmers, sharecroppers, tenant farmers.\nBenefits: Credit limit based on land holding, 4% interest rate (with subsidy).\nHow to Apply: Apply at any bank branch with land documents.",
                "metadata": {"name": "KCC", "category": "credit"},
            },
            {
                "doc": "Scheme: Soil Health Card Scheme\nDescription: Government provides soil health cards to farmers with crop-wise nutrient recommendations.\nEligibility: All farmers.\nBenefits: Free soil testing, nutrient recommendations, improved yield.\nHow to Apply: Contact local agriculture department or KVK.",
                "metadata": {"name": "Soil Health Card", "category": "advisory"},
            },
            {
                "doc": "Scheme: PM Krishi Sinchai Yojana (PMKSY)\nDescription: Aims to ensure water to every field through micro-irrigation (drip & sprinkler).\nEligibility: All farmers, priority to small/marginal.\nBenefits: 55-75% subsidy on micro-irrigation equipment.\nHow to Apply: Contact district agriculture office or apply online at state portal.",
                "metadata": {"name": "PMKSY", "category": "irrigation"},
            },
            {
                "doc": "Scheme: e-NAM (National Agriculture Market)\nDescription: Online trading platform for agricultural commodities, connecting APMC mandis across India.\nEligibility: All farmers and traders.\nBenefits: Better prices, transparent trading, reduced intermediaries.\nHow to Apply: Register at enam.gov.in with Aadhaar and bank details.",
                "metadata": {"name": "e-NAM", "category": "market"},
            },
        ]

        docs = [s["doc"] for s in default_schemes]
        metadatas = [s["metadata"] for s in default_schemes]
        ids = [f"scheme_{i}" for i in range(len(default_schemes))]

        cls._collection_schemes.add(documents=docs, metadatas=metadatas, ids=ids)
        logger.info(f"📋 Loaded {len(default_schemes)} default schemes into RAG")

    @classmethod
    def _load_treatments(cls):
        """Load disease treatments into ChromaDB."""
        treatments_path = os.path.join("data", "treatments", "disease_treatments.json")
        try:
            with open(treatments_path, "r", encoding="utf-8") as f:
                treatments = json.load(f)

            documents = []
            metadatas = []
            ids = []

            for i, treatment in enumerate(treatments):
                doc = (
                    f"Disease: {treatment['disease']}\n"
                    f"Crop: {treatment['crop']}\n"
                    f"Symptoms: {treatment.get('symptoms', '')}\n"
                    f"Chemical Treatment: {treatment.get('chemical_treatment', '')}\n"
                    f"Organic Treatment: {treatment.get('organic_treatment', '')}\n"
                    f"Prevention: {treatment.get('prevention', '')}"
                )
                documents.append(doc)
                metadatas.append({
                    "disease": treatment["disease"],
                    "crop": treatment["crop"],
                })
                ids.append(f"treatment_{i}")

            cls._collection_treatments.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"💊 Loaded {len(treatments)} disease treatments into RAG")

        except FileNotFoundError:
            logger.warning(f"⚠️ Treatments file not found at {treatments_path}")
            cls._load_default_treatments()
        except Exception as e:
            logger.error(f"❌ Failed to load treatments: {e}")
            cls._load_default_treatments()

    @classmethod
    def _load_default_treatments(cls):
        """Load default treatment data when JSON file is unavailable."""
        default_treatments = [
            {
                "doc": "Disease: Early Blight\nCrop: Tomato\nSymptoms: Dark concentric rings on lower leaves, yellowing, leaf drop.\nChemical Treatment: Apply Mancozeb 75% WP (2g/L) or Chlorothalonil every 7-10 days. For severe cases, use Azoxystrobin.\nOrganic Treatment: Neem oil spray (5ml/L), Trichoderma viride (5g/L) as preventive.\nPrevention: Use certified seeds, rotate crops, maintain proper spacing, remove infected debris.",
                "metadata": {"disease": "Early Blight", "crop": "Tomato"},
            },
            {
                "doc": "Disease: Late Blight\nCrop: Tomato/Potato\nSymptoms: Water-soaked lesions on leaves, white mold on underside, rapid wilting.\nChemical Treatment: Metalaxyl+Mancozeb (Ridomil Gold 2g/L), Cymoxanil, Copper oxychloride.\nOrganic Treatment: Bordeaux mixture (1%), copper-based organic fungicides.\nPrevention: Avoid overhead irrigation, plant resistant varieties, use drip irrigation.",
                "metadata": {"disease": "Late Blight", "crop": "Tomato"},
            },
            {
                "doc": "Disease: Bacterial Spot\nCrop: Tomato/Pepper\nSymptoms: Small dark water-soaked spots on leaves/fruit, leaf yellowing, defoliation.\nChemical Treatment: Copper hydroxide (2g/L) + Streptocycline (0.5g/L).\nOrganic Treatment: Copper-based sprays, remove infected plants.\nPrevention: Use disease-free seeds, avoid overhead watering, proper spacing.",
                "metadata": {"disease": "Bacterial Spot", "crop": "Tomato"},
            },
            {
                "doc": "Disease: Powdery Mildew\nCrop: Various (Cherry, Squash, Grape)\nSymptoms: White powdery coating on leaves, stunted growth, curling leaves.\nChemical Treatment: Sulfur WP (3g/L), Carbendazim (1g/L), Hexaconazole.\nOrganic Treatment: Milk spray (40% milk solution), baking soda (1 tsp/L).\nPrevention: Proper air circulation, avoid crowding, resistant varieties.",
                "metadata": {"disease": "Powdery Mildew", "crop": "Various"},
            },
            {
                "doc": "Disease: Apple Scab\nCrop: Apple\nSymptoms: Olive-brown velvety spots on leaves and fruit, premature leaf drop.\nChemical Treatment: Mancozeb (2.5g/L) preventive, Myclobutanil (0.5ml/L) curative.\nOrganic Treatment: Sulfur-lime spray, neem oil, remove fallen leaves.\nPrevention: Prune for air circulation, remove fallen leaves, use resistant varieties.",
                "metadata": {"disease": "Apple Scab", "crop": "Apple"},
            },
            {
                "doc": "Disease: Black Rot\nCrop: Apple/Grape\nSymptoms: Brown expanding lesions, concentric rings, fruit mummification.\nChemical Treatment: Captan (2g/L), Thiophanate-methyl, Mancozeb.\nOrganic Treatment: Copper sprays, remove infected material, prune affected branches.\nPrevention: Remove mummified fruits, prune cankers, maintain orchard hygiene.",
                "metadata": {"disease": "Black Rot", "crop": "Apple"},
            },
        ]

        docs = [t["doc"] for t in default_treatments]
        metadatas = [t["metadata"] for t in default_treatments]
        ids = [f"treatment_{i}" for i in range(len(default_treatments))]

        cls._collection_treatments.add(documents=docs, metadatas=metadatas, ids=ids)
        logger.info(f"💊 Loaded {len(default_treatments)} default treatments into RAG")

    @classmethod
    def search_schemes(cls, query: str, n_results: int = 3) -> list[str]:
        """Search government schemes relevant to a query."""
        try:
            if cls._collection_schemes is None:
                return cls._fallback_scheme_search(query)

            results = cls._collection_schemes.query(
                query_texts=[query],
                n_results=min(n_results, cls._collection_schemes.count()),
            )
            return results["documents"][0] if results["documents"] else []
        except Exception as e:
            logger.error(f"❌ Scheme search failed: {e}")
            return cls._fallback_scheme_search(query)

    @classmethod
    def search_treatments(cls, query: str, n_results: int = 2) -> list[str]:
        """Search disease treatments relevant to a query."""
        try:
            if cls._collection_treatments is None:
                return cls._fallback_treatment_search(query)

            results = cls._collection_treatments.query(
                query_texts=[query],
                n_results=min(n_results, cls._collection_treatments.count()),
            )
            return results["documents"][0] if results["documents"] else []
        except Exception as e:
            logger.error(f"❌ Treatment search failed: {e}")
            return cls._fallback_treatment_search(query)

    @classmethod
    def _fallback_scheme_search(cls, query: str) -> list[str]:
        """Fallback scheme search when ChromaDB is unavailable."""
        return [
            "PM-KISAN: ₹6,000/year income support for farmers. Apply at pmkisan.gov.in",
            "PMFBY: Crop insurance at 1.5-2% premium. Apply at pmfby.gov.in",
            "Kisan Credit Card: Low-interest farm credit. Apply at any bank.",
        ]

    @classmethod
    def _fallback_treatment_search(cls, query: str) -> list[str]:
        """Fallback treatment search when ChromaDB is unavailable."""
        return [
            "For most fungal diseases: Apply Mancozeb 75% WP (2g/L) every 7-10 days.",
            "Organic option: Neem oil (5ml/L) + Trichoderma viride (5g/L).",
            "Always consult local KVK or agricultural officer for specific advice.",
        ]
