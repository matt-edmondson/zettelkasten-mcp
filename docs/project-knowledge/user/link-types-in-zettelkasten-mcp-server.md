================================================================
Start of Project Knowledge File
================================================================

Purpose:
--------
This file is designed to be consumed by AI systems for analysis, review,
or other automated processes. It solely serves the purpose of background
information and should NOT under any circumstances leak into the user's
interaction with the AI when actually USING the Zettelkasten MCP tools to
process, explore or synthesize user-supplied information.

Content:
--------

# Link Types In Zettelkasten MCP Server

The Zettelkasten MCP server uses a comprehensive semantic linking system that creates meaningful connections between notes. Each link type represents a specific relationship, allowing for a rich, multi-dimensional knowledge graph.

## Primary Link Types and Their Inverses

| Primary Link Type | Inverse Link Type | Relationship Description |
|-------------------|-------------------|--------------------------|
| `reference` | `reference` | Simple reference to related information (symmetric relationship) |
| `extends` | `extended_by` | One note builds upon or develops concepts from another |
| `refines` | `refined_by` | One note clarifies or improves upon another |
| `contradicts` | `contradicted_by` | One note presents opposing views to another |
| `questions` | `questioned_by` | One note poses questions about another |
| `supports` | `supported_by` | One note provides evidence for another |
| `related` | `related` | Generic relationship (symmetric relationship) |

## Using Link Types

When creating links between notes with `zk_create_link`, you can specify the link type to establish the appropriate relationship:

```
zk_create_link source_id=202504010930 target_id=202503251045 link_type=supports
```

The link type parameter can be any of the values from either the "Primary Link Type" or "Inverse Link Type" columns in the table above.

## Bidirectional Links

When creating links, you can set `bidirectional=true` to automatically create a complementary link in the reverse direction using the semantic inverse:

```
zk_create_link source_id=202504010930 target_id=202503251045 link_type=supports bidirectional=true
```

This will create:
1. A `supports` link from 202504010930 to 202503251045
2. A `supported_by` link from 202503251045 to 202504010930

The system automatically applies the correct semantic inverse relationship:
- If note A `extends` note B, then note B is `extended_by` note A
- If note A `contradicts` note B, then note B is `contradicted_by` note A
- And so on for all relationship pairs

For symmetric relationships (`reference` and `related`), the same link type is used in both directions.

## Custom Bidirectional Types

If you want to specify a custom relationship type for the reverse direction, use the `bidirectional_type` parameter:

```
zk_create_link source_id=202504010930 target_id=202503251045 link_type=supports bidirectional=true bidirectional_type=questions
```

This would create:
1. A `supports` link from 202504010930 to 202503251045
2. A `questions` link from 202503251045 to 202504010930

## Best Practices

- **Choose Specific Link Types**: Use specific semantic relationships rather than generic `reference` or `related` when possible
- **Consider Directionality**: The direction of links matters - pay attention to which note is the source and which is the target
- **Use Inverse Pairs Consistently**: Maintain semantic consistency by using the proper pairs of relationships
- **Create Strategic Bidirectional Links**: Not all links need to be bidirectional - use this feature for important conceptual relationships
- **Build Knowledge Paths**: Create intentional sequences of links that guide through a line of thinking
- **Balance Link Types**: A healthy Zettelkasten uses a mix of supportive, contradictory, and questioning links

## Link Type Meanings in Detail

- **reference/reference**: Simple connection between related notes without implying a specific relationship
- **extends/extended_by**: Indicates development or elaboration - the source note builds upon concepts in the target note
- **refines/refined_by**: Indicates improvement or clarification - the source note makes the target note's concepts more precise
- **contradicts/contradicted_by**: Indicates opposition or conflict - the source note challenges the target note's concepts
- **questions/questioned_by**: Indicates inquiry or uncertainty - the source note raises questions about the target note
- **supports/supported_by**: Indicates evidence or backing - the source note provides support for the target note's claims
- **related/related**: Indicates a general thematic connection when more specific relationships don't apply

By using this rich semantic linking system, your Zettelkasten becomes a sophisticated network of ideas with clearly defined relationships, facilitating deeper understanding and novel insights.

================================================================
End of Project Knowledge File
================================================================