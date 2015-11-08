..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

====================================
Example Spec - The title of your RFE
====================================

Include the URL of your launchpad RFE:

https://bugs.launchpad.net/kuryr/+bug/example-id

Introduction paragraph -- why are we doing this feature? A single paragraph of
prose that **deployers, and developers, and operators** can understand.

Do you even need to file a spec? Most features can be done by filing an RFE bug
and moving on with life. In most cases, filing an RFE and documenting your
design is sufficient. If the feature seems very large or contentious, then
you may want to consider filing a spec.


Problem Description
===================

A detailed description of the problem:

* For a new feature this should be use cases. Ensure you are clear about the
  actors in each use case: End User vs Deployer

* For a major reworking of something existing it would describe the
  problems in that feature that are being addressed.

Note that the RFE filed for this feature will have a description already. This
section is not meant to simply duplicate that; you can simply refer to that
description if it is sufficient, and use this space to capture changes to
the description based on bug comments or feedback on the spec.


Proposed Change
===============

How do you propose to solve this problem?

This section is optional, and provides an area to discuss your high-level
design at the same time as use cases, if desired.  Note that by high-level,
we mean the "view from orbit" rough cut at how things will happen.

This section should 'scope' the effort from a feature standpoint: how is the
'kuryr end-to-end system' going to look like after this change? What Kuryr
areas do you intend to touch and how do you intend to work on them? The list
below is not meant to be a template to fill in, but rather a jumpstart on the
sorts of areas to consider in your proposed change description.

You do not need to detail API or data model changes.


References
==========

Please add any useful references here. You are not required to have any
reference. Moreover, this specification should still make sense when your
references are unavailable.
