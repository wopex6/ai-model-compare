"""
Medical Knowledge APIs - Real-time medical evidence for Dr. Health
Integrates free public APIs: PubMed, OpenFDA, WHO, RxNorm, ICD-10
No API keys required for any of these services.
"""
import asyncio
import aiohttp
import json
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from functools import lru_cache


class MedicalKnowledgeManager:
    """Orchestrates all medical knowledge API calls"""

    def __init__(self):
        self.pubmed = PubMedAPI()
        self.openfda = OpenFDAAPI()
        self.rxnorm = RxNormAPI()
        self.icd10 = ICD10API()
        self.who = WHOAPI()
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour cache

    async def get_evidence_context(self, user_message: str, health_profile: dict = None) -> str:
        """
        Main entry: analyze the user's message, query relevant APIs,
        and return formatted medical evidence context for the AI prompt.
        """
        topics = self._extract_medical_topics(user_message, health_profile)
        if not topics:
            return ""

        evidence_parts = []

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                tasks = []

                # PubMed research for medical topics
                if topics.get('conditions') or topics.get('symptoms') or topics.get('general_query'):
                    query = topics.get('general_query', '')
                    if topics.get('conditions'):
                        query = ' OR '.join(topics['conditions'][:2])
                    elif topics.get('symptoms'):
                        query = ' OR '.join(topics['symptoms'][:2])
                    tasks.append(('pubmed', self.pubmed.search(session, query, max_results=3)))

                # Drug info from OpenFDA
                if topics.get('drugs') or topics.get('supplements'):
                    items = (topics.get('drugs', []) + topics.get('supplements', []))[:2]
                    for item in items:
                        tasks.append(('openfda', self.openfda.search_drug(session, item)))

                # Drug interactions
                if topics.get('drugs') and len(topics['drugs']) >= 2:
                    tasks.append(('interactions', self.rxnorm.check_interactions(
                        session, topics['drugs'][:4]
                    )))
                elif topics.get('supplements') and topics.get('drugs'):
                    combined = (topics['drugs'] + topics['supplements'])[:4]
                    tasks.append(('interactions', self.rxnorm.check_interactions(
                        session, combined
                    )))

                # ICD-10 codes for conditions
                if topics.get('conditions'):
                    for cond in topics['conditions'][:2]:
                        tasks.append(('icd10', self.icd10.search(session, cond)))

                # WHO data for infectious diseases
                if topics.get('infectious'):
                    tasks.append(('who', self.who.get_disease_info(session, topics['infectious'][0])))

                # Run all in parallel with timeout
                if tasks:
                    labels = [t[0] for t in tasks]
                    coros = [t[1] for t in tasks]
                    results = await asyncio.gather(*coros, return_exceptions=True)

                    for label, result in zip(labels, results):
                        if isinstance(result, Exception):
                            continue
                        if result:
                            evidence_parts.append(result)

        except Exception as e:
            # Fail silently — evidence is supplementary
            pass

        if not evidence_parts:
            return ""

        context = "\n--- MEDICAL EVIDENCE (from public databases) ---\n"
        context += "\n".join(evidence_parts)
        context += "\n--- END MEDICAL EVIDENCE ---\n"
        context += "Use the above evidence to support your response where relevant. Cite sources when possible.\n"
        return context

    def _extract_medical_topics(self, message: str, profile: dict = None) -> dict:
        """Extract medical topics from user message + profile context"""
        msg_lower = message.lower()
        topics = {
            'conditions': [],
            'symptoms': [],
            'drugs': [],
            'supplements': [],
            'foods': [],
            'infectious': [],
            'general_query': ''
        }

        # Common condition keywords
        condition_patterns = [
            r'\b(diabetes|hypertension|hypothyroid\w*|hyperthyroid\w*|thyroid\w*|'
            r'asthma|arthritis|cancer|depression|anxiety|insomnia|obesity|'
            r'cholesterol|anemia|anaemia|gout|eczema|psoriasis|migraine|'
            r'osteoporosis|fibromyalgia|ibs|crohn|celiac|lupus|copd|'
            r'incontinence|nocturia|prostatitis|bph|kidney|liver|heart\s*disease|'
            r'stroke|alzheimer|parkinson|epilepsy|multiple\s*sclerosis)\b'
        ]

        # Symptom keywords
        symptom_patterns = [
            r'\b(headache|fatigue|nausea|dizziness|chest\s*pain|back\s*pain|'
            r'joint\s*pain|bloating|constipation|diarrhea|fever|cough|'
            r'shortness\s*of\s*breath|palpitation|swelling|rash|'
            r'hair\s*loss|hair\s*whit\w+|dry\s*mouth|frequent\s*urinat\w+|'
            r'bladder\s*leak|weight\s*loss|weight\s*gain|tingling|numbness)\b'
        ]

        # Drug/medication keywords
        drug_patterns = [
            r'\b(aspirin|ibuprofen|paracetamol|acetaminophen|metformin|'
            r'lisinopril|amlodipine|atorvastatin|simvastatin|omeprazole|'
            r'levothyroxine|metoprolol|losartan|gabapentin|sertraline|'
            r'fluoxetine|amoxicillin|azithromycin|prednisone|insulin|'
            r'warfarin|clopidogrel|pantoprazole|tamsulosin)\b'
        ]

        # Supplement keywords
        supplement_patterns = [
            r'\b(vitamin\s*[a-ekd]\d?|vitamin\s*b\d{0,2}|zinc|magnesium|iron|'
            r'calcium|omega[\s\-]*3|fish\s*oil|probiotics?|turmeric|curcumin|'
            r'ginkgo|ashwagandha|melatonin|coq10|collagen|biotin|folate|'
            r'folic\s*acid|selenium|chromium|saw\s*palmetto|milk\s*thistle|'
            r'st\s*john|echinacea|ginseng|maca|spirulina|creatine)\b'
        ]

        # Infectious disease keywords
        infectious_patterns = [
            r'\b(covid|influenza|flu|malaria|tuberculosis|tb|hepatitis|hiv|'
            r'measles|dengue|cholera|ebola|zika|mpox|monkeypox)\b'
        ]

        for pattern in condition_patterns:
            matches = re.findall(pattern, msg_lower)
            topics['conditions'].extend(matches)

        for pattern in symptom_patterns:
            matches = re.findall(pattern, msg_lower)
            topics['symptoms'].extend(matches)

        for pattern in drug_patterns:
            matches = re.findall(pattern, msg_lower)
            topics['drugs'].extend(matches)

        for pattern in supplement_patterns:
            matches = re.findall(pattern, msg_lower)
            topics['supplements'].extend(matches)

        for pattern in infectious_patterns:
            matches = re.findall(pattern, msg_lower)
            topics['infectious'].extend(matches)

        # Add profile context
        if profile:
            for cond in profile.get('conditions', []):
                name = cond.get('name', '').lower()
                if name and any(kw in msg_lower for kw in name.split()[:2]):
                    if name not in topics['conditions']:
                        topics['conditions'].append(name)
            for supp in profile.get('supplements', []):
                name = supp.get('name', '').lower()
                if name and name in msg_lower:
                    if name not in topics['supplements']:
                        topics['supplements'].append(name)

        # Build general query for PubMed if we have topics
        query_parts = topics['conditions'] + topics['symptoms']
        if query_parts:
            topics['general_query'] = ' '.join(query_parts[:3])
        elif any(kw in msg_lower for kw in ['healthy', 'health', 'risk', 'safe', 'side effect', 'benefit', 'dosage']):
            # Use the full message as a general health query
            # Remove common filler words
            words = [w for w in message.split() if len(w) > 3 and w.lower() not in
                     {'what', 'that', 'this', 'with', 'from', 'have', 'does', 'your', 'about', 'would', 'could', 'should'}]
            topics['general_query'] = ' '.join(words[:5])

        # Only return if we found something
        has_content = any(v for v in topics.values() if v)
        return topics if has_content else {}


