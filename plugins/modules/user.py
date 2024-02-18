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
    password:
      description:
        - The password of the user.
      required: True
      type: str
    roles:
      description:
        - A list of the roles the user should have
      required: True
      type: list
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
    password: not_a_real_password
    roles:
      - Contributor
      - Operator
      - Auditor
      - Viewer
      - Admin
      - Editor
    state: present
    eda_host: eda.example.com
    eda_username: admin
    eda_password: Sup3r53cr3t

"""

from ..module_utils.eda_module import EDAModule


def main():
    # TODO: email can be specified, but the current EDA API
    # does not return the email when you retrieve all the users
    # in the system (see below for more info about why we need
    # to do that)
    # The email parameter should be added back to the argument_spec
    # once emails can be retrieved from the API
    #
    argument_spec = dict(
        username=dict(required=True),
        new_username=dict(),
        first_name=dict(),
        last_name=dict(),
        roles=dict(type="list",elements="str",required=True),
        password=dict(required=True,no_log=True),
        is_superuser=dict(type="bool",required=False,default=False),
        state=dict(choices=["present", "absent"], default="present"),
    )

    # Create a module for ourselves
    module = EDAModule(argument_spec=argument_spec)

    module.IDENTITY_FIELDS["users"] = "username"

    # Extract our parameters
    username = module.params.get("username")
    new_username = module.params.get("new_username")
    state = module.params.get("state")

    new_fields = {}

    # Attempt to look up an existing item based on the provided data
    # Because of limitations in the users api (ie. there is no search/filtering by username)
    # we will retrieve *all* users, and manually look for an existing one.
    # TODO: Implement a better method here once the EDA API is updated
    all_existing_items = module.get_all_endpoint("users")
    existing_item = None
    if all_existing_items["json"]["count"] > 0:
      for check_existing_item in all_existing_items["json"]["results"]:
        if check_existing_item["username"] == username:
          existing_item = module.existing_item_add_url(check_existing_item, "users", key="req_url")
          
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
        "password",
        "is_superuser",
    ):
        field_val = module.params.get(field_name)
        if field_val is not None:
            new_fields[field_name] = field_val

    # Roles use a predefined set of role objects stored in the EDA database
    # The API requires you to provide a list of the UUIDs (role.id)
    submitted_roles = []
    system_roles = module.get_all_endpoint("roles")
    selected_roles = module.params.get("roles")
    for role_name in selected_roles:
      find_role = None
      for system_role in system_roles["json"]["results"]:
        if system_role["name"] == role_name:
          find_role = system_role
      if find_role:
        submitted_roles.append(find_role['id'])
      else:
        module.fail_json(msg = "Unable to find role {}".format(role_name))
    new_fields["roles"] = submitted_roles

    # Because the API expects roles to be submitted as a list of UUIDs,
    # but retrieving the existing user record returns the roles as role
    # objects, we need to "flatten" the roles list
    if existing_item:
      new_roles = []
      for role in existing_item["roles"]:
        new_roles.append(role["id"])
      # To ensure comparison between the existing
      # and new role list, we sort the role UUIDs
      new_roles.sort()
      new_fields["roles"].sort()
      existing_item["roles"] = new_roles

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
