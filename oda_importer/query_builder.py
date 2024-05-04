""" A module for constructing SDMX API queries for the OECD data. """
from oda_importer.common import logger

V1_BASE_URL: str = "https://sdmx.oecd.org/public/rest/data/"
V2_BASE_URL: str = "https://sdmx.oecd.org/public/rest/v2/data/dataflow/"
AGENCY_ID: str = "OECD.DCD.FSD"
SHAPE: str = "dimensionAtObservation=AllDimensions"
FORMAT: str = "csvfilewithlabels"


class QueryBuilder:
    """
    A builder class for constructing SDMX API queries for the OECD data.

    Attributes:
        agency_id (str): The agency ID used in the query.
        base_url (str): The base URL for the query, dynamically determined by the API version.
        params (dict): A dictionary of query parameters, initialized with default format.
        api_version (int): The version of the API to use.
    """

    def __init__(
        self,
        dataflow_id: str,
        dataflow_version: str = None,
        api_version: int = 2,
    ) -> None:
        """
        Initialize the QueryBuilder with specific settings for the API and data flow.

        Args:
            dataflow_id (str): The identifier for the dataflow.
            dataflow_version (str): The version of the dataflow
            api_version (int): The version of the API to use, default is 2.
        """

        # If dataflow_version is not provided, use the latest version
        dataflow_version = "+" if api_version == 2 and not dataflow_version else ""

        # Set the base URL and separator based on the API version
        base_url = V2_BASE_URL if api_version == 2 else V1_BASE_URL
        self._separator = "/" if api_version == 2 else ","

        # Set the agency ID
        self.agency_id = AGENCY_ID

        # Set the dimensions filter to all
        self.filter = "*" if api_version == 2 else "all"

        # Construct the base URL
        self.base_url = (
            f"{base_url}{self.agency_id}"
            f"{self._separator}{dataflow_id}"
            f"{self._separator}{dataflow_version}/"
        )

        # Initialize the query parameters with the default format
        self.params = {"format": FORMAT}

        # Store the API version
        self.api_version = api_version

    def _to_filter_str(self, param: str | list[str] | None) -> str:
        """Convert a string parameter to a list, if it is not already a list.

        Args:
            param (str | list[str] | None): The parameter to convert.
            api_version (int): The version of the API to use.

        Returns:
            list[str]: The parameter as a list.
        """

        if param is None:
            return "*" if self.api_version == 2 else ""
        if isinstance(param, str):
            param = [param]

        if (self.api_version == 2) & (len(param) > 1):
            logger.info(
                f"API version 2 does not support filtering on multiple values:"
                f"\n{(', '.join(param))} \n"
                "Returning all values."
            )
            return "*"

        return "+".join(param)

    def set_time_period(self, start: int | str, end: int | str) -> "QueryBuilder":
        """Set the time period for the query. The time period is inclusive.

        Args:
            start (int | str): The start year or date.
            end (int | str): The end year or date.

        Returns:
            Self: Returns self to allow for method chaining.
        """
        if self.api_version == 2:
            self.params["c[TIME_PERIOD]"] = f"ge:{start}+le:{end}"
        else:
            self.params["startPeriod"] = start
            self.params["endPeriod"] = end

        return self

    def build_dac1_filter(
        self,
        donor: str | list[str] | None = None,
        measure: str | list[str] | None = None,
        flow_type: str | list[str] | None = None,
        unit_measure: str | list[str] | None = None,
        price_base: str | list[str] | None = None,
    ) -> str:
        # if any of the parameters are None, set them to the default value
        donor = self._to_filter_str(donor)
        measure = self._to_filter_str(measure)
        untied = self._to_filter_str(None)
        flow_type = self._to_filter_str(flow_type)
        unit_measure = self._to_filter_str(unit_measure)
        price_base = self._to_filter_str(price_base)
        period = self._to_filter_str(None)

        return ".".join(
            [donor, measure, untied, flow_type, unit_measure, price_base, period]
        )

    def set_filter(self, filter_string: str) -> "QueryBuilder":
        """Set the dimensions parameter for the query.

        Args:
            filter_string (str): The filter string for the query.

        Returns:
            Self: Returns self to allow for method chaining.
        """

        self.filter = filter_string
        return self

    def set_last_n_observations(self, n: int) -> "QueryBuilder":
        """Set the number of most recent observations to return.

        Args:
            n (int): The number of most recent observations to return.

        Returns:
            Self: Returns self to allow for method chaining.
        """
        self.params["lastNObservations"] = n
        return self

    def set_format(self, file_format) -> "QueryBuilder":
        """Set the format of the output file.

        Args:
            file_format (str): The file format for the output.

        Returns:
            Self: Returns self to allow for method chaining.
        """
        self.params["format"] = file_format
        return self

    def build_query(self) -> str:
        """Construct and return the full query URL.

        Returns:
            str: The fully constructed URL.
        """
        # Create list to contain query parts
        query_parts = [self.base_url + self.filter + "?"]

        # Add each parameter to the query
        query_parts.extend(f"{key}={value}&" for key, value in self.params.items())

        # Return the full query URL, removing the trailing "&"
        return "".join(query_parts).rstrip("&")
