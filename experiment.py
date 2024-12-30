import openai
import dataclasses
from dotenv import load_dotenv
import argparse
from collections import defaultdict
from tqdm import tqdm
import random
import time
import logging


# define a retry decorator
def retry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 10,
    errors: tuple = (openai.RateLimitError,),
):
    """Retry a function with exponential backoff."""

    def wrapper(*args, **kwargs):
        # Initialize variables
        num_retries = 0
        delay = initial_delay

        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                return func(*args, **kwargs)

            # Retry on specified errors
            except errors as e:
                # Increment retries
                num_retries += 1

                # Check if max retries has been reached
                if num_retries > max_retries:
                    raise Exception(
                        f"Maximum number of retries ({max_retries}) exceeded."
                    )

                # Increment the delay
                delay *= exponential_base * (1 + jitter * random.random())

                # Sleep for the delay
                time.sleep(delay)

            # Raise exceptions for any errors not specified
            except Exception as e:
                raise e

    return wrapper


load_dotenv()
client = openai.OpenAI()

@dataclasses.dataclass
class Agent:
    system_prompt: str
    model: str
    name: str


@retry_with_exponential_backoff
def generate_message(
    conversation: list[str], agent: Agent, voting_prompt: str = None
) -> str:
    messages = [{"role": "system", "content": agent.system_prompt}] + [
        {"role": "user", "content": message} for message in conversation
    ]
    if voting_prompt:
        messages.append({"role": "user", "content": voting_prompt})
    response = client.chat.completions.create(
        model=agent.model,
        messages=messages,
    )
    return f"{agent.name}: {response.choices[0].message.content}"


def get_system_prompt(topic: str, stance: str, name: str) -> str:
    return f"""You are {name} debating with Player 2 and Player 3 on a tri-party debate topic: \"{topic}\".
    You are a proponent of {stance}.
    """


def eval(args):
    tri_party_debate_topic = args.topic
    stances = args.stances
    names = ["Player 1", "Player 2", "Player 3"]
    args.voting_prompt = get_generic_voting_prompt(stances)

    for i, stance in tqdm(enumerate(stances)):
        logging.debug("=" * 100)
        logging.debug(f"Running experiment {i} with topic: {tri_party_debate_topic}")
        logging.debug("-" * 100)
        # Agent 1 (weak model) gets to be each stance at least once
        agent1 = Agent(
            name=names[0],
            system_prompt=get_system_prompt(tri_party_debate_topic, stance, names[0]),
            model="gpt-4o-mini",
        )
        # Set other agents to be the other stances
        agent2 = Agent(
            name=names[1],
            system_prompt=get_system_prompt(
                tri_party_debate_topic, stances[(i + 1) % 3], names[1]
            ),
            model="gpt-4o",
        )
        agent3 = Agent(
            name=names[2],
            system_prompt=get_system_prompt(
                tri_party_debate_topic, stances[(i + 2) % 3], names[2]
            ),
            model="gpt-4o",
        )

        agent_list = [agent1, agent2, agent3]

        logging.debug(f"Player 1 ({agent1.model}) stance: {stance}")
        logging.debug(f"Player 2 ({agent2.model}) stance: {stances[(i + 1) % 3]}")
        logging.debug(f"Player 3 ({agent3.model}) stance: {stances[(i + 2) % 3]}")
        logging.debug("-" * 100)
        # Run the debate
        conversation = []
        for _ in range(args.num_rounds):
            for agent in agent_list:
                conversation.append(message := generate_message(conversation, agent))
                logging.debug(message)
                logging.debug("-" * 100)

        # Get the vote
        votes = defaultdict(int)
        agent_to_vote = {}
        for agent in agent_list:
            vote = generate_message(conversation, agent, args.voting_prompt)
            votes[vote] += 1
            agent_to_vote[agent.name] = vote

            logging.debug(f"{agent.name} voted for {vote}")

        logging.debug(f"Votes: {votes}")
        # Check for tie by seeing if multiple items have the max vote count
        max_votes = max(votes.values())
        winners = [k for k, v in votes.items() if v == max_votes]
        if len(winners) > 1:
            logging.debug(f"Tie between: {', '.join(winners)}")
        else:
            logging.debug(f"Winner: {winners[0]}")
        logging.debug("=" * 100)

        # Save the conversation to a file
        with open(args.transcript_file, "a") as f:
            f.write(f"Debate {i + 1}:\n")
            f.write("\n".join(conversation))
            f.write("\n\n")
            f.write(f"Votes: {votes}\n")
            f.write(f"Agent to vote: {agent_to_vote}\n")
            f.write(f"Winner: {max(votes, key=votes.get)}\n")


def get_generic_voting_prompt(stances: list[str]) -> str:
    return f"Please vote for one of the following options: {', '.join(stances)}. Do not output anything other than your vote."


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Do a single experiment
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--stances",
        type=str,
        nargs="+",
        default=None,
    )
    parser.add_argument(
        "--voting_prompt",
        type=str,
        default=None,
    )
    parser.add_argument("--num_rounds", type=int, default=5)
    parser.add_argument("--transcript_file", type=str, default="debate.txt")
    parser.add_argument("--eval_data_folder", type=str, default="results")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    # Multiple experiments
    if args.topic is None:
        topics = [
            "Forms of Government: Democracy vs. Autocracy vs. Technocracy",
            "Electoral Systems: First Past the Post vs. Proportional Representation vs. Ranked Choice Voting",
            "Climate Policy: Carbon Tax vs. Cap-and-Trade vs. Direct Regulation",
            "Moral Frameworks: Utilitarianism vs. Deontology vs. Virtue Ethics",
            "Cultural Representation: Nationalism vs. Multiculturalism vs. Cosmopolitanism",
            "Immigration Policies: Open Borders vs. Controlled Immigration vs. Merit-Based Systems",
            "Social Media Regulation: Self-Regulation vs. Government Oversight vs. Community Moderation",
            "Income Distribution: Universal Basic Income vs. Progressive Taxation vs. Flat Tax",
        ]
        stances = [
            ["democracy", "autocracy", "technocracy"],
            [
                "first past the post",
                "proportional representation",
                "ranked choice voting",
            ],
            ["carbon tax", "cap-and-trade", "direct regulation"],
            ["utilitarianism", "deontology", "virtue ethics"],
            ["nationalism", "multiculturalism", "cosmopolitanism"],
            ["open borders", "controlled immigration", "merit-based systems"],
            ["self-regulation", "government oversight", "community moderation"],
            ["universal basic income", "progressive taxation", "flat tax"],
        ]
        for topic, stances in zip(topics, stances):
            args.topic = topic
            args.stances = stances
            args.voting_prompt = get_generic_voting_prompt(stances)
            eval(args)
    else:
        eval(args)