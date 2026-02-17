# this is a virtual module that is entirely implemented server side

DOCUMENTATION = """
---
module: jsonnet
short_description: Renders template files using jsonnet format
version_added: "2.6.0"
description:
  - The module is an extension of the P(ansible.builtin.copy#module) module and all of attributes that can be
    set there are available to be set here.
options:
  src:
    description:
      - Path of a Jsonnet formatted template on the local server. This can be a relative
        or absolute path.
    required: true
    default: null
  dest:
    description:
      - Location to render the template to on the remote machine.
    required: true
    default: null
  format:
    description:
      - Template result format
    default: json
    choices: [json, yaml]
  include_dir:
    description:
      - Template include dir
    default: templates

# extends_documentation_fragment:
#   - action_common_attributes
#   - action_common_attributes.flow
#   - action_common_attributes.files
#   # - backup
#   # - files
#   # - template_common
#   # - validate

author:
  - Lucas Romero
"""

EXAMPLES = """
- name: Run alert template
  jsonnet:
    src: node.jsonnet
    dest: /etc/prometheus/rules/node.yml
    format: yaml
"""
