"""
spam_detector.py - Rule-based spam detection for university marketplace
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class SpamDetector:
    """
    Rule-based spam detection system for university marketplace posts
    """
    
    def __init__(self):
        self.spam_keywords = {
            'general': [
                'click here', 'free money', 'make money fast', 'get rich quick',
                'guaranteed income', 'work from home', 'no experience needed',
                'limited time offer', 'act now', 'urgent', 'exclusive deal',
                'crypto investment', 'bitcoin', 'forex trading', 'mlm',
                'pyramid scheme', 'get paid to', 'easy money', 'cash advance',
                'loan approved', 'credit repair', 'debt consolidation',
                'viagra', 'cialis', 'weight loss', 'lose weight fast',
                'miracle cure', 'pharmacy', 'prescription', 'medications'
            ],
            'roommate': [
                'cash only', 'no questions asked', 'under the table',
                'off the books', 'bring friends over anytime', 'party house',
                'no rules', 'anything goes', 'adults only', 'massage',
                'modeling opportunity', 'photo shoot', 'entertainment industry',
                'flexible arrangements', 'special services', 'private sessions'
            ],
            'sell': [
                'brand new in box', 'never used', 'retail $', 'msrp',
                'wholesale price', 'bulk order', 'dropship', 'reseller',
                'business opportunity', 'investment opportunity',
                'too good to be true', 'clearance sale', 'liquidation',
                'going out of business', 'estate sale', 'moving sale',
                'stolen', 'hot item', 'no receipt', 'cash transaction only'
            ],
            'carpool': [
                'unmarked van', 'windowless van', 'pickup location varies',
                'cash payment only', 'no id required', 'anonymous ride',
                'special detour', 'private route', 'extra stops',
                'meet in parking lot', 'abandoned area', 'remote location'
            ]
        }
        
        self.suspicious_patterns = [
            r'\b(?:\d{1,3}[-.]){2,3}\d{1,4}\b',  # IP addresses
            r'https?://[^\s]+',  # URLs (context dependent)
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
            r'\b[A-Z]{2,}\b(?:\s[A-Z]{2,}){2,}',  # Multiple consecutive uppercase words
            r'[!]{2,}|[?]{2,}|[.]{3,}',  # Excessive punctuation
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*-\s*\$\d+(?:,\d{3})*(?:\.\d{2})?)?',  # Price ranges
            r'\b(?:whatsapp|telegram|signal|wickr|kik)\b',  # Alternative messaging apps
            r'\b(?:venmo|paypal|cashapp|zelle|bitcoin|crypto)\s*(?:only|required|preferred)\b',  # Payment restrictions
            r'\b(?:contact|call|text|email)\s*(?:me|us)\s*(?:at|on|via)\b',  # Contact solicitation
            r'\b(?:dm|pm|private message)\s*(?:me|for)\b'  # Private messaging requests
        ]
        
        self.spam_thresholds = {
            'keyword_score': 3,  # Max allowed keyword matches
            'pattern_score': 2,  # Max allowed pattern matches
            'caps_ratio': 0.3,   # Max ratio of uppercase characters
            'special_char_ratio': 0.15,  # Max ratio of special characters
            'min_word_length': 2,  # Minimum average word length
            'max_repeated_chars': 3,  # Max consecutive repeated characters
            'min_text_length': 10,  # Minimum text length
            'max_number_density': 0.3  # Max ratio of numbers to total characters
        }
    
    def detect_spam(self, text: str, category: str = 'general', **kwargs) -> Dict[str, Any]:
        """
        Analyze text content for spam indicators
        
        Args:
            text: The text content to analyze
            category: Post category ('roommate', 'sell', 'carpool', 'general')
            **kwargs: Additional context (price, location, etc.)
        
        Returns:
            Dict containing spam analysis results
        """
        if not text or not isinstance(text, str):
            return self._empty_result()
        
        text_lower = text.lower().strip()
        if len(text_lower) < self.spam_thresholds['min_text_length']:
            return {
                'is_spam': True,
                'confidence': 0.8,
                'spam_score': 5,
                'reasons': ['Text too short - likely spam'],
                'keyword_matches': [],
                'pattern_matches': []
            }
        
        reasons = []
        spam_score = 0
        
        # 1. Keyword detection
        keyword_matches = self._detect_keywords(text_lower, category)
        if len(keyword_matches) > self.spam_thresholds['keyword_score']:
            reasons.append(f"Multiple spam keywords: {', '.join(keyword_matches[:3])}")
            spam_score += len(keyword_matches)
        
        # 2. Suspicious pattern detection
        pattern_matches = self._detect_patterns(text)
        if len(pattern_matches) > self.spam_thresholds['pattern_score']:
            reasons.append(f"Suspicious patterns detected: {len(pattern_matches)} matches")
            spam_score += len(pattern_matches)
        
        # 3. Text quality analysis
        quality_issues, quality_score = self._analyze_text_quality(text)
        reasons.extend(quality_issues)
        spam_score += quality_score
        
        # 4. Category-specific analysis
        category_issues, category_score = self._analyze_category_specific(text, category, **kwargs)
        reasons.extend(category_issues)
        spam_score += category_score
        
        # 5. Context analysis
        context_issues, context_score = self._analyze_context(text, **kwargs)
        reasons.extend(context_issues)
        spam_score += context_score
        
        # Calculate confidence score
        max_possible_score = 20  # Estimated maximum spam indicators
        confidence = min(spam_score / max_possible_score, 1.0)
        
        # Determine if it's spam
        is_spam = spam_score >= 5 or confidence >= 0.7
        
        return {
            'is_spam': is_spam,
            'confidence': round(confidence, 3),
            'spam_score': spam_score,
            'reasons': reasons,
            'keyword_matches': keyword_matches,
            'pattern_matches': pattern_matches,
            'analysis_timestamp': datetime.now(timezone.utc)
        }
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty spam analysis result"""
        return {
            'is_spam': False,
            'confidence': 0.0,
            'spam_score': 0,
            'reasons': [],
            'keyword_matches': [],
            'pattern_matches': []
        }
    
    def _detect_keywords(self, text_lower: str, category: str) -> List[str]:
        """Detect spam keywords in text"""
        keywords_to_check = self.spam_keywords.get('general', [])
        if category in self.spam_keywords:
            keywords_to_check.extend(self.spam_keywords[category])
        
        matches = []
        for keyword in keywords_to_check:
            if keyword.lower() in text_lower:
                matches.append(keyword)
        
        return matches
    
    def _detect_patterns(self, text: str) -> List[str]:
        """Detect suspicious patterns in text"""
        matches = []
        for pattern in self.suspicious_patterns:
            pattern_matches = re.findall(pattern, text, re.IGNORECASE)
            if pattern_matches:
                matches.extend([str(m) for m in pattern_matches])
        
        return matches
    
    def _analyze_text_quality(self, text: str) -> tuple[List[str], int]:
        """Analyze text quality for spam indicators"""
        issues = []
        score = 0
        
        # Check capitalization
        caps_count = sum(1 for c in text if c.isupper())
        caps_ratio = caps_count / len(text) if len(text) > 0 else 0
        if caps_ratio > self.spam_thresholds['caps_ratio']:
            issues.append(f"Excessive capitalization: {caps_ratio:.1%}")
            score += 2
        
        # Check special characters
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        special_char_ratio = special_chars / len(text) if len(text) > 0 else 0
        if special_char_ratio > self.spam_thresholds['special_char_ratio']:
            issues.append(f"Excessive special characters: {special_char_ratio:.1%}")
            score += 1
        
        # Check for repeated characters
        repeated_pattern = r'(.)\1{' + str(self.spam_thresholds['max_repeated_chars']) + ',}'
        if re.search(repeated_pattern, text):
            issues.append("Excessive character repetition")
            score += 1
        
        # Check word quality
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            if avg_word_length < self.spam_thresholds['min_word_length']:
                issues.append(f"Short average word length: {avg_word_length:.1f}")
                score += 1
        
        # Check number density
        numbers = re.findall(r'\d', text)
        number_density = len(numbers) / len(text) if len(text) > 0 else 0
        if number_density > self.spam_thresholds['max_number_density']:
            issues.append(f"High number density: {number_density:.1%}")
            score += 1
        
        return issues, score
    
    def _analyze_category_specific(self, text: str, category: str, **kwargs) -> tuple[List[str], int]:
        """Perform category-specific spam analysis"""
        issues = []
        score = 0
        text_lower = text.lower()
        
        if category == 'roommate':
            # Check for unrealistic rent prices
            rent_matches = re.findall(r'\$(\d+)', text)
            for rent_str in rent_matches:
                rent = int(rent_str)
                if rent < 100 or rent > 4000:  # Unrealistic rent range
                    issues.append(f"Suspicious rent price: ${rent}")
                    score += 3
                    break
            
            # Check for inappropriate roommate requests
            inappropriate_terms = ['no boyfriend', 'single only', 'attractive', 'photos required']
            if any(term in text_lower for term in inappropriate_terms):
                issues.append("Potentially inappropriate roommate requirements")
                score += 2
        
        elif category == 'sell':
            # Check for multiple prices (possible scam)
            price_matches = re.findall(r'\$(\d+)', text)
            if len(price_matches) > 3:
                issues.append("Multiple prices mentioned")
                score += 1
            
            # Check for unrealistic prices
            if kwargs.get('price'):
                price = float(kwargs['price'])
                if price <= 0 or price >= 10000:  # Suspiciously low/high
                    issues.append(f"Unrealistic price: ${price}")
                    score += 2
            
            # Check for stolen goods indicators
            stolen_indicators = ['no questions', 'quick sale', 'need gone asap', 'moving tonight']
            if any(indicator in text_lower for indicator in stolen_indicators):
                issues.append("Possible stolen goods indicators")
                score += 3
        
        elif category == 'carpool':
            # Check for suspicious location descriptions
            suspicious_locations = ['abandoned', 'remote area', 'isolated', 'no one around', 'empty lot']
            if any(location in text_lower for location in suspicious_locations):
                issues.append("Suspicious location descriptions")
                score += 3
            
            # Check for cash-only requirements
            if 'cash only' in text_lower and 'venmo' not in text_lower and 'paypal' not in text_lower:
                issues.append("Cash-only payment requirement")
                score += 2
        
        return issues, score
    
    def _analyze_context(self, text: str, **kwargs) -> tuple[List[str], int]:
        """Analyze contextual spam indicators"""
        issues = []
        score = 0
        
        # Check for urgency indicators
        urgency_words = ['urgent', 'asap', 'immediately', 'right now', 'today only', 'limited time']
        urgency_count = sum(1 for word in urgency_words if word in text.lower())
        if urgency_count >= 2:
            issues.append("Multiple urgency indicators")
            score += 2
        
        # Check for contact method diversity (spam often lists many ways to contact)
        contact_methods = ['email', 'call', 'text', 'whatsapp', 'telegram', 'dm', 'message']
        contact_count = sum(1 for method in contact_methods if method in text.lower())
        if contact_count >= 3:
            issues.append("Multiple contact methods listed")
            score += 1
        
        return issues, score
    
    def batch_detect_spam(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch process multiple posts for spam detection
        
        Args:
            posts: List of post dictionaries with 'title', 'description', 'category' keys
        
        Returns:
            List of spam analysis results
        """
        results = []
        for post in posts:
            title = post.get('title', '')
            description = post.get('description', '')
            category = post.get('category', 'general')
            
            # Analyze title and description separately, then combine
            title_result = self.detect_spam(title, category, **post)
            description_result = self.detect_spam(description, category, **post)
            
            # Combine results
            combined_result = {
                'is_spam': title_result['is_spam'] or description_result['is_spam'],
                'confidence': max(title_result['confidence'], description_result['confidence']),
                'spam_score': title_result['spam_score'] + description_result['spam_score'],
                'reasons': title_result['reasons'] + description_result['reasons'],
                'keyword_matches': list(set(title_result['keyword_matches'] + description_result['keyword_matches'])),
                'pattern_matches': list(set(title_result['pattern_matches'] + description_result['pattern_matches'])),
                'title_analysis': title_result,
                'description_analysis': description_result,
                'post_id': post.get('_id', post.get('id', 'unknown'))
            }
            
            results.append(combined_result)
        
        return results
    
    def update_keywords(self, category: str, new_keywords: List[str], action: str = 'add'):
        """
        Update spam keywords dynamically
        
        Args:
            category: Category to update ('general', 'roommate', 'sell', 'carpool')
            new_keywords: List of keywords to add or remove
            action: 'add' or 'remove'
        """
        if category not in self.spam_keywords:
            self.spam_keywords[category] = []
        
        if action == 'add':
            self.spam_keywords[category].extend(new_keywords)
            self.spam_keywords[category] = list(set(self.spam_keywords[category]))  # Remove duplicates
        elif action == 'remove':
            self.spam_keywords[category] = [kw for kw in self.spam_keywords[category] if kw not in new_keywords]
        
        logger.info(f"Updated {category} keywords: {action} {len(new_keywords)} keywords")
    
    def update_thresholds(self, **new_thresholds):
        """Update spam detection thresholds"""
        for key, value in new_thresholds.items():
            if key in self.spam_thresholds:
                old_value = self.spam_thresholds[key]
                self.spam_thresholds[key] = value
                logger.info(f"Updated threshold {key}: {old_value} -> {value}")
    
    def get_spam_statistics(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate spam statistics from a batch of posts
        
        Returns:
            Dictionary with spam detection statistics
        """
        results = self.batch_detect_spam(posts)
        
        total_posts = len(results)
        spam_posts = sum(1 for r in results if r['is_spam'])
        avg_confidence = sum(r['confidence'] for r in results) / total_posts if total_posts > 0 else 0
        
        # Most common spam reasons
        all_reasons = []
        for r in results:
            all_reasons.extend(r['reasons'])
        
        reason_counts = {}
        for reason in all_reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        top_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_posts_analyzed': total_posts,
            'spam_posts_detected': spam_posts,
            'spam_rate': spam_posts / total_posts if total_posts > 0 else 0,
            'average_confidence': round(avg_confidence, 3),
            'top_spam_reasons': top_reasons,
            'analysis_timestamp': datetime.now(timezone.utc)
        }


# Convenience functions for easy importing
def detect_spam(text: str, category: str = 'general', **kwargs) -> Dict[str, Any]:
    """Convenience function for spam detection"""
    detector = SpamDetector()
    return detector.detect_spam(text, category, **kwargs)

def create_spam_detector() -> SpamDetector:
    """Factory function to create a spam detector instance"""
    return SpamDetector()
    
