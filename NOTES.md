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
```

## Parser
- Uses [LARk](https://github.com/lark-parser/lark)
- Very loose parser, with additional checks later

## Core table
`| id | link | updates | hidden | tags |`

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
A bunch of ideas that are worth exploring
- Improve get/add/update messages
- Type check commands
- Safe database updates
    - How to update the bot with newe features while making sure no data is lost?
    - Should also support rollbacks
- Limit number of items shown
    - Look through multiple slices
- Improve updates
    - Add and remove values from tags (needs syntax)
- Improve search
    - Look at description, creator, scores...
    - Automatic tags?
    - Look at file content
    - Image classification?
- Improve big archive scalling
- Which messages to answer to, which to ignore?
- User permissions
- Check if link works, save article
- Plugins