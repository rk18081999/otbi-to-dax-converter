import argparse
from llm_reasoner import LLMReasoner

def main():
    parser = argparse.ArgumentParser(description='Convert OTBI Physical SQL to Power BI DAX using LLM reasoning')
    parser.add_argument('input_file', help='Input SQL file path')
    parser.add_argument('--output', '-o', help='Output DAX file path (default: input_file.dax)')
    parser.add_argument('--api-key', help='Gemini API key (or set GEMINI_API_KEY env var)')
    parser.add_argument('--show-analysis', action='store_true', help='Show semantic and join analysis')
    
    args = parser.parse_args()
    
    # Read input SQL
    print(f"Reading SQL from {args.input_file}...")
    with open(args.input_file, 'r') as f:
        sql_text = f.read()
    
    # Initialize LLM reasoner
    try:
        reasoner = LLMReasoner(api_key=args.api_key)
    except ValueError as e:
        print(f"Error: {e}")
        print("\nTo use the LLM-powered converter, you need a Gemini API key.")
        print("Get one at: https://makersuite.google.com/app/apikey")
        print("\nSet it in llm_config.py or pass via --api-key")
        return 1
    
    # Convert SQL to DAX
    print("\n🧠 Using LLM reasoning engine for conversion...")
    result = reasoner.convert_sql_to_dax(sql_text)
    
    # Show analysis if requested
    if args.show_analysis:
        import json
        print("\n=== SEMANTIC ANALYSIS ===")
        print(json.dumps(result['semantic_analysis'], indent=2))
        print("\n=== JOIN ANALYSIS ===")
        print(json.dumps(result['join_analysis'], indent=2))
    
    # Write output
    output_file = args.output or args.input_file.replace('.sql', '.dax')
    print(f"\nWriting DAX to {output_file}...")
    with open(output_file, 'w') as f:
        f.write(result['dax'])
    
    print("✅ Conversion complete!")
    return 0

if __name__ == '__main__':
    exit(main())
