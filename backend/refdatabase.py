import wikipediaapi
import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)

class WikipediaVerifier:
    """Verify facts against Wikipedia"""
    
    def __init__(self):
        # Initialize Wikipedia API with user agent
        self.wiki = wikipediaapi.Wikipedia(
            language='en',
            user_agent='HallucinationPrevention/1.0 (Educational Project)'
        )
        logger.info("Wikipedia verifier initialized")
    
    def verify_fact(self, fact: Dict) -> Dict:
        """
        Verify a single fact against Wikipedia
        Returns the fact with verification results added
        """
        entity = fact['entity']
        entity_type = fact['entity_type']
        
        logger.info(f"Verifying: {entity} ({entity_type})")
        
        # Create search query based on entity type
        search_query = self._create_search_query(entity, entity_type, fact['sentence'])
        
        # Skip if search query is invalid
        if not search_query or len(search_query.strip()) < 2:
            logger.info(f"  Skipping invalid search query: {search_query}")
            return {
                **fact,
                "verified": False,
                "confidence": "unknown",
                "wikipedia_url": None,
                "verification_note": "Could not create valid search query"
            }
        
        # Search Wikipedia
        try:
            page = self.wiki.page(search_query)
            
            if not page.exists():
                logger.info(f"  No Wikipedia page found for: {search_query}")
                return {
                    **fact,
                    "verified": False,
                    "confidence": "unknown",
                    "wikipedia_url": None,
                    "verification_note": f"No Wikipedia page found for '{search_query}'"
                }
            
            # Get page content
            page_text = page.text.lower()
            page_summary = page.summary.lower()
            
            # Verify the fact
            verification_result = self._verify_against_content(
                fact, page_text, page_summary
            )
            
            return {
                **fact,
                **verification_result,
                "wikipedia_url": page.fullurl,
                "wikipedia_title": page.title
            }
            
        except Exception as e:
            logger.error(f"  Error searching Wikipedia: {str(e)}")
            return {
                **fact,
                "verified": False,
                "confidence": "unknown",
                "wikipedia_url": None,
                "verification_note": f"Error accessing Wikipedia: {str(e)}"
            }
    
    def verify_facts(self, facts: List[Dict]) -> List[Dict]:
        """Verify multiple facts"""
        verified_facts = []
        
        for fact in facts:
            verified_fact = self.verify_fact(fact)
            verified_facts.append(verified_fact)
        
        logger.info(f"Verified {len(verified_facts)} facts")
        return verified_facts
    
    def _create_search_query(self, entity: str, entity_type: str, sentence: str) -> str:
        """Create optimal search query for Wikipedia"""
        
        # For locations, people, organizations - use entity directly
        if entity_type in ["GPE", "LOC", "PERSON", "ORG"]:
            return entity
        
        # For dates, numbers, measurements - extract main subject from sentence
        if entity_type in ["DATE", "CARDINAL", "QUANTITY", "MONEY", "MEASUREMENT", "POPULATION", "WEIGHT", "TEMPERATURE"]:
            # Extract the main subject (proper noun) from the sentence
            subject = self._extract_subject_from_sentence(sentence)
            
            if subject:
                logger.info(f"  Extracted subject for verification: {subject}")
                return subject
            
            # Fallback: return empty string to skip verification
            logger.info(f"  Could not extract subject from: {sentence}")
            return ""
        
        return entity
    
    def _extract_subject_from_sentence(self, sentence: str) -> Optional[str]:
        """
        Extract the main subject (proper noun) from a sentence
        Examples:
        - "Tokyo's population is 14 million" -> "Tokyo"
        - "The Eiffel Tower is 330 meters" -> "Eiffel Tower"
        - "Paris has 2.2 million people" -> "Paris"
        """
        # Pattern 1: Capitalized word(s) at the start
        match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', sentence)
        if match:
            return match.group(1)
        
        # Pattern 2: "The [Proper Noun]"
        match = re.search(r'[Tt]he\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', sentence)
        if match:
            return match.group(1)
        
        # Pattern 3: Look for any capitalized phrase
        match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', sentence)
        if match:
            return match.group(1)
        
        return None
    
    def _verify_against_content(self, fact: Dict, page_text: str, page_summary: str) -> Dict:
        """
        Verify fact against Wikipedia content
        Returns verification result with confidence level
        """
        entity = fact['entity'].lower()
        entity_type = fact['entity_type']
        
        # For different entity types, use different verification strategies
        
        if entity_type in ["GPE", "LOC", "PERSON", "ORG"]:
            # For entities, just check if mentioned
            if entity in page_text or entity in page_summary:
                return {
                    "verified": True,
                    "confidence": "high",
                    "verification_note": "Entity found in Wikipedia"
                }
            else:
                return {
                    "verified": False,
                    "confidence": "low",
                    "verification_note": "Entity not found in Wikipedia page"
                }
        
        elif entity_type in ["DATE", "CARDINAL", "QUANTITY", "MEASUREMENT", "POPULATION", "MONEY", "WEIGHT", "TEMPERATURE"]:
            # For numbers/dates, check if the specific value appears
            entity_clean = re.sub(r'[,\s]', '', entity)  # Remove commas and spaces
            page_text_clean = re.sub(r'[,\s]', '', page_text)
            
            if entity_clean in page_text_clean:
                return {
                    "verified": True,
                    "confidence": "high",
                    "verification_note": f"Value '{entity}' found in Wikipedia"
                }
            
            # Check for similar values (e.g., 14 million vs 14.2 million)
            if self._check_similar_numbers(entity, page_text):
                return {
                    "verified": True,
                    "confidence": "medium",
                    "verification_note": f"Similar value found in Wikipedia"
                }
            
            return {
                "verified": False,
                "confidence": "low",
                "verification_note": f"Value '{entity}' not found in Wikipedia"
            }
        
        # Default: unknown
        return {
            "verified": False,
            "confidence": "unknown",
            "verification_note": "Could not verify"
        }
    
    def _check_similar_numbers(self, entity: str, text: str) -> bool:
        """Check if similar numbers appear (handles minor variations)"""
        
        # Extract number from entity
        number_match = re.search(r'([\d.]+)', entity)
        if not number_match:
            return False
        
        try:
            value = float(number_match.group(1))
            
            # Look for similar values in text (within 10% tolerance)
            text_numbers = re.findall(r'([\d.]+)\s*(?:million|billion|thousand|meters|feet|km)?', text.lower())
            
            for text_num in text_numbers:
                try:
                    text_value = float(text_num)
                    # Check if within 10% tolerance
                    if abs(text_value - value) / value < 0.1:
                        return True
                except:
                    continue
            
        except:
            pass
        
        return False

# Create singleton instance
wikipedia_verifier = WikipediaVerifier()