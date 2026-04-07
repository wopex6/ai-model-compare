"""
Advanced Comparison Metrics System
Implements semantic analysis, token efficiency, coherence scoring, and factual accuracy
"""

import asyncio
import json
import math
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import statistics
from collections import Counter
import numpy as np

@dataclass
class AdvancedComparisonMetrics:
    """Advanced metrics for AI model comparison"""
    semantic_similarity: float = 0.0
    token_efficiency: float = 0.0
    coherence_score: float = 0.0
    factual_accuracy: float = 0.0
    response_relevance: float = 0.0
    clarity_score: float = 0.0
    creativity_score: float = 0.0
    helpfulness_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class SemanticAnalyzer:
    """Analyzes semantic similarity between responses"""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Convert to lowercase and extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove stop words and short words
        keywords = [word for word in words 
                  if word not in self.stop_words and len(word) > 2]
        
        return keywords
    
    def calculate_jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts"""
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        
        if not keywords1 and not keywords2:
            return 1.0
        
        intersection = keywords1.intersection(keywords2)
        union = keywords1.union(keywords2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def calculate_cosine_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity using word frequencies"""
        keywords1 = self.extract_keywords(text1)
        keywords2 = self.extract_keywords(text2)
        
        # Create word frequency vectors
        all_words = list(set(keywords1 + keywords2))
        
        vec1 = [keywords1.count(word) for word in all_words]
        vec2 = [keywords2.count(word) for word in all_words]
        
        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def analyze_semantic_similarity(self, responses: List[str]) -> Dict[str, float]:
        """Analyze semantic similarity between multiple responses"""
        if len(responses) < 2:
            return {}
        
        similarities = {}
        
        for i, response1 in enumerate(responses):
            for j, response2 in enumerate(responses[i+1:], i+1):
                jaccard_sim = self.calculate_jaccard_similarity(response1, response2)
                cosine_sim = self.calculate_cosine_similarity(response1, response2)
                
                # Average of both similarity measures
                avg_similarity = (jaccard_sim + cosine_sim) / 2
                
                similarities[f"response_{i}_vs_{j}"] = avg_similarity
        
        # Calculate overall similarity score
        if similarities:
            overall_similarity = statistics.mean(similarities.values())
            similarities['overall'] = overall_similarity
        
        return similarities

class TokenEfficiencyAnalyzer:
    """Analyzes token efficiency of AI responses"""
    
    def __init__(self):
        # Approximate token counts for different models
        self.token_ratios = {
            'gpt-4': 4.0,      # ~4 characters per token
            'gpt-3.5': 4.0,
            'claude': 4.0,
            'gemini': 4.0
        }
    
    def estimate_token_count(self, text: str, model: str = 'gpt-4') -> int:
        """Estimate token count for text"""
        ratio = self.token_ratios.get(model, 4.0)
        return int(len(text) / ratio)
    
    def calculate_efficiency_metrics(self, response: str, model: str) -> Dict[str, float]:
        """Calculate various efficiency metrics"""
        token_count = self.estimate_token_count(response, model)
        char_count = len(response)
        word_count = len(re.findall(r'\b\w+\b', response))
        sentence_count = len(re.findall(r'[.!?]+', response))
        
        # Efficiency metrics
        if token_count > 0:
            chars_per_token = char_count / token_count
            words_per_token = word_count / token_count
            sentences_per_token = sentence_count / token_count
        else:
            chars_per_token = words_per_token = sentences_per_token = 0
        
        # Information density (unique words / total words)
        words = re.findall(r'\b\w+\b', response.lower())
        if words:
            unique_words = len(set(words))
            information_density = unique_words / len(words)
        else:
            information_density = 0
        
        # Overall efficiency score (0-100)
        efficiency_score = min(100, (
            (chars_per_token / 5) * 25 +           # Ideal: ~5 chars/token
            (words_per_token / 0.75) * 25 +        # Ideal: ~0.75 words/token
            (information_density) * 25 +            # Higher is better
            (min(1, sentence_count / max(1, word_count / 15)) * 25)  # Good sentence length
        ))
        
        return {
            'token_count': token_count,
            'chars_per_token': chars_per_token,
            'words_per_token': words_per_token,
            'sentences_per_token': sentences_per_token,
            'information_density': information_density,
            'efficiency_score': efficiency_score
        }

