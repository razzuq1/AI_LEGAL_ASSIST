import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List

import google.generativeai as genai


class RAGPipeline:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", embedding_model: str = "text-embedding-004"):
        self.api_key = api_key
        self.model_name = model
        self.embedding_model = embedding_model
        self.documents = {}
        self.vector_store = {}

        # Check if we have AI capabilities
        self.ai_available = bool(api_key)
        if self.ai_available:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(model)
                print(f"✅ Gemini AI initialized with model: {model}")
            except Exception as e:
                print(f"⚠️ Gemini initialization failed: {e}")
                self.ai_available = False
        else:
            print("⚠️ No AI key - Using basic analysis")

    def create_vector_store(self, docs: List, document_id: str):
        """Create vector store for document chunks with robust error handling"""
        try:
            if not docs:
                print("⚠️ No documents provided for vector store")
                self.vector_store[document_id] = []
                return []

            processed_docs = []
            for i, doc in enumerate(docs):
                try:
                    if isinstance(doc, dict):
                        content = doc.get('page_content', str(doc))
                        metadata = doc.get('metadata', {})
                    elif hasattr(doc, 'page_content'):
                        content = doc.page_content
                        metadata = getattr(doc, 'metadata', {}) if hasattr(doc, 'metadata') else {}
                    else:
                        content = str(doc)
                        metadata = {'source': 'string_conversion', 'index': i}

                    # Validate content
                    if not content or not content.strip():
                        print(f"⚠️ Empty content in document {i}, skipping")
                        continue

                    processed_docs.append(
                        {
                            'content': content.strip(),
                            'metadata': {**metadata, 'doc_index': i, 'processed_at': datetime.now().isoformat()},
                        }
                    )

                except Exception as e:
                    print(f"⚠️ Error processing document {i}: {e}")
                    continue

            # Ensure we have at least one document
            if not processed_docs:
                processed_docs = [
                    {
                        'content': 'No valid content found in uploaded documents',
                        'metadata': {'fallback': True, 'doc_count': len(docs)},
                    }
                ]

            self.vector_store[document_id] = processed_docs
            print(f"✅ Vector store created with {len(processed_docs)} documents")
            return processed_docs

        except Exception as e:
            print(f"❌ Vector store creation failed: {e}")
            fallback_docs = [
                {'content': f'Vector store error: {str(e)}', 'metadata': {'error': True, 'fallback': True}}
            ]
            self.vector_store[document_id] = fallback_docs
            return fallback_docs

    def analyze_document(self, docs: List, document_id: str) -> Dict[str, Any]:
        """Analyze documents with comprehensive error handling"""
        try:
            if not docs:
                return self._create_error_analysis(document_id, "No documents provided")

            # Create vector store with error handling
            try:
                vector_docs = self.create_vector_store(docs, document_id)
            except Exception as e:
                print(f"⚠️ Vector store creation failed: {e}")
                vector_docs = []

            # Extract full text safely
            try:
                full_text = self._extract_full_text(docs)
                if not full_text or not full_text.strip():
                    return self._create_error_analysis(document_id, "No text content found")
            except Exception as e:
                print(f"⚠️ Text extraction failed: {e}")
                full_text = "Text extraction failed"

            # Store document info with full text for Q&A
            self.documents[document_id] = {
                'full_text': full_text,
                'doc_count': len(docs),
                'vector_count': len(vector_docs),
                'created_at': datetime.now().isoformat(),
                'status': 'analyzed',
            }

            print(f"📄 Document {document_id} stored with {len(full_text)} characters")

            # Basic analysis (always works)
            try:
                analysis = self._analyze_basic(full_text, document_id)
            except Exception as e:
                print(f"⚠️ Basic analysis failed: {e}")
                analysis = self._create_error_analysis(document_id, f"Basic analysis error: {str(e)}")

            # Try AI analysis if available
            if self.ai_available and len(full_text.strip()) > 50:
                try:
                    ai_analysis = self._analyze_with_ai(full_text)
                    if ai_analysis and isinstance(ai_analysis, dict):
                        analysis.update(ai_analysis)
                        print("✅ AI analysis completed successfully")
                except Exception as e:
                    print(f"⚠️ AI analysis failed: {e}")
                    analysis['ai_error'] = str(e)

            return analysis

        except Exception as e:
            print(f"❌ Document analysis failed: {e}")
            return self._create_error_analysis(document_id, f"Analysis error: {str(e)}")

    def _create_error_analysis(self, document_id: str, error_msg: str) -> Dict[str, Any]:
        """Create a basic error analysis response"""
        return {
            'document_id': document_id,
            'document_type': 'Error',
            'summary': f'Document processing encountered an issue: {error_msg}',
            'risks_analysis': 'Could not analyze risks due to processing error',
            'key_terms': 'Could not extract key terms',
            'document_length': 0,
            'chunk_count': 0,
            'word_count': 0,
            'error': error_msg,
            'ai_enhanced': False,
        }

    def _extract_full_text(self, docs: List) -> str:
        """Safely extract full text from documents"""
        text_parts = []

        for i, doc in enumerate(docs):
            try:
                if isinstance(doc, dict):
                    content = doc.get('page_content', doc.get('content', str(doc)))
                elif hasattr(doc, 'page_content'):
                    content = getattr(doc, 'page_content', '')
                else:
                    content = str(doc) if doc else ''

                if content and isinstance(content, str) and content.strip():
                    text_parts.append(content.strip())
                elif content:
                    text_parts.append(str(content).strip())

            except Exception as e:
                print(f"⚠️ Error extracting text from document {i}: {e}")
                continue

        full_text = "\n\n".join(text_parts) if text_parts else ""

        # Ensure reasonable text length
        if len(full_text) > 50000:
            full_text = full_text[:50000] + "\n\n[Content truncated for processing...]"

        return full_text

    def _clean_ai_response(self, text: str) -> str:
        """Clean AI response by removing asterisks and markdown formatting"""
        try:
            # Remove multiple asterisks (**, ***, etc.)
            cleaned_text = re.sub(r'\*+', '', text)

            # Remove markdown-style formatting
            cleaned_text = re.sub(r'__([^_]+)__', r'\1', cleaned_text)  # Remove __bold__
            cleaned_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_text)  # Remove **bold**
            cleaned_text = re.sub(r'\*([^*]+)\*', r'\1', cleaned_text)  # Remove *italic*

            # Clean up extra spaces and line breaks
            cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)  # Max 2 line breaks
            cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)  # Multiple spaces to single

            # Remove leading/trailing whitespace from each line
            lines = [line.strip() for line in cleaned_text.split('\n')]
            cleaned_text = '\n'.join(lines)

            return cleaned_text.strip()

        except Exception as e:
            print(f"⚠️ Text cleaning error: {e}")
            return text  # Return original if cleaning fails

    def _analyze_basic(self, text: str, document_id: str) -> Dict[str, Any]:
        """Basic analysis with error handling"""
        try:
            if not text or not isinstance(text, str):
                text = str(text) if text else "No content"

            word_count = len(text.split()) if text else 0
            text_lower = text.lower() if text else ""

            # Simple document type detection
            doc_type = 'Legal Document'
            if any(word in text_lower for word in ['employment', 'employee', 'job', 'salary']):
                doc_type = 'Employment Contract'
            elif any(word in text_lower for word in ['service', 'services', 'consultant']):
                doc_type = 'Service Agreement'
            elif any(word in text_lower for word in ['confidential', 'non-disclosure', 'nda']):
                doc_type = 'Non-Disclosure Agreement'
            elif any(word in text_lower for word in ['lease', 'rent', 'premises']):
                doc_type = 'Lease Agreement'
            elif any(word in text_lower for word in ['purchase', 'sale', 'buy', 'sell']):
                doc_type = 'Purchase Agreement'

            # Basic risk detection with error handling
            risks = []
            try:
                if 'termination' in text_lower or 'terminate' in text_lower:
                    risks.append("Termination clauses detected")
                if 'liability' in text_lower:
                    risks.append("Liability terms found")
                if 'payment' in text_lower or 'fee' in text_lower:
                    risks.append("Payment obligations identified")
                if 'penalty' in text_lower or 'fine' in text_lower:
                    risks.append("Penalty clauses found")
            except Exception as e:
                print(f"⚠️ Risk detection error: {e}")
                risks = ["Basic risk analysis unavailable"]

            # Extract key terms safely
            try:
                key_terms = self._extract_basic_terms(text_lower)
            except Exception as e:
                print(f"⚠️ Key term extraction error: {e}")
                key_terms = [f"Term extraction error: {str(e)}"]

            return {
                'document_id': document_id,
                'document_type': doc_type,
                'summary': f'This appears to be a {doc_type} containing {word_count} words. The document includes standard legal provisions and clauses typical for this type of agreement.',
                'risks_analysis': (
                    f'Detected {len(risks)} potential areas requiring attention: {"; ".join(risks)}'
                    if risks
                    else 'No obvious risk indicators found in basic analysis.'
                ),
                'key_terms': (
                    "\n".join([f"- {term}" for term in key_terms]) if key_terms else "- No key terms extracted"
                ),
                'document_length': len(text),
                'chunk_count': len(text.split('\n')) if text else 0,
                'word_count': word_count,
                'ai_enhanced': False,
            }

        except Exception as e:
            print(f"❌ Basic analysis error: {e}")
            return self._create_error_analysis(document_id, f"Basic analysis failed: {str(e)}")

    def _extract_basic_terms(self, text_lower: str) -> List[str]:
        """Safely extract basic key terms from text"""
        try:
            if not text_lower or not isinstance(text_lower, str):
                return ["No text available for term extraction"]

            terms = []

            # Common legal terms to look for
            term_patterns = {
                'Contract Duration': ['term', 'duration', 'period'],
                'Payment Terms': ['payment', 'fee', 'compensation', 'salary'],
                'Termination': ['termination', 'end', 'expire'],
                'Confidentiality': ['confidential', 'non-disclosure', 'proprietary'],
                'Liability': ['liability', 'responsible', 'damages'],
                'Governing Law': ['governing', 'jurisdiction', 'court'],
            }

            for term_name, keywords in term_patterns.items():
                try:
                    if any(keyword in text_lower for keyword in keywords):
                        terms.append(f"{term_name}: Found relevant clauses in document")
                except Exception as e:
                    print(f"⚠️ Error checking term {term_name}: {e}")
                    continue

            if not terms:
                terms.append("Document Type: Standard legal document format detected")

            return terms

        except Exception as e:
            print(f"⚠️ Term extraction error: {e}")
            return [f"Term extraction failed: {str(e)}"]

    def _analyze_with_ai(self, text: str) -> Dict[str, Any]:
        """AI analysis with clean output (no asterisks)"""
        try:
            if not self.ai_available:
                return {'ai_error': 'AI not available'}

            if not text or len(text.strip()) < 50:
                return {'ai_error': 'Insufficient text for AI analysis'}

            # Truncate text if too long
            analysis_text = text[:8000] if len(text) > 8000 else text

            # Updated prompt that specifically requests clean formatting
            prompt = f"""
            As a legal document expert, analyze this document and provide a clear, professional analysis.

            IMPORTANT: Use clean, plain text formatting. Do not use asterisks (*), bold formatting, or markdown. Write in clear, simple paragraphs.

            1. DOCUMENT TYPE: What kind of legal document is this?

            2. SUMMARY: Provide a comprehensive 150-200 word summary in plain English that explains:
               - What this document is about
               - Who the main parties are
               - What the key purposes and objectives are
               - Main obligations and rights

            3. KEY RISKS: Identify and explain 3-5 main risks or concerns

            4. IMPORTANT TERMS: List and explain 5-7 key legal terms or clauses

            5. CRITICAL DATES: Any important deadlines, expiration dates, or time periods

            6. FINANCIAL TERMS: Payment obligations, fees, penalties, or monetary amounts

            Document to analyze:
            {analysis_text}

            Please provide clear, practical insights using simple, clean text formatting without asterisks or special characters.
            """

            response = self.model.generate_content(prompt)

            if not response or not response.text:
                return {'ai_error': 'Empty AI response'}

            # Clean the response text by removing asterisks and markdown formatting
            ai_text = self._clean_ai_response(response.text.strip())

            return {
                'ai_enhanced': True,
                'summary': ai_text[:1000] + "..." if len(ai_text) > 1000 else ai_text,
                'ai_analysis_full': ai_text,
                'ai_processed_at': datetime.now().isoformat(),
                'document_type': self._extract_doc_type_from_ai_response(ai_text),
                'risks_analysis': self._extract_risks_from_ai_response(ai_text),
                'key_terms': self._extract_terms_from_ai_response(ai_text),
            }

        except Exception as e:
            print(f"❌ AI analysis error: {e}")
            return {'ai_error': str(e)}

    def _extract_doc_type_from_ai_response(self, ai_text: str) -> str:
        """Extract document type from AI response"""
        try:
            lines = ai_text.split('\n')
            for line in lines:
                if 'document type' in line.lower() or 'type:' in line.lower():
                    if ':' in line:
                        doc_type = line.split(':', 1)[1].strip()
                        # Clean asterisks from document type
                        doc_type = re.sub(r'\*+', '', doc_type).strip()
                        return doc_type
            return 'Legal Document'
        except:
            return 'Legal Document'

    def _extract_risks_from_ai_response(self, ai_text: str) -> str:
        """Extract risks section from AI response"""
        try:
            text_lower = ai_text.lower()
            start_markers = ['key risks', 'risks:', 'risk assessment', 'concerns']
            end_markers = ['important terms', 'key terms', 'critical dates', 'financial']

            start_pos = -1
            for marker in start_markers:
                pos = text_lower.find(marker)
                if pos != -1:
                    start_pos = pos
                    break

            if start_pos == -1:
                return 'Risk analysis completed by AI'

            # Find end position
            end_pos = len(ai_text)
            for marker in end_markers:
                pos = text_lower.find(marker, start_pos + 50)
                if pos != -1:
                    end_pos = min(end_pos, pos)

            risks_text = ai_text[start_pos:end_pos].strip()
            # Clean asterisks from risks text
            risks_text = self._clean_ai_response(risks_text)
            return risks_text[:500] + "..." if len(risks_text) > 500 else risks_text

        except:
            return 'AI risk analysis completed'

    def _extract_terms_from_ai_response(self, ai_text: str) -> str:
        """Extract key terms section from AI response"""
        try:
            text_lower = ai_text.lower()
            start_markers = ['important terms', 'key terms', 'terms:']
            end_markers = ['critical dates', 'financial', 'conclusion']

            start_pos = -1
            for marker in start_markers:
                pos = text_lower.find(marker)
                if pos != -1:
                    start_pos = pos
                    break

            if start_pos == -1:
                return 'Key terms identified by AI'

            # Find end position
            end_pos = len(ai_text)
            for marker in end_markers:
                pos = text_lower.find(marker, start_pos + 50)
                if pos != -1:
                    end_pos = min(end_pos, pos)

            terms_text = ai_text[start_pos:end_pos].strip()
            # Clean asterisks from terms text
            terms_text = self._clean_ai_response(terms_text)
            return terms_text[:800] + "..." if len(terms_text) > 800 else terms_text

        except:
            return 'AI key terms analysis completed'

    def debug_document_status(self, document_id: str) -> dict:
        """Debug method to check document status"""
        return {
            'document_exists_in_documents': document_id in self.documents,
            'document_exists_in_vector_store': document_id in self.vector_store,
            'ai_available': self.ai_available,
            'total_documents': len(self.documents),
            'total_vector_docs': len(self.vector_store),
            'document_keys': list(self.documents.keys()),
            'vector_keys': list(self.vector_store.keys()),
            'document_data': self.documents.get(document_id, {}) if document_id in self.documents else None,
        }

    def test_ai_connection(self) -> str:
        """Test if AI is working with a simple question"""
        if not self.ai_available:
            return "AI not available - no API key configured"

        try:
            response = self.model.generate_content("Hello, please respond with 'AI is working'")
            if response and response.text:
                return f"AI Test Success: {response.text.strip()}"
            else:
                return "AI Test Failed: Empty response"
        except Exception as e:
            return f"AI Test Failed: {str(e)}"

    def answer_question(self, document_id: str, question: str) -> str:
        """Answer questions with improved error handling and debugging"""
        try:
            print(f"🔍 Processing question: {question}")
            print(f"📄 Document ID: {document_id}")

            if not document_id or not question:
                return "Error: Document ID and question are required."

            # Check if document exists
            if document_id not in self.vector_store and document_id not in self.documents:
                print(f"❌ Document {document_id} not found")
                print(f"Available documents: {list(self.documents.keys())}")
                return "Document not found. Please upload and analyze the document first."

            # Get document text safely
            full_text = ""
            try:
                if document_id in self.documents:
                    full_text = self.documents[document_id].get('full_text', '')
                    print(f"📖 Found document text: {len(full_text)} characters")
                elif document_id in self.vector_store:
                    docs = self.vector_store[document_id]
                    full_text = "\n".join([doc.get('content', '') for doc in docs])
                    print(f"📖 Found vector store text: {len(full_text)} characters")

                if not full_text or len(full_text.strip()) < 20:
                    print("⚠️ Document text too short or empty")
                    return "Document text is not available or too short for analysis. Please try re-uploading the document."

            except Exception as e:
                print(f"❌ Error retrieving document: {e}")
                return f"Error retrieving document: {str(e)}"

            # Try AI-powered Q&A if available
            if self.ai_available:
                try:
                    print("🤖 Attempting AI-powered Q&A")
                    answer = self._answer_with_ai(full_text, question)
                    print(f"✅ AI answer generated: {len(answer)} characters")
                    return answer
                except Exception as e:
                    print(f"❌ AI Q&A failed: {e}")
                    # Continue to basic answer instead of returning error

            # Fallback to basic keyword matching
            print("📝 Using basic keyword matching")
            return self._answer_basic(full_text, question)

        except Exception as e:
            print(f"❌ Question answering error: {e}")
            return f"I encountered an error while processing your question. Please try asking a simpler question about the document content."

    def _answer_with_ai(self, text: str, question: str) -> str:
        """AI-powered question answering with better error handling"""
        try:
            print(f"🧠 AI processing question: {question[:50]}...")

            # Truncate text if too long for AI processing
            analysis_text = text[:6000] if len(text) > 6000 else text
            print(f"📄 Text length for AI: {len(analysis_text)} characters")

            # Simpler, more reliable prompt
            prompt = f"""
            You are a helpful legal document assistant. Answer this question based on the document provided.

            Question: {question}

            Document: {analysis_text}

            Please provide a clear, helpful answer. If the information is not in the document, say so clearly.
            """

            print("🚀 Sending request to Gemini...")
            response = self.model.generate_content(prompt)

            if response and response.text:
                clean_answer = self._clean_ai_response(response.text.strip())
                print("✅ AI response received and cleaned")
                return clean_answer
            else:
                print("⚠️ Empty AI response")
                return "I received an empty response from the AI. Please try rephrasing your question."

        except Exception as e:
            print(f"❌ Detailed AI Q&A error: {e}")
            raise e  # Re-raise to be caught by parent function

    def _answer_basic(self, text: str, question: str) -> str:
        """Basic keyword-based Q&A with error handling"""
        try:
            if not text or not question:
                return "Invalid input for question processing."

            question_lower = question.lower()
            text_lower = text.lower()

            # Extract meaningful keywords from question
            stop_words = ['what', 'when', 'where', 'how', 'does', 'this', 'that', 'they', 'with', 'the', 'and', 'or']
            question_words = [w for w in question_lower.split() if len(w) > 3 and w not in stop_words]
            found_words = [w for w in question_words if w in text_lower]

            if found_words:
                # Find relevant sentences
                sentences = [s.strip() for s in text.split('.') if s.strip()]
                relevant_sentences = []

                for sentence in sentences:
                    try:
                        if any(word in sentence.lower() for word in found_words):
                            relevant_sentences.append(sentence)
                        if len(relevant_sentences) >= 3:  # Limit to 3 most relevant
                            break
                    except Exception as e:
                        print(f"⚠️ Error processing sentence: {e}")
                        continue

                if relevant_sentences:
                    answer = "Based on the document content:\n\n"
                    for i, sentence in enumerate(relevant_sentences, 1):
                        try:
                            display_sentence = sentence[:200] + "..." if len(sentence) > 200 else sentence
                            answer += f"{i}. {display_sentence}\n\n"
                        except Exception as e:
                            answer += f"{i}. [Error processing sentence]\n\n"

                    answer += "Note: This is a basic keyword search. For more detailed AI-powered answers, ensure your Gemini API key is properly configured."
                    return answer

            # No relevant information found
            return f"I couldn't find specific information about '{question}' in the document. Try rephrasing your question or using different keywords. The document appears to contain information about legal terms, contracts, agreements, or similar topics."

        except Exception as e:
            print(f"❌ Basic Q&A error: {e}")
            return f"Error processing question: {str(e)}"

    def parse_risks(self, risks_text: str) -> List[Dict[str, str]]:
        """Parse risks with comprehensive error handling"""
        try:
            if not risks_text or not isinstance(risks_text, str):
                return [
                    {
                        'title': 'Analysis Complete',
                        'description': 'Document processed successfully. Risk analysis may be limited.',
                        'level': 'Low',
                    }
                ]

            risks = []
            risks_text_lower = risks_text.lower()

            risk_indicators = {
                'termination': (
                    'Termination Clauses',
                    'Document contains termination-related provisions that should be reviewed',
                    'Medium',
                ),
                'liability': (
                    'Liability Terms',
                    'Liability provisions detected - review limitations and responsibilities',
                    'Medium',
                ),
                'payment': ('Payment Obligations', 'Payment terms and financial obligations identified', 'Low'),
                'penalty': ('Penalty Clauses', 'Penalty or fine provisions found - review carefully', 'High'),
                'confidential': (
                    'Confidentiality Requirements',
                    'Confidentiality or non-disclosure terms present',
                    'Medium',
                ),
                'indemnification': (
                    'Indemnification Clauses',
                    'Indemnification provisions require legal review',
                    'High',
                ),
            }

            for keyword, (title, description, level) in risk_indicators.items():
                try:
                    if keyword in risks_text_lower:
                        risks.append({'title': title, 'description': description, 'level': level})
                except Exception as e:
                    print(f"⚠️ Error checking risk indicator {keyword}: {e}")
                    continue

            # Add default risk if none found
            if not risks:
                risks.append(
                    {
                        'title': 'General Legal Review',
                        'description': 'Document processed successfully. Professional legal review recommended for important agreements.',
                        'level': 'Low',
                    }
                )

            return risks

        except Exception as e:
            print(f"❌ Risk parsing error: {e}")
            return [
                {'title': 'Risk Analysis Error', 'description': f'Could not parse risks: {str(e)}', 'level': 'Medium'}
            ]
