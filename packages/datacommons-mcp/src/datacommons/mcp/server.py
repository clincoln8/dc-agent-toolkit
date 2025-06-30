# server.py
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Data Commons")


@mcp.tool()
async def fetch_observations(
    variable_dcid: str,
    place_dcids: list[str] | None = None,
    parent_place_dcid: str | None = None,
    child_place_type_dcid: str | None = None,
    facet_id_override: str | None = None,
) -> dict:
  """Get observations for a given concept or indicator (called a statistical variable in Data Commons parlance) about a place from Data Commons.
    This tool can retrieve various types of data, including time series, single values,
    or categorical information, depending on the concept requested and the available data.

    Note: This tool retrieves observations for all dates.
    Unlike get_observations_for_child_places, this tool does NOT support filtering the results by a specific date.

    You must provide either a variable_desc or a variable_dcid, but not both.
    You must provide either a place_name or a place_dcid, but not both.

    Guidance on Variable Selection:

    When the user is asking for data about a place_name or place_dcid for which
    you have previously successfully called get_available_variables_for_place,
    you will have access to a list of available variable DCIDs and their id_name_mappings.

    Prioritization: Before attempting to use the variable_desc parameter,
    if you have previously called get_available_variables_for_place for this place,
    FIRST examine the user's request and compare it to the id_name_mappings
    you already possess for this place.

    If you find a variable name in your id_name_mappings that appears to be a close
    or exact match to the concept or indicator the user is asking for,
    use the corresponding variable_dcid in your call to get_observations.
    This is the preferred method when relevant DCIDs are known.
    Example: If the user asks for "mean rainfall in Mumbai" and your id_name_mappings
    for Mumbai includes "Mean_Rainfall": "Mean Rainfall",
    use variable_dcid="Mean_Rainfall" and place_dcid="wikidataId/Q1156"
    (assuming you have the place DCID).

    Fallback: If you cannot find a sufficiently relevant variable name
    in your existing id_name_mappings for the requested place,
    should you use the variable_desc parameter to provide a natural language description
    of the variable you are looking for.

    Args:
      variable_dcid (str, optional): The DCID of the statistical variable.
      place_dcid (str, optional): The DCID of the place.
      parent_place_dcid(str): The DCID of the larger geographic region or administrative division containing the places to fetch data for.
        This can be a city, county, state, country, a continent (like "Europe" or "Asia"), or the entire world.
      child_place_type (str): The DCID of the type of child places within the parent place to fetch data for. The valid types depend on the parent.
        Use the fetch_child_place_types tool to check valid child place types for a given parent place.
        Use the returned list to determine the correct child place type when calling this tool.
      facet_id_override (str, optional): An optional facet ID to force the selection of a specific data source.
        If not specified, the tool will select the best data source based on the observation count.
    Returns:
      dict: A dictionary containing the status of the request and the data if available.

      The dictionary has the following format:
      {
        "status": "SUCCESS" | "NO_DATA_FOUND" | "ERROR",
        "data": <data_by_variable>,
        "message": "..."
      }

      The data has the following format:
      {
            "dc_provider": "...",
            "lookups": {
                "id_name_mappings": { ... }
            },
            "data_by_variable": {
                "variable_id_1": {
                    "source": {
                        "facet_id": "best_facet_id",
                        "provenanceUrl": "...",
                        "unit": "...",
                        "observation_count": 120
                    },
                    "observations": [
                        ["entity_id_1", "date_1", "value_1"],
                        ["entity_id_2", "date_2", "value_2"]
                    ],
                    "other_available_sources": [
                        {
                            "facet_id": "other_facet_456",
                            "provenanceUrl": "...",
                            "unit": "...",
                            "observation_count": 50
                        }
                    ]
                }
            }
        }

      The facet_id is a unique identifier for the data source.
      Data is returned from a single source (facet).
      Other available sources are returned in the other_available_sources list.
      If the user asks for a specific data source, you can use the facet_id_override to force the selection of that source.

      In your response, use the id_name_mappings to convert the variable_id, entity_id, and facet_id to human-readable names.

      Also, cite the source of the data in your response and suffix it with "(Powered by {dc_provider})".
    """
  # 1. Input validation
  has_dcids = bool(place_dcids)
  has_pair = bool(parent_place_dcid and child_place_type_dcid)

  if has_dcids == has_pair:
    raise ValueError(
        "Supply EITHER a list of place_dcids OR a complete (parent_place_dcid, child_place_type_dcid) pair."
    )

  # 2. Process results and set DCIDs
  sv_dcid_to_use = variable_dcid
  dc_id_to_use = BASE_DC_ID if variable_dcid else None
  place_dcid_to_use = place_dcid

  if svs:
    sv_data = svs.get(variable_desc, {})
    print(f"sv_data: {variable_desc} -> {sv_data}")
    dc_id_to_use = sv_data.get("dc_id")
    sv_dcid_to_use = sv_data.get("SV", "")

  if places:
    place_dcid_to_use = places.get(place_name, "")
    print(f"place: {place_name} -> {place_dcid_to_use}")

  # 4. Final validation and fetch
  if not sv_dcid_to_use or not place_dcid_to_use or not dc_id_to_use:
    return {"status": "NO_DATA_FOUND"}

  response = await multi_dc_client.fetch_obs(dc_id_to_use, sv_dcid_to_use,
                                             place_dcid_to_use)
  dc_client = multi_dc_client.dc_map.get(dc_id_to_use)
  response["dc_provider"] = dc_client.dc_name

  return {
      "status":
          "SUCCESS",
      "data":
          transform_obs_response(response,
                                 dc_client.fetch_entity_names,
                                 facet_id_override=facet_id_override),
  }
