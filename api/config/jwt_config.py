from flask_jwt_extended import JWTManager

# To store blacklisted tokens (in production, use Redis database)
blacklisted_tokens = set()

def init_jwt(app):
    """Initialize JWT manager and configure token blacklist"""
    jwt = JWTManager(app)
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']  # JWT ID
        return jti in blacklisted_tokens
    
    return jwt

def blacklist_token(jti):
    """Add token to blacklist"""
    blacklisted_tokens.add(jti)