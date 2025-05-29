# Developer Documentation

## User Input via Forms

We often need to gather data from the user that is:

- structured - has pre-determined named fields
- typed - e.g. numbers rather than strings
- validated - has been checked for correctness

Cases that meet these criteria should make of use the [Forms module]. The reference
documentation for the module provides an introduction to its design, functionality and
usage.

[Forms module]: reference/solidity_gui/main/forms/index.md

The Forms module is still in an early stage of development so it's expected that it will
have to be extended to suit future use-cases. Please note that if the Forms module does
not currently address your use-case you are strongly recommended to consider extending
it rather than implementing custom code for an individual form. In particular, the
following current limitations are noted:

- Limited range of fields and widgets available.
- No ability to specify default values for fields.
- No nesting of forms.
- No inter-field dependencies - e.g. checking a box to another field available

Implementing additional field and widget classes will probably be the most common
extension and should be relatively straightforward based on the existing examples.
