"""Sherlock Notify Module

This module defines the objects for notifying the caller about the
results of queries.
"""
import webbrowser

from colorama import Fore, Style

from sherlock_project.result import QueryStatus

# Global variable to count the number of results.
globvar = 0


class QueryNotify:
    """Query Notify Object.

    Base class that describes methods available to notify the results of
    a query.
    It is intended that other classes inherit from this base class and
    override the methods to implement specific functionality.
    """

    def __init__(self, result=None):
        """Create Query Notify Object.

        Contains information about a specific method of notifying the results
        of a query.

        Keyword Arguments:
        self                   -- This object.
        result                 -- Object of type QueryResult() containing
                                  results for this query.

        Return Value:
        Nothing.
        """

        self.result = result


    def start(self, message=None):
        """Notify Start.

        Notify method for start of query.  This method will be called before
        any queries are performed.  This method will typically be
        overridden by higher level classes that will inherit from it.

        Keyword Arguments:
        self                   -- This object.
        message                -- Object that is used to give context to start
                                  of query.
                                  Default is None.

        Return Value:
        Nothing.
        """


    def update(self, result):
        """Notify Update.

        Notify method for query result.  This method will typically be
        overridden by higher level classes that will inherit from it.

        Keyword Arguments:
        self                   -- This object.
        result                 -- Object of type QueryResult() containing
                                  results for this query.

        Return Value:
        Nothing.
        """

        self.result = result


    def finish(self, message=None):
        """Notify Finish.

        Notify method for finish of query.  This method will be called after
        all queries have been performed.  This method will typically be
        overridden by higher level classes that will inherit from it.

        Keyword Arguments:
        self                   -- This object.
        message                -- Object that is used to give context to start
                                  of query.
                                  Default is None.

        Return Value:
        Nothing.
        """


    def __str__(self):
        """Convert Object To String.

        Keyword Arguments:
        self                   -- This object.

        Return Value:
        Nicely formatted string to get information about this object.
        """
        return str(self.result)


