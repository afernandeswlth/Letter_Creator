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

# The "Valuations" custom object (portal 4267461). Each valuation tile associated
# with a deal has its property address as the record title (primaryDisplayProperty).
VALUATION_OBJECT = '2-34929813'

# Deal properties we read from HubSpot to build the CAM prefill.
_PROPS = [
    'dealname',
    'borrower__last_name_s__company_name__trust_name__or_smsf_name__temp_',
    'amount',                       # Proposed Balance
    'primary_deal_purpose',         # Loan Purpose (combined with the loan type)
    'primary_loan_type',
    'split_account_number__loan_facility_number_',
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


def _get_json(url, token):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8'))


def _get_deal(deal_id, token):
    qs = urllib.parse.urlencode({'properties': ','.join(_PROPS)})
    url = f'{HUBSPOT_API}/crm/v3/objects/deals/{urllib.parse.quote(deal_id)}?{qs}'
    return _get_json(url, token)


def _valuation_securities(deal_id, token):
    """Return the security addresses of every valuation tile attached to the deal.

    Each associated Valuations record's title is its property address; these become
    the Proposed Security. Returns [] if none are attached or the lookup fails
    (e.g. the token lacks custom-object scope), so the import degrades gracefully.
    """
    try:
        assoc = _get_json(
            f'{HUBSPOT_API}/crm/v4/objects/deals/{urllib.parse.quote(deal_id)}'
            f'/associations/{VALUATION_OBJECT}', token)
        ids = [r.get('toObjectId') for r in assoc.get('results', []) if r.get('toObjectId')]
        out = []
        for vid in ids:
            rec = _get_json(
                f'{HUBSPOT_API}/crm/v3/objects/{VALUATION_OBJECT}/{vid}'
                f'?properties=security_address', token)
            addr = (rec.get('properties', {}) or {}).get('security_address')
            if addr and addr.strip():
                out.append(addr.strip())
        return out
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError, KeyError):
        return []


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

    # Proposed Security = the address(es) of the valuation tile(s) attached to the deal.
    security = '\n'.join(_valuation_securities(deal_id, token))

    # Loan Purpose = Primary Deal Purpose + Primary Loan Type (e.g. "Purchase — Investment").
    loan_purpose = ' — '.join(x for x in (g('primary_deal_purpose'), g('primary_loan_type')) if x)

    # Refinance 1 notes = current lender + its balance (the form stores refinances
    # as a JSON array of note strings; here we prefill the first one).
    refi_note = ' — '.join(x for x in (
        g('lead___current_lender_name'),
        _money(g('lead___current_loan_balance_for_refinance'))) if x)

    values = {
        'borrowers': g('borrower__last_name_s__company_name__trust_name__or_smsf_name__temp_'),
        'exposureAccount': g('split_account_number__loan_facility_number_'),
        'exposureBalance': _money(g('amount')),
        'exposureLoanPurpose': loan_purpose,
        'proposedSecurity': security,
        'refinanceNotes': json.dumps([refi_note]) if refi_note else '',
    }
    return {k: v for k, v in values.items() if v}
