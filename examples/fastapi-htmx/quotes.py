"""Build a random quote fragment for the index page."""

from random import choice

from htmlkit import Fragment, p

QUOTES = (
    ("He who is brave is free.", "Seneca"),
    ("Leave no stone unturned.", "Euripides"),
    ("Whatever you are, be a good one.", "Abraham Lincoln"),
    ("Why fit in when you were born to stand out.", "Dr. Seuss"),
    ("If you’re going through hell, keep going.", "Winston Churchill"),
    ("Once you choose hope, anything’s possible.", "Christopher Reeve"),
    ("That which does not kill us makes us stronger.", "Friedrich Nietzsche"),
    ("My life is my message.", "Mahatma Gandhi"),
    ("Be yourself; everyone else is already taken.", "Oscar Wilde"),
    ("So many books, so little time.", "Frank Zappa"),
)


def random_quote() -> Fragment:
    """Create an HTML fragment containing one randomly selected quote."""
    quote = choice(QUOTES)
    text = quote[0]
    author = quote[1]
    fragment = Fragment(p(text), p(f"~ {author}"))
    return fragment