class PubMedAPI:
    """NCBI PubMed E-utilities — free, no API key required (limited to 3 req/sec)"""
    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    async def search(self, session: aiohttp.ClientSession, query: str, max_results: int = 3) -> str:
        """Search PubMed and return formatted research summaries"""
        if not query:
            return ""
        try:
            # Step 1: Search for article IDs
            search_url = f"{self.BASE}/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": f"{query} AND (review[pt] OR systematic review[pt] OR meta-analysis[pt])",
                "retmax": max_results,
                "sort": "relevance",
                "retmode": "json"
            }
            async with session.get(search_url, params=params) as resp:
                if resp.status != 200:
                    return ""
                data = await resp.json()
                id_list = data.get("esearchresult", {}).get("idlist", [])

            if not id_list:
                return ""

            # Step 2: Fetch article summaries
            fetch_url = f"{self.BASE}/esummary.fcgi"
            params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json"
            }
            async with session.get(fetch_url, params=params) as resp:
                if resp.status != 200:
                    return ""
                data = await resp.json()

            articles = []
            result = data.get("result", {})
            for uid in id_list:
                article = result.get(uid, {})
                if isinstance(article, dict) and article.get("title"):
                    title = article.get("title", "")
                    authors_list = article.get("authors", [])
                    first_author = authors_list[0].get("name", "") if authors_list else "Unknown"
                    pub_date = article.get("pubdate", "")
                    source = article.get("source", "")
                    articles.append(
                        f"  • {title} ({first_author} et al., {source}, {pub_date}) [PMID:{uid}]"
                    )

            if articles:
                return "📚 PubMed Research:\n" + "\n".join(articles)
            return ""

        except Exception:
            return ""


