"""Practice topics and Maxwell-inspired focus skills for elocution coaching."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class FocusSkill:
    name: str
    tip: str
    cue: str


FOCUS_SKILLS: list[FocusSkill] = [
    FocusSkill(
        name="Simplicity",
        tip="Pick one clear idea. Say it in short sentences. Cut anything that does not serve that idea.",
        cue="Can a listener repeat your main point in one sentence?",
    ),
    FocusSkill(
        name="Connecting",
        tip="Speak to the listener, not at them. Use 'you', concrete examples, and shared situations.",
        cue="Did you make the audience feel included at least twice?",
    ),
    FocusSkill(
        name="Storytelling",
        tip="Use a simple arc: setup → tension → point. One short story beats three vague claims.",
        cue="Is there a moment of change or surprise in what you said?",
    ),
    FocusSkill(
        name="Conviction",
        tip="Replace hedges ('maybe', 'I think', 'sort of') with clear verbs. Own your view.",
        cue="Would a listener trust that you believe what you are saying?",
    ),
    FocusSkill(
        name="Preparation",
        tip="Open with purpose, develop two or three points, close with a memorable takeaway.",
        cue="Could someone outline your talk as open / body / close?",
    ),
]


TOPICS: list[str] = [
    # Everyday UK life
    "Should the UK keep the monarchy, or move to an elected head of state?",
    "Is the British weather something to complain about — or something that shapes character?",
    "Describe your ideal Sunday in a British city or town.",
    "Should tip culture grow in the UK the way it has in the US?",
    "What does 'a good cup of tea' mean to you, and why does it matter?",
    "Is queuing a British virtue or an outdated habit?",
    "Should more high streets ban cars and favour pedestrians?",
    "Talk about a place in the UK that surprised you.",
    "Is working from a café productive, or just fashionable?",
    "Should public transport be free in major UK cities?",
    # Work and career
    "Should remote work stay the default after the pandemic years?",
    "What makes a meeting worth attending?",
    "Describe a time you had to explain a complex idea simply at work.",
    "Is 'hustle culture' helpful or harmful?",
    "How should someone prepare for a job interview in English as a non-native speaker?",
    "Should companies ban phones in meetings?",
    "What is the difference between being busy and being effective?",
    "Talk about a skill you learned that changed how you work.",
    "Should performance reviews be abolished?",
    "How do you ask for a raise without sounding awkward?",
    # Opinions and debate
    "Is social media making us worse listeners?",
    "Should AI tools be allowed in university coursework?",
    "Is it better to be liked or to be respected?",
    "Should voting be compulsory?",
    "Are smartphones making us less articulate in person?",
    "Is failure a better teacher than success?",
    "Should schools teach public speaking as a core subject?",
    "Is multitasking a myth?",
    "Should people be paid for their data?",
    "Is optimism a skill you can practise?",
    # Storytelling prompts
    "Describe a time you changed your mind about something important.",
    "Tell the story of a conversation that went better than you expected.",
    "Describe a moment when language barriers made something funny — or difficult.",
    "Talk about the first time you felt at home in a new country.",
    "Describe a mistake you made while speaking English, and what you learned.",
    "Tell a story about asking for help when you did not want to.",
    "Describe a time you had to persuade someone who disagreed with you.",
    "Talk about a small act of kindness that stayed with you.",
    "Describe the most nervous you have ever been before speaking.",
    "Tell the story of a goal you almost gave up on.",
    # Articulation / communication practice
    "Explain something you know well to someone who knows nothing about it.",
    "Give a two-minute toast for a friend's birthday.",
    "Pitch a simple idea as if you had thirty seconds with a busy manager.",
    "Argue for and against living in a big city — then pick a side.",
    "Describe your morning routine as if it were a short radio segment.",
    "Teach someone how to make your favourite meal, step by step.",
    "Explain why someone should visit your hometown.",
    "Give advice to your past self on learning English in the UK.",
    "Describe a book or film that changed how you see people.",
    "What does 'good communication' mean to you personally?",
    # Extra variety
    "Should the working week be four days?",
    "Is small talk shallow — or a social skill worth mastering?",
    "How should we talk about mental health at work?",
    "Should children learn a second language from primary school?",
    "What is one British custom you admire, and one you find odd?",
    "Describe a time silence was more powerful than words.",
    "Should news be free for everyone?",
    "Is confidence the same as competence?",
    "Talk about a mentor who improved how you communicate.",
    "If you could give one speech to the whole country, what would it be about?",
    # Leadership and relationships
    "What makes someone a trustworthy leader?",
    "Describe how to disagree with someone respectfully.",
    "Is listening more important than speaking well?",
    "How can a manager give difficult feedback constructively?",
    "What is the best way to apologise after a misunderstanding?",
    "Should leaders admit when they do not know the answer?",
    "Describe a conversation that strengthened a relationship.",
    "How can people communicate better across different cultures?",
    "What makes advice helpful rather than intrusive?",
    "How would you encourage someone who has lost confidence?",
    # Ideas, learning, and society
    "Should adults continue studying throughout their careers?",
    "What is one technology you could happily live without?",
    "Is curiosity more valuable than intelligence?",
    "Should everyone spend some time living abroad?",
    "What makes a neighbourhood feel like a community?",
    "Does convenience always improve our lives?",
    "What is one everyday problem you would like to solve?",
    "Should museums and galleries be free to visit?",
    "What lesson should every young adult learn before leaving school?",
    "How can we become better at changing our minds?",
]


def pick_practice(
    excluded_topics: set[str] | None = None,
) -> tuple[str, FocusSkill]:
    """Return a random unused topic and focus skill for one practice round."""
    excluded_topics = excluded_topics or set()
    available_topics = [topic for topic in TOPICS if topic not in excluded_topics]
    if not available_topics:
        available_topics = TOPICS
    return random.choice(available_topics), random.choice(FOCUS_SKILLS)
