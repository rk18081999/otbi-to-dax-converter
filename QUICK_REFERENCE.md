# Quick Reference Guide - OTBI to DAX Converter

## 🚀 Quick Start

### 1. Setup
```bash
# Get Gemini API key from: https://makersuite.google.com/app/apikey

# Configure in llm_config.py
GEMINI_API_KEY = "your-api-key-here"
```

### 2. Run Web UI
```bash
cd "/Users/coher/My Pc/Rite/venv/OTBI2PWBI"
.venv/bin/python app.py
# Open: http://127.0.0.1:5000
```

### 3. Or Use CLI
```bash
.venv/bin/python main.py input.sql --output output.dax --show-analysis
```

---

## 📊 How It Works (Simple Explanation)

### Traditional Approach ❌
```
SQL → Parse tokens → Map syntax → DAX
```
**Problem**: Fails on generated SQL with aliases like `T12345.C67890`

### LLM Approach ✅
```
SQL → Understand Intent → Reason About Joins → Generate DAX
```
**Solution**: LLM understands WHAT the SQL is trying to do, not just HOW it's written

---

## 🧠 Three-Stage Reasoning

### Stage 1: Semantic Analysis
**Question**: "What is this SQL trying to do?"

**LLM Analyzes**:
- Business intent (e.g., "Show customer accounts by county")
- Which tables are facts vs dimensions
- Output grain (e.g., "One row per account")
- Filters and their purpose

**Output**: JSON with semantic understanding

### Stage 2: Join Reasoning
**Question**: "How should these joins work in DAX?"

**LLM Analyzes**:
- Join cardinality (1:1, 1:M, M:M)
- Does this join multiply rows?
- Should we use LOOKUPVALUE or relationships?
- Any double-counting risks?

**Output**: JSON with join strategies

### Stage 3: DAX Generation
**Question**: "Generate the actual DAX code"

**LLM Generates**:
- Uses `SELECTCOLUMNS + LOOKUPVALUE` pattern
- Converts WHERE clauses to FILTER context
- Adds DISTINCT if needed
- Includes inline comments

**Output**: Executable DAX query

---

## 📁 File Structure

```
OTBI2PWBI/
├── llm_reasoner.py          # 🧠 Core LLM reasoning engine
├── llm_config.py             # 🔑 API key configuration
├── prompts/                  # 📝 Prompt templates
│   ├── semantic_analysis.txt
│   ├── join_reasoning.txt
│   └── dax_generation.txt
├── app.py                    # 🌐 Web UI (Flask)
├── main.py                   # 💻 CLI tool
├── Demo_SQL.sql              # 📚 Example input
├── Demo_DAXquery.dax         # 📚 Example output
├── DOCUMENTATION.md          # 📖 Full technical docs
└── README.md                 # 📄 User guide
```

---

## 🎯 Example Conversion

### Input: OTBI SQL
```sql
SELECT DISTINCT
    hp.PARTY_NAME,
    hca.ACCOUNT_NUMBER
FROM HZ_CUST_ACCOUNTS hca
LEFT JOIN HZ_PARTIES hp ON hca.PARTY_ID = hp.PARTY_ID
WHERE hp.COUNTY = 'FAIRFAX'
```

### What LLM Understands
```
Business Intent: "Show customer accounts in Fairfax county"
Driving Table: HZ_CUST_ACCOUNTS (fact)
Join: M:1 lookup to HZ_PARTIES (dimension)
Strategy: Use LOOKUPVALUE
```