class OpenFDAAPI:
    """OpenFDA — free drug, adverse event, and label data"""
    BASE = "https://api.fda.gov"

    async def search_drug(self, session: aiohttp.ClientSession, drug_name: str) -> str:
        """Get drug label information including warnings and interactions"""
        if not drug_name:
            return ""
        try:
            url = f"{self.BASE}/drug/label.json"
            params = {
                "search": f'openfda.generic_name:"{drug_name}" OR openfda.brand_name:"{drug_name}"',
                "limit": 1
            }
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return ""
                data = await resp.json()

            results = data.get("results", [])
            if not results:
                return ""

            label = results[0]
            parts = [f"💊 FDA Drug Info — {drug_name.title()}:"]

            # Warnings
            warnings = label.get("warnings", [])
            if warnings:
                warn_text = warnings[0][:300]
                parts.append(f"  Warnings: {warn_text}")

            # Drug interactions
            interactions = label.get("drug_interactions", [])
            if interactions:
                inter_text = interactions[0][:300]
                parts.append(f"  Interactions: {inter_text}")

            # Adverse reactions
            adverse = label.get("adverse_reactions", [])
            if adverse:
                adv_text = adverse[0][:200]
                parts.append(f"  Adverse reactions: {adv_text}")

            # Indications
            indications = label.get("indications_and_usage", [])
            if indications:
                ind_text = indications[0][:200]
                parts.append(f"  Indications: {ind_text}")

            return "\n".join(parts) if len(parts) > 1 else ""

        except Exception:
            return ""

    async def get_adverse_events(self, session: aiohttp.ClientSession, drug_name: str, limit: int = 5) -> str:
        """Get reported adverse events for a drug"""
        if not drug_name:
            return ""
        try:
            url = f"{self.BASE}/drug/event.json"
            params = {
                "search": f'patient.drug.openfda.generic_name:"{drug_name}"',
                "count": "patient.reaction.reactionmeddrapt.exact",
                "limit": limit
            }
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return ""
                data = await resp.json()

            results = data.get("results", [])
            if not results:
                return ""

            reactions = [f"{r['term']} ({r['count']} reports)" for r in results[:5]]
            return f"⚠️ Top reported adverse events for {drug_name.title()}: {', '.join(reactions)}"

        except Exception:
            return ""


