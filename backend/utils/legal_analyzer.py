import re
from datetime import datetime
from typing import Any, Dict, List


class L:
    def __init__(self):
        self.p = {
            'termination': [
                r'terminat[e|ion|ed].*?(?:clause|provision|section)',
                r'end.*?(?:agreement|contract)',
                r'breach.*?(?:terminat|dissolv)',
            ],
            'payment': [
                r'payment.*?(?:due|term|schedule)',
                r'invoice.*?(?:within|days|payment)',
                r'\$\d+.*?(?:paid|due|owed)',
            ],
            'liability': [
                r'liabilit.*?(?:limit|exclud|disclaim)',
                r'damages.*?(?:consequential|indirect|special)',
                r'indemnif.*?(?:hold harmless|defend)',
            ],
            'confidentiality': [
                r'confidential.*?(?:information|material|data)',
                r'non.*?disclosure',
                r'proprietary.*?information',
            ],
            'intellectual_property': [
                r'intellectual.*?property',
                r'copyright.*?(?:own|transfer|assign)',
                r'patent.*?(?:right|license|infring)',
            ],
        }

    def ct(self, t: str) -> str:
        tl = t.lower()

        cts = {
            'employment': ['employment', 'employee', 'salary', 'wage', 'job', 'work agreement'],
            'service': ['service agreement', 'services', 'consultant', 'contractor'],
            'nda': ['non-disclosure', 'confidentiality agreement', 'confidential'],
            'lease': ['lease', 'rent', 'premises', 'landlord', 'tenant'],
            'purchase': ['purchase', 'sale', 'buy', 'sell', 'goods'],
            'license': ['license', 'licensing', 'grant', 'permit'],
        }

        scores = {}
        for ct, kws in cts.items():
            score = sum(1 for kw in kws if kw in tl)
            if score > 0:
                scores[ct] = score

        if scores:
            return max(scores.items(), key=lambda x: x[1])[0].replace('_', ' ').title()

        return 'General Contract'

    def ep(self, t: str) -> List[str]:
        parties = []

        pps = [
            r'between\s+(.*?)\s+and\s+(.*?)(?:\s|,|\.|$)',
            r'party.*?(?:"([^"]+)"|\'([^\']+)\')',
            r'(?:company|corporation|individual).*?"([^"]+)"',
        ]

        for p in pps:
            matches = re.finditer(p, t, re.IGNORECASE)
            for m in matches:
                for g in m.groups():
                    if g and len(g.strip()) > 2:
                        parties.append(g.strip())

        parties = list(set([p for p in parties if len(p) < 100]))
        return parties[:5]

    def ed(self, t: str) -> List[Dict[str, str]]:
        dates = []

        dps = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4})',
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{2,4})',
        ]

        for p in dps:
            matches = re.finditer(p, t, re.IGNORECASE)
            for m in matches:
                dc = t[max(0, m.start() - 50) : m.end() + 50]
                dates.append({'date': m.group(1), 'context': dc.strip()})

        return dates[:10]

    def em(self, t: str) -> List[Dict[str, str]]:
        amounts = []

        mps = [
            r'\$[\d,]+(?:\.\d{2})?',
            r'(?:USD|dollars?)\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*(?:USD|dollars?)',
        ]

        for p in mps:
            matches = re.finditer(p, t, re.IGNORECASE)
            for m in matches:
                ac = t[max(0, m.start() - 30) : m.end() + 30]
                amounts.append({'amount': m.group(0), 'context': ac.strip()})

        return amounts[:10]

    def ar(self, t: str) -> List[Dict[str, str]]:
        risks = []
        tl = t.lower()

        ri = {
            'high': {
                'patterns': [
                    'unlimited liability',
                    'personal guarantee',
                    'automatic renewal',
                    'non-compete',
                    'liquidated damages',
                ],
                'descriptions': {
                    'unlimited liability': 'Contract may expose unlimited financial liability',
                    'personal guarantee': 'Personal assets may be at risk',
                    'automatic renewal': 'Contract may renew automatically',
                    'non-compete': 'May restrict ability to work',
                    'liquidated damages': 'Pre-determined penalty amounts may be high',
                },
            },
            'medium': {
                'patterns': [
                    'force majeure',
                    'arbitration required',
                    'choice of law',
                    'indemnification',
                    'termination for convenience',
                ],
                'descriptions': {
                    'force majeure': 'Contract may be suspended due to circumstances',
                    'arbitration required': 'Disputes through arbitration',
                    'choice of law': 'Governed by specific laws',
                    'indemnification': 'May need to defend other party',
                    'termination for convenience': 'May be terminated without cause',
                },
            },
            'low': {
                'patterns': ['confidentiality', 'intellectual property', 'payment terms', 'delivery schedule'],
                'descriptions': {
                    'confidentiality': 'Standard confidentiality obligations',
                    'intellectual property': 'IP ownership terms specified',
                    'payment terms': 'Payment schedule defined',
                    'delivery schedule': 'Delivery timelines established',
                },
            },
        }

        for rl, rd in ri.items():
            for p in rd['patterns']:
                if p in tl:
                    risks.append(
                        {
                            'title': p.replace('_', ' ').title(),
                            'description': rd['descriptions'].get(p, f'{p} detected'),
                            'level': rl.title(),
                        }
                    )

        return risks

    def gs(self, t: str) -> Dict[str, Any]:
        return {
            'contract_type': self.ct(t),
            'parties': self.ep(t),
            'dates': self.ed(t),
            'monetary_amounts': self.em(t),
            'word_count': len(t.split()),
            'character_count': len(t),
            'analysis_date': datetime.now().isoformat(),
        }
