"""
TSA API Views
Gerçek TSA servisleri için API endpoint'leri
"""

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
import hashlib
import base64
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class TSAAPIView(View):
    """TSA API Endpoint"""
    
    def post(self, request):
        """Timestamp request endpoint"""
        try:
            # Content-Type kontrolü
            content_type = request.content_type
            if content_type not in ['application/timestamp-query', 'application/json']:
                return HttpResponse(
                    'Unsupported Media Type',
                    status=415,
                    content_type='text/plain'
                )
            
            # Request body'yi al
            if content_type == 'application/json':
                data = json.loads(request.body)
                hash_value = data.get('hash')
                nonce = data.get('nonce')
            else:
                # RFC 3161 format (basit implementasyon)
                hash_value = request.body.decode()
                nonce = None
            
            if not hash_value:
                return HttpResponse(
                    'Bad Request: Hash required',
                    status=400,
                    content_type='text/plain'
                )
            
            # Timestamp oluştur
            timestamp = datetime.now(timezone.utc)
            
            # Basit timestamp token oluştur
            token_data = {
                'hash': hash_value,
                'timestamp': timestamp.isoformat(),
                'nonce': nonce,
                'algorithm': 'SHA256',
                'version': '1.0',
                'tsa': '5651Log-TSA'
            }
            
            # Token'ı encode et
            token_json = json.dumps(token_data)
            token_b64 = base64.b64encode(token_json.encode()).decode()
            
            # Response oluştur
            response_data = {
                'status': 'success',
                'timestamp_token': token_b64,
                'timestamp': timestamp.isoformat(),
                'hash': hash_value,
                'algorithm': 'SHA256'
            }
            
            logger.info(f"TSA timestamp request successful: {hash_value[:16]}...")
            
            return JsonResponse(response_data, status=200)
            
        except json.JSONDecodeError:
            return HttpResponse(
                'Bad Request: Invalid JSON',
                status=400,
                content_type='text/plain'
            )
        except Exception as e:
            logger.error(f"TSA API error: {str(e)}")
            return HttpResponse(
                f'Internal Server Error: {str(e)}',
                status=500,
                content_type='text/plain'
            )
    
    def get(self, request):
        """TSA status endpoint"""
        return JsonResponse({
            'status': 'active',
            'service': '5651Log TSA',
            'version': '1.0',
            'algorithm': 'SHA256',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })


@csrf_exempt
@require_http_methods(["POST"])
def verify_timestamp(request):
    """Timestamp verification endpoint"""
    try:
        data = json.loads(request.body)
        timestamp_token = data.get('timestamp_token')
        original_hash = data.get('hash')
        
        if not timestamp_token or not original_hash:
            return JsonResponse({
                'status': 'error',
                'message': 'timestamp_token and hash required'
            }, status=400)
        
        # Token'ı decode et
        try:
            token_json = base64.b64decode(timestamp_token).decode()
            token_data = json.loads(token_json)
        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid timestamp token'
            }, status=400)
        
        # Hash kontrolü
        hash_match = token_data.get('hash') == original_hash
        
        # Timestamp kontrolü (basit)
        timestamp_str = token_data.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                time_diff = abs((now - timestamp).total_seconds())
                time_valid = time_diff < 86400  # 24 saat
            except Exception:
                time_valid = False
        else:
            time_valid = False
        
        # Sonuç
        is_valid = hash_match and time_valid
        
        response_data = {
            'status': 'success',
            'valid': is_valid,
            'hash_match': hash_match,
            'time_valid': time_valid,
            'timestamp': token_data.get('timestamp'),
            'algorithm': token_data.get('algorithm'),
            'tsa': token_data.get('tsa')
        }
        
        logger.info(f"TSA verification: {original_hash[:16]}... -> {'valid' if is_valid else 'invalid'}")
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"TSA verification error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
