"""
Dynamic Prompt Generator for AI Legal Assistant
Generates contextual questions based on document type and content
"""

import re
from typing import Dict, List, Tuple


class PromptGenerator:
    """Generate dynamic prompts based on document analysis"""

    def __init__(self):
        self.document_patterns = {
            'employment': [
                'employment',
                'employee',
                'employer',
                'job',
                'salary',
                'wages',
                'benefits',
                'vacation',
                'sick leave',
                'termination',
            ],
            'service_agreement': [
                'service',
                'services',
                'consultant',
                'contractor',
                'deliverable',
                'milestone',
                'project',
                'scope of work',
            ],
            'nda': ['confidential', 'non-disclosure', 'proprietary', 'trade secret', 'confidentiality', 'disclosure'],
            'lease': [
                'lease',
                'rent',
                'tenant',
                'landlord',
                'premises',
                'property',
                'monthly payment',
                'security deposit',
            ],
            'purchase': [
                'purchase',
                'sale',
                'buy',
                'sell',
                'buyer',
                'seller',
                'goods',
                'merchandise',
                'delivery',
                'warranty',
            ],
            'partnership': [
                'partner',
                'partnership',
                'joint venture',
                'equity',
                'profit sharing',
                'management',
                'capital contribution',
            ],
            'license': ['license', 'licensing', 'intellectual property', 'copyright', 'patent', 'trademark', 'royalty'],
        }

        self.prompt_templates = {
            'employment': [
                "What is the salary and compensation structure?",
                "What are the employee benefits and perks?",
                "What are the termination conditions and notice periods?",
                "Are there any non-compete or non-solicitation clauses?",
                "What are the working hours and vacation policies?",
                "What are the performance evaluation criteria?",
                "Are there any stock options or equity compensation?",
                "What are the confidentiality requirements for employees?",
            ],
            'service_agreement': [
                "What specific services are being provided?",
                "What are the key deliverables and timelines?",
                "How is the quality of service measured?",
                "What are the payment terms and fee structure?",
                "What happens if the service provider fails to deliver?",
                "Are there any penalties for late delivery?",
                "What are the intellectual property ownership rights?",
                "How can this agreement be terminated?",
            ],
            'nda': [
                "What information is considered confidential?",
                "How long does the confidentiality obligation last?",
                "What are the permitted uses of confidential information?",
                "What are the exceptions to confidentiality requirements?",
                "What are the penalties for unauthorized disclosure?",
                "Are there any return or destruction requirements?",
                "Does this cover future information shared?",
                "What happens if confidential information is accidentally disclosed?",
            ],
            'lease': [
                "What is the monthly rent and when is it due?",
                "What is the lease term and renewal options?",
                "What utilities and services are included?",
                "What are the tenant's maintenance responsibilities?",
                "Are pets allowed and what are the restrictions?",
                "What is the security deposit amount and terms?",
                "What are the rules for subletting or assignment?",
                "What happens if rent is paid late?",
            ],
            'purchase': [
                "What is being purchased and at what price?",
                "What are the delivery terms and timeline?",
                "What warranties are provided with the goods?",
                "What are the payment terms and methods?",
                "Who bears the risk of loss during shipping?",
                "What happens if goods are defective or damaged?",
                "Are there any return or exchange policies?",
                "What are the dispute resolution procedures?",
            ],
            'partnership': [
                "What are each partner's capital contributions?",
                "How are profits and losses distributed?",
                "What are the management responsibilities of each partner?",
                "How are major decisions made in the partnership?",
                "What happens if a partner wants to leave?",
                "How are new partners admitted to the partnership?",
                "What are the restrictions on partner activities?",
                "How is the partnership dissolved?",
            ],
            'license': [
                "What intellectual property is being licensed?",
                "Is this an exclusive or non-exclusive license?",
                "What are the permitted uses of the licensed property?",
                "What royalties or fees must be paid?",
                "How long does the license term last?",
                "Can the license be transferred to others?",
                "What are the quality control requirements?",
                "Under what conditions can the license be terminated?",
            ],
            'general': [
                "What are the main obligations of each party?",
                "What are the key dates and deadlines mentioned?",
                "What are the payment terms and amounts?",
                "What happens if someone breaches this agreement?",
                "How can this agreement be terminated?",
                "What are the dispute resolution procedures?",
                "Are there any penalties or liquidated damages?",
                "What law governs this agreement?",
            ],
        }

    def detect_document_type(self, text: str) -> str:
        """Detect document type based on content analysis"""
        text_lower = text.lower()
        scores = {}

        for doc_type, keywords in self.document_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[doc_type] = score

        if not scores or max(scores.values()) == 0:
            return 'general'

        return max(scores.items(), key=lambda x: x[1])[0]

    def extract_contextual_info(self, text: str) -> Dict[str, List[str]]:
        """Extract contextual information for more specific prompts"""
        info = {'parties': [], 'amounts': [], 'dates': [], 'terms': []}

        # Extract monetary amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*dollars?'
        amounts = re.findall(money_pattern, text, re.IGNORECASE)
        info['amounts'] = amounts[:5]  # Limit to first 5

        # Extract dates
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        ]

        for pattern in date_patterns:
            dates = re.findall(pattern, text, re.IGNORECASE)
            info['dates'].extend(dates)

        info['dates'] = list(set(info['dates']))[:5]  # Remove duplicates, limit to 5

        # Extract potential party names (capitalized words/phrases)
        party_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|LLC|Corp|Ltd|Company)\.?)?'
        parties = re.findall(party_pattern, text)

        # Filter out common legal terms
        exclude_terms = {
            'Agreement',
            'Contract',
            'Party',
            'Parties',
            'This',
            'The',
            'Terms',
            'Conditions',
            'Section',
            'Article',
            'Clause',
        }

        parties = [p for p in parties if p not in exclude_terms]
        info['parties'] = list(set(parties))[:3]  # Unique parties, limit to 3

        return info

    def generate_contextual_prompts(self, text: str, doc_type: str, context_info: Dict[str, List[str]]) -> List[str]:
        """Generate contextual prompts based on document content"""
        contextual_prompts = []

        # Add amount-specific prompts
        if context_info['amounts']:
            contextual_prompts.extend(
                [
                    f"What does the amount {context_info['amounts'][0]} represent?",
                    "Are there any additional fees or costs mentioned?",
                ]
            )

        # Add date-specific prompts
        if context_info['dates']:
            contextual_prompts.extend(
                [
                    f"What is the significance of {context_info['dates'][0]}?",
                    "What are all the important deadlines in this document?",
                ]
            )

        # Add party-specific prompts
        if len(context_info['parties']) >= 2:
            party1, party2 = context_info['parties'][:2]
            contextual_prompts.extend(
                [
                    f"What are {party1}'s main responsibilities?",
                    f"What are {party2}'s main obligations?",
                    f"How is the relationship between {party1} and {party2} structured?",
                ]
            )

        # Add document-specific contextual prompts
        text_lower = text.lower()

        if 'indemnify' in text_lower or 'indemnification' in text_lower:
            contextual_prompts.append("What are the indemnification provisions?")

        if 'force majeure' in text_lower:
            contextual_prompts.append("What constitutes a force majeure event?")

        if 'arbitration' in text_lower:
            contextual_prompts.append("What are the arbitration procedures?")

        if 'intellectual property' in text_lower:
            contextual_prompts.append("How are intellectual property rights handled?")

        return contextual_prompts[:6]  # Limit to 6 contextual prompts

    def generate_prompts(self, document_text: str, analysis_data: Dict = None) -> List[str]:
        """Generate dynamic prompts based on document content and analysis"""

        # Detect document type
        if analysis_data and 'document_type' in analysis_data:
            doc_type_full = analysis_data['document_type'].lower()
            # Map full document type to our categories
            if 'employment' in doc_type_full:
                doc_type = 'employment'
            elif 'service' in doc_type_full:
                doc_type = 'service_agreement'
            elif 'disclosure' in doc_type_full or 'nda' in doc_type_full:
                doc_type = 'nda'
            elif 'lease' in doc_type_full:
                doc_type = 'lease'
            elif 'purchase' in doc_type_full or 'sale' in doc_type_full:
                doc_type = 'purchase'
            elif 'partnership' in doc_type_full:
                doc_type = 'partnership'
            elif 'license' in doc_type_full:
                doc_type = 'license'
            else:
                doc_type = self.detect_document_type(document_text)
        else:
            doc_type = self.detect_document_type(document_text)

        # Get base prompts for document type
        base_prompts = self.prompt_templates.get(doc_type, self.prompt_templates['general'])

        # Extract contextual information
        context_info = self.extract_contextual_info(document_text)

        # Generate contextual prompts
        contextual_prompts = self.generate_contextual_prompts(document_text, doc_type, context_info)

        # Combine and prioritize prompts
        all_prompts = base_prompts[:4] + contextual_prompts[:4]

        # Remove duplicates while preserving order
        seen = set()
        unique_prompts = []
        for prompt in all_prompts:
            if prompt not in seen:
                seen.add(prompt)
                unique_prompts.append(prompt)

        return unique_prompts[:8]

    def get_document_description(self, doc_type: str) -> str:
        """Get a user-friendly description of the document type"""
        descriptions = {
            'employment': 'Employment Contract - Governs the relationship between employer and employee',
            'service_agreement': 'Service Agreement - Defines services to be provided and terms',
            'nda': 'Non-Disclosure Agreement - Protects confidential information',
            'lease': 'Lease Agreement - Rental terms for property or equipment',
            'purchase': 'Purchase Agreement - Terms for buying/selling goods or services',
            'partnership': 'Partnership Agreement - Structure and terms for business partnership',
            'license': 'License Agreement - Terms for using intellectual property',
            'general': 'Legal Document - Contains legal terms and obligations',
        }
        return descriptions.get(doc_type, descriptions['general'])