class CoherenceAnalyzer:
    """Analyzes coherence and logical flow of responses"""
    
    def __init__(self):
        self.coherence_indicators = [
            'therefore', 'however', 'furthermore', 'moreover', 'consequently',
            'because', 'since', 'although', 'despite', 'in addition', 'first',
            'second', 'finally', 'in conclusion', 'for example', 'specifically'
        ]
    
    def analyze_coherence(self, response: str) -> Dict[str, float]:
        """Analyze coherence of a response"""
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 2:
            return {
                'coherence_score': 1.0,  # Single sentence is coherent by default
                'logical_flow': 1.0,
                'transition_usage': 0.0,
                'topic_consistency': 1.0
            }
        
        # Transition word usage
        transition_count = 0
        for sentence in sentences:
            sentence_lower = sentence.lower()
            transition_count += sum(1 for indicator in self.coherence_indicators 
                                   if indicator in sentence_lower)
        
        transition_usage = transition_count / len(sentences)
        
        # Topic consistency (keyword overlap between sentences)
        keywords_per_sentence = []
        for sentence in sentences:
            words = set(re.findall(r'\b\w+\b', sentence.lower()))
            keywords_per_sentence.append(words)
        
        topic_similarities = []
        for i in range(len(keywords_per_sentence) - 1):
            current_words = keywords_per_sentence[i]
            next_words = keywords_per_sentence[i + 1]
            
            if current_words and next_words:
                overlap = len(current_words.intersection(next_words))
                similarity = overlap / len(current_words.union(next_words))
                topic_similarities.append(similarity)
        
        topic_consistency = statistics.mean(topic_similarities) if topic_similarities else 0.0
        
        # Logical flow (sentence length variation)
        sentence_lengths = [len(sentence) for sentence in sentences]
        if len(sentence_lengths) > 1:
            length_variance = statistics.variance(sentence_lengths)
            # Normalize variance (lower is better for flow)
            logical_flow = max(0, 1 - (length_variance / (max(sentence_lengths) ** 2)))
        else:
            logical_flow = 1.0
        
        # Overall coherence score
        coherence_score = (
            transition_usage * 0.3 +
            topic_consistency * 0.4 +
            logical_flow * 0.3
        )
        
        return {
            'coherence_score': min(1.0, coherence_score),
            'logical_flow': logical_flow,
            'transition_usage': transition_usage,
            'topic_consistency': topic_consistency
        }

class FactualAccuracyAnalyzer:
    """Analyzes factual accuracy of responses"""
    
    def __init__(self):
        # Common factual indicators
        self.factual_patterns = [
            r'\b\d{4}\b',  # Years
            r'\b\d+%\b',  # Percentages
            r'\$\d+',     # Money amounts
            r'\b\d+\.\d+\b',  # Decimals
        ]
        
        # Confidence indicators
        self.confidence_words = [
            'definitely', 'certainly', 'absolutely', 'clearly', 'obviously',
            'probably', 'likely', 'perhaps', 'maybe', 'possibly',
            'uncertain', 'unclear', 'unknown', 'debatable'
        ]
    
    def analyze_factual_content(self, response: str) -> Dict[str, float]:
        """Analyze factual content and confidence"""
        # Count factual statements
        factual_count = 0
        for pattern in self.factual_patterns:
            matches = re.findall(pattern, response)
            factual_count += len(matches)
        
        # Count confidence indicators
        high_confidence = 0
        low_confidence = 0
        
        response_lower = response.lower()
        for word in self.confidence_words:
            if word in response_lower:
                if word in ['definitely', 'certainly', 'absolutely', 'clearly', 'obviously']:
                    high_confidence += 1
                elif word in ['uncertain', 'unclear', 'unknown', 'debatable']:
                    low_confidence += 1
        
        # Calculate scores
        word_count = len(re.findall(r'\b\w+\b', response))
        factual_density = factual_count / max(1, word_count)
        
        confidence_score = 0.5  # Neutral default
        if high_confidence > low_confidence:
            confidence_score = 0.8
        elif low_confidence > high_confidence:
            confidence_score = 0.3
        
        # Factual accuracy score (heuristic - would need fact-checking API for real accuracy)
        accuracy_score = min(1.0, factual_density * 10 + confidence_score * 0.2)
        
        return {
            'factual_density': factual_density,
            'confidence_score': confidence_score,
            'accuracy_score': accuracy_score,
            'factual_statements': factual_count
        }

