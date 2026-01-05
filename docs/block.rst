Block Notation
================
This document describes block notation, which is a simple text notation inspired by
ledger notation for representing structs of content.

Block Notation Basics
----------------------
Block notation represents data in blocks, which are delimited by indentation.
Each block starts with a header line, followed by indented lines that represent
the fields of the block. Each field line consists of a decimal value and a field
name in any order.

Example Block::

    legs workout
        20 squats
        15 wall sits
        10 lunges

In this example, "legs workout" is the block header, and the indented lines are the fields
of the block, representing different exercises and their counts.

Metadata in Blocks
-------------------
Blocks can include metadata in the header line, including dates, or a brief description
following a colon.

Example Block with Metadata::

    2023-10-05 legs workout
        20 squats
        15 wall sits
        10 lunges

    2023-10-06 legs workout: was tough!
        20 squats
        15 wall sits
        10 lunges

Block References
------------------
Once a block has been declared, you can reuse it by reference without redeclaring its contents.
Rather than repeating the field values, simply reference the block by name::

    2023-10-05 legs workout
        20 squats
        15 wall sits
        10 lunges

    2023-10-06 legs workout: was tough!



Nesting Blocks
-----------------
Blocks can be nested within other blocks to represent hierarchical data.
Example Nested Block::

    arms workout
        15 push-ups
        10 pull-ups
        20 bicep curls

    legs workout
        20 squats
        15 wall sits
        10 lunges

    daily workout
        legs workout
        arms workout

    new daily workout
        daily workout
        new workout
            5 burpees
            10 jumping jacks

    2023-10-07 new daily workout : was too exhausting
    2023-10-08
        new daily workout
        5 burpees
    2023-10-09 new daily workout

.. note::

    ``new workout`` is defined within a block but still is a valid reference in other blocks.
