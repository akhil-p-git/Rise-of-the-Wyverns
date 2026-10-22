# AI-generated art: licensing and disclosure notes

Checked 2026-10-20. This is a research summary, not legal advice. Re-read the linked pages before release; terms change.

## Google Gemini output

Primary source: Google Terms of Service, https://policies.google.com/terms (page effective date shown: July 30, 2026).

- Ownership: "Some of our services allow you to generate original content. Google won't claim ownership over that content."
- Commercial use: the Terms say nothing explicit about commercial use of generated output, neither a grant nor a ban. Several third-party explainers read this as "likely allowed" (for example https://licenseorg.com/guide/ai-content/google-gemini-image), but that is their interpretation, not Google's wording.
- Restrictions that matter here: you may not use AI-generated content from the services "to develop machine learning models or related AI technology", and you may not mislead others "into thinking that generative AI content was created by a human".
- Generative AI Prohibited Use Policy (last modified December 17, 2024), https://policies.google.com/terms/generative-ai/use-policy: bans "Misrepresenting the provenance of generated content by claiming it was created solely by a human, in order to deceive". It does not address commercial use or require disclosure.
- The old Generative AI Additional Terms no longer apply to most users since the May 22, 2024 Terms update, https://policies.google.com/terms/generative-ai.
- Indemnity: none found in the sources read (third-party claim only, https://licenseorg.com/guide/ai-content/google-gemini-image). Google would not cover a claim that an image infringes someone else's work.
- Watermark: Google offers a SynthID check for images from its models, https://support.google.com/gemini/answer/16722517. Third parties say every generated image carries an invisible SynthID mark; not confirmed on a Google page.

Not checked: the exact Gemini app terms page for the model used, and whether the free or paid tier changes anything. Open the Gemini app's own terms once and screenshot the date.

## Copyright

The U.S. Copyright Office published Part 2 (Copyrightability) of its AI report on January 29, 2025, https://www.copyright.gov/ai/. Secondary summaries (https://copyrightalliance.org/ai-report-part-2-copyrightability/, https://ipwatchdog.com/2025/01/29/part-two-copyright-office-ai-report-says-creative-prompting-doesnt-constitute-authorship/id=185455/) say prompting alone is not enough human authorship; human selection, arrangement and modification can be protected, case by case. I could not read the report text itself.

Practical meaning: purely Gemini-generated sprites may not be protectable, so a competitor could copy them. Our cleanup (cropping, rescaling to the pixel grid, palette reduction, arrangement into scenes) is human work, but how much counts is uncertain. Commissioned or hand-made final art for the hero, logo and key art avoids the question.

## Steam

Steam's content survey requires describing AI use for content that ships with the game ("Pre-Generated": "created with the help of AI tools during development"), https://partner.steamgames.com/doc/gettingstarted/contentsurvey. Disclose the Gemini art and the FLUX-assisted work. Do not describe AI art as hand-drawn anywhere (store page, credits, marketing): that conflicts with both Steam and Google's policy above.

## Recommendation

1. Fine to prototype and playtest with these assets.
2. Before a paid release: confirm Gemini's current terms for commercial use in writing, disclose on Steam, and replace the hero, logo and key art with commissioned work.
3. Keep `ASSETS.md` current: every AI-generated file, the tool, the date, the prompt file.
