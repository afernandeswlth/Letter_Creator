"""Fetch a HubSpot deal by ID and map it to Credit Approval Memorandum fields.

Requires a HubSpot private-app token in the HUBSPOT_TOKEN environment variable
(scope: crm.objects.deals.read). Uses only the Python standard library so it runs
both in the Nitro dev server (shelled out via cli.py) and the Flask function.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

HUBSPOT_API = 'https://api.hubapi.com'

# Deal properties we read from HubSpot to build the CAM prefill.
_PROPS = [
    'dealname',
    'borrower__last_name_s__company_name__trust_name__or_smsf_name__temp_',
    'loan_amount__excluding_fees_',
    'lead___loan_purpose',
    'primary_loan_type',
    'split_account_number__loan_facility_number_',
    'security_address_1', 'security_address_2', 'security_address_3', 'security_address_4',
    'security_primary_use',
    'lead___property_value',
    'lead___current_lender_name',
    'lead___current_loan_balance_for_refinance',
]


def _money(v):
    """Format a loan amount as $#,###.## — HubSpot stores it as a plain string."""
    if not v:
        return ''
    s = str(v).strip().lstrip('$').replace(',', '')
    try:
        return '${:,.2f}'.format(float(s))
    except ValueError:
        return f'${str(v).strip()}'


def _get_deal(deal_id, token):
    qs = urllib.parse.urlencode({'properties': ','.join(_PROPS)})
    url = f'{HUBSPOT_API}/crm/v3/objects/deals/{urllib.parse.quote(deal_id)}?{qs}'
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8'))


def fetch_deal_values(deal_id):
    """Return a dict of CAM field ids -> values pulled from the HubSpot deal.

    Only non-empty fields are returned, so the form is prefilled with whatever
    HubSpot actually has and the rest is left for the assessor to complete.
    """
    token = os.environ.get('HUBSPOT_TOKEN')
    if not token:
        raise RuntimeError('HUBSPOT_TOKEN is not set on the server.')
    deal_id = (deal_id or '').strip()
    if not deal_id:
        raise RuntimeError('A HubSpot Deal ID is required.')

    try:
        deal = _get_deal(deal_id, token)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise RuntimeError('HubSpot rejected the token (check HUBSPOT_TOKEN and its scopes).')
        if e.code == 404:
            raise RuntimeError(f'No HubSpot deal found with ID {deal_id}.')
        raise RuntimeError(f'HubSpot request failed ({e.code}).')
    except urllib.error.URLError as e:
        raise RuntimeError(f'Could not reach HubSpot: {e.reason}')

    p = deal.get('properties', {}) or {}
    g = lambda k: (p.get(k) or '').strip()  # noqa: E731

    # Security: join the non-empty address lines.
    security = ', '.join(x for x in (
        g('security_address_1'), g('security_address_2'),
        g('security_address_3'), g('security_address_4')) if x)

    # Refinance history: current lender + balance, when present.
    refi_bits = []
    if g('lead___current_lender_name'):
        refi_bits.append(f"Current lender: {g('lead___current_lender_name')}")
    if g('lead___current_loan_balance_for_refinance'):
        refi_bits.append(f"Current balance: {_money(g('lead___current_loan_balance_for_refinance'))}")
    refinance = '\n'.join(refi_bits)

    values = {
        'borrowers': g('borrower__last_name_s__company_name__trust_name__or_smsf_name__temp_'),
        'exposureAccount': g('split_account_number__loan_facility_number_'),
        'exposureBalance': _money(g('loan_amount__excluding_fees_')),
        'exposureLoanPurpose': g('lead___loan_purpose'),
        'proposedSecurity': security,
        'refinanceHistory': refinance,
    }
    return {k: v for k, v in values.items() if v}
