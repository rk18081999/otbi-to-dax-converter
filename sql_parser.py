import re
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Parenthesis, Comparison
from sqlparse.tokens import Keyword, DML, CTE, Name

class RecursiveOTBISQLParser:
    def __init__(self):
        self.ctes = {} # name -> {sql_text, ...}
        self.all_filters = [] 
        self.joins = []

    def parse(self, sql_text):
        # Clean comments
        sql_text = re.sub(r'/\*.*?\*/', '', sql_text, flags=re.DOTALL)
        
        parsed = sqlparse.parse(sql_text)[0]
        
        # 1. Extract CTEs
        self._extract_ctes(parsed)
        
        # 2. Parse Main Query
        # We assume the main query is the final SELECT
        # We need to find the main SELECT statement tokens.
        # If there are CTEs, the main SELECT is after them.
        
        # We'll use a heuristic: The last Token that starts with SELECT
        # Or better, we trace logic from the "Resolution" perspective.
        # We want to resolve the "Final Select List".
        
        final_block = self._find_final_select_block(parsed)
        if not final_block:
            raise ValueError("Could not find main SELECT statement")

        final_cols, final_tables, final_filters = self._parse_query_block(final_block)
        print("DEBUG: Final Tables:", final_tables)
        
        resolved_columns = []
        for col in final_cols:
            # Resolve lineage
            res = self._resolve_lineage(col['expression'], final_tables)
            res['target_name'] = col['alias']
            resolved_columns.append(res)
            
        # Collect filters from the final block and recursively from used tables
        self._collect_filters_recursive(final_tables, final_filters)
        
        return {
            "columns": resolved_columns,
            "filters": list(set(self.all_filters)), # dedup
            "joins": self.joins
        }

    def _extract_ctes(self, parsed):
        # We iterate tokens. If we see "Identifier AS (", it's a CTE.
        # sqlparse is tricky with CTEs.
        # We will try a regex approach for CTE extraction as it is often more robust for specific Oracle CTE patterns
        # pattern: name AS ( ... )
        # But nested parens make regex hard.
        
        # Let's use sqlparse but manually iterate
        tokens = list(parsed.flatten())
        
        # This is too low level.
        # Let's rely on `parsed.tokens`
        # Common structure:
        # [CTE_Definition, CTE_Definition, ..., DML(SELECT...)]
        
        # Loop through top-level tokens
        in_with = False
        for token in parsed.tokens:
            if token.ttype is Keyword.CTE:
                in_with = True
            
            if in_with and isinstance(token, IdentifierList):
                for id_tok in token.get_identifiers():
                    self._register_cte(id_tok)
            elif in_with and isinstance(token, Identifier):
                self._register_cte(token)
        print("DEBUG: Extracted CTEs:", list(self.ctes.keys()))

    def _register_cte(self, token):
        name = token.get_real_name()
        # Find content
        # Usually 'Identifier' has 'Parenthesis' as child
        # Flatten and look for Parenthesis?
        # or token.value might be "Name AS (...)"
        
        # We need the content INSIDE the parens.
        match = re.search(r'AS\s*\((.*)\)', token.value, re.IGNORECASE | re.DOTALL)
        if match:
            # This regex is greedy and might eat too much if multiple CTEs are strictly adjacent?
            # actually valid SQL separates with comma.
            # But regex on the *token value* is safer than whole string
            
            # Problem: Nested parens in the CTE content.
            # We should peer into the token structure if possible.
            pass
        
        # Fallback: sqlparse Child of type Parenthesis
        parens = next((t for t in token.tokens if isinstance(t, Parenthesis)), None)
        if parens and name:
            content = parens.value.strip()
            if content.startswith('(') and content.endswith(')'):
                content = content[1:-1]
            self.ctes[name.upper()] = content
            if name.upper() == 'SAWITH0':
                print(f"DEBUG: SAWITH0 content start: {content[:50]}...")
                print(f"DEBUG: SAWITH0 content end: ...{content[-50:]}")
            
    def _find_final_select_block(self, parsed):
        # The main query is the one that follows the CTEs.
        # It is strictly a DML 'SELECT'
        for token in reversed(parsed.tokens):
            if token.ttype is DML and token.value.upper() == 'SELECT':
                return parsed # The whole thing?
                # No, sqlparse structures are weird.
                # If there are CTEs, the main SELECT is part of the root statement.
                pass
        
        # If we can't find it easily, let's assume the whole text is valid and identifying the *last* SELECT
        # that is not inside a parenthesis is key.
        # Actually, let's just parse the DML part.
        
        # We will iterate and find the first SELECT that is NOT part of a CTE definition.
        # But we already extracted CTEs.
        # The main query tokens are the ones remaining?
        
        # Let's look for the keyword SELECT at top level
        for i, token in enumerate(parsed.tokens):
            if token.ttype is DML and token.value.upper() == 'SELECT':
                # This could be the main query.
                # But is it inside a CTE? Top level tokens usually separate CTEs and Main Query.
                return parsed # We return the root, but _parse_query_block needs to handle "starting" from this token?
        
        return parsed

    def _parse_query_block(self, token_list):
        # Returns columns, tables, filters
        
        # We need to find SELECT, FROM, WHERE in this list of tokens
        # BUT `token_list` might be the whole file (with CTEs).
        # We need to ignore CTEs here.
        
        if hasattr(token_list, 'tokens'):
            tokens = token_list.tokens
        else:
            tokens = token_list

        columns = []
        tables = {}
        filters = []
        
        # State machine
        state = 'NONE'
        
        for token in tokens:
            if token.is_whitespace: continue
            
            if token.ttype is DML and token.value.upper() == 'SELECT':
                state = 'SELECT'
                continue
            elif token.ttype is Keyword and token.value.upper() == 'FROM':
                state = 'FROM'
                continue
            elif isinstance(token, Where):
                # Where token includes the keyword "WHERE"
                state = 'WHERE'
                # parse the content of Where
                self._parse_where(token, filters)
                continue
            elif token.ttype is Keyword and token.value.upper() in ['GROUP BY', 'ORDER BY']:
                state = 'OTHER'
                continue
                
            if state == 'SELECT':
                if isinstance(token, IdentifierList):
                    for id_tok in token.get_identifiers():
                        self._add_col(id_tok, columns)
                elif isinstance(token, Identifier):
                    self._add_col(token, columns)
            
            elif state == 'FROM':
                # print(f"DEBUG: FROM Processing Token: {token.ttype} - {type(token)} - {token.value[:20]}")
                if isinstance(token, IdentifierList):
                    for id_tok in token.get_identifiers():
                        self._add_table(id_tok, tables)
                elif isinstance(token, Identifier):
                    self._add_table(token, tables)
                elif isinstance(token, Parenthesis):
                    # Subquery without Alias or sqlparse failed to group
                    # We treat it as a table? Or wait for Alias?
                    # Common in Oracle: (SELECT ...) Alias
                    # sqlparse might give Parenthesis then Identifier.
                    # We need to handle this.
                    # For now just print
                    print(f"DEBUG: Found Parenthesis in FROM: {token.value[:20]}...")
                    # We should probably capture it if we want to handle "Parenthesis Alias"
                elif isinstance(token, Comparison): 
                    # JOIN syntax "Table A LEFT JOIN Table B ON ..." might appear as Comparison or just keywords?
                    # sqlparse usually puts JOINs into identifiers or flat list.
                    # We might need to handle raw keywords for joins.
                    pass
                else:
                    # Maybe it is just a name (Keyword parsing failed?)
                    # print(f"DEBUG: Unhandled FROM token: {token.value[:20]}")
                    pass
        
        return columns, tables, filters

    def _add_col(self, token, columns):
        # Handle "Expr AS Alias"
        alias = token.get_alias()
        name = token.get_real_name()
        val = token.value
        
        # If AS is implicit or explicit
        # We want the expression *before* the alias
        # sqlparse splits logic:
        # if alias exists, token has 'get_real_name()' ? No, 'get_real_name' returns the name part.
        
        # Regex to be sure
        # pattern: (.*) AS (.*)
        # or (.*) (Alias)
        
        # Simple approach
        expr = val
        if alias:
            # remove alias from end
            # This is risky with spaces.
            # Use split
             parts = re.split(r'\s+(AS\s+)?' + re.escape(alias) + r'$', val, flags=re.IGNORECASE)
             if len(parts) > 0:
                 expr = parts[0].strip()
        
        columns.append({"alias": alias or name, "expression": expr})

    def _add_table(self, token, tables):
        # Handle "Table T" or "(Select ...) T" or "A JOIN B ON ..."
        
        # 1. Check for explicit Subquery (Token structure)
        if hasattr(token, 'tokens'):
             subquery = next((t for t in token.tokens if isinstance(t, Parenthesis)), None)
             if subquery:
                 content = subquery.value.strip()
                 if content.startswith('(') and content.endswith(')'):
                     content = content[1:-1]
                 
                 alias = token.get_alias()
                 if not alias:
                     # Check if token value ends with word that is not the subquery
                     # token.value is "(...) Alias"
                     # subquery.value is "(...)"
                     # Just try regex on the full token value to find alias at end
                     match_alias = re.search(r'\)\s+([a-zA-Z0-9_]+)$', token.value)
                     if match_alias:
                         alias = match_alias.group(1)
                 
                 if alias:
                     tables[alias] = {"type": "subquery", "content": content}
                     return

        val = token.value
        val_norm = re.sub(r'\s+', ' ', val)
        
        # 2. Check for Subquery (Regex fallback)
        # Pattern: (SELECT ...) Alias
        # We need to match balanced parens strictly? 
        # Or just checking if it ends with " ) Alias"
        if val_norm.startswith('('):
            # Likely subquery
            # Try to split by last closing paren
            last_paren_idx = val_norm.rfind(')')
            if last_paren_idx != -1 and last_paren_idx < len(val_norm) - 1:
                # There is content after parens
                potential_alias = val_norm[last_paren_idx+1:].strip()
                # Check if alias is valid identifier (no spaces)
                if ' ' not in potential_alias:
                    content = val_norm[:last_paren_idx+1].strip()
                    if content.startswith('(') and content.endswith(')'):
                        content = content[1:-1]
                    tables[potential_alias] = {"type": "subquery", "content": content}
                    return

        # 3. Naive join splitter / Normal Table
        # We look for "JOIN" keywords
        # Split by JOINS
        # Strip ON ...
        pre_on = re.split(r'\s+ON\s+', val_norm, flags=re.IGNORECASE)[0]
        
        keywords = r'(?:LEFT|RIGHT|OUTER|INNER|FULL|CROSS)?\s*JOIN'
        parts = re.split(rf'\s+{keywords}\s+', pre_on, flags=re.IGNORECASE)
        
        for part in parts:
            part = part.strip()
            if not part: continue
            
            # "Table Alias" or "Table"
            subparts = part.split()
            if len(subparts) >= 2:
                alias = subparts[-1]
                name = subparts[-2] # Assuming "Name Alias"
                
                # Check if name is garbage (e.g. '))')
                if name == '))' or name.startswith(')'):
                    # Parsing failed earlier.
                    continue
                    
                tables[alias] = {"type": "ref", "name": name}
            elif len(subparts) == 1:
                name = subparts[0]
                tables[name] = {"type": "ref", "name": name}

    def _parse_where(self, where_token, filters):
        val = where_token.value.replace('WHERE', '', 1).strip()
        conds = self._split_and(val)
        filters.extend(conds)

    def _split_and(self, text):
        # Split by "AND" but ignore AND inside parens or quotes
        if not text: return []
        
        parts = []
        current = []
        depth = 0
        quote = None
        
        # Tokenize by char is slow but accurate for this
        i = 0
        n = len(text)
        while i < n:
            char = text[i]
            
            if quote:
                current.append(char)
                if char == quote:
                    quote = None
            else:
                if char in ("'", '"'):
                    quote = char
                    current.append(char)
                elif char == '(':
                    depth += 1
                    current.append(char)
                elif char == ')':
                    depth -= 1
                    current.append(char)
                elif depth == 0 and text[i:i+3].upper() == 'AND' and (i+3 >= n or text[i+3].isspace()) and (i==0 or text[i-1].isspace() or text[i-1]==')'):
                    # Found top-level AND
                    parts.append("".join(current).strip())
                    current = []
                    i += 2 # skip ND
                else:
                    current.append(char)
            i += 1
            
        if current:
            parts.append("".join(current).strip())
            
        return [p for p in parts if p]

    def _resolve_lineage(self, expression, context_tables):
        # Clean expression
        expression = expression.strip()
        
        # Check for aggregation / NVL
        agg_func = None
        match = re.search(r'^([A-Z0-9_]+)\((.*)\)$', expression, re.IGNORECASE)
        if match:
             func_name = match.group(1).upper()
             inner = match.group(2)
             if func_name in ['SUM', 'COUNT', 'AVG', 'MIN', 'MAX']:
                 agg_func = func_name
                 # recurse on inner
                 res = self._resolve_lineage(inner, context_tables)
                 res['aggregation'] = agg_func
                 return res
             elif func_name == 'NVL':
                 # Oracle NVL(a, b) -> DAX COALESCE(a, b) or just use 'a' logic?
                 # Agent requirement: "resolve alias mappings back to real column meaning"
                 # We resolve the first non-null arg.
                 args = self._split_args(inner)
                 if args:
                     # Just verify the first one? the primary one.
                     res = self._resolve_lineage(args[0], context_tables)
                     # Maybe note that NVL was used?
                     res['notes'] = 'NVL wrapper'
                     return res
        
        # Check for Table.Column
        parts = expression.split('.')
        col_name = expression
        table_alias = None
        
        if len(parts) == 2:
            table_alias = parts[0]
            col_name = parts[1]
        
        if table_alias and table_alias in context_tables:
            source = context_tables[table_alias]
            
            if source['type'] == 'ref':
                ref_name = source['name'].upper()
                
                if ref_name in self.ctes:
                    # Resolve in CTE
                    cte_sql = self.ctes[ref_name]
                    cte_cols, cte_tables, cte_filters = self._parse_query_block(sqlparse.parse(cte_sql)[0])
                    # Recursively collect filters from implied CTE usage
                    self._collect_filters_recursive(cte_tables, cte_filters)
                    
                    # Find matching alias in CTE
                    target = next((c for c in cte_cols if c['alias'] and c['alias'].upper() == col_name.upper()), None)
                    if not target:
                        # Maybe implied alias?
                        target = next((c for c in cte_cols if c['expression'].upper().endswith(col_name.upper())), None)
                    
                    if target:
                        return self._resolve_lineage(target['expression'], cte_tables)
                else:
                    # Physical table
                    return {"physical_table": ref_name, "physical_column": col_name}
            
            elif source['type'] == 'subquery':
                # Recurse into subquery
                sub_sql = source['content']
                sub_cols, sub_tables, sub_filters = self._parse_query_block(sqlparse.parse(sub_sql)[0])
                self._collect_filters_recursive(sub_tables, sub_filters)
                
                target = next((c for c in sub_cols if c['alias'] and c['alias'].upper() == col_name.upper()), None)
                if not target:
                    target = next((c for c in sub_cols if c['expression'].upper().endswith(col_name.upper())), None)
                    
                if target:
                    res = self._resolve_lineage(target['expression'], sub_tables)
                    if not res.get('aggregation') and agg_func:
                        res['aggregation'] = agg_func
                    return res
                
        # If no alias, or alias not found, return as is (maybe scalar or error)
        return {"physical_table": None, "physical_column": expression, "unknown": True}

    def _split_args(self, text):
        # Split by comma, respecting parens
        # Simple version
        return [a.strip() for a in text.split(',')]

    def _collect_filters_recursive(self, tables, filters):
        # 1. Process current level filters
        for f in filters:
            # Try to resolve columns in the filter
            resolved_f = self._resolve_filter_string(f, tables)
            if resolved_f:
                self.all_filters.append(resolved_f)
                
        # 2. Recurse into tables (if CTEs or Subqueries)
        
        for alias, info in tables.items():
            if info['type'] == 'ref':
                ref_name = info['name'].upper()
                if ref_name in self.ctes:
                    cte_sql = self.ctes[ref_name]
                    c_cols, c_tables, c_filters = self._parse_query_block(sqlparse.parse(cte_sql)[0])
                    self._collect_filters_recursive(c_tables, c_filters)
            elif info['type'] == 'subquery':
                # Parse subquery content
                sub_sql = info['content']
                # Subquery content might be just the SELECT ... part
                c_cols, c_tables, c_filters = self._parse_query_block(sqlparse.parse(sub_sql)[0])
                self._collect_filters_recursive(c_tables, c_filters)

    def _resolve_filter_string(self, filter_str, context_tables):
        # "T.Col = 'Val'" -> "Physical.Col = 'Val'"
        # Handle "NVL(T.Col, 'X') = 'Y'" ?
        # Handle "T.Col = T2.Col (+)"
        
        # Remove (+)
        filter_str = filter_str.replace('(+)', '').strip()
        
        # Regex to find Identifiers "A.B"
        # We replace them one by one.
        
        def replacement(match):
            full = match.group(0)
            # Try resolve
            res = self._resolve_lineage(full, context_tables)
            if res.get('physical_table'):
                return f"'{res['physical_table']}'[{res['physical_column']}]"
            return full
            
        # Pattern: Word.Word
        resolved = re.sub(r'\b([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\b', replacement, filter_str)
        
        # Handle "IS NULL" -> ISBLANK conversion could happen here or in DAX generator
        # Let's keep it close to SQL here, but mapped to physical columns.
        
        return resolved


if __name__ == "__main__":
    with open("Unified_Oracle_Query.sql", "r") as f:
        sql = f.read()
    parser = RecursiveOTBISQLParser()
    import json
    print(json.dumps(parser.parse(sql), indent=2))
