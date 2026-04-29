# Objective
Analysis of the the copilot chat debug logs to understand the usage patterns and identify areas for improvement, capturing the statistics and insights.
Secondary objective is to create a report with the findings and recommendations.

# Instructions
- Use the copilot chat debug logs to understand the structure and content of the logs, how to parse them and extract the relevant information.
- build a json schema to represent the data structure
- design(write a specification first) and build a parser to extract the relevant information from the logs, capture the statistics and insights e.g. total messages, total tokens. other usage patterns etc.
- design(write a specification first) and build a report generator to create a report with the findings and recommendations tailored to the user's needs(the person who requested the analysis); the report should be in markdown format and should include the statistics and insights - also in the form of charts and graphs; we should choose the most appropriate chart type for each statistic and the data available; the language and the stack for this tool should assume minimal dependencies and be easy to maintain and extend.; follow best practices for code organization, documentation, and testing.
- the tool should assume some defaults(e.g plan: business), but allow the user to override them
- the analysis should "tell the story" about the session in scope: what was the topic, the duration, usage patterns over time and correlated with the task performed at that moment in time, what model was used at that point, identify the hotspots i.e. tasks where copilot had to run significantly more turns or tokens than usual.

# Additional Notes
- GitHub Copilot udage based billing for Enterprise and Business plans: `https://docs.github.com/en/copilot/concepts/billing/usage-based-billing-for-organizations-and-enterprises`
- Models and pricing for copilot: `https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing`

Make sure you run a deep research on the topic first, then design then you challenge the design with edge cases and unexpected scenarios and you iterate until you have a robust design. 
Once the design is solid, write product/functional as well as technical specifications. 
Once done implement the solution using the most appropriate technology stack and best practices for code organization, documentation, and testing. 
Consider TDD and clean architecture(hexagonal) and the best practices for library and cli development to make it reusable and maintainable.
Use git for version control and keep the commit history clean and meaningful(conventional commits). Commit often and with clear messages - only the clean and validated code should be committed.
