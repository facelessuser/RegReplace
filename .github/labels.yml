# Wildcard labels

brace_expansion: true
extended_glob: true

rules:
  - labels: [infrastructure]
    patterns: ['*|-@(*.md|*.py|*.sublime-@(keymap|menu|settings|commands))', '@(requirements|.github)/**']

  - labels: [source]
    patterns: ['**/*.py|-tests']

  - labels: [docs]
    patterns: ['**/*.md|docs/**']

  - labels: [tests]
    patterns: ['tests/**']

  - labels: [plugins]
    patterns: ['rr_modules/**|rr_plugin.py']

  - labels: [edit]
    patterns: ['rr_edit.py']

  - labels: [notify]
    patterns: ['rr_notify.py']

  - labels: [replacer]
    patterns: ['rr_replacer.py']

  - labels: [sequencer]
    patterns: ['rr_sequencer.py']

  - labels: [upgrade]
    patterns: ['rr_upgrade.py']

  - labels: [settings]
    patterns: ['*.sublime-@(keymap|menu|settings|commands)']

# WIP

wip:
  - work-in-progress
  - needs-review
  - needs-decision
  - needs-confirmation
  - requires-changes
  - rejected

# Label management

delete_labels: true

colors:
    bug: '#c45b46'
    feature: '#7b17d8'
    enhancement: '#0b9e9e'
    support: '#efbe62'
    maintenance: '#b2ffeb'
    category: '#709ad8'
    subcategory: '#bfd4f2'
    pending: '#f0f49a'
    rejected: '#f7c7be'
    approved: '#beed6d'
    low: '#dddddd'
    bot: '#000000'

labels:
- name: bug
  color: bug
  description: Bug report.

- name: feature
  color: feature
  description: Feature request.

- name: enhancement
  color: enhancement
  description: Enhancement

- name: maintenance
  color: maintenance
  description: Maintenance chore.

- name: support
  color: support
  description: Support request.

- name: tests
  color: category
  description: Related to testing.

- name: infrastructure
  color: category
  description: Related to project infrastructure.

- name: source
  color: category
  description: Related to source code.

- name: docs
  color: category
  description: Related to documentation.

- name: plugins
  color: subcategory
  description: Related to plugins.

- name: edit
  color: subcategory
  description: Related to the edit library.

- name: notify
  color: subcategory
  description: Related to the notify library.

- name: replacer
  color: subcategory
  description: Related to the replacer library.

- name: sequencer
  color: subcategory
  description: Related to the sequencer library.

- name: upgrade
  color: subcategory
  description: Related to upgrade library.

- name: settings
  color: subcategory
  description: Related to Sublime settings files.

- name: more-info-needed
  color: pending
  description: More information is required.

- name: needs-confirmation
  color: pending
  description: The alleged behavior needs to be confirmed.

- name: needs-decision
  color: pending
  description: A decision needs to be made regarding request.

- name: confirmed
  color: approved
  description: Confirmed bug report or approved feature request.

- name: maybe
  color: low
  description: Pending approval of low priority request.

- name: duplicate
  color: rejected
  description: The issue has been previously reported.

- name: wontfix
  color: rejected
  description: The issue will not be fixed for the stated reasons.

- name: invalid
  color: rejected
  description: Invalid report (user error, upstream issue, etc).

- name: triage
  color: pending
  description: Issue needs triage.

- name: work-in-progress
  color: pending
  description: A partial solution. More changes will be coming.

- name: needs-review
  color: pending
  description: Needs to be reviewed and/or approved.

- name: requires-changes
  color: pending
  description: Awaiting updates after a review.

- name: approved
  color: approved
  description: The pull request is ready to be merged.

- name: rejected
  color: rejected
  description: The pull request is rejected for the stated reasons.

- name: skip-triage
  color: bot
  description: Tells bot to not tag a new issue with 'triage'.

- name: skip-review
  color: bot
  description: Tells bot to not tag a reviews with 'needs-review'.
