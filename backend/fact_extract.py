import spacy
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model loaded successfully")
except:
    logger.error("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None

class FactExtractor:
    """Extract factual claims from text"""
    
    def __init__(self):
        self.nlp = nlp
    
    def extract_facts(self, text: str) -> List[Dict]:
        """
        Extract factual claims from text
        Returns list of facts with metadata
        """
        if not self.nlp:
            return []
        
        facts = []
        doc = self.nlp(text)
        
        # Extract named entities (people, places, orgs, dates)
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "GPE", "LOC", "ORG", "DATE", "TIME", "MONEY", "QUANTITY", "CARDINAL"]:
                # Get the sentence containing this entity
                sentence = self._get_sentence_for_entity(ent, doc)
                
                facts.append({
                    "claim": sentence.text.strip(),
                    "entity": ent.text,
                    "entity_type": ent.label_,
                    "sentence": sentence.text.strip()
                })
        
        # Extract numeric facts (population, measurements, etc.)
        numeric_facts = self._extract_numeric_facts(text)
        facts.extend(numeric_facts)
        
        # Extract date patterns
        date_facts = self._extract_date_patterns(text)
        facts.extend(date_facts)
        
        # Remove duplicates based on entity + sentence combination
        # This allows multiple facts per sentence
        seen = set()
        unique_facts = []
        for fact in facts:
            # Create unique key from entity and first 50 chars of sentence
            key = f"{fact['entity']}:{fact['sentence'][:50]}"
            if key not in seen:
                seen.add(key)
                unique_facts.append(fact)
        
        logger.info(f"Extracted {len(unique_facts)} unique facts")
        return unique_facts
    
    def _get_sentence_for_entity(self, entity, doc):
        """Get the sentence containing an entity"""
        for sent in doc.sents:
            if entity.start >= sent.start and entity.end <= sent.end:
                return sent
        return doc[entity.start:entity.end]
    
    def _extract_numeric_facts(self, text: str) -> List[Dict]:
        """Extract facts with numbers (population, measurements, prices)"""
        facts = []
        
        # Patterns like "population of X million", "costs $X", "X meters tall"
        patterns = [
            (r'([\d,.]+ (?:million|billion|thousand|hundred)(?: people)?)', "POPULATION"),
            (r'(\$[\d,.]+)', "MONEY"),
            (r'([\d,.]+ (?:meters|feet|kilometers|miles|km|ft))', "MEASUREMENT"),
            (r'([\d,.]+ (?:kg|tons|pounds|grams))', "WEIGHT"),
            (r'([\d,.]+ (?:degrees|°[CF]))', "TEMPERATURE"),
        ]
        
        for pattern, fact_type in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get the full sentence containing this number
                sent_start = text.rfind('.', 0, match.start()) + 1
                sent_end = text.find('.', match.end())
                if sent_end == -1:
                    sent_end = len(text)
                sentence = text[sent_start:sent_end].strip()
                
                facts.append({
                    "claim": sentence,
                    "entity": match.group(1).strip(),
                    "entity_type": fact_type,
                    "sentence": sentence
                })
        
        return facts
    
    def _extract_date_patterns(self, text: str) -> List[Dict]:
        """Extract date-related facts"""
        facts = []
        
        # Patterns like "in 2020", "built in 1889", "founded in 1995"
        date_patterns = [
            (r'(?:in|during|since|from)\s+(\d{4})', "DATE"),
            (r'(?:established|built|founded|created|born|died)\s+(?:in\s+)?(\d{4})', "DATE"),
        ]
        
        for pattern, fact_type in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get the full sentence
                sent_start = text.rfind('.', 0, match.start()) + 1
                sent_end = text.find('.', match.end())
                if sent_end == -1:
                    sent_end = len(text)
                sentence = text[sent_start:sent_end].strip()
                
                facts.append({
                    "claim": sentence,
                    "entity": match.group(1),
                    "entity_type": fact_type,
                    "sentence": sentence
                })
        
        return facts

# Create singleton instance
fact_extractor = FactExtractor()