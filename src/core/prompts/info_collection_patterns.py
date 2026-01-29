"""
Information collection patterns for the Sentinel Insurance Agent.

This module contains patterns used to detect when user information should be collected
and patterns for extracting specific information from user input.
"""

from typing import Dict, List


class InfoCollectionPatterns:
    """Container for all information collection patterns."""
    
    @staticmethod
    def get_collection_triggers() -> Dict[str, List[str]]:
        """
        Returns patterns that trigger information collection.
        
        Returns:
            Dictionary mapping field names to their trigger patterns
        """
        return {
            'name': InfoCollectionPatterns.NAME_TRIGGERS,
            'policy_number': InfoCollectionPatterns.POLICY_NUMBER_TRIGGERS,
            'contact_info': InfoCollectionPatterns.CONTACT_INFO_TRIGGERS,
            'inquiry_type': InfoCollectionPatterns.INQUIRY_TYPE_TRIGGERS,
        }
    
    @staticmethod
    def get_extraction_patterns() -> Dict[str, List[str]]:
        """
        Returns patterns for extracting specific information from user input.
        
        Returns:
            Dictionary mapping field names to their extraction patterns
        """
        return {
            'name': InfoCollectionPatterns.NAME_EXTRACTION_PATTERNS,
            'policy_number': InfoCollectionPatterns.POLICY_NUMBER_EXTRACTION_PATTERNS,
            'contact_info': InfoCollectionPatterns.CONTACT_INFO_EXTRACTION_PATTERNS,
            'inquiry_type': InfoCollectionPatterns.INQUIRY_TYPE_EXTRACTION_PATTERNS,
        }
    
    @staticmethod
    def get_triggers(field_name: str) -> List[str]:
        """
        Get trigger patterns for a specific field.
        
        Args:
            field_name: Name of the field to get triggers for
            
        Returns:
            List of trigger patterns for the field
        """
        triggers = InfoCollectionPatterns.get_collection_triggers()
        return triggers.get(field_name, [])
    
    @staticmethod
    def get_extraction(field_name: str) -> List[str]:
        """
        Get extraction patterns for a specific field.
        
        Args:
            field_name: Name of the field to get extraction patterns for
            
        Returns:
            List of extraction patterns for the field
        """
        patterns = InfoCollectionPatterns.get_extraction_patterns()
        return patterns.get(field_name, [])
    
    # Name Collection Triggers
    NAME_TRIGGERS = [
        r"\b(my name is|i'm|i am|call me)\b",
        r"\b(name|called)\b",
    ]
    
    # Name Extraction Patterns
    NAME_EXTRACTION_PATTERNS = [
        r"(?:my name is|i'm|i am|call me)\s+([a-zA-Z\s]{2,30}?)(?:\s+and|\s*,|\s*$)",
        r"^([a-zA-Z\s]{2,30}?)(?:\s+here|$)",  # Simple name at start
    ]
    
    # Policy Number Collection Triggers
    POLICY_NUMBER_TRIGGERS = [
        r"\b(policy|policy number|account number)\b",
        r"\b[a-zA-Z]{2,3}\d{6,10}\b",  # Policy-like format
        r"\b\d{8,12}\b",  # Long numeric string
    ]
    
    # Policy Number Extraction Patterns
    POLICY_NUMBER_EXTRACTION_PATTERNS = [
        r"(?:policy number|policy|number)\s*(?:is|:)?\s*([a-zA-Z0-9\-]+)",
        r"\b([a-zA-Z]{2,3}\d{6,10})\b",  # Common policy format
        r"\b(\d{8,12})\b",  # Numeric policy
    ]
    
    # Contact Info Collection Triggers
    CONTACT_INFO_TRIGGERS = [
        r"@",  # Email indicator
        r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # Phone pattern
        r"\b(email|phone|contact)\b",
    ]
    
    # Contact Info Extraction Patterns
    CONTACT_INFO_EXTRACTION_PATTERNS = [
        r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",  # Email
        r"(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})",  # Phone
    ]
    
    # Inquiry Type Collection Triggers
    INQUIRY_TYPE_TRIGGERS = [
        r"\b(help|support|problem|issue|claim)\b",
        r"\b(buy|purchase|quote|new policy)\b",
    ]
    
    # Inquiry Type Extraction Patterns
    INQUIRY_TYPE_EXTRACTION_PATTERNS = [
        r"\b(support|help|assistance|problem|issue|claim)\b",
        r"\b(sales|buy|purchase|quote|new policy|insurance)\b",
    ]