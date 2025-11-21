import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """Format responses with inline fact verification markers"""
    
    def __init__(self):
        pass
    
    def format_response(self, original_text: str, verified_facts: List[Dict], contradictions: List[Dict]) -> Dict:
        """
        Format response with inline verification markers
        Returns formatted response with HTML markup
        """
        # Create a mapping of text spans to their verification status
        fact_spans = self._create_fact_spans(verified_facts, contradictions)
        
        # Generate both plain and HTML formatted versions
        html_formatted = self._create_html_format(original_text, fact_spans)
        markdown_formatted = self._create_markdown_format(original_text, fact_spans)
        
        # Generate fact summary
        fact_summary = self._create_fact_summary(verified_facts, contradictions)
        
        return {
            "original": original_text,
            "html": html_formatted,
            "markdown": markdown_formatted,
            "fact_summary": fact_summary,
            "has_issues": len(contradictions) > 0 or any(not f.get('verified') for f in verified_facts)
        }
    
    def _create_fact_spans(self, verified_facts: List[Dict], contradictions: List[Dict]) -> List[Dict]:
        """
        Create spans marking where facts appear in the text
        Returns list of {text, status, confidence, url}
        """
        spans = []
        
        # Get contradicted entities
        contradicted_entities = set()
        for cont in contradictions:
            if 'current_value' in cont:
                contradicted_entities.add(cont['current_value'].lower())
        
        for fact in verified_facts:
            entity = fact['entity']
            
            # Determine status
            if entity.lower() in contradicted_entities:
                status = "contradicted"
                color = "red"
                emoji = "❌"
            elif fact.get('verified') and fact.get('confidence') == 'high':
                status = "verified"
                color = "green"
                emoji = "✅"
            elif fact.get('verified') and fact.get('confidence') == 'medium':
                status = "uncertain"
                color = "yellow"
                emoji = "⚠️"
            else:
                status = "unverified"
                color = "orange"
                emoji = "❓"
            
            spans.append({
                "text": entity,
                "status": status,
                "color": color,
                "emoji": emoji,
                "confidence": fact.get('confidence', 'unknown'),
                "wikipedia_url": fact.get('wikipedia_url'),
                "note": fact.get('verification_note', '')
            })
        
        return spans
    
    def _create_html_format(self, text: str, fact_spans: List[Dict]) -> str:
        """Create HTML formatted version with colored highlights"""
        formatted = text
        
        # Sort spans by length (longest first to avoid nested replacements)
        sorted_spans = sorted(fact_spans, key=lambda x: len(x['text']), reverse=True)
        
        # Keep track of what we've already replaced
        replaced_positions = set()
        
        for span in sorted_spans:
            entity = span['text']
            color = span['color']
            emoji = span['emoji']
            url = span['wikipedia_url']
            note = span['note']
            
            # Create HTML span with tooltip
            if url:
                html_span = f'<span class="fact-{color}" title="{note}" data-url="{url}">{emoji} {entity}</span>'
            else:
                html_span = f'<span class="fact-{color}" title="{note}">{emoji} {entity}</span>'
            
            # Replace first occurrence only
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(entity) + r'\b'
            formatted = re.sub(pattern, html_span, formatted, count=1)
        
        return formatted
    
    def _create_markdown_format(self, text: str, fact_spans: List[Dict]) -> str:
        """Create Markdown formatted version"""
        formatted = text
        
        # Sort spans by length
        sorted_spans = sorted(fact_spans, key=lambda x: len(x['text']), reverse=True)
        
        for span in sorted_spans:
            entity = span['text']
            emoji = span['emoji']
            
            # Replace with emoji marker
            pattern = r'\b' + re.escape(entity) + r'\b'
            formatted = re.sub(pattern, f'{emoji} {entity}', formatted, count=1)
        
        return formatted
    
    def _create_fact_summary(self, verified_facts: List[Dict], contradictions: List[Dict]) -> List[Dict]:
        """Create a summary of all facts with their status"""
        summary = []
        
        for fact in verified_facts:
            summary.append({
                "entity": fact['entity'],
                "type": fact['entity_type'],
                "verified": fact.get('verified', False),
                "confidence": fact.get('confidence', 'unknown'),
                "wikipedia_url": fact.get('wikipedia_url'),
                "note": fact.get('verification_note', '')
            })
        
        return summary

# Create singleton instance
response_formatter = ResponseFormatter()