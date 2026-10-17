# Adding a template: the SQL family

Fourteen entries, one language, and almost none of them interchangeable.

## The trap

`SELECT 'Hello World!'` is valid in some of these, invalid in others, and a
syntax error in the one that matters most. Linguist distinguishes SQL:2003,
SQL/MM, SQL/PL, PL/SQL, T-SQL, PSQL, and then the search and query DSLs on top:
Solr Query, MongoDB Query, Cypher, Neo4j, InfluxQL, PromQL, YQL, KQL, JQL,
Trino, XPath, FiQL, JMESPath, GraphQL.

None of them should share a template.

| entry | what its Hello World is |
|---|---|
| SQL:2003 | the standard: a bare `SELECT` |
| SQL/MM | Oracle's dialect, where a bare select is not allowed — `FROM DUAL` is mandatory |
| T-SQL | `PRINT 'Hello World!';` — there is no `SELECT` without a `FROM` |
| PL/SQL and SQL/PL | procedural blocks with `DBMS_OUTPUT.PUT_LINE`, wrapped in `BEGIN`/`END` |
| PSQL | ordinary SQL, because PostgreSQL allows a bare select |
| Cypher, Neo4j | `RETURN 'Hello World!';` — Cypher's keyword is RETURN |
| Solr Query | `q=Hello World!` — a URL parameter, not SQL at all |
| MongoDB Query | `db.greeting.find({ greeting: "Hello World!" })` |
| JQL | `text ~ "Hello World!"` — Jira's own syntax |
| XPath 2.0 | `string("Hello World!")` — an expression language, not a query language |
| JMESPath | a bare JSON string literal |

## The ones with no output at all

**PromQL** returns vectors and cannot print. Its entry is a labelled vector
literal with a comment explaining why.

**FiQL** is OpenSearch's query language and its "program" is the request line it
produces.

**GraphQL SDL** — a schema, not a query — is a *declaration*, so the greeting
belongs in a type description.

## Before you write one

- Check whether a bare `SELECT` needs a `FROM`. In two of these it does.
- Check whether the keyword is `RETURN`, `PRINT` or `SELECT`. It is not always
  `SELECT`.
- Check whether the entry is a query language or a query *result* syntax. Solr's
  is a parameter.
- XPath is an expression language: `string(...)`, not `SELECT`.