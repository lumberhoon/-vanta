from core.brain import process_input

def main():
    print("> VANTA 0.1 online")
    while True:
        user_input = input(">>> ").strip()

        #temprary hard exit
        if user_input.lower() in {"exit", "quit"}:
            print("Shutting down...")
            break

        response = process_input(user_input)
        print(response)


if __name__ ==  "__main__":

    main()