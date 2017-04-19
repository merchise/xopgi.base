xopgi_directory (XOPGI Directory)
=================================
Introduce the "fake partner" as a trick to solve the problem that in odoo the
contact information is not concentrated in one place and may have several
origins.

A partner can have more than one contact information and the information of
the same contact can be in different objects such as (contracts,
accounts ..).  This results in that when we are going to manage or consult the
information of a contact this can be dispersed in different places.

'Fake partner': This trick helps us to classify `` res.partners ``
or contacts with the objective that can be classified, filtered and related
between them.

For example, suppose we have an 'A' contact registered with the following
information, name, phone, associated accounts, and for the activities that it
performs is considered as a customer and is classified as such.  Such contact
could designate a person to represent him to carry out his activities on his
behalf.

This person who fulfills the role of 'representative' needs to communicate and
be contacted to perform their functions.  The contact 'A' could also be notified
to keep informed of the fulfillment of the duties of his subordinate.

For them it is necessary to have the data of both people registered and have
them well identified and related to each other. In this case the 'representative'
could be registered as a 'fake partner' because in reality our customer is the
contact 'A'.  Many scenarios can be given where it is necessary to register
"fake partner" but the essence is to be able to differentiate them and relate
them to each other to have information concentrated in one place.

In odoo the contacts are represented through a ``res.partner``, and a
res.partner can be present in the logic of many models.  This cant means
that the information of a contact can be collected from different
models.

This addons allow you to configure partner directories across the models,
model fields, and fields of a res_partner, establishing a sort of mapping
between them. Allowing us to show the attributes of a model as contact
information for a 'fake partner'.

When these models are configured in the 'Directory configuration' will bring
as a result that when you create or update objects of its type. Fake partners
will be created or updated automatically by displaying your contact
information as a result of the previously made configuration. To see this
result we must visit the 'Contacts' menu and perform a search filtered by 'fake'.
