# this is a virtual module that is entirely implemented server side

DOCUMENTATION = """
---
module: config_template
version_added: "2.0.0"
short_description: Renders template files providing a create/update override interface
description:
  - The module contains the template functionality with the ability to override items
    in config, in transit, through the use of a simple dictionary without having to
    write out various temp files on target machines. The module renders all of the
    potential jinja a user could provide in both the template file and in the override
    dictionary which is ideal for deployers who may have lots of different configs
    using a similar code base.
  - The module is an extension of the P(ansible.builtin.copy#module) module and all of attributes that can be
    set there are available to be set here.
notes:
  - O(config_type=hjson) converted to JSON on the output.
  - Has alias C(vooon.config.template).
options:
  src:
    description:
      - Path of a Jinja2 formatted template on the local server. This can be a relative
        or absolute path.
    required: true
    default: null
  dest:
    description:
      - Location to render the template to on the remote machine.
    required: true
    default: null
  config_overrides:
    description:
      - "Support two modes of operation: simple dict merge and RFC 6902 JSON Patch."
      - >-
        B(Simple merge).
        A dictionary used to update or override items within a configuration template.
        The dictionary data structure may be nested. If the target config file is an ini
        file the nested keys in the O(config_overrides) will be used as section
        headers.
      - >-
        B(JSON Patch). A list of dicts like C({"op": "add", "path": "/foo", "value": "bar"})
    type: json
  config_type:
    description:
      - A string value describing the target config type.
    choices:
      - ini
      - json
      - hjson
      - yaml
      - toml
  list_extend:
    description:
      - By default a list item in a JSON or YAML format will extend if
        its already defined in the target template and a config_override
        using a list is being set for the existing "key". This functionality
        can be toggled on or off using this option. If disabled an override
        list will replace an existing "key".
    type: bool
  ignore_none_type:
    description:
      - Can be true or false. If ignore_none_type is set to true, then
        valueless INI options will not be written out to the resultant file.
        If it's set to false, then config_template will write out only
        the option name without the '=' or ':' suffix. The default is true.
    type: bool
  default_section:
    description:
      - Specify the default section for INI configuration files. This is the
        section that will appear at the top of the configuration file. For
        example V(global).
    default: 'DEFAULT'
  remote_src:
    description:
      - Influence whether the template needs to be transferred or already is
        present remotely.
      - If false, it will search the originating machine.
      - If true, it will go to the remote/target machine to inject the
        template. If the remote source does not exist the module will fail.
    type: bool
    default: false
  render_template:
    description:
      - Enable or disable the template render engine. This is useful when
        dealing with remote data that may have jinja content in the comment
        sections but is not in need of rendering.
    type: bool
    default: true
  strip_comments:
    description:
      - Strip all comment and empty lines in INI
    type: bool
    default: false
  json_indent:
    description:
      - JSON and HJSON identation
    type: int
    default: 4
  json_sort_keys:
    description:
      - Sort dict keys in JSON result
    type: bool
    default: false
  yaml_indent_mapping:
    description:
      - YAML mapping indent
    type: int
    default: 2
  yaml_indent_sequence:
    description:
      - YAML sequence indent
    type: int
    default: 4
  yaml_indent_offset:
    description:
      - YAML offset indent
    type: int
    default: 2
author: Kevin Carter
"""

EXAMPLES = """
- name: run config template ini
  config_template:
    src: templates/test.ini.j2
    dest: /tmp/test.ini
    config_overrides: {}
    top_ini_section: 'global'
    config_type: ini

- name: run config template json
  config_template:
    src: templates/test.json.j2
    dest: /tmp/test.json
    config_overrides: {}
    config_type: json

- name: run config template yaml
  config_template:
    src: templates/test.yaml.j2
    dest: /tmp/test.yaml
    config_overrides: {}
    config_type: yaml
"""
