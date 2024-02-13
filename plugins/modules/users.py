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
module: user
author: "Derek Waters (dwaters@redhat.com)"
short_description: Manage a user in EDA Controller
description:
    - Create, update and delete users in EDA Controller
options:
    username:
      description:
        - The username of the user.
      required: True
      type: str
    new_username:
      description:
        - Setting this option will change the existing username (looked up via the username field).
      type: str
    first_name:
      description:
        - The first name of the user.
      required: False
      type: str
    last_name:
      description:
        - The last name of the user.
      required: False
      type: str
    email:
      description:
        - The email address of the user.
      required: False
      type: str
    password:
      description:
        - The password of the user.
      required: True
      type: str
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str

extends_documentation_fragment: infra.eda_configuration.auth
"""


EXAMPLES = """
- name: Create eda user
  infra.eda_configuration.user:
    username: test_user
    first_name: Test
    last_name: User
    email: test_user@example.com
    password: not_a_real_password
    state: present
    eda_host: eda.example.com
    eda_username: admin
    eda_password: Sup3r53cr3t

"""

from ..module_utils.eda_module import EDAModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        username=dict(required=True),
        new_username=dict(),
        first_name=dict(),
        last_name=dict(),
        email=dict(),
        password=dict(required=True),
        state=dict(choices=["present", "absent"], default="present"),
    )

    # Create a module for ourselves
    module = EDAModule(argument_spec=argument_spec)

    # Extract our parameters
    username = module.params.get("username")
    new_username = module.params.get("new_username")
    state = module.params.get("state")

    new_fields = {}

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one("users", name_or_id=name, key="req_url")

    if state == "absent":
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_item, key="req_url")

    # Create the data that gets sent for create and update
    # Remove these two comments for final
    # Check that Links and groups works with this.
    new_fields["username"] = new_username if new_username else (existing_item["username"] if existing_item else username)
    for field_name in (
        "first_name",
        "last_name",
        "email",
    ):
        field_val = module.params.get(field_name)
        if field_val is not None:
            new_fields[field_name] = field_val

    # If the state was present and we can let the module build or update the existing item, this will return on its own
    module.create_or_update_if_needed(
        existing_item,
        new_fields,
        endpoint="users",
        item_type="users",
        key="req_url",
    )


if __name__ == "__main__":
    main()
