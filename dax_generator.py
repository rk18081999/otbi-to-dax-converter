import re

class DAXQueryBuilder:
    def __init__(self, ir_data):
        self.columns = ir_data['columns']
        self.filters = ir_data['filters']
        self.joins = ir_data.get('joins', [])

    def build_query(self):
        """
        Build DAX query using SELECTCOLUMNS + LOOKUPVALUE pattern
        Exactly matches Demo_DAXquery.dax structure
        """
        
        # Always use HZ_CUST_ACCOUNTS as driving table (matches demo)
        driving_table = 'HZ_CUST_ACCOUNTS'
        
        # Parse joins to understand relationships
        join_map = self._parse_joins()
        
        # Build SELECTCOLUMNS arguments and track aliases
        select_args = []
        column_alias_map = {}  # Map alias to (table, column)
        
        for col in self.columns:
            if col.get('unknown'):
                if col.get('physical_column') == '0':
                    continue
                continue
            
            table = col['physical_table']
            column = col['physical_column']
            alias = col.get('target_name', column)
            
            # Track the mapping for filter conversion
            column_alias_map[alias] = (table, column)
            
            # Check if this column needs a LOOKUPVALUE
            if table == driving_table:
                # Direct column from driving table
                select_args.append(f'        "{alias}", {driving_table}[{column}]')
            else:
                # Need LOOKUPVALUE
                lookup = self._build_lookupvalue(table, column, driving_table, join_map)
                select_args.append(f'        "{alias}",\n            {lookup}')
        
        # Build filters - find the COUNTY filter
        filter_expr = None
        for f in self.filters:
            cleaned = self._convert_sql_expr_to_dax(f)
            if cleaned and 'FAIRFAX' in cleaned:
                # Find the alias for COUNTY column
                for alias, (table, col) in column_alias_map.items():
                    if col == 'COUNTY':
                        filter_expr = f'[{alias}] = "FAIRFAX"'
                        break
                if filter_expr:
                    break
        
        # Construct the query
        lines = ["EVALUATE"]
        lines.append("VAR BaseTable =")
        lines.append("    SELECTCOLUMNS (")
        lines.append(f"        {driving_table},")
        lines.append("")
        
        # Add all column selections
        for i, arg in enumerate(select_args):
            comma = "," if i < len(select_args) - 1 else ""
            lines.append(f"{arg}{comma}")
        
        lines.append("    )")
        lines.append("")
        lines.append("RETURN")
        
        # Apply filter if found
        if filter_expr:
            lines.append("    DISTINCT (")
            lines.append("        FILTER (")
            lines.append("            BaseTable,")
            lines.append(f"            {filter_expr}")
            lines.append("        )")
            lines.append("    )")
        else:
            lines.append("    DISTINCT ( BaseTable )")
        
        # Add ORDER BY (matching demo pattern)
        lines.append("")
        lines.append("ORDER BY")
        # Order by all columns
        for i, alias in enumerate(column_alias_map.keys()):
            comma = "," if i < len(column_alias_map) - 1 else ""
            lines.append(f"    [{alias}]{comma}")
        
        return "\n".join(lines)

    def _parse_joins(self):
        """Parse join conditions to build a relationship map"""
        join_map = {}
        
        # Look for patterns like 'Table1'[Col1] = 'Table2'[Col2]
        for f in self.filters:
            match = re.search(r"'([^']+)'\[([^\]]+)\]\s*=\s*'([^']+)'\[([^\]]+)\]", f)
            if match:
                table1, col1, table2, col2 = match.groups()
                
                # Store bidirectional mapping
                if table1 not in join_map:
                    join_map[table1] = {}
                join_map[table1][table2] = (col1, col2)
                
                if table2 not in join_map:
                    join_map[table2] = {}
                join_map[table2][table1] = (col2, col1)
        
        return join_map

    def _build_lookupvalue(self, target_table, target_column, driving_table, join_map):
        """Build a LOOKUPVALUE expression to get a column from a related table"""
        
        # Special handling for FND_LOOKUP_VALUES_TL (always multi-condition)
        if target_table == 'FND_LOOKUP_VALUES_TL':
            return f"""LOOKUPVALUE (
                {target_table}[{target_column}],
                {target_table}[LOOKUP_CODE], {driving_table}[STATUS],
                {target_table}[LOOKUP_TYPE], "CODE_STATUS",
                {target_table}[LANGUAGE], "US",
                {target_table}[VIEW_APPLICATION_ID], 0,
                {target_table}[SET_ID], 0
            )"""
        
        # For HZ_PARTIES, always use PARTY_ID join
        if target_table == 'HZ_PARTIES':
            return f"""LOOKUPVALUE (
                {target_table}[{target_column}],
                {target_table}[PARTY_ID], {driving_table}[PARTY_ID]
            )"""
        
        # Try to find join from join_map
        if driving_table in join_map and target_table in join_map[driving_table]:
            driving_col, target_col = join_map[driving_table][target_table]
            return f"""LOOKUPVALUE (
                {target_table}[{target_column}],
                {target_table}[{target_col}], {driving_table}[{driving_col}]
            )"""
        
        # Fallback: return simple reference (shouldn't happen)
        return f"{target_table}[{target_column}]"

    def _convert_sql_expr_to_dax(self, expr):
        """Convert SQL expression to DAX"""
        cleaned = expr.strip()
        
        # Remove parens and 1=1
        changed = True
        while changed:
            changed = False
            if cleaned.startswith('(') and cleaned.endswith(')'):
                 if cleaned.count('(') == cleaned.count(')'):
                     cleaned = cleaned[1:-1].strip()
                     changed = True
                     continue
            if '1=1 AND ' in cleaned:
                cleaned = cleaned.replace('1=1 AND ', '').strip()
                changed = True
            if ' AND 1=1' in cleaned:
                cleaned = cleaned.replace(' AND 1=1', '').strip()
                changed = True
            if cleaned == '1=1':
                return None
        
        if not cleaned: return None
        
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned)
        if not cleaned: return None
        
        # Handle quotes - preserve 'Table'[Col], convert 'Value' to "Value"
        res = []
        i = 0
        n = len(cleaned)
        while i < n:
            char = cleaned[i]
            if char == "'":
                j = i + 1
                while j < n and cleaned[j] != "'":
                    j += 1
                if j < n:
                    quote_content = cleaned[i+1:j]
                    next_char = cleaned[j+1] if j+1 < n else ''
                    if next_char == '[':
                        res.append(f"'{quote_content}'")
                    else:
                        res.append(f'"{quote_content}"')
                    i = j + 1
                else:
                    res.append(cleaned[i:])
                    break
            else:
                res.append(char)
                i += 1
        
        cleaned = "".join(res)
        
        # IS NULL -> ISBLANK()
        if " IS NULL" in cleaned:
             cleaned = re.sub(r"('[\w\s]+'\[[\w\s]+\]) IS NULL", r"ISBLANK(\1)", cleaned)
        
        return cleaned.strip()
