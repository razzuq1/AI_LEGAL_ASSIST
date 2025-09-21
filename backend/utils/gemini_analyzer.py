import json
import re
from typing import Dict, List

import google.generativeai as genai


class GeminiAnalyzer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def analyze_document(self, text: str) -> Dict:
        try:
            prompt = f"""
            Analyze this legal document comprehensively:

            {text[:8000]}  # Limit to avoid token limits

            Please provide:
            1. Document Type (contract, agreement, policy, etc.)
            2. Detailed Summary (minimum 200 words)
            3. Key Parties Involved
            4. Important Dates and Deadlines
            5. Financial Terms and Amounts
            6. Key Terms and Definitions (at least 10)
            7. Rights and Obligations of each party
            8. Risks and Red Flags (categorize as High, Medium, Low)
            9. Recommendations and Action Items

            Format as JSON with these keys: document_type, summary, parties, dates, financial_terms, key_terms, rights_obligations, risks, recommendations
            """

            response = self.model.generate_content(prompt)

            # Try to parse JSON, fallback to structured text
            try:
                result = json.loads(response.text)
            except:
                result = self._parse_text_response(response.text)

            return self._format_analysis(result)

        except Exception as e:
            return {
                'document_type': 'Legal Document',
                'summary': f'Analysis error: {str(e)}. Document processed but detailed analysis unavailable.',
                'parties': [],
                'dates': [],
                'financial_terms': [],
                'key_terms': [],
                'rights_obligations': {},
                'risks': [],
                'recommendations': [],
            }

    def answer_question(self, text: str, question: str, context: Dict = None) -> str:
        try:
            context_info = ""
            if context:
                context_info = f"Previous analysis: {json.dumps(context, indent=2)}"

            prompt = f"""
            Document content:
            {text[:6000]}
            
            {context_info}
            
            Question: {question}
            
            Please provide a detailed, accurate answer based on the document content. 
            If the information is not in the document, clearly state that.
            Cite specific sections when possible.
            """

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            return f"Sorry, I couldn't process your question: {str(e)}"

    def _parse_text_response(self, text: str) -> Dict:
        """Parse non-JSON response into structured format"""
        result = {
            'document_type': 'Legal Document',
            'summary': '',
            'parties': [],
            'dates': [],
            'financial_terms': [],
            'key_terms': [],
            'rights_obligations': {},
            'risks': [],
            'recommendations': [],
        }

        # Extract sections using regex
        sections = {
            'summary': r'(?i)summary[:\-]?\s*(.*?)(?=\n\n|\n[A-Z]|$)',
            'document_type': r'(?i)document type[:\-]?\s*(.*?)(?=\n|\.|,)',
        }

        for key, pattern in sections.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                result[key] = match.group(1).strip()

        return result

    def _format_analysis(self, result: Dict) -> Dict:
        """Format and validate analysis results"""
        formatted = {
            'document_type': result.get('document_type', 'Legal Document'),
            'summary': result.get('summary', 'Document analysis completed.'),
            'parties': result.get('parties', []),
            'dates': result.get('dates', []),
            'financial_terms': result.get('financial_terms', []),
            'key_terms': self._format_key_terms(result.get('key_terms', [])),
            'rights_obligations': result.get('rights_obligations', {}),
            'risks': self._format_risks(result.get('risks', [])),
            'recommendations': result.get('recommendations', []),
        }

        return formatted

    def _format_key_terms(self, terms) -> List[Dict]:
        """Format key terms into consistent structure"""
        if isinstance(terms, dict):
            return [{'term': k, 'definition': v} for k, v in terms.items()]
        elif isinstance(terms, list):
            formatted = []
            for term in terms:
                if isinstance(term, dict) and 'term' in term:
                    formatted.append(term)
                elif isinstance(term, str) and ':' in term:
                    parts = term.split(':', 1)
                    formatted.append({'term': parts[0].strip(), 'definition': parts[1].strip()})
            return formatted
        return []

    def _format_risks(self, risks) -> List[Dict]:
        """Format risks into consistent structure"""
        if not risks:
            return [
                {'title': 'No specific risks identified', 'description': 'Document appears standard', 'level': 'Low'}
            ]

        formatted = []
        for risk in risks:
            if isinstance(risk, dict):
                formatted.append(
                    {
                        'title': risk.get('title', 'Risk'),
                        'description': risk.get('description', 'Review required'),
                        'level': risk.get('level', 'Medium'),
                    }
                )
            elif isinstance(risk, str):
                formatted.append(
                    {'title': risk[:50] + '...' if len(risk) > 50 else risk, 'description': risk, 'level': 'Medium'}
                )

        return formatted
