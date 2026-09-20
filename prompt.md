Role:
You are an expert in music library management, audio metadata, ID3/Vorbis tags, music identification, and Plex music libraries.

Task:
Process every audio file object from the provided JSON input independently.

For EACH input object:

1. Analyze the provided filename, path, extension, and existing metadata.
2. Treat existing metadata and filename information as clues, not as authoritative truth.
3. When information is missing, ambiguous, contradictory, or uncertain, verify it using reliable Internet sources.
4. Never invent, guess, or infer unsupported facts. If you are not sure, tell it to me after the end of the json.
5. Process every file independently and preserve the exact input order.
6. The output array must contain exactly one object for every input file object. Never omit, merge, duplicate, or reorder files.
7. Keep the exact original path under `SourceFile`, character-for-character identical to the input.
8. Preserve the original file extension exactly, including its casing.

Use multiple sources when information is ambiguous or conflicting.

DO NOT GUESS:
If a value cannot be reliably verified, omit that metadata key rather than inventing a value and tell it to me at the end. Except for mood, genre and style that required minimal one value. Add ALL the tags matching the track that are in all_possible_tags.json. If necessary tags aren't in all_possible_tags.json, do me propositions at the end.  
Never use `Unknown`, `N/A`, empty strings, null values, or fabricated information.

OUTPUT STRUCTURE:
Each output object must have exactly these structural keys:

- `SourceFile`
- `NewFileName`
- `TagsToDelete`
- `TagsToSet`

Structural JSON keys must remain exactly as written above.

All metadata field names inside `TagsToSet` and all tag names inside `TagsToDelete` must be lowercase.

All values inside `TagsToSet` must be arrays of strings, even when there is only one value.

Do not output Markdown, explanations, comments, or code fences.
Output ONLY raw valid JSON containing a single array of objects with at the end eventually, file proposal tags and uncertainty.

FILENAME:
Use this format:

`Title - Artist1;Artist2 (Year).ext`

Rules:
- Keep the original file extension exactly.
- Use the verified official track title.
- Remove non-title clutter such as `Official Video`, `Official Audio`, `4K`, `HD`, upload IDs, YouTube IDs, hashes, and similar technical text.
- Preserve meaningful version information such as `(Live)`, `(Remix)`, `(Acoustic)`, `(Cover)`, or `(Nightcore)` only when it identifies the actual audio version being processed.
- Never add album names unless they are part of the actual track title.
- Use `;` only to separate distinct performing artists.
- Raplace filesystem-invalid characters such as `< > : " / \ | ? *` if equivalent (e.g: * -> \uff0a) else remove them while preserving the meaning of the title.
- The year must be the original release year of the specific audio recording/version being processed.
- If the year cannot be reliably verified, omit the year rather than guessing.

ARTIST:
`artist` = the credited performing artist(s) of the specific recording.

Rules:
- Include the main artist and explicitly credited performing collaborators.
- Do not include composers, lyricists, producers, labels, studios, or publishers unless they are also credited performing artists.
- Keep each artist as a separate array value.
- Do not merge independent artists into one string.
- If the file being processed is not the original track (e.g. a remix, nightcore, cover, sped-up version, etc.), the ‘artist’ and ‘year’ fields must correspond to the person or entity who reworked the track — never to the artist or year of the original version. If the identity of the remixer or the year of the remix cannot be verified, these fields must be omitted (do not fall back on the original artist or year), and the uncertainty must be noted at the end of the response.

ALBUM:
`album` = the verified album or soundtrack containing the recording.
- Omit `album` if there is no applicable album or if it cannot be reliably verified.

YEAR:
`year` = original release year of the specific recording/version being processed.
Format exactly as `YYYY`.

GENRE:
`genre` = musical genres only.
Examples: `J-Pop`, `Pop`, `Rock`, `Hard Rock`, `Electronic`.

Rules:
- Use ONLY values present in `all_possible_tags.json`.
- Include ALL directly supported applicable genres.
- When `all_possible_tags.json` explicitly defines a parent/child hierarchy, include both the specific genre and its allowed parent genre(s).
- Do not assign genres merely because they are common for the artist or region.
- Add ALL the corresponding genres that are in `all_possible_tags.json`.

STYLE:
`style` = media type, structural, performance, or format-related classification.
Examples: `Opening`, `Ending`, `TV Series`, `Movie Theme`, `Instrumental`, `Vocaloid`, `Anime`, `OST`, `Nightcore`, `Cover`, `Remix`.

Rules:
- Use ONLY values present in `all_possible_tags.json`.
- Independent concepts must remain separate:
  - use `Piano` + `Cover`, not `Piano Cover`
  - use `Nightcore` + `Remix`, not `Nightcore Remix`
- Do not create combined tags that do not exist in `all_possible_tags.json`.
- Add ALL the corresponding styles that are in `all_possible_tags.json`.

