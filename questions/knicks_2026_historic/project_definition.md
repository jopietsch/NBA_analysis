# a plan to get this projet jump started

- create  a plan to deep dive into our primary question "did the 2025–26 New York Knicks have a historic playoff run?" People have said that it is because they had such a good record of 16-3. However, another explanation could be that the easter conference was much weaker than the west conference and so they had an exaggerated record. There might also be other explanations for why it's not as historically significant as people naively seem.
- We want to get data from nba_api that will help us answer all our questions. 
- as part of this examination, we want to know if the eastern conference was weaker than the western conference and how much that contributed to the schedule
- what graphs and statistical analysis will allow us to answer these questions? start with the data from nba_api.
- make sure that all analysis we do uses python do any calculation, and not Claude
- run the analysis and get the data into @RESULTS.md and create graphs in generated/*
- create @knicks_2026_historic_findings.md that references the data in RESULTS.md and all the graphs we just produced 
- run set of prompts to make sure that conclusions are accurate and useful
	- go through the @knicks_2026_historic_findings.md and make sure that each section is supported by data in RESULTS.md and all the graphs we just produced. does each section make sense and does it contribute to the overall story? 
	- Are the sections in the right order
	- we want some of the main concusions in the intro section so that our readers don't get bored before they get all the way to the end
	- is the overall argument coherent, is it clear, does it have statistical terms that our readers won't understand or appreciate?
	- Act as a reviewer of a publication that takes itself seriously. You will lose your job and reputation if you are wrong about facts, or if the conlusions are not justified. review @knicks_2026_historic_findings.md and make sure it's all correct based on data from @RESULTS.md and all the graphs in @generated/*.png
- after we exhaust the data from nba_api, is there other data we could get that that would help us answer these questions?
	- if so , create the python necessary to do that and do the analysis
	- update @knicks_2026_historic_findings.md based on this analsis and run through the same prompts as described above