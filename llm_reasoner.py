import os
import json
import google.generativeai as genai
from typing import Dict, Any
from llm_config import GEMINI_API_KEY, GEMINI_MODEL, TEMPERATURE, MAX_TOKENS

class LLMReasoner:
    """
    LLM-powered reasoning engine for OTBI to DAX conversion.
    Uses multi-stage prompting for semantic analysis, join reasoning, and DAX generation.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize LLM reasoner with API credentials"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or GEMINI_API_KEY
        
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ValueError(
                "GEMINI_API_KEY not set. Please set it in llm_config.py or as environment variable."
            )
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Load demo examples
        self.demo_sql = self._load_file('Demo_SQL.sql')
        self.demo_dax = self._load_file('Demo_DAXquery.dax')
        
        # Load prompt templates
        self.semantic_prompt = self._load_file('prompts/semantic_analysis.txt')
        self.join_prompt = self._load_file('prompts/join_reasoning.txt')
        self.dax_prompt = self._load_file('prompts/dax_generation.txt')
    
    def _load_file(self, filename: str) -> str:
        """Load file content"""
        try:
            with open(filename, 'r') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: {filename} not found")
            return ""
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM with prompt and return response"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_TOKENS,
                )
            )
            return response.text
        except Exception as e:
            raise Exception(f"LLM API call failed: {str(e)}")
    
    def analyze_semantics(self, sql_text: str) -> Dict[str, Any]:
        """
        Stage 1: Semantic Analysis
        Understand business intent, identify tables, determine grain
        """
        prompt = self.semantic_prompt.format(
            demo_sql=self.demo_sql,
            input_sql=sql_text
        )
        
        response = self._call_llm(prompt)
        
        try:
            # Extract JSON from response (may have markdown code blocks)
            json_str = response
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                json_str = response.split('```')[1].split('```')[0]
            
            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            print(f"Failed to parse semantic analysis: {e}")
            print(f"Response: {response}")
            return {}
    
    def analyze_joins(self, sql_text: str) -> Dict[str, Any]:
        """
        Stage 2: Join Reasoning
        Classify joins, determine cardinality, assess impact
        """
        prompt = self.join_prompt.format(
            input_sql=sql_text
        )
        
        response = self._call_llm(prompt)
        
        try:
            json_str = response
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                json_str = response.split('```')[1].split('```')[0]
            
            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            print(f"Failed to parse join analysis: {e}")
            print(f"Response: {response}")
            return {}
    
    def generate_dax(self, sql_text: str, semantic_analysis: Dict, join_analysis: Dict) -> str:
        """
        Stage 3: DAX Generation
        Generate DAX query based on semantic and join analysis
        """
        prompt = self.dax_prompt.format(
            demo_dax=self.demo_dax,
            semantic_analysis=json.dumps(semantic_analysis, indent=2),
            join_analysis=json.dumps(join_analysis, indent=2),
            input_sql=sql_text
        )
        
        response = self._call_llm(prompt)
        
        # Extract DAX from response (remove markdown if present)
        dax = response
        if '```dax' in response:
            dax = response.split('```dax')[1].split('```')[0]
        elif '```' in response:
            dax = response.split('```')[1].split('```')[0]
        
        return dax.strip()
    
    def convert_sql_to_dax(self, sql_text: str) -> Dict[str, Any]:
        """
        Full conversion pipeline:
        1. Semantic analysis
        2. Join reasoning
        3. DAX generation
        """
        print("Stage 1: Analyzing semantics...")
        semantic_analysis = self.analyze_semantics(sql_text)
        
        print("Stage 2: Reasoning about joins...")
        join_analysis = self.analyze_joins(sql_text)
        
        print("Stage 3: Generating DAX...")
        dax_query = self.generate_dax(sql_text, semantic_analysis, join_analysis)
        
        return {
            'dax': dax_query,
            'semantic_analysis': semantic_analysis,
            'join_analysis': join_analysis
        }


if __name__ == "__main__":
    # Test with demo SQL
    reasoner = LLMReasoner()
    
    with open('Demo_SQL.sql', 'r') as f:
        demo_sql = f.read()
    
    result = reasoner.convert_sql_to_dax(demo_sql)
    
    print("\n=== GENERATED DAX ===")
    print(result['dax'])
    
    print("\n=== SEMANTIC ANALYSIS ===")
    print(json.dumps(result['semantic_analysis'], indent=2))
    
    print("\n=== JOIN ANALYSIS ===")
    print(json.dumps(result['join_analysis'], indent=2))