class AdvancedComparisonEngine:
    """Main engine for advanced AI model comparison"""
    
    def __init__(self):
        self.semantic_analyzer = SemanticAnalyzer()
        self.token_analyzer = TokenEfficiencyAnalyzer()
        self.coherence_analyzer = CoherenceAnalyzer()
        self.factual_analyzer = FactualAccuracyAnalyzer()
    
    async def compare_responses_advanced(
        self, 
        responses: List[Dict[str, str]], 
        prompt: str
    ) -> Dict[str, Any]:
        """
        Perform advanced comparison of AI responses
        
        Args:
            responses: List of {'model_id': str, 'response': str, 'response_time': float}
            prompt: Original prompt for context
            
        Returns:
            Advanced comparison results with metrics
        """
        if len(responses) < 2:
            return {'error': 'Need at least 2 responses for comparison'}
        
        results = {
            'prompt': prompt,
            'responses': [],
            'semantic_analysis': {},
            'individual_metrics': {},
            'comparison_summary': {}
        }
        
        # Extract response texts
        response_texts = [r['response'] for r in responses]
        model_ids = [r['model_id'] for r in responses]
        
        # Semantic similarity analysis
        semantic_results = self.semantic_analyzer.analyze_semantic_similarity(response_texts)
        results['semantic_analysis'] = semantic_results
        
        # Individual metrics for each response
        for i, response_data in enumerate(responses):
            model_id = response_data['model_id']
            response_text = response_data['response']
            response_time = response_data.get('response_time', 0)
            
            # Token efficiency
            token_metrics = self.token_analyzer.calculate_efficiency_metrics(
                response_text, model_id
            )
            
            # Coherence analysis
            coherence_metrics = self.coherence_analyzer.analyze_coherence(response_text)
            
            # Factual accuracy
            factual_metrics = self.factual_analyzer.analyze_factual_content(response_text)
            
            # Response relevance (how well it addresses the prompt)
            relevance_score = self._calculate_relevance(response_text, prompt)
            
            # Clarity score
            clarity_score = self._calculate_clarity(response_text)
            
            # Creativity score
            creativity_score = self._calculate_creativity(response_text)
            
            # Helpfulness score
            helpfulness_score = self._calculate_helpfulness(response_text, prompt)
            
            # Compile individual metrics
            individual_metrics = AdvancedComparisonMetrics(
                semantic_similarity=semantic_results.get('overall', 0),
                token_efficiency=token_metrics['efficiency_score'] / 100,
                coherence_score=coherence_metrics['coherence_score'],
                factual_accuracy=factual_metrics['accuracy_score'] / 100,
                response_relevance=relevance_score,
                clarity_score=clarity_score,
                creativity_score=creativity_score,
                helpfulness_score=helpfulness_score
            )
            
            results['individual_metrics'][model_id] = {
                'token_metrics': token_metrics,
                'coherence_metrics': coherence_metrics,
                'factual_metrics': factual_metrics,
                'advanced_metrics': individual_metrics.__dict__,
                'response_time': response_time
            }
            
            results['responses'].append({
                'model_id': model_id,
                'response': response_text,
                'metrics': individual_metrics.__dict__
            })
        
        # Generate comparison summary
        results['comparison_summary'] = self._generate_comparison_summary(
            results['individual_metrics']
        )
        
        return results
    
    def _calculate_relevance(self, response: str, prompt: str) -> float:
        """Calculate how relevant the response is to the prompt"""
        prompt_keywords = set(self.semantic_analyzer.extract_keywords(prompt))
        response_keywords = set(self.semantic_analyzer.extract_keywords(response))
        
        if not prompt_keywords:
            return 0.5  # Neutral if no keywords in prompt
        
        overlap = len(prompt_keywords.intersection(response_keywords))
        relevance = overlap / len(prompt_keywords)
        
        return min(1.0, relevance * 2)  # Scale up a bit
    
    def _calculate_clarity(self, response: str) -> float:
        """Calculate clarity of response"""
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # Average sentence length (ideal: 15-25 words)
        sentence_lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences]
        avg_length = statistics.mean(sentence_lengths)
        
        # Clarity score based on sentence length
        if 15 <= avg_length <= 25:
            length_score = 1.0
        elif 10 <= avg_length <= 30:
            length_score = 0.8
        elif 5 <= avg_length <= 35:
            length_score = 0.6
        else:
            length_score = 0.4
        
        # Penalize very short or very long sentences
        variance_penalty = min(0.2, statistics.variance(sentence_lengths) / 100)
        
        return max(0.0, length_score - variance_penalty)
    
    def _calculate_creativity(self, response: str) -> float:
        """Calculate creativity score of response"""
        creative_indicators = [
            'imagine', 'innovative', 'creative', 'original', 'unique',
            'breakthrough', 'revolutionary', 'transformative', 'novel'
        ]
        
        response_lower = response.lower()
        creative_count = sum(1 for indicator in creative_indicators 
                             if indicator in response_lower)
        
        # Vocabulary diversity
        words = re.findall(r'\b\w+\b', response_lower)
        unique_words = len(set(words))
        vocabulary_diversity = unique_words / len(words) if words else 0
        
        # Creativity score
        creativity_score = min(1.0, (creative_count * 0.3 + vocabulary_diversity * 0.7))
        
        return creativity_score
    
    def _calculate_helpfulness(self, response: str, prompt: str) -> float:
        """Calculate how helpful the response is"""
        helpful_indicators = [
            'step', 'guide', 'how', 'solution', 'answer', 'help',
            'recommend', 'suggest', 'advise', 'tip', 'instruction'
        ]
        
        response_lower = response.lower()
        helpful_count = sum(1 for indicator in helpful_indicators 
                           if indicator in response_lower)
        
        # Actionable content
        action_indicators = ['you can', 'try to', 'consider', 'use', 'apply']
        action_count = sum(1 for indicator in action_indicators 
                          if indicator in response_lower)
        
        # Length appropriateness (not too short, not too long)
        word_count = len(re.findall(r'\b\w+\b', response))
        if 50 <= word_count <= 300:
            length_score = 1.0
        elif 20 <= word_count <= 500:
            length_score = 0.8
        else:
            length_score = 0.6
        
        helpfulness_score = min(1.0, (
            float(helpful_count) * 0.3 +
            float(action_count) * 0.3 +
            length_score * 0.4
        ))
        
        return helpfulness_score
    
    def _generate_comparison_summary(self, individual_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary comparison of all models"""
        summary = {
            'best_performers': {},
            'metric_averages': {},
            'overall_ranking': []
        }
        
        # Calculate averages for each metric
        all_metrics = {}
        for model_id, metrics in individual_metrics.items():
            advanced_metrics = metrics['advanced_metrics']
            for metric_name, value in advanced_metrics.items():
                if metric_name not in all_metrics:
                    all_metrics[metric_name] = []
                all_metrics[metric_name].append(value)
        
        for metric_name, values in all_metrics.items():
            summary['metric_averages'][metric_name] = {
                'mean': statistics.mean(values),
                'min': min(values),
                'max': max(values),
                'std': statistics.stdev(values) if len(values) > 1 else 0
            }
        
        # Find best performers for each metric
        for metric_name in all_metrics.keys():
            best_model = max(individual_metrics.keys(), 
                           key=lambda x: individual_metrics[x]['advanced_metrics'][metric_name])
            summary['best_performers'][metric_name] = best_model
        
        # Calculate overall ranking (weighted sum of all metrics)
        model_scores = {}
        for model_id, metrics in individual_metrics.items():
            advanced_metrics = metrics['advanced_metrics']
            # Weight different metrics
            weights = {
                'semantic_similarity': 0.1,
                'token_efficiency': 0.15,
                'coherence_score': 0.2,
                'factual_accuracy': 0.25,
                'response_relevance': 0.15,
                'clarity_score': 0.1,
                'creativity_score': 0.05
            }
            
            score = sum(advanced_metrics[metric] * weight 
                       for metric, weight in weights.items())
            model_scores[model_id] = score
        
        # Sort by score
        summary['overall_ranking'] = sorted(model_scores.items(), 
                                          key=lambda x: x[1], reverse=True)
        
        return summary

# Test the advanced comparison system
async def test_advanced_comparison():
    """Run automatic tests for advanced comparison metrics"""
    print("🧪 Testing Advanced Comparison Metrics...")
    
    test_results = []
    
    # Test 1: Semantic similarity analysis
    try:
        analyzer = SemanticAnalyzer()
        
        text1 = "Machine learning is a subset of artificial intelligence"
        text2 = "ML is a branch of AI that focuses on learning from data"
        text3 = "The weather is nice today"
        
        similarity_1_2 = analyzer.calculate_jaccard_similarity(text1, text2)
        similarity_1_3 = analyzer.calculate_jaccard_similarity(text1, text3)
        
        success = similarity_1_2 > similarity_1_3
        test_results.append({
            'test': 'Semantic Similarity Analysis',
            'passed': success,
            'details': f"Similar(1,2): {similarity_1_2:.3f}, Similar(1,3): {similarity_1_3:.3f}"
        })
        
    except Exception as e:
        test_results.append({
            'test': 'Semantic Similarity Analysis',
            'passed': False,
            'details': str(e)
        })
    
    # Test 2: Token efficiency analysis
    try:
        token_analyzer = TokenEfficiencyAnalyzer()
        
        response = "This is a comprehensive response that provides detailed information about the topic."
        metrics = token_analyzer.calculate_efficiency_metrics(response, 'gpt-4')
        
        success = (
            'token_count' in metrics and
            'efficiency_score' in metrics and
            metrics['efficiency_score'] >= 0
        )
        
        test_results.append({
            'test': 'Token Efficiency Analysis',
            'passed': success,
            'details': f"Tokens: {metrics['token_count']}, Efficiency: {metrics['efficiency_score']:.1f}"
        })
        
    except Exception as e:
        test_results.append({
            'test': 'Token Efficiency Analysis',
            'passed': False,
            'details': str(e)
        })
    
    # Test 3: Coherence analysis
    try:
        coherence_analyzer = CoherenceAnalyzer()
        
        coherent_text = "First, we need to understand the problem. Therefore, we can develop a solution. In conclusion, this approach works well."
        incoherent_text = "Random words here. Another sentence. No connection. Final thought."
        
        coherent_metrics = coherence_analyzer.analyze_coherence(coherent_text)
        incoherent_metrics = coherence_analyzer.analyze_coherence(incoherent_text)
        
        success = coherent_metrics['coherence_score'] > incoherent_metrics['coherence_score']
        test_results.append({
            'test': 'Coherence Analysis',
            'passed': success,
            'details': f"Coherent: {coherent_metrics['coherence_score']:.3f}, Incoherent: {incoherent_metrics['coherence_score']:.3f}"
        })
        
    except Exception as e:
        test_results.append({
            'test': 'Coherence Analysis',
            'passed': False,
            'details': str(e)
        })
    
    # Test 4: Full advanced comparison
    try:
        engine = AdvancedComparisonEngine()
        
        responses = [
            {
                'model_id': 'gpt-4',
                'response': 'Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data.',
                'response_time': 1.5
            },
            {
                'model_id': 'claude',
                'response': 'ML represents a data analysis approach that automates the creation of analytical models. As an AI subset, it operates on the principle that systems have the capability to learn from information.',
                'response_time': 1.2
            }
        ]
        
        prompt = "Explain machine learning"
        
        comparison_results = await engine.compare_responses_advanced(responses, prompt)
        
        success = (
            'individual_metrics' in comparison_results and
            'semantic_analysis' in comparison_results and
            'comparison_summary' in comparison_results
        )
        
        test_results.append({
            'test': 'Full Advanced Comparison',
            'passed': success,
            'details': f"Models compared: {len(responses)}, Metrics generated: {len(comparison_results.get('individual_metrics', {}))}"
        })
        
    except Exception as e:
        test_results.append({
            'test': 'Full Advanced Comparison',
            'passed': False,
            'details': str(e)
        })
    
    # Print results
    passed = sum(1 for result in test_results if result['passed'])
    total = len(test_results)
    
    print(f"\n📊 Advanced Comparison Test Results:")
    print(f"Passed: {passed}/{total}")
    
    for result in test_results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status}: {result['test']}")
        if not result['passed']:
            print(f"   Details: {result['details']}")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(test_advanced_comparison())
