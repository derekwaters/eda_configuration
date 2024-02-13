#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2024, Derek Waters <dwaters@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
---
module: rulebook_activation
author: "Derek Waters (dwaters@redhat.com)"
short_description: Manage a Rulebook Activation in EDA Controller
description:
    - Create, update and delete rulebook activations in EDA Controller
options:
    name:
      description:
        - The name of the rulebook activation.
      required: True
      type: str
    new_name:
      description:
        - Setting this option will change the existing name (looked up via the name field).
      type: str
    description:
      description:
        - The description of the rulebook activation.
      required: False
      type: str
    project:
      description:
        - The name of the EDA project to use for the rulebook activation.
      required: True
      type: str
    rulebook:
      description:
        - The name of the rulebook within the EDA project to use for the rulebook activation.
      required: True
      type: str
    decision_environment:
      description:
        - The name of the Decision Environment to use for the rulebook activation.
      required: True
      type: str
    restart_policy:
      description:
        - The restart policy for the rulebook activation.
      choices: ["always", "never", "on-failure"]
      default: "always"
      type: str
    is_enabled:
      description:
        - Whether the rulebook activation should be enabled.
      choices: ["true", "false"]
      default: "true"
      type: str
    variables:
      description:
        - A dictionary defining additional variables passed to the rulebook.
      type: dict
      required: False
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str

extends_documentation_fragment: infra.eda_configuration.auth
"""


EXAMPLES = """
- name: Create eda rulebook activation
  infra.eda_configuration.rulebook_activation:
    name: my_activation
    description: my awesome rulebook activation
    project: my_project
    rulebook: listen_for_events.yaml
    decision_environment: default-de
    restart_policy: always
    is_enabled: true
    variables:
      listen_to_server: event_source_host.example.com
      listen_to_port: 8765
    state: present
    eda_host: eda.example.com
    eda_username: admin
    eda_password: Sup3r53cr3t

"""

from ..module_utils.eda_module import EDAModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        description=dict(),
        project=dict(required=True),
        rulebook=dict(required=True),
        decision_environment=dict(required=True),
        restart_policy=dict(choices=["always", "never", "on-failure"], default="always"),
        is_enabled=dict(choices=["true", "false"], default="true"),
        variables=dict(),
        state=dict(choices=["present", "absent"], default="present"),
    )

    # Create a module for ourselves
    module = EDAModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get("name")
    new_name = module.params.get("new_name")
    state = module.params.get("state")

    new_fields = {}

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one("activations", name_or_id=name, key="req_url")

    if state == "absent":
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_item, key="req_url")

    # Create the data that gets sent for create and update
    # Remove these two comments for final
    # Check that Links and groups works with this.
    new_fields["name"] = new_name if new_name else (module.get_item_name(existing_item) if existing_item else name)
    for field_name in (
        "description",
        "variables",
    ):
        field_val = module.params.get(field_name)
        if field_val is not None:
            new_fields[field_name] = field_val

    if module.params.get("project") is not None:
        new_fields["project_id"] = module.resolve_name_to_id("projects", module.params.get("project"))
    if module.params.get("decision_environment") is not None:
        new_fields["decision_environment_id"] = module.resolve_name_to_id("decision_environments", module.params.get("decision_environment"))

    # If the state was present and we can let the module build or update the existing item, this will return on its own
    module.create_or_update_if_needed(
        existing_item,
        new_fields,
        endpoint="activations",
        item_type="activations",
        key="req_url",
    )


if __name__ == "__main__":
    main()
