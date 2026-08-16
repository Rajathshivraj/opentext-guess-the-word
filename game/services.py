"""
Core game logic services.
"""


def evaluate_guess(target: str, guess: str) -> list:
    """
    Evaluate a guess against the target word using a two-pass Wordle algorithm.

    Returns a list of 5 strings, each one of:
      - 'green'  : correct letter, correct position
      - 'orange' : correct letter, wrong position
      - 'grey'   : letter not in target

    Correctly handles duplicate letters.

    Args:
        target: 5-letter uppercase target word
        guess:  5-letter uppercase guessed word

    Returns:
        List of 5 colour strings.
    """
    target = target.upper()
    guess = guess.upper()

    result = ['grey'] * 5
    target_remaining = list(target)

    # First pass: mark greens
    for i in range(5):
        if guess[i] == target[i]:
            result[i] = 'green'
            target_remaining[i] = None   # consumed

    # Second pass: mark oranges
    for i in range(5):
        if result[i] == 'green':
            continue
        if guess[i] in target_remaining:
            result[i] = 'orange'
            # consume the first matching character in target_remaining
            target_remaining[target_remaining.index(guess[i])] = None

    return result
