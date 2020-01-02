# Work in progress

## Basics
- Save either the file, or a link to get it
- Description
- Read or not, by whom
- Score
- Tags (automatically generated?)

## Works for
- Books / Papers
- Articles
- Ideas
- Music, Film
- Food recipes

## Examples

```
!add [file/link] tags: [one, two] description: "looks really cool"
!edit [id] tags: [one]
!get [id]
!find "keyword"
!find tags: [one, two]

experiments
!undo
```

## Parser
- Uses [LARk](https://github.com/lark-parser/lark)
- Very loose parser, with additional checks later

# Search
- Probabily need to index documents and use something like pysolr
- https://github.com/django-haystack/pysolr

## Core table
`| id | name | updates | hidden | tags | link | file |`

## Pieces
- Discord bot frontend
- Console frontend
- Database
    - Files
    - Entries
- Backend
    - Add [file]
    - Add [link]
    - Get ---
    - Find
        - Search options: [tag, keyword, advanced]
        - Result options: [what, order]


## DB Methods
An archive works similarly to a database, it might be interesting to emulate most of the database functionality
- Select
    - Select [] from table where [] order by []
- Create
- Alter table
- Insert
- Drop table


## Install
Install required python modules:
- discord.py
- lark
- texttable


## Todo
- Improve documentation
- Notes

## Bugs
- Editing update message to change the id doesn't restore deleted message

### Ideas
A bunch of ideas that are worth exploring
- Safe database updates
    - How to update the bot with new features while making sure no data is lost?
    - Should also support rollbacks
- Improve updates
    - Group edits
- Improve search
    - Look at description, creator, scores...
    - Automatic tags?
    - Look at file content
    - Image classification?
    - Search metadata (who are all known authors?)
- Tags are powerful and can be used to implement other features
    - author:slysherz
    - author:? (query who the autor is)
    - special tag restrictitions: score:value with value in 0-5
- Improve big archive scalling
- Which messages to answer to, which to ignore?
- User permissions
- Check if link works, save article
- Plugins
- Playlist
- Show entry's history
- Improve discord integration
- Consider keeping updated entry on the same id
    - Message edits already improve this use case
- Search inside vs outside database
- Load from history
    - Needs strong backward compatibility
- Type check commands
    - Improve error messages
    - Usage command
- Improve get/add/update messages
    - File / link preview
- Configuration
    - Load settings from a file which can be reloaded
- Knowledge graphs
    - How to tell: you should read this before you read that
- Rethink how to select which fields are shown
- Consider merging get and find
- Consider having multiple files per entry
- What to do when getting an hidden item
    - Show an error?
    - Get the newest version?

### Backlog
Low importance nice to haves
- Support edits for older messages

## Values
- Support few commands, but support them really well
    - Be overwelmingly nice
    - If it seems like it should work, it probably should
- Never lose data
    - Files are small, we can keep them forever