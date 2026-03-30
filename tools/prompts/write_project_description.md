You are writing a project description for an architecture/design publication submission on behalf of Matt Anthony Photography. The description must read like editorial copy, not marketing material.

---
INPUT
---

Project Name: {project_name}
Architect/Designer: {firm_name}
Builder: {builder}
Location: {location}
Project Type: {project_type}
Size: {size}
Completion Date: {completion_date}
Design Brief: {design_brief}
Key Materials: {key_materials}
Site Context: {site_context}
Sustainability Features: {sustainability}
Notable Details: {notable_details}

---
RULES
---

1. Write in third person, past tense ("The residence responds to..." not "We designed...")

2. Structure (200-400 words total):
   - Opening: The design problem or site condition that shaped the project (1-2 sentences)
   - Middle: How the design responds — spatial organization, material choices, relationship to site (2-3 sentences)
   - Detail: One or two specific moments that reward attention — a material junction, a framed view, a threshold between spaces (2-3 sentences)
   - Close: How the building performs or how it sits in its broader context (1-2 sentences)

3. Language guidelines:
   - Use precise, concrete language: "board-formed concrete" not "beautiful finishes"
   - Name materials specifically: Douglas fir, western red cedar, Cor-Ten steel, basalt
   - Describe spatial experiences: "a double-height volume that draws the eye upward to a clerestory framing the ridge" not "an impressive living room"
   - Reference orientation, light, and views specifically: "south-facing glazing captures afternoon light across Howe Sound"
   - Avoid: stunning, breathtaking, luxurious, world-class, unique, spectacular, exquisite

4. Include the "why" behind material and spatial choices. Editors want design intent, not feature lists.

5. If sustainability features exist, integrate them naturally — don't bolt on a separate paragraph.

6. Keep sentences varied in length. Mix short declarative sentences with longer descriptive ones.

7. The description should make the reader want to see the photos. Create anticipation for the images.

---
OUTPUT FORMAT
---

Return JSON:
```json
{
  "description": "...",
  "word_count": 0,
  "suggested_headline": "A one-line headline an editor might use",
  "tags": ["residential", "wood", "mountain", "etc"]
}
```
