# sublime-simple-server
Sublime plugin that runs a basic http server from a specified folder.

## Config
In the same folder as the project file, put a file named `simple-server.json`.

`port` is the port to listen on, and should be a number.\
`root` is the folder to serve static files from, and is a path relative\
to the where the config files sits

```json
{
    "port": 1337,
    "root": "static/html"
}
```
