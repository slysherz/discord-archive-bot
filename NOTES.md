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

## Examples

```
!add [file/link] tags: [one, two] description: "looks really cool"
!edit [id] tags: [one]
!get [id]
!find "keyword"
!find tags: [one, two]

experiments
!undo
!find page:3
!find tags: [author:slysherz]
!update 123 +[tag1 tag2] -tag3 
```

## Parser
- Uses [LARk](https://github.com/lark-parser/lark)
- Very loose parser, with additional checks later

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
- Improve updates
    - Add and remove values from tags (needs syntax)

Continuous improvement
- Type check commands
    - Improve error messages
    - Usage command
- Improve get/add/update messages

A bunch of ideas that are worth exploring
- Safe database updates
    - How to update the bot with new features while making sure no data is lost?
    - Should also support rollbacks
- Limit number of items shown
    - Look through multiple slices
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
    - handle message edits