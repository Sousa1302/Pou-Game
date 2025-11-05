from game import Game

if __name__ == "__main__":
    try:
        Game().run()
    except Exception as e:
        print("Fatal error:", e)