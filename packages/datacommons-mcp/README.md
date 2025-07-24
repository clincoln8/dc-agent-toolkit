# DC MCP Server

A MCP server for fetching statistical data from Data Commons instances.

## Usage


### Start MCP Server

Option 1: Use the datacommons-mcp cli
```
export DC_API_KEY={YOUR_API_KEY}
uv run datacommons-mcp serve (http|stdio)
```

Option 2: Use the mcp cli
To start the MCP server, run:
```
export DC_API_KEY={YOUR_API_KEY}
cd packages/datacommons-mcp # navigate to package dir
uv run mcp run datacommons_mcp/server.py:mcp --t (sse|stdio)
```


### Test with MCP Inspector
To run with MCP Inspector, **from this dir** run:

```
export DC_API_KEY={YOUR_API_KEY}
uv run mcp dev datacommons_mcp/server.py
```

Make sure to use the MCP Inspector URL with the prefilled session token!

The connection arguments should be prefilled with 
* `Transport Type` = "STDIO"
* `Command` = "uv"
* `Arguments` = "run --with mcp mcp run datacommons_mcp/server.py"

### Configuration

The server uses configuration from [config.py](config.py) which supports:

- Base Data Commons instance
- Custom Data Commons instances
- Federation of multiple DC instances

Instantiate the clients in [server.py](server.py) based on the configuration.

```python
# Base DC client
multi_dc_client = create_clients(config.BASE_DC_CONFIG)

# Custom DC client
multi_dc_client = create_clients(config.CUSTOM_DC_CONFIG)

# Federation of multiple DC clients
multi_dc_client = create_clients(config.FEDERATED_DC_CONFIG)
```