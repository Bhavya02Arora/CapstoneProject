import re
from typing import Dict, List, Tuple
from datetime import datetime, timezone

class TextModerationService:
    """
    Enhanced text moderation service for detecting inappropriate content,
    spam, and policy violations in user posts.
    """
    
    def __init__(self):
        # Define inappropriate content patterns
        self.profanity_patterns = [
            r'\b(?:fuck|shit|damn|bitch|asshole|bastard|crap)\b',
            r'\b(?:wtf|stfu|gtfo)\b',
            # Add more patterns as needed
        ]
        
        # Spam indicators
        self.spam_patterns = [
            r'\b(?:buy now|limited time|act fast|urgent|guaranteed)\b',
            r'\b(?:free money|work from home|make \$\d+)\b',
            r'(?:http[s]?://|www\.)[^\s]+',  # URLs (suspicious in some contexts)
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
        ]
        
        # Suspicious content patterns
        self.suspicious_patterns = [
            r'\b(?:drugs|weed|marijuana|cocaine|pills|mdma)\b',
            r'\b(?:fake id|fake ids|underage drinking)\b',
            r'\b(?:cheat|plagiarism|essay writing service)\b',
            r'\b(?:harassment|stalking|threatening)\b',
        ]
        
        # Academic dishonesty patterns
        self.academic_dishonesty_patterns = [
            r'\b(?:homework help|do my homework|write my essay)\b',
            r'\b(?:test answers|exam solutions|assignment answers)\b',
            r'\b(?:chegg|course hero|studyblue) (?:account|answers)\b',
        ]
        
        # Price manipulation patterns (for marketplace posts)
        self.price_patterns = [
            r'\$0\.01|\$1\.00|free(?!\s+(?:shipping|delivery))',
            r'(?:dm|message|text) (?:me )?for (?:price|cost)',
        ]
    
    def moderate_text(self, text: str, category: str = 'general', context: Dict = None) -> Dict:
        """
        Main moderation function that analyzes text content.
        
        Args:
            text: The text content to moderate
            category: The category of the post (roommate, sell, carpool, general)
            context: Additional context like user info, price, etc.
            
        Returns:
            Dict with moderation results
        """
        if not text or not isinstance(text, str):
            return self._create_result(False, 0.0, [], "Empty or invalid text")
        
        text = text.lower().strip()
        
        if len(text) < 5:
            return self._create_result(False, 0.1, [], "Text too short for meaningful analysis")
        
        issues = []
        confidence_scores = []
        
        # Check for profanity
        profanity_result = self._check_profanity(text)
        if profanity_result['found']:
            issues.extend(profanity_result['issues'])
            confidence_scores.append(profanity_result['confidence'])
        
        # Check for spam
        spam_result = self._check_spam_patterns(text, category, context)
        if spam_result['found']:
            issues.extend(spam_result['issues'])
            confidence_scores.append(spam_result['confidence'])
        
        # Check for suspicious content
        suspicious_result = self._check_suspicious_content(text)
        if suspicious_result['found']:
            issues.extend(suspicious_result['issues'])
            confidence_scores.append(suspicious_result['confidence'])
        
        # Check for academic dishonesty
        academic_result = self._check_academic_dishonesty(text)
        if academic_result['found']:
            issues.extend(academic_result['issues'])
            confidence_scores.append(academic_result['confidence'])
        
        # Category-specific checks
        category_result = self._check_category_specific(text, category, context)
        if category_result['found']:
            issues.extend(category_result['issues'])
            confidence_scores.append(category_result['confidence'])
        
        # Calculate overall confidence
        max_confidence = max(confidence_scores) if confidence_scores else 0.0
        should_flag = max_confidence > 0.6 or len(issues) >= 3
        
        return self._create_result(
            should_flag, 
            max_confidence, 
            issues,
            "Content flagged for review" if should_flag else "Content passed moderation"
        )
    
    def _check_profanity(self, text: str) -> Dict:
        """Check for profanity and inappropriate language"""
        issues = []
        confidence = 0.0
        
        for pattern in self.profanity_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                issues.append(f"Inappropriate language detected: {len(matches)} instances")
                confidence = max(confidence, 0.8)
        
        return {'found': len(issues) > 0, 'issues': issues, 'confidence': confidence}
    
    def _check_spam_patterns(self, text: str, category: str, context: Dict = None) -> Dict:
        """Check for spam patterns"""
        issues = []
        confidence = 0.0
        
        # Basic spam patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append("Potential spam content detected")
                confidence = max(confidence, 0.7)
        
        # Repetitive content
        words = text.split()
        if len(set(words)) < len(words) * 0.5 and len(words) > 10:
            issues.append("Repetitive content detected")
            confidence = max(confidence, 0.6)
        
        # Excessive capitalization
        if len(re.findall(r'[A-Z]', text)) > len(text) * 0.3:
            issues.append("Excessive capitalization")
            confidence = max(confidence, 0.5)
        
        # Multiple exclamation marks
        if len(re.findall(r'!{2,}', text)) > 0:
            issues.append("Excessive punctuation")
            confidence = max(confidence, 0.4)
        
        return {'found': len(issues) > 0, 'issues': issues, 'confidence': confidence}
    
    def _check_suspicious_content(self, text: str) -> Dict:
        """Check for suspicious or prohibited content"""
        issues = []
        confidence = 0.0
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append("Suspicious content detected")
                confidence = max(confidence, 0.9)
        
        return {'found': len(issues) > 0, 'issues': issues, 'confidence': confidence}
    
    def _check_academic_dishonesty(self, text: str) -> Dict:
        """Check for academic dishonesty patterns"""
        issues = []
        confidence = 0.0
        
        for pattern in self.academic_dishonesty_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append("Potential academic dishonesty detected")
                confidence = max(confidence, 0.8)
        
        return {'found': len(issues) > 0, 'issues': issues, 'confidence': confidence}
    
    def _check_category_specific(self, text: str, category: str, context: Dict = None) -> Dict:
        """Category-specific moderation checks"""
        issues = []
        confidence = 0.0
        
        if category == 'sell':
            # Check for suspicious pricing
            for pattern in self.price_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    issues.append("Suspicious pricing detected")
                    confidence = max(confidence, 0.6)
        
        elif category == 'roommate':
            # Check for discriminatory language
            discriminatory_patterns = [
                r'\b(?:no (?:blacks|whites|asians|hispanics|jews|muslims|christians))\b',
                r'\b(?:males only|females only|boys only|girls only)\b',
            ]
            for pattern in discriminatory_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    issues.append("Potentially discriminatory language")
                    confidence = max(confidence, 0.9)
        
        elif category == 'carpool':
            # Check for safety concerns
            safety_patterns = [
                r'\b(?:party|drinking|alcohol|drunk driving)\b',
                r'\b(?:no questions asked|cash only|off the books)\b',
            ]
            for pattern in safety_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    issues.append("Safety concerns detected")
                    confidence = max(confidence, 0.7)
        
        return {'found': len(issues) > 0, 'issues': issues, 'confidence': confidence}
    
    def _create_result(self, is_flagged: bool, confidence: float, issues: List[str], message: str) -> Dict:
        """Create a standardized moderation result"""
        return {
            'is_flagged': is_flagged,
            'confidence': round(confidence, 3),
            'issues': issues,
            'message': message,
            'timestamp': datetime.now(timezone.utc),
            'total_issues': len(issues)
        }
    
    def get_moderation_summary(self, title_result: Dict, description_result: Dict) -> Dict:
        """Combine moderation results for title and description"""
        combined_issues = title_result['issues'] + description_result['issues']
        max_confidence = max(title_result['confidence'], description_result['confidence'])
        is_flagged = title_result['is_flagged'] or description_result['is_flagged']
        
        return {
            'is_flagged': is_flagged,
            'confidence': max_confidence,
            'total_issues': len(combined_issues),
            'issues': combined_issues,
            'title_analysis': title_result,
            'description_analysis': description_result,
            'recommendation': 'REJECT' if is_flagged else 'APPROVE',
            'message': 'Content requires review' if is_flagged else 'Content approved'
        }