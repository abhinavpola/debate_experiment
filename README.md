# LLM Debate experiment

Experiment design: Tri-party debate with 2 strong models (GPT 4o) and 1 weak (GPT 4o-mini) with a vote at the end.

- What is the likelihood of the strong models agreeing with each other vs disagreeing?
- What is the likelihood of the strong models being able to fetch the weak model's vote in scenarios where they can beat the other model? (i.e exclude scenarios where all 3 agree)

Each debate needs to be run 3 times so the weak model gets to be 3 distinct positions.
Debate lengths - 5 turns, 10 turns, 20 turns

## Results

First round of this experiment was run with kind of a bad prompt. It lacks conversationality. The arguments just end up being repeated over and over with no real rebuttals.

### 5 turns
Trial 2 of debate 1:
- Democracy gets 2 votes (strong models agree with each other)

Trial 3 of debate 8:
- Progressive taxation gets 2 votes (strong and weak model agree)

Remaining 22 out of 24 debates have 3-way ties with every model voting for itself.

### 10 turns
Trial 2 of debate 1:
- Democracy gets 2 votes (strong and weak agree)

Trial 3 of debate 1:
- Democracy gets 2 votes (strong and strong agree)

Trial 1 of debate 2:
- Ranked choice voting gets 2 votes (strong and weak agree)

Trial 3 of debate 8:
- Progressive taxation gets 2 votes (strong and weak agree)