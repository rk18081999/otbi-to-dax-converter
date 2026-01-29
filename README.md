# OTBI to DAX Converter - LLM-Powered

A semantic reasoning engine that converts Oracle OTBI Physical SQL to Power BI DAX using Large Language Models.

## 🧠 Why LLM-Powered?

OTBI Physical SQL is **generated, not semantic**. Simple rule-based parsing fails because:
- Aliases and subqueries require **reasoning**, not pattern matching
- SQL-to-DAX is **not** a 1:1 syntax conversion
- Business intent must be inferred from structure

## ✨ Features

- 🎯 **Semantic Understanding** - LLM infers business intent from SQL
- 🔗 **Join Reasoning** - Classifies joins (fact vs dimension, cardinality)
- 📊 **Smart DAX Generation** - Translates concepts, not syntax
- 📚 **Example-Driven** - Learns from Demo_SQL.sql → Demo_DAXquery.dax
- 🌐 **Web UI** - Beautiful interface for easy conversion

## 🚀 Quick Start

### 1. Get Gemini API Key

Get a free API key from: https://makersuite.google.com/app/apikey

### 2. Configure API Key

Edit `llm_config.py`:
```python
GEMINI_API_KEY = "your-api-key-here"
```

Or set environment variable:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 3. Run Web UI

```bash
cd "/Users/coher/My Pc/Rite/venv/OTBI2PWBI"
.venv/bin/python app.py
```

Open: **http://127.0.0.1:5000**

### 4. Or Use CLI

```bash
.venv/bin/python main.py input.sql --output output.dax --show-analysis
```

## 🧠 How It Works

### Multi-Stage LLM Reasoning

```
Input SQL → Stage 1: Semantic Analysis → Stage 2: Join Reasoning → Stage 3: DAX Generation → Output DAX
                ↓                            ↓                           ↓
         Business Intent              Join Classification         SELECTCOLUMNS + LOOKUPVALUE
         Fact/Dimension Tables        Cardinality Analysis        Filter Context
         Grain Determination          Impact Assessment           Proper Aggregation
```

### Stage 1: Semantic Analysis
- What business question is being answered?
- Which tables are facts vs dimensions?
- What is the grain of the output?
- What filters are implied?

### Stage 2: Join Reasoning
- Does this join multiply rows?
- What is the cardinality (1:1, 1:M, M:M)?
- Should this use LOOKUPVALUE or relationship?
- Could it cause double counting?

### Stage 3: DAX Generation
- Uses SELECTCOLUMNS + LOOKUPVALUE pattern
- Handles multi-condition lookups
- Applies filters correctly
- Matches Demo_DAXquery.dax style

## 📁 File Structure

```
OTBI2PWBI/
├── llm_reasoner.py          # LLM reasoning engine
├── llm_config.py             # API configuration
├── prompts/                  # Prompt templates
│   ├── semantic_analysis.txt
│   ├── join_reasoning.txt
│   └── dax_generation.txt
├── app.py                    # Web UI (Flask)
├── main.py                   # CLI tool
├── Demo_SQL.sql              # Example input
└── Demo_DAXquery.dax         # Example output
```

## 🎯 Example

### Input: OTBI Physical SQL
```sql
SELECT DISTINCT
    hp.PARTY_NUMBER,
    hp.PARTY_NAME,
    hca.ACCOUNT_NUMBER,
    flv.MEANING
FROM HZ_CUST_ACCOUNTS hca
LEFT JOIN HZ_PARTIES hp ON hca.PARTY_ID = hp.PARTY_ID
LEFT JOIN FND_LOOKUP_VALUES_TL flv ON hca.STATUS = flv.LOOKUP_CODE
WHERE hp.COUNTY = 'FAIRFAX'
```

### LLM Analysis
```json
{
  "business_intent": "Show customer accounts filtered by county",
  "driving_table": "HZ_CUST_ACCOUNTS",
  "grain": "One row per customer account",
  "joins": [
    {
      "table": "HZ_PARTIES",
      "type": "lookup",
      "cardinality": "M:1",
      "strategy": "LOOKUPVALUE"
    }
  ]
}
```

### Output: DAX
```dax
EVALUATE
VAR BaseTable =
    SELECTCOLUMNS (
        HZ_CUST_ACCOUNTS,
        "PARTY_NUMBER",
            LOOKUPVALUE (
                HZ_PARTIES[PARTY_NUMBER],
                HZ_PARTIES[PARTY_ID], HZ_CUST_ACCOUNTS[PARTY_ID]
            ),
        ...
    )
RETURN
    DISTINCT (
        FILTER (
            BaseTable,
            [COUNTY] = "FAIRFAX"
        )
    )
```

## 🔧 Requirements

- Python 3.7+
- Flask
- google-generativeai
- Gemini API key

## 📝 CLI Options

```bash
python main.py input.sql [options]

Options:
  --output, -o FILE      Output DAX file (default: input.dax)
  --api-key KEY          Gemini API key
  --show-analysis        Show semantic and join analysis
```

## 🐛 Troubleshooting

**API Key Error?**
- Set `GEMINI_API_KEY` in `llm_config.py`
- Or use `--api-key` flag
- Or set environment variable

**Conversion Fails?**
- Check SQL is valid OTBI Physical SQL
- Ensure Demo_SQL.sql and Demo_DAXquery.dax exist
- Review error message for LLM reasoning issues

**Web UI Not Loading?**
- Use `http://127.0.0.1:5000` (not localhost)
- Check Flask server is running
- Verify port 5000 is available

## 🎓 Learn More

- [Gemini API Docs](https://ai.google.dev/docs)
- [Power BI DAX Reference](https://dax.guide/)
- [OTBI Documentation](https://docs.oracle.com/en/cloud/saas/analytics/)