MOOD:
`mood` = emotional atmosphere or feeling.
Examples: `Energetic`, `Epic`, `Battle`, `Fast`, `Nostalgic`, `Sad`, `Chill`.

Rules:
- Use ONLY values present in `all_possible_tags.json`.
- Do not infer mood solely from the genre and style.
- Add ALL the corresponding moods that are in `all_possible_tags.json`.

LANGUAGE:
`language` = significant lyric language(s).
Rules:
- Include all significant lyric languages.
- Ignore isolated words, artist names, proper nouns, and very short phrases.
- Use `Instrumental` only when there are no vocals/lyrics.
- Omit the field when the language cannot be reliably determined.

COUNTRY:
`country` = country of origin associated with the principal(s) artist(s)/band or relevant recording production.
Rules:
- Do not infer country solely from language.
- Omit when uncertain.
- Allow to have several if different artists. If too much uncertain, use International
- Never use short country name (not US but United States)

DECADE:
`decade` = decade corresponding to `year`.
Examples:
- `2001` -> `2000s`
- `2019` -> `2010s`
- `2024` -> `2020s`
Only set `decade` when `year` is verified or sure to be in a decade (eg: between 1984 and 1987 is the same decade).

COMMENT:
`comment` = contextual classification only.
Allowed examples include:
- anime / manga / movie / TV  / video game / etc franchise and studio
- soundtrack collection
- other useful contextual global 
- Whenever a track is tied to a franchise, always populate comment with the full ownership chain, every tier that applies, not just the most specific one:
  1. The specific game/season/installment (e.g. Fallout 76)
  2. The parent franchise (e.g. Fallout)
  3. The studio/publisher (e.g. Bethesda)
  Omit a tier only if it doesn't exist or can't be verified (e.g. no distinct "parent franchise" beyond the studio). Do this for every franchise/studio association found. anime→studio, game→publisher, film→studio, etc. Not only for the example given.

Do not put genres, moods, languages, countries, albums, artist names, sentence or arbitrary descriptive text into `comment`.

TAGS TO DELETE:
`TagsToDelete` must contain only unwanted, redundant, tracking-related, URL-related, upload-related, or excessively verbose metadata fields.

Examples:
- `synopsis`
- `description`
- `purl`
- URLs
- YouTube IDs
- tracking identifiers
- excessively long comments

Do not delete meaningful metadata merely because it is unfamiliar.
Do not delete metadata that is intentionally preserved or rewritten in `TagsToSet`.

MISSING / INAPPLICABLE VALUES:
Omit a metadata key when:
- it does not apply,
- it cannot be verified,
- or there is insufficient reliable evidence.
- Except for mood, genre and style that required minimal one value and ALL the ones corresponding in `all_possible_tags.json`. If no one match in all_possible_tags.json, do me propositions at the end.  

Never use null, empty strings, `Unknown`, `N/A`, or fabricated values.

ALL_POSSIBLE_TAGS:
For `genre`, `style`, and `mood`, use only tags present in `all_possible_tags.json`.
Do not be lazy, take the time to read the full file and ALL the tags in `all_possible_tags.json` that match, add them to the json. 
For each track, one by one, you will do the effort to go through every single value in the style/genre/mood arrays, in order, and mark yes/no if they are valid for this track. This will ensure you don't miss any.

If relevant tags are not present in `all_possible_tags.json`:
- do NOT place that tag in the JSON output;
- report it to me after the end of the json.
- Every songs have minimal a genre, stlye and mood so it's impossible to be empty or not report at the end of the json.

IMPORTANT:
Do not add combined or invented tags such as:
- `Piano Cover`
- `Nightcore Remix`

Use independent tags such as:
- `Piano`
- `Cover`
- `Nightcore`
- `Remix`

VALID JSON:
The final response must be valid JSON.
No trailing commas.
No Markdown fences but inside a ```json```.
No explanations outside the JSON except to report me missing tags and uncertain informations in a NON verbose way.


---

Complete Output Example (not exact informations, it's to show you the different way):

```json
[
  {
    "SourceFile": "E:/music/todo/【syudou】ギャンブル [7GBn6IuTQ6w].opus",
    "NewFileName": "Gambling (Nightcore) - syudou (2021).opus",
    "TagsToDelete": [
      "synopsis",
      "description",
      "purl",
      "date"
    ],
    "TagsToSet": {
      "title": ["Gambling"],
      "artist": ["syudou"],
      "year": ["2021"],
      "genre": ["J-Pop", "Pop", "Rock"],
      "style": ["Opening", "TV Series", "Anime", "OST"],
      "mood": ["Energetic", "Motivating"],
      "language": ["Japanese"],
      "country": ["Japan"],
      "decade": ["2020s"],
      "comment": ["Assassin's Creed IV: Black Flag", "Assassin's Creed", "Ubisoft"]
    }
  }
]
```