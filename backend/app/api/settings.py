from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)
settings_bp = Blueprint('settings', __name__)

# In-memory storage for API keys (per session)
# In production, you might want to use encrypted storage or session management
api_keys_storage = {
    'openai': None,
    'claude': None
}


@settings_bp.route('/api-keys', methods=['GET'])
def get_api_keys():
    """Get current API key status (without exposing the actual keys)"""
    return jsonify({
        'openai': {
            'configured': bool(api_keys_storage.get('openai'))
        },
        'claude': {
            'configured': bool(api_keys_storage.get('claude'))
        }
    }), 200


@settings_bp.route('/api-keys', methods=['POST'])
def update_api_keys():
    """Update API keys"""
    try:
        data = request.get_json()
        
        if 'openai_api_key' in data:
            api_key = data['openai_api_key'].strip()
            if api_key:
                api_keys_storage['openai'] = api_key
                logger.info("OpenAI API key updated")
            else:
                api_keys_storage['openai'] = None
                logger.info("OpenAI API key cleared")
        
        if 'claude_api_key' in data:
            api_key = data['claude_api_key'].strip()
            if api_key:
                api_keys_storage['claude'] = api_key
                logger.info("Claude API key updated")
            else:
                api_keys_storage['claude'] = None
                logger.info("Claude API key cleared")
        
        return jsonify({
            'success': True,
            'message': 'API keys updated',
            'status': {
                'openai': bool(api_keys_storage.get('openai')),
                'claude': bool(api_keys_storage.get('claude'))
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error updating API keys: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_api_key(provider):
    """Get API key for a specific provider"""
    return api_keys_storage.get(provider)