### Output: DAX
```dax
EVALUATE
VAR BaseTable =
    SELECTCOLUMNS (
        HZ_CUST_ACCOUNTS,
        "PARTY_NAME",
            LOOKUPVALUE (
                HZ_PARTIES[PARTY_NAME],
                HZ_PARTIES[PARTY_ID], HZ_CUST_ACCOUNTS[PARTY_ID]
            ),
        "ACCOUNT_NUMBER", HZ_CUST_ACCOUNTS[ACCOUNT_NUMBER]
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

## 🔧 CLI Commands

### Basic Conversion
```bash
python main.py input.sql
# Creates: input.dax
```

### Custom Output
```bash
python main.py input.sql --output custom.dax
```

### Show Analysis
```bash
python main.py input.sql --show-analysis
# Displays semantic and join analysis
```

### Use Different API Key
```bash
python main.py input.sql --api-key "your-key"
```

---

## 🌐 Web UI Features

1. **Drag & Drop** - Upload SQL files easily
2. **Real-time Conversion** - See results instantly
3. **Analysis View** - Inspect LLM reasoning
4. **Download** - Get DAX file with one click

---

## 🐛 Troubleshooting

### "API key not configured"
```python
# Edit llm_config.py
GEMINI_API_KEY = "your-api-key-here"
```

### "Conversion failed"
- Check SQL is valid OTBI Physical SQL
- Ensure Demo_SQL.sql and Demo_DAXquery.dax exist
- Review error message for details

### Web UI not loading
- Use `http://127.0.0.1:5000` (not localhost)
- Check port 5000 is available
- Verify Flask is running

---

## 💡 Key Concepts

### Why Multi-Stage?
- **Better Accuracy** - Each stage focuses on one task
- **Debuggable** - Can inspect intermediate outputs
- **Maintainable** - Can improve prompts independently

### Why LLM vs Rules?
- **Handles Ambiguity** - Generated SQL is not semantic
- **Context Aware** - Understands business intent
- **Flexible** - Adapts to different SQL patterns

### DAX Pattern: SELECTCOLUMNS + LOOKUPVALUE
```dax
SELECTCOLUMNS (
    BaseTable,
    "Column", LOOKUPVALUE(DimTable[Col], DimTable[Key], BaseTable[Key])
)
```
**Why?** Works in Live/DirectQuery mode without model changes

---

## 📚 Learn More

- **Full Documentation**: `DOCUMENTATION.md`
- **Gemini API**: https://ai.google.dev/docs
- **DAX Guide**: https://dax.guide/
- **OTBI Docs**: https://docs.oracle.com/en/cloud/saas/analytics/

---

## 🎓 Understanding the Magic

### What Makes This Special?

**Traditional Parser**:
```python
if "LEFT JOIN" in sql:
    dax += "LOOKUPVALUE(...)"
```
❌ Breaks on complex SQL

**LLM Reasoner**:
```python
"Analyze this join. Is it 1:M or M:M? 
 Should we use LOOKUPVALUE or RELATED?"
```
✅ Understands context and intent

### The Secret Sauce: Few-Shot Learning

We show the LLM examples:
```
Input: Demo_SQL.sql
Output: Demo_DAXquery.dax

Now convert this new SQL...
```

The LLM learns the pattern and applies it!

---

## 🚦 When to Use This Tool

### ✅ Good Use Cases
- Converting OTBI Physical SQL to DAX
- Understanding complex SQL semantics
- Learning DAX patterns from SQL
- Batch converting multiple queries

### ⚠️ Limitations
- Requires internet connection
- Subject to API rate limits
- Very complex nested queries may need review
- Cannot modify Power BI model

---

## 🎯 Success Metrics

**Good Conversion**:
- ✅ Returns same row count as OTBI
- ✅ Aggregations match
- ✅ Executes without errors in Power BI
- ✅ Uses proper filter context

**Needs Review**:
- ⚠️ Row count differs
- ⚠️ Aggregations don't match
- ⚠️ DAX syntax errors
- ⚠️ Performance issues

---

## 🔄 Workflow

```
1. Export OTBI Physical SQL
   ↓
2. Upload to converter (Web UI or CLI)
   ↓
3. LLM analyzes in 3 stages
   ↓
4. Review generated DAX
   ↓
5. Test in Power BI DAX Query View
   ↓
6. Refine if needed
```

---

## 📞 Support

For issues or questions:
1. Check `DOCUMENTATION.md` for technical details
2. Review error messages carefully
3. Ensure API key is configured
4. Verify demo files exist
