# Services package
from .utils import generate_log_hash, write_log_to_csv, check_tc_kimlik_no
from .analytics import AnalyticsService

# Alias for validate_tc_kimlik_no
def validate_tc_kimlik_no(tc):
    return check_tc_kimlik_no(tc)

__all__ = [
    'generate_log_hash',
    'write_log_to_csv', 
    'check_tc_kimlik_no',
    'validate_tc_kimlik_no',
    'AnalyticsService'
]