class QueryNotifyPrint(QueryNotify):
    """Query Notify Print Object.

    Query notify class that prints results.
    """

    def __init__(
        self,
        result=None,
        verbose=False,
        print_all=False,
        browse=False,
        monitor=False,
        total_sites=0,
    ):
        """Create Query Notify Print Object.

        Contains information about a specific method of notifying the results
        of a query.

        Keyword Arguments:
        self                   -- This object.
        result                 -- Object of type QueryResult() containing
                                  results for this query.
        verbose                -- Boolean indicating whether to give verbose output.
        print_all              -- Boolean indicating whether to only print all sites, including not found.
        browse                 -- Boolean indicating whether to open found sites in a web browser.
        monitor                -- Boolean indicating whether to display live endpoint health.
        total_sites            -- Number of sites included in this search.

        Return Value:
        Nothing.
        """

        super().__init__(result)
        self.verbose = verbose
        self.print_all = print_all
        self.browse = browse
        self.monitor = monitor
        self.total_sites = total_sites
        self.completed_sites = 0
        self.health_counts = {"responsive": 0, "unavailable": 0, "skipped": 0}


    def start(self, message):
        """Notify Start.

        Will print the title to the standard output.

        Keyword Arguments:
        self                   -- This object.
        message                -- String containing username that the series
                                  of queries are about.

        Return Value:
        Nothing.
        """

        title = "Checking username"
        self.completed_sites = 0

        print(Style.BRIGHT + Fore.GREEN + "[" +
              Fore.YELLOW + "*" +
              Fore.GREEN + f"] {title}" +
              Fore.WHITE + f" {message}" +
              Fore.GREEN + " on:")
        # An empty line between first line and the result(more clear output)
        print('\r')


    def countResults(self):
        """This function counts the number of results. Every time the function is called,
        the number of results is increasing.

        Keyword Arguments:
        self                   -- This object.

        Return Value:
        The number of results by the time we call the function.
        """
        global globvar
        globvar += 1
        return globvar

    def update(self, result):
        """Notify Update.

        Will print the query result to the standard output.

        Keyword Arguments:
        self                   -- This object.
        result                 -- Object of type QueryResult() containing
                                  results for this query.

        Return Value:
        Nothing.
        """
        self.result = result

        if self.monitor:
            self._update_monitor(result)
            return

        response_time_text = ""
        if self.result.query_time is not None and self.verbose is True:
            response_time_text = f" [{round(self.result.query_time * 1000)}ms]"

        # Output to the terminal is desired.
        if result.status == QueryStatus.CLAIMED:
            self.countResults()
            print(Style.BRIGHT + Fore.WHITE + "[" +
                  Fore.GREEN + "+" +
                  Fore.WHITE + "]" +
                  response_time_text +
                  Fore.GREEN +
                  f" {self.result.site_name}: " +
                  Style.RESET_ALL +
                  f"{self.result.site_url_user}")
            if self.browse:
                webbrowser.open(self.result.site_url_user, 2)

        elif result.status == QueryStatus.AVAILABLE:
            if self.print_all:
                print(Style.BRIGHT + Fore.WHITE + "[" +
                      Fore.RED + "-" +
                      Fore.WHITE + "]" +
                      response_time_text +
                      Fore.GREEN + f" {self.result.site_name}:" +
                      Fore.YELLOW + " Not Found!")

        elif result.status == QueryStatus.UNKNOWN:
            if self.print_all:
                print(Style.BRIGHT + Fore.WHITE + "[" +
                      Fore.RED + "-" +
                      Fore.WHITE + "]" +
                      Fore.GREEN + f" {self.result.site_name}:" +
                      Fore.RED + f" {self.result.context}" +
                      Fore.YELLOW + " ")

        elif result.status == QueryStatus.ILLEGAL:
            if self.print_all:
                msg = "Illegal Username Format For This Site!"
                print(Style.BRIGHT + Fore.WHITE + "[" +
                      Fore.RED + "-" +
                      Fore.WHITE + "]" +
                      Fore.GREEN + f" {self.result.site_name}:" +
                      Fore.YELLOW + f" {msg}")

        elif result.status == QueryStatus.WAF:
            if self.print_all:
                print(Style.BRIGHT + Fore.WHITE + "[" +
                      Fore.RED + "-" +
                      Fore.WHITE + "]" +
                      Fore.GREEN + f" {self.result.site_name}:" +
                      Fore.RED + " Blocked by bot detection" +
                      Fore.YELLOW + " (proxy may help)")

        else:
            # It should be impossible to ever get here...
            raise ValueError(
                f"Unknown Query Status '{result.status}' for site '{self.result.site_name}'"
            )

    def _update_monitor(self, result):
        self.completed_sites += 1
        if result.status == QueryStatus.ILLEGAL:
            endpoint_status = "SKIPPED (invalid username)"
            self.health_counts["skipped"] += 1
        elif (
            isinstance(result.http_status, int)
            and 100 <= result.http_status < 500
        ):
            endpoint_status = f"RESPONSIVE (HTTP {result.http_status})"
            self.health_counts["responsive"] += 1
        else:
            status_text = (
                f"HTTP {result.http_status}"
                if isinstance(result.http_status, int)
                else "no HTTP response"
            )
            endpoint_status = f"UNAVAILABLE ({status_text})"
            self.health_counts["unavailable"] += 1

        response_time_text = ""
        if result.query_time is not None:
            response_time_text = f" [{round(result.query_time * 1000)}ms]"

        total_text = str(self.total_sites) if self.total_sites else "?"
        print(
            f"[{self.completed_sites}/{total_text}] {result.site_name}: "
            f"{result.status} | endpoint {endpoint_status}{response_time_text}"
        )

        if result.status == QueryStatus.CLAIMED:
            self.countResults()
            if self.browse:
                webbrowser.open(result.site_url_user, 2)
        elif result.status not in (
            QueryStatus.AVAILABLE,
            QueryStatus.UNKNOWN,
            QueryStatus.ILLEGAL,
            QueryStatus.WAF,
        ):
            raise ValueError(
                f"Unknown Query Status '{result.status}' for site '{result.site_name}'"
            )

    def finish(self, message="The processing has been finished."):
        """Notify Finish.
        Will print the last line to the standard output.
        Keyword Arguments:
        self                   -- This object.
        message                -- The 2 last phrases.
        Return Value:
        Nothing.
        """
        NumberOfResults = self.countResults() - 1

        print(Style.BRIGHT + Fore.GREEN + "[" +
              Fore.YELLOW + "*" +
              Fore.GREEN + "] Search completed with" +
              Fore.WHITE + f" {NumberOfResults} " +
              Fore.GREEN + "results" + Style.RESET_ALL
              )
        if self.monitor:
            print("Endpoint health summary (HTTP reachability):")
            print(f"  Responsive (HTTP 1xx-4xx): {self.health_counts['responsive']}")
            print(f"  Unavailable (HTTP 5xx/no response): {self.health_counts['unavailable']}")
            print(f"  Skipped (invalid username): {self.health_counts['skipped']}")

    def __str__(self):
        """Convert Object To String.

        Keyword Arguments:
        self                   -- This object.

        Return Value:
        Nicely formatted string to get information about this object.
        """
        return str(self.result)