class RxNormAPI:
    """NLM RxNorm — drug normalization and interaction checking"""
    BASE = "https://rxnav.nlm.nih.gov/REST"

    async def get_rxcui(self, session: aiohttp.ClientSession, drug_name: str) -> Optional[str]:
        """Get RxNorm Concept Unique Identifier for a drug"""
        try:
            url = f"{self.BASE}/rxcui.json"
            params = {"name": drug_name, "search": 2}
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                ids = data.get("idGroup", {}).get("rxnormId", [])
                return ids[0] if ids else None
        except Exception:
            return None

    async def check_interactions(self, session: aiohttp.ClientSession, drug_names: List[str]) -> str:
        """Check drug-drug interactions via NLM Interaction API"""
        if len(drug_names) < 2:
            return ""
        try:
            # Get RxCUIs for all drugs
            rxcuis = []
            for name in drug_names:
                rxcui = await self.get_rxcui(session, name)
                if rxcui:
                    rxcuis.append(rxcui)

            if len(rxcuis) < 2:
                return ""

            # Check interactions
            url = f"{self.BASE}/interaction/list.json"
            params = {"rxcuis": "+".join(rxcuis)}
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return ""
                data = await resp.json()

            interactions = data.get("fullInteractionTypeGroup", [])
            if not interactions:
                return f"✅ No known interactions found between: {', '.join(drug_names)}"

            parts = [f"⚠️ Drug Interactions Found:"]
            for group in interactions:
                for inter_type in group.get("fullInteractionType", [])[:3]:
                    for pair in inter_type.get("interactionPair", [])[:2]:
                        desc = pair.get("description", "")
                        severity = pair.get("severity", "N/A")
                        if desc:
                            parts.append(f"  • [{severity}] {desc[:250]}")

            return "\n".join(parts) if len(parts) > 1 else ""

        except Exception:
            return ""


class ICD10API:
    """WHO ICD-10 code lookup via NLM Clinical Tables"""
    BASE = "https://clinicaltables.nlm.nih.gov/api"

    async def search(self, session: aiohttp.ClientSession, term: str) -> str:
        """Search ICD-10 codes for a condition"""
        if not term:
            return ""
        try:
            url = f"{self.BASE}/icd10cm/v3/search"
            params = {"sf": "code,name", "terms": term, "maxList": 3}
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return ""
                data = await resp.json()

            # Response format: [total_count, codes, extra, [code, name] pairs]
            if len(data) < 4 or not data[3]:
                return ""

            codes = [f"{item[0]}: {item[1]}" for item in data[3][:3]]
            return f"🏥 ICD-10 Classification for '{term}': " + "; ".join(codes)

        except Exception:
            return ""


class WHOAPI:
    """WHO Disease Outbreak News and health topics via MedlinePlus"""

    async def get_disease_info(self, session: aiohttp.ClientSession, disease: str) -> str:
        """Get health topic info from MedlinePlus (NLM/NIH) — more reliable than WHO API"""
        if not disease:
            return ""
        try:
            # Use MedlinePlus Connect (NLM) — reliable, structured health info
            url = "https://wsearch.nlm.nih.gov/ws/query"
            params = {
                "db": "healthTopics",
                "term": disease,
                "retmax": 3
            }
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return ""
                text = await resp.text()

            # Parse XML response for titles and summaries
            import xml.etree.ElementTree as ET
            root = ET.fromstring(text)
            
            results = []
            for doc in root.findall('.//document')[:3]:
                title_el = doc.find('.//content[@name="title"]')
                snippet_el = doc.find('.//content[@name="FullSummary"]')
                url_el = doc.find('.//content[@name="url"]')
                
                title_raw = title_el.text if title_el is not None else ""
                title = re.sub(r'<[^>]+>', '', title_raw)
                snippet = ""
                if snippet_el is not None and snippet_el.text:
                    # Strip HTML tags and truncate
                    clean = re.sub(r'<[^>]+>', '', snippet_el.text)
                    snippet = clean[:200]
                source_url = url_el.text if url_el is not None else ""
                
                if title:
                    entry = f"  • {title}"
                    if snippet:
                        entry += f": {snippet}"
                    if source_url:
                        entry += f" [{source_url}]"
                    results.append(entry)

            if results:
                return "🌍 NIH/MedlinePlus Health Info:\n" + "\n".join(results)
            return ""

        except Exception:
            return ""


# Singleton instance
_medical_knowledge = None

def get_medical_knowledge() -> MedicalKnowledgeManager:
    """Get or create the singleton MedicalKnowledgeManager"""
    global _medical_knowledge
    if _medical_knowledge is None:
        _medical_knowledge = MedicalKnowledgeManager()
    return _medical_knowledge
