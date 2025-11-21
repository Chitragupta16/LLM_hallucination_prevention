from confidence_scorer import confidence_scorer

# Test Case 1: All facts verified
test_facts_high = [
    {"entity": "Tokyo", "entity_type": "GPE", "verified": True, "confidence": "high"},
    {"entity": "14 million", "entity_type": "CARDINAL", "verified": True, "confidence": "high"},
    {"entity": "2020", "entity_type": "DATE", "verified": True, "confidence": "high"},
]

# Test Case 2: Mixed verification
test_facts_medium = [
    {"entity": "Paris", "entity_type": "GPE", "verified": True, "confidence": "high"},
    {"entity": "2.2 million", "entity_type": "CARDINAL", "verified": True, "confidence": "medium"},
    {"entity": "unknown city", "entity_type": "GPE", "verified": False, "confidence": "unknown"},
]

# Test Case 3: Low confidence
test_facts_low = [
    {"entity": "Fake City", "entity_type": "GPE", "verified": False, "confidence": "low"},
    {"entity": "999 billion", "entity_type": "CARDINAL", "verified": False, "confidence": "low"},
]

print("Testing Confidence Scorer\n")
print("="*70)

for i, (test_facts, label) in enumerate([
    (test_facts_high, "High Confidence"),
    (test_facts_medium, "Medium Confidence"),
    (test_facts_low, "Low Confidence")
], 1):
    print(f"\nTest Case {i}: {label}")
    print("-"*70)
    
    result = confidence_scorer.score_response(test_facts)
    
    print(f"{result['emoji']} Overall Confidence: {result['overall_confidence'].upper()}")
    print(f"Score: {result['confidence_score']}/1.0")
    print(f"Color: {result['color']}")
    print(f"Summary: {result['summary']}")
    print(f"\nStats:")
    print(f"  Total Facts: {result['stats']['total_facts']}")
    print(f"  Verified: {result['stats']['verified']}")
    print(f"  Unverified: {result['stats']['unverified']}")
    print(f"  Unknown: {result['stats']['unknown']}")
    print("="*70)