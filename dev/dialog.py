def choose(choices, display=str):
    print("choose an item:")
    for index, choice in enumerate(choices):
        print("\t", index, display(choice))
    print()
    chosen_item = None
    while chosen_item is None:
        answer = input("? ")
        try:
            chosen_index = int(answer)
        except ValueError:
            print("answer must be an integer")
            continue
        try:
            chosen_item = choices[chosen_index]
        except IndexError:
            print("index out of range")
    return chosen_item


def choose_action(choices):
    print("choose an action:")
    key = choose(list(choices.keys()))
    choices[key]()
