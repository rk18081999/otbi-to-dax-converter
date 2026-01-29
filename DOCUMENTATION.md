# OTBI to DAX Converter - Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Architecture](#architecture)
4. [LLM Reasoning Engine](#llm-reasoning-engine)
5. [Prompt Engineering Strategy](#prompt-engineering-strategy)
6. [Data Flow](#data-flow)
7. [Module Breakdown](#module-breakdown)
8. [Example Walkthrough](#example-walkthrough)
9. [Limitations & Future Work](#limitations--future-work)

---

## Overview

This system converts **Oracle OTBI Physical SQL** (extracted from `NQQuery.log`) into **Power BI DAX queries** using a **Large Language Model (LLM) as a reasoning engine**.

### Why LLM-Powered?

Traditional rule-based parsers fail because:
- **OTBI SQL is generated, not semantic** - It uses auto-generated aliases like `T12345.C67890`
- **SQL-to-DAX is NOT 1:1 syntax translation** - It requires understanding business intent
- **Join semantics matter** - A SQL LEFT JOIN might need `LOOKUPVALUE` or relationship navigation in DAX
- **Context transformation** - SQL WHERE clauses become DAX filter contexts

**Solution**: Use an LLM to **reason about the SQL semantically** rather than parse it syntactically.

---

## Problem Statement

### Input: OTBI Physical SQL
```sql
SELECT DISTINCT
    T289289.C15439104 AS LEDGER_ID,
    T289289.C10223035 AS LEDGER_NAME,
    T289289.C355935403 AS PERIOD_NAME,
    SUM(T289289.C214435915) AS PERIOD_NET_ACTIVITY
FROM 
    GL_LEDGERS T289289,
    GL_BALANCES T12345
WHERE
    T289289.CURRENCY_CODE = 'USD'
    AND T289289.DESCRIPTION IS NULL
GROUP BY
    T289289.C15439104,
    T289289.C10223035,
    T289289.C355935403
```

### Challenges
1. **Alias Resolution**: What does `T289289.C15439104` actually mean?
2. **Join Intent**: Is this a fact-to-dimension lookup or a many-to-many join?
3. **Aggregation Grain**: What is the business grain of the output?
4. **Filter Context**: How do WHERE clauses translate to DAX filter context?
5. **DAX Pattern Selection**: Should we use `SUMMARIZECOLUMNS`, `SELECTCOLUMNS`, or `ADDCOLUMNS`?

### Expected Output: DAX Query
```dax
EVALUATE
VAR BaseTable =
    SELECTCOLUMNS (
        GL_LEDGERS,
        "LEDGER_ID", GL_LEDGERS[LEDGER_ID],
        "LEDGER_NAME", GL_LEDGERS[LEDGER_NAME],
        "PERIOD_NAME", GL_LEDGERS[PERIOD_NAME],
        "PERIOD_NET_ACTIVITY",
            LOOKUPVALUE (
                GL_BALANCES[PERIOD_NET_ACTIVITY],
                GL_BALANCES[LEDGER_ID], GL_LEDGERS[LEDGER_ID]
            )
    )
RETURN
    DISTINCT (
        FILTER (
            BaseTable,
            [CURRENCY_CODE] = "USD"
                && ISBLANK([DESCRIPTION])
        )
    )
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                               │
│                   OTBI Physical SQL File                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Reasoner Module                           │
│                  (llm_reasoner.py)                               │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Stage 1: Semantic Analysis                              │   │
│  │  - What is the business question?                        │   │
│  │  - Which tables are facts vs dimensions?                 │   │
│  │  - What is the output grain?                             │   │
│  │  - What filters are applied?                             │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                        │
│                         ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Stage 2: Join Reasoning                                 │   │
│  │  - Classify each join (1:1, 1:M, M:M)                    │   │
│  │  - Determine cardinality impact                          │   │
│  │  - Choose DAX strategy (LOOKUPVALUE vs relationship)     │   │
│  │  - Identify potential double-counting risks              │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                        │
│                         ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Stage 3: DAX Generation                                 │   │
│  │  - Select DAX pattern (SELECTCOLUMNS + LOOKUPVALUE)      │   │
│  │  - Map columns with proper references                    │   │
│  │  - Convert WHERE to FILTER context                       │   │
│  │  - Apply DISTINCT if needed                              │   │
│  │  - Add inline comments                                   │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                        │
└─────────────────────────┼────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT: DAX Query                             │
│              Ready for Power BI Execution                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## LLM Reasoning Engine

### Core Philosophy

Instead of parsing SQL tokens, we ask the LLM to **reason about the SQL** in three stages:

1. **Semantic Analysis** - Understand the business intent
2. **Join Reasoning** - Classify relationships and cardinality
3. **DAX Generation** - Translate concepts into DAX syntax

### Why Multi-Stage?

**Single-shot prompting fails** because:
- Too much cognitive load in one prompt
- LLM tries to generate DAX before understanding semantics
- Hard to debug when output is wrong

**Multi-stage reasoning succeeds** because:
- Each stage has a focused task
- Intermediate outputs are structured (JSON)
- Later stages build on earlier analysis
- Easier to debug and refine prompts

---

## Prompt Engineering Strategy

### Stage 1: Semantic Analysis Prompt

**Goal**: Extract business meaning from SQL

**Prompt Structure**:
```
You are an expert in Oracle OTBI and Power BI.

Analyze this OTBI Physical SQL and extract semantic meaning:

[SQL TEXT]

Reference Examples:
[Demo_SQL.sql]
[Demo_DAXquery.dax]

Return JSON with:
{
  "business_intent": "What business question is being answered?",
  "driving_table": "Which table is the primary fact/grain?",
  "output_grain": "One row per ___",
  "tables": [
    {
      "name": "TABLE_NAME",
      "alias": "T12345",
      "type": "fact|dimension",
      "role": "Description of role"
    }
  ],
  "columns": [
    {
      "alias": "C67890",
      "real_name": "LEDGER_NAME",
      "table": "GL_LEDGERS",
      "aggregation": "SUM|COUNT|NONE"
    }
  ],
  "filters": [
    {
      "column": "CURRENCY_CODE",
      "operator": "=",
      "value": "USD",
      "intent": "Restrict to USD currency"
    }
  ]
}
```

**Key Techniques**:
- **Few-shot learning**: Include `Demo_SQL.sql` and `Demo_DAXquery.dax` as examples
- **Structured output**: Request JSON for easy parsing
- **Business context**: Ask "why" not just "what"

### Stage 2: Join Reasoning Prompt

**Goal**: Classify joins and determine DAX strategy

**Prompt Structure**:
```
You are a data modeling expert.

Given this semantic analysis:
[STAGE 1 OUTPUT]

And this SQL:
[SQL TEXT]

Analyze each join and return JSON:
{
  "joins": [
    {
      "left_table": "GL_BALANCES",
      "right_table": "GL_LEDGERS",
      "join_type": "LEFT JOIN",
      "cardinality": "M:1",
      "multiplies_rows": false,
      "dax_strategy": "LOOKUPVALUE",
      "reasoning": "GL_BALANCES (fact) looks up GL_LEDGERS (dimension)"
    }
  ],
  "double_count_risk": false,
  "recommendations": "Use LOOKUPVALUE for dimension lookups"
}
```

**Key Techniques**:
- **Cardinality analysis**: Understand 1:1, 1:M, M:M relationships
- **Strategy selection**: Choose between `LOOKUPVALUE`, `RELATED`, or explicit `FILTER`
- **Risk assessment**: Flag potential double-counting issues

### Stage 3: DAX Generation Prompt

**Goal**: Generate executable DAX code

**Prompt Structure**:
```
You are a Power BI DAX expert.

Generate a DAX query based on:

Semantic Analysis:
[STAGE 1 OUTPUT]

Join Analysis:
[STAGE 2 OUTPUT]

SQL:
[SQL TEXT]

Reference Example:
[Demo_DAXquery.dax]

Requirements:
1. Use SELECTCOLUMNS + LOOKUPVALUE pattern
2. Handle multi-condition lookups
3. Convert WHERE to FILTER context
4. Add inline comments explaining mappings
5. Match the style of Demo_DAXquery.dax

Return ONLY the DAX query, no explanations.
```

**Key Techniques**:
- **Pattern enforcement**: Require specific DAX patterns
- **Style matching**: Reference demo file for consistency
- **Comment generation**: Explain non-obvious mappings
- **Clean output**: Request only DAX code

---

## Data Flow

### Step-by-Step Execution

```python
# 1. User provides SQL file
sql_text = read_file("Demo_SQL.sql")

# 2. Initialize LLM reasoner
reasoner = LLMReasoner(api_key="...")

# 3. Stage 1: Semantic Analysis
semantic_analysis = reasoner._analyze_semantics(sql_text)
# Output: JSON with business intent, tables, columns, filters

# 4. Stage 2: Join Reasoning
join_analysis = reasoner._analyze_joins(sql_text, semantic_analysis)
# Output: JSON with join classifications and DAX strategies

# 5. Stage 3: DAX Generation
dax_query = reasoner._generate_dax(sql_text, semantic_analysis, join_analysis)
# Output: Executable DAX code

# 6. Return complete result
result = {
    'dax': dax_query,
    'semantic_analysis': semantic_analysis,
    'join_analysis': join_analysis
}
```

### Error Handling

```python
try:
    result = reasoner.convert_sql_to_dax(sql_text)
except ValueError as e:
    # API key not configured
    print("Set GEMINI_API_KEY in llm_config.py")
except Exception as e:
    # LLM error or invalid SQL
    print(f"Conversion failed: {e}")
```

---

## Module Breakdown

### 1. `llm_reasoner.py`

**Purpose**: Core LLM reasoning engine

**Key Classes**:
```python
class LLMReasoner:
    def __init__(self, api_key=None)
    def convert_sql_to_dax(self, sql_text) -> dict
    def _analyze_semantics(self, sql_text) -> dict
    def _analyze_joins(self, sql_text, semantic_analysis) -> dict
    def _generate_dax(self, sql_text, semantic_analysis, join_analysis) -> str
    def _load_demo_files(self) -> tuple
    def _call_llm(self, prompt) -> str
```

**Configuration**:
- Uses `llm_config.py` for API key
- Falls back to environment variable `GEMINI_API_KEY`
- Loads demo files for few-shot learning

### 2. `llm_config.py`

**Purpose**: API configuration

```python
import os

# Set your Gemini API key here
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Or hardcode (not recommended for production)
# GEMINI_API_KEY = "your-api-key-here"
```

### 3. `main.py`

**Purpose**: CLI interface

**Usage**:
```bash
python main.py input.sql --output output.dax --show-analysis
```

**Features**:
- File I/O handling
- Optional analysis display
- Error reporting

### 4. `app.py`

**Purpose**: Web UI (Flask)

**Routes**:
- `GET /` - Main interface
- `POST /convert` - Upload SQL, get DAX
- `POST /download` - Download DAX file

**Features**:
- Drag-and-drop file upload
- Real-time conversion
- Analysis display
- File download

### 5. Prompt Templates (`prompts/`)

**Files**:
- `semantic_analysis.txt` - Stage 1 prompt
- `join_reasoning.txt` - Stage 2 prompt
- `dax_generation.txt` - Stage 3 prompt

**Purpose**: Separate prompts from code for easy iteration

---

## Example Walkthrough

### Input SQL
```sql
SELECT DISTINCT
    hp.PARTY_NUMBER,
    hp.PARTY_NAME,
    hca.ACCOUNT_NUMBER,
    flv.MEANING AS STATUS_MEANING
FROM HZ_CUST_ACCOUNTS hca
LEFT JOIN HZ_PARTIES hp ON hca.PARTY_ID = hp.PARTY_ID
LEFT JOIN FND_LOOKUP_VALUES_TL flv 
    ON hca.STATUS = flv.LOOKUP_CODE
    AND flv.LANGUAGE = 'US'
WHERE hp.COUNTY = 'FAIRFAX'
```

### Stage 1: Semantic Analysis Output
```json
{
  "business_intent": "List customer accounts with party details filtered by county",
  "driving_table": "HZ_CUST_ACCOUNTS",
  "output_grain": "One row per customer account",
  "tables": [
    {
      "name": "HZ_CUST_ACCOUNTS",
      "alias": "hca",
      "type": "fact",
      "role": "Primary table containing customer accounts"
    },
    {
      "name": "HZ_PARTIES",
      "alias": "hp",
      "type": "dimension",
      "role": "Party master data for customer details"
    },
    {
      "name": "FND_LOOKUP_VALUES_TL",
      "alias": "flv",
      "type": "dimension",
      "role": "Lookup table for status code translation"
    }
  ],
  "columns": [
    {
      "alias": "PARTY_NUMBER",
      "real_name": "PARTY_NUMBER",
      "table": "HZ_PARTIES",
      "aggregation": "NONE"
    },
    {
      "alias": "ACCOUNT_NUMBER",
      "real_name": "ACCOUNT_NUMBER",
      "table": "HZ_CUST_ACCOUNTS",
      "aggregation": "NONE"
    }
  ],
  "filters": [
    {
      "column": "COUNTY",
      "operator": "=",
      "value": "FAIRFAX",
      "intent": "Filter to accounts in Fairfax county"
    }
  ]
}
```

### Stage 2: Join Analysis Output
```json
{
  "joins": [
    {
      "left_table": "HZ_CUST_ACCOUNTS",
      "right_table": "HZ_PARTIES",
      "join_type": "LEFT JOIN",
      "cardinality": "M:1",
      "multiplies_rows": false,
      "dax_strategy": "LOOKUPVALUE",
      "reasoning": "Many accounts can belong to one party. Use LOOKUPVALUE to fetch party details."
    },
    {
      "left_table": "HZ_CUST_ACCOUNTS",
      "right_table": "FND_LOOKUP_VALUES_TL",
      "join_type": "LEFT JOIN",
      "cardinality": "M:1",
      "multiplies_rows": false,
      "dax_strategy": "LOOKUPVALUE",
      "reasoning": "Lookup table for status translation. Use LOOKUPVALUE with multi-condition."
    }
  ],
  "double_count_risk": false,
  "recommendations": "All joins are M:1 lookups. Safe to use LOOKUPVALUE pattern."
}
```

### Stage 3: DAX Output
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
        "PARTY_NAME",
            LOOKUPVALUE (
                HZ_PARTIES[PARTY_NAME],
                HZ_PARTIES[PARTY_ID], HZ_CUST_ACCOUNTS[PARTY_ID]
            ),
        "ACCOUNT_NUMBER", HZ_CUST_ACCOUNTS[ACCOUNT_NUMBER],
        "STATUS_MEANING",
            LOOKUPVALUE (
                FND_LOOKUP_VALUES_TL[MEANING],
                FND_LOOKUP_VALUES_TL[LOOKUP_CODE], HZ_CUST_ACCOUNTS[STATUS],
                FND_LOOKUP_VALUES_TL[LANGUAGE], "US"
            )
    )
RETURN
    DISTINCT (
        FILTER (
            BaseTable,
            LOOKUPVALUE (
                HZ_PARTIES[COUNTY],
                HZ_PARTIES[PARTY_ID], HZ_CUST_ACCOUNTS[PARTY_ID]
            ) = "FAIRFAX"
        )
    )
```

---

## Limitations & Future Work

### Current Limitations

1. **LLM Dependency**
   - Requires API key and internet connection
   - Subject to LLM rate limits
   - Cost per conversion (though minimal with Gemini)

2. **Complex Subqueries**
   - Deeply nested subqueries may confuse the LLM
   - May require manual review for very complex SQL

3. **Model Assumptions**
   - Assumes Power BI model already exists
   - Assumes relationships are defined or can be inferred
   - Cannot create calculated tables or modify model

4. **Performance**
   - LLM calls take 5-15 seconds per conversion
   - Not suitable for real-time/high-volume scenarios

### Future Enhancements

1. **Caching Layer**
   - Cache LLM responses for identical SQL
   - Store semantic analysis for reuse

2. **Validation Module**
   - Syntax check DAX before returning
   - Validate against Power BI model metadata

3. **Optimization**
   - Suggest DAX performance improvements
   - Identify inefficient patterns

4. **Model Introspection**
   - Read Power BI model metadata
   - Validate table/column existence
   - Use actual relationships in DAX generation

5. **Batch Processing**
   - Convert multiple SQL files at once
   - Generate comparison reports

6. **Interactive Refinement**
   - Allow user to provide feedback
   - Iteratively improve DAX output

---

## Conclusion

This LLM-powered converter represents a **paradigm shift** from rule-based parsing to **semantic reasoning**. By leveraging the LLM's ability to understand context and intent, we can handle the complexity of OTBI-generated SQL and produce high-quality DAX queries that would be extremely difficult to generate with traditional parsing techniques.

The multi-stage prompting strategy ensures:
- ✅ **Accuracy** - Each stage focuses on one aspect
- ✅ **Debuggability** - Intermediate outputs are inspectable
- ✅ **Maintainability** - Prompts can be refined independently
- ✅ **Extensibility** - New stages can be added easily

This approach is particularly well-suited for **generated SQL** where business semantics are obscured by auto-generated aliases and complex join structures.
