# MCP server that enables any LLM to function as a Siri/Alexa/Google-style AI assistant

this is a very flexible and capable MCP server intended to be run on your own device. it's inspired by classic AI assistants like Siri, Alexa and Google Assistant but adding an LLM to that mix turns it all up to 11!

unlike many solutions so far, this is independent of the UI you choose to use for your AI assistant because it's using MCP and can be plugged into any system that supports MCP.

it's cross platform and what tools your LLM will see depends on what operating system you're using (windows, mac, or linux)

it enables your chosen AI assistant to:

- browse, read and modify your files (with safety features such as automatic backups before modification)
- read and process a wide range of file types (it can do things like look inside zip archives, see video metadata, stuff like that)
- read and process remote URLs (links) of those same file types and with the same extraction abilities
- manage a complete life organization system for you with notes, tasks, events/calendar/appointments, bookmarks, recipes, and so on. it's stored as a plain text markdown database (basically just a simple human readable folder) so it can easily be copied or backed up and you don't have to worry about being locked in to a database format!
- control a bunch of things about your device (it can even lock your screen!)
- get a ton of information about your device and then use it to diagnose problems
- transcribe youtube videos

if you use this with a good model, it'll smartly chain multiple actions together, and you can start doing things like asking it to summarize a youtube video and save it to your notes. or to create a recipe with some healthy vegetables and then save it to your recipes. it gets really powerful real fast! 

# how to install

run this:

```console
git clone https://github.com/Rose22/mcp_tools_server.git
cd mcp_tools_server
python -m venv venv
python -r requirements.txt
```

then you will need a way to run a python program in a virtualenv.
the simplest way is to use this command:
```console
/path/to/mcp_tools_server/venv/bin/python /path/to/mcp_tools_server/main.py
```

add that as the command in your AI user interface of choice. the transport type is stdio, but you can uncomment the relevant lines in `main.py` depending on which type of transport you need

(there will be a proper config system soon..)

# see it in action!

<img width="545" height="877" alt="image" src="https://github.com/user-attachments/assets/c6e03c7c-9bb3-4e95-b049-01fc81588e8b" />  

<img width="500" height="749" alt="image" src="https://github.com/user-attachments/assets/f4f361d9-d00c-4b81-afdb-04c2a218ab6a" />  

<img width="494" height="800" alt="image" src="https://github.com/user-attachments/assets/d704164b-2845-474d-825f-d2e3641f87ef" />

<img width="545" height="877" alt="image" src="https://github.com/user-attachments/assets/7f49f7ea-ca74-45e9-9e9e-309e54e34171" />

<img width="545" height="877" alt="image" src="https://github.com/user-attachments/assets/753b9639-00fd-4df1-a151-9feace7d3e00" />

<img width="545" height="877" alt="image" src="https://github.com/user-attachments/assets/ae212531-3e04-42ff-b3ae-22a4c45bcafd" />
