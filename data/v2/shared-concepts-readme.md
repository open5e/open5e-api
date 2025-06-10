# Shared concepts

In the current implementation, certain concepts are so universal that we have decided to have them be shared across documents, as they are basic world concepts with no unique values between implementations. Exceptions that arise should ideally be modeled on the shared core concept as nullable values or similar. If that is not possible, good topic to bring up in the discord.

These concepts include:
- Size
- Rarity
- Damage Types
- Creature Types
- Alignment
- Conditions
- 

These are advantageous to share because they improve filtering and searching: there is no benefit to the end user in having a "wrong" fire damage to filter monster resistances by, since fire resistance is effectively the same between 2024 and 2014 edition.

We should only be separating these concepts when they have dramatically different mechanics or value lists that make sharing them infeasible.