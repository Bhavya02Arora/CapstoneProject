import threading
from datetime import datetime, timezone
from typing import Dict, List
from bson import ObjectId

from .text_moderation import TextModerationService
from .image_moderation import ImageModerationService
from models import PostStatus
from config.database import get_posts_collection

class ModerationService:
    """
    Combined moderation service that orchestrates text and image moderation.
    """
    
    def __init__(self):
        self.text_moderator = TextModerationService()
        self.image_moderator = ImageModerationService()
    
    def moderate_post_async(self, post_id: ObjectId, post_data: Dict, images: List[str]):
        """
        Start asynchronous moderation of a post with both text and images.
        
        Args:
            post_id: MongoDB ObjectId of the post
            post_data: Post data dictionary
            images: List of base64-encoded images
        """
        threading.Thread(
            target=self._moderate_post_complete,
            args=(post_id, post_data, images),
            daemon=True
        ).start()
    
    def _moderate_post_complete(self, post_id: ObjectId, post_data: Dict, images: List[str]):
        """
        Complete moderation process including text and image analysis.
        """
        posts_collection = get_posts_collection()
        
        try:
            print(f"[DEBUG] Starting complete moderation for post {post_id}")
            
            # Step 1: Text Moderation
            text_result = self._moderate_text_content(post_data)
            print(f"[DEBUG] Text moderation completed. Flagged: {text_result['is_flagged']}")
            
            # Step 2: Image Moderation (if images exist)
            image_result = None
            if images and len(images) > 0:
                print(f"[DEBUG] Starting image moderation for {len(images)} images")
                image_result = self.image_moderator.moderate_images(
                    images, 
                    post_data.get('category', 'general')
                )
                print(f"[DEBUG] Image moderation completed. Flagged: {image_result['is_flagged']}")
            
            # Step 3: Combine results and make decision
            moderation_decision = self._make_moderation_decision(text_result, image_result)
            
            # Step 4: Update post based on decision
            self._update_post_status(posts_collection, post_id, moderation_decision)
            
            print(f"[DEBUG] Moderation completed for post {post_id}. Decision: {moderation_decision['action']}")
            
        except Exception as e:
            print(f"[ERROR] Moderation failed for post {post_id}: {str(e)}")
            self._handle_moderation_error(posts_collection, post_id, str(e))
    
    def _moderate_text_content(self, post_data: Dict) -> Dict:
        """
        Moderate text content (title and description)
        """
        category_map = {
            'ROOMMATE': 'roommate',
            'SELL': 'sell',
            'CARPOOL': 'carpool'
        }
        
        category = category_map.get(post_data.get('category', ''), 'general')
        
        # Prepare context for moderation
        context = {
            'price': post_data.get('price'),
            'rent': post_data.get('rent'),
            'location': post_data.get('community') or post_data.get('from_location'),
            'user_email': post_data.get('owner')
        }
        
        # Moderate title and description
        title_result = self.text_moderator.moderate_text(
            post_data.get('title', ''),
            category,
            context
        )
        
        description_result = self.text_moderator.moderate_text(
            post_data.get('description', ''),
            category,
            context
        )
        
        # Get combined summary
        return self.text_moderator.get_moderation_summary(title_result, description_result)
    
    def _make_moderation_decision(self, text_result: Dict, image_result: Dict = None) -> Dict:
        """
        Make final moderation decision based on text and image results.
        """
        decision = {
            'action': 'APPROVE',
            'reason': '',
            'confidence': 0.0,
            'all_issues': [],
            'text_analysis': text_result,
            'image_analysis': image_result,
            'timestamp': datetime.now(timezone.utc)
        }
        
        # Check text moderation
        if text_result['is_flagged']:
            decision['action'] = 'REJECT'
            decision['reason'] = 'Text content flagged for review'
            decision['confidence'] = text_result['confidence']
            decision['all_issues'].extend(text_result['issues'])
        
        # Check image moderation
        if image_result and image_result['is_flagged']:
            decision['action'] = 'REJECT'
            if decision['reason']:
                decision['reason'] += '; Images flagged for review'
            else:
                decision['reason'] = 'Images flagged for review'
            decision['confidence'] = max(decision['confidence'], image_result['confidence'])
            decision['all_issues'].extend(image_result['issues'])
        
        # If both passed
        if decision['action'] == 'APPROVE':
            decision['reason'] = 'Content passed all moderation checks'
            decision['confidence'] = max(
                text_result.get('confidence', 0.0),
                image_result.get('confidence', 0.0) if image_result else 0.0
            )
        
        return decision
    
    def _update_post_status(self, posts_collection, post_id: ObjectId, decision: Dict):
        """
        Update post status in database based on moderation decision.
        """
        if decision['action'] == 'APPROVE':
            update_data = {
                "status": PostStatus.PUBLISHED.value,
                "moderation_passed_at": datetime.now(timezone.utc),
                "moderation_analysis": {
                    'text_analysis': decision['text_analysis'],
                    'image_analysis': decision['image_analysis'],
                    'confidence': decision['confidence'],
                    'checked_at': decision['timestamp']
                }
            }
        else:
            update_data = {
                "status": PostStatus.FAILED.value,
                "moderation_reason": decision['reason'],
                "moderation_completed_at": datetime.now(timezone.utc),
                "moderation_analysis": {
                    'text_analysis': decision['text_analysis'],
                    'image_analysis': decision['image_analysis'],
                    'confidence': decision['confidence'],
                    'issues': decision['all_issues'],
                    'detected_at': decision['timestamp']
                }
            }
        
        posts_collection.update_one({"_id": post_id}, {"$set": update_data})
    
    def _handle_moderation_error(self, posts_collection, post_id: ObjectId, error_message: str):
        """
        Handle moderation errors by updating post status.
        """
        posts_collection.update_one(
            {"_id": post_id},
            {"$set": {
                "status": PostStatus.FAILED.value,
                "moderation_error": error_message,
                "failed_at": datetime.now(timezone.utc)
            }}
        )
    
    def check_spam_preview(self, title: str, description: str, category: str = 'general') -> Dict:
        """
        Preview spam check for testing purposes (synchronous).
        """
        title_result = self.text_moderator.moderate_text(title, category)
        description_result = self.text_moderator.moderate_text(description, category)
        
        return self.text_moderator.get_moderation_summary(title_result, description_result)