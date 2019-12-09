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
- Drop [table]


## Install
Install required python modules:
- discord.py
- lark
- texttable


## Todo
- Draw tables
- Save and retrieve files