# Notes

## How a sentence embedding is built

Text is mapped to tokens. Each token corresponds to a particular vector in a 384-dimensional space (for this model), taken from a lookup table. Then 6 transformer layers add context to every token vector, and finally all the token vectors are pooled (averaged) into one.

The text could be a 10-word query or a 500-word chunk; both end up as a single 384-dimensional vector. This has many consequences: a long chunk that covers several topics is averaged into one point, and only the first 256 tokens are read at all. The cosine similarity can only catch as much as that single vector keeps.
