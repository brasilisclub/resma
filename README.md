# Resma CLI
A CLI tool to generate static websites. 

- [Installation](#Installation)

## Instalation
There are multiple ways to install Resma.

### MacOS and GNU-Linux
You are able to install Resma from its binaries, simply run:

```
curl -sSL https://install.resma.dev | python3 -
```

### All OSes
You can also install it from PyPI:

```
pip install resma
```

## Folder Structure
To easy our users transition, Resma-CLI use a similiar folder structure as others famous SSGs:

|-- config.toml

|-- content

|-- templates

|-- styles

|-- static

The `content` folder holds all markdown files, each of them represents an active page of your website, 
while a section (such as a blog) is represented by a folder and defined with a `_index.md` file. 

├── content/

│   └── blog/

│       ├── _index.md

│       ├── first.md

│       └── second.md


A `public` folder will be generated containing all your website files, after the build.

