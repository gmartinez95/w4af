"""
sqli.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.dbms as dbms
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.quick_match.multi_re import MultiRE
from w3af.core.data.quick_match.multi_in import MultiIn
from w3af.core.data.kb.vuln import Vuln


class sqli(AuditPlugin):
    """
    Find SQL injection bugs.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    SQL_ERRORS_STR = (
        # ASP / MSSQL
        (b'System.Data.OleDb.OleDbException', dbms.MSSQL),
        (b'[SQL Server]', dbms.MSSQL),
        (b'[Microsoft][ODBC SQL Server Driver]', dbms.MSSQL),
        (b'[SQLServer JDBC Driver]', dbms.MSSQL),
        (b'[SqlException', dbms.MSSQL),
        (b'System.Data.SqlClient.SqlException', dbms.MSSQL),
        (b'Unclosed quotation mark after the character string', dbms.MSSQL),
        (b"'80040e14'", dbms.MSSQL),
        (b'mssql_query()', dbms.MSSQL),
        (b'odbc_exec()', dbms.MSSQL),
        (b'Microsoft OLE DB Provider for ODBC Drivers', dbms.MSSQL),
        (b'Microsoft OLE DB Provider for SQL Server', dbms.MSSQL),
        (b'Incorrect syntax near', dbms.MSSQL),
        (b'Sintaxis incorrecta cerca de', dbms.MSSQL),
        (b'Syntax error in string in query expression', dbms.MSSQL),
        (b'ADODB.Field (0x800A0BCD)<br>', dbms.MSSQL),
        (b"ADODB.Recordset'", dbms.MSSQL),
        (b"Unclosed quotation mark before the character string", dbms.MSSQL),
        (b"'80040e07'", dbms.MSSQL),
        (b'Microsoft SQL Native Client error', dbms.MSSQL),
        (b'SQL Server Native Client', dbms.MSSQL),
        (b'Invalid SQL statement', dbms.MSSQL),

        # DB2
        (b'SQLCODE', dbms.DB2),
        (b'DB2 SQL error:', dbms.DB2),
        (b'SQLSTATE', dbms.DB2),
        (b'[CLI Driver]', dbms.DB2),
        (b'[DB2/6000]', dbms.DB2),

        # Sybase
        (b"Sybase message:", dbms.SYBASE),
        (b"Sybase Driver", dbms.SYBASE),
        (b"[SYBASE]", dbms.SYBASE),

        # Access
        (b'Syntax error in query expression', dbms.ACCESS),
        (b'Data type mismatch in criteria expression.', dbms.ACCESS),
        (b'Microsoft JET Database Engine', dbms.ACCESS),
        (b'[Microsoft][ODBC Microsoft Access Driver]', dbms.ACCESS),

        # ORACLE
        (b'Microsoft OLE DB Provider for Oracle', dbms.ORACLE),
        (b'wrong number or types', dbms.ORACLE),

        # POSTGRE
        (b'PostgreSQL query failed:', dbms.POSTGRE),
        (b'supplied argument is not a valid PostgreSQL result', dbms.POSTGRE),
        (b'unterminated quoted string at or near', dbms.POSTGRE),
        (b'pg_query() [:', dbms.POSTGRE),
        (b'pg_exec() [:', dbms.POSTGRE),

        # MYSQL
        (b'supplied argument is not a valid MySQL', dbms.MYSQL),
        (b'Column count doesn\'t match value count at row', dbms.MYSQL),
        (b'mysql_fetch_array()', dbms.MYSQL),
        (b'mysql_', dbms.MYSQL),
        (b'on MySQL result index', dbms.MYSQL),
        (b'You have an error in your SQL syntax;', dbms.MYSQL),
        (b'You have an error in your SQL syntax near', dbms.MYSQL),
        (b'MySQL server version for the right syntax to use', dbms.MYSQL),
        (b'Division by zero in', dbms.MYSQL),
        (b'not a valid MySQL result', dbms.MYSQL),
        (b'[MySQL][ODBC', dbms.MYSQL),
        (b"Column count doesn't match", dbms.MYSQL),
        (b"the used select statements have different number of columns",
            dbms.MYSQL),
        (b"DBD::mysql::st execute failed", dbms.MYSQL),
        (b"DBD::mysql::db do failed:", dbms.MYSQL),

        # Informix
        (b'com.informix.jdbc', dbms.INFORMIX),
        (b'Dynamic Page Generation Error:', dbms.INFORMIX),
        (b'An illegal character has been found in the statement',
            dbms.INFORMIX),
        (b'[Informix]', dbms.INFORMIX),
        (b'<b>Warning</b>:  ibase_', dbms.INTERBASE),
        (b'Dynamic SQL Error', dbms.INTERBASE),

        # DML
        (b'[DM_QUERY_E_SYNTAX]', dbms.DMLDATABASE),
        (b'has occurred in the vicinity of:', dbms.DMLDATABASE),
        (b'A Parser Error (syntax error)', dbms.DMLDATABASE),

        # Java
        (b'java.sql.SQLException', dbms.JAVA),
        (b'Unexpected end of command in statement', dbms.JAVA),

        # Coldfusion
        (b'[Macromedia][SQLServer JDBC Driver]', dbms.MSSQL),

        # SQLite
        (b'could not prepare statement', dbms.SQLITE),

        # Generic errors..
        (b'Unknown column', dbms.UNKNOWN),
        (b'where clause', dbms.UNKNOWN),
        (b'SqlServer', dbms.UNKNOWN),
        (b'syntax error', dbms.UNKNOWN),
        (b'Microsoft OLE DB Provider', dbms.UNKNOWN),
    )
    _multi_in = MultiIn(x[0] for x in SQL_ERRORS_STR)

    SQL_ERRORS_RE = (
        # ASP / MSSQL
        (r"Procedure '[^']+' requires parameter '[^']+'", dbms.MSSQL),
        # ORACLE
        (r'PLS-[0-9][0-9][0-9][0-9]', dbms.ORACLE),
        (r'ORA-[0-9][0-9][0-9][0-9]', dbms.ORACLE),
        # MYSQL
        (r"Table '[^']+' doesn't exist", dbms.MYSQL),
        # Generic errors..
        (r'SELECT .*? FROM .*?', dbms.UNKNOWN),
        (r'UPDATE .*? SET .*?', dbms.UNKNOWN),
        (r'INSERT INTO .*?', dbms.UNKNOWN),
    )
    _multi_re = MultiRE(SQL_ERRORS_RE)

    # Note that these payloads are similar but they do generate different errors
    # depending on the SQL query context they are used. Removing one or the
    # other will lower our SQLMap testenv coverage
    SQLI_STRINGS = ("a'b\"c'd\"",
                    "1'2\"3")

    SQLI_MESSAGE = ('A SQL error was found in the response supplied by '
                    'the web application, the error is (only a fragment is '
                    'shown): "%s". The error was found on response with id'
                    ' %s.')

    def __init__(self):
        AuditPlugin.__init__(self)

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for SQL injection vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        mutants = create_mutants(freq, self.SQLI_STRINGS, orig_resp=orig_response)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result,
                                      debugging_id=debugging_id)

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        """
        sql_error_list = self._findsql_error(response)
        orig_resp_body = mutant.get_original_response_body()

        for sql_error_string, dbms_type in sql_error_list:
            if sql_error_string not in orig_resp_body:
                if self._has_no_bug(mutant):
                    # Create the vuln,
                    desc = 'SQL injection in a %s was found at: %s'
                    desc %= dbms_type, mutant.found_at()
                                        
                    v = Vuln.from_mutant('SQL injection', desc, severity.HIGH,
                                         response.id, self.get_name(), mutant)

                    v.add_to_highlight(sql_error_string)
                    v['error'] = sql_error_string
                    v['db'] = dbms_type
                    
                    self.kb_append_uniq(self, 'sqli', v)
                    break

    def _findsql_error(self, response):
        """
        This method searches for SQL errors in html's.

        :param response: The HTTP response object
        :return: A list of errors found on the page
        """
        res = []

        for match in self._multi_in.query(response.body):
            om.out.information(self.SQLI_MESSAGE % (match, response.id))
            dbms_types = [x[1] for x in self.SQL_ERRORS_STR if x[0] == match]
            if len(dbms_types) > 0:
                res.append((match.decode('utf-8'), dbms_types[0]))

        for match, _, regex_comp, dbms_type in self._multi_re.query(response.body):
            om.out.information(self.SQLI_MESSAGE % (match.group(0), response.id))
            res.append((match.group(0), dbms_type))

        return res

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds SQL injections. To find this vulnerabilities the
        plugin sends the string d'z"0 to every injection point, and searches
        for SQL errors in the response body.
        """
