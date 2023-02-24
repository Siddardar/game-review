from details import USERNAME
import time
import requests
import chess
import chess.pgn
from stockfish import Stockfish
import pgn
import datetime
import json
from colorama import Fore, Back, Style
import PySimpleGUI as sg
from fentoboardimage import fenToImage, loadPiecesFolder


class ChessAnalysis:
    def __init__(self):
        self.time = datetime.datetime.now()

        settings = {

            "Debug Log File": "",
            "Contempt": 0,
            "Min Split Depth": 0,
            "Threads": 4,
            "Ponder": "false",
            "Hash": 2048,
            "MultiPV": 1,
            "Skill Level": 20,
            "Move Overhead": 10,
            "Minimum Thinking Time": 20,
            "Slow Mover": 100,
            "UCI_Chess960": "false",
            "UCI_LimitStrength": "false",
            "UCI_Elo": 3500

        }

        self.engine = Stockfish(
            path="stockfish_15.1_win_x64_avx2\stockfish-windows-2022-x86-64-avx2.exe", depth=18, parameters=settings)

        self.board = chess.Board()

    def info(self):

        print(f"Getting last game played by {USERNAME}")
        username = USERNAME
        YYYY = str(self.time.year)
        MM = f'{self.time.month:02d}'

        api = f"https://api.chess.com/pub/player/{username}/games/{YYYY}/{MM}"

        last_game = requests.get(api).json()['games'][-1]

        with open("chess_games.pgn", "w") as f:
            f.write(last_game['pgn'])

        pgn = open("chess_games.pgn")
        game = chess.pgn.read_game(pgn)

        players = f"{game.headers['White']} vs {game.headers['Black']}"

        reviews = ["Starting position"]
        evals = ["0.00"]
        fens = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"]
        best_moves = ["None"]

        m = 0

        print("Analysing game")
        for move in game.mainline_moves():

            best_move = self.engine.get_top_moves(1)[0]

            # Not a guarenteed Checkmate
            if best_move["Mate"] == None:

                if str(move) == str(best_move["Move"]):
                    review = "Best Move ✅"
                    self.engine.make_moves_from_current_position([move])
                    best = True

                else:
                    best = False
                    self.engine.make_moves_from_current_position([move])

                    after_eval = self.engine.get_evaluation()['value']
                    best_eval = int(best_move["Centipawn"])
                    diff = best_eval - after_eval

                    if best_eval * after_eval > 0:
                        if diff < 50:
                            review = "Good Move ✔ "
                        elif 50 < diff < 100:
                            review = "Inaccuracy ❓"
                        elif 100 < diff < 250:
                            review = "Mistake ❌"
                        else:
                            review = "Blunder ❎"

                    else:
                        if diff < 100:
                            review = "Inaccuracy ❓"
                        elif 100 < diff < 250:
                            review = "Mistake ❌"
                        else:
                            review = "Blunder ❎"

            # It is a guarenteed Mate
            else:
                if str(move) == str(best_move["Move"]):
                    review = "Best Move ✅"
                    self.engine.make_moves_from_current_position([move])
                    best = True

                else:
                    best = False
                    self.engine.make_moves_from_current_position([move])
                    after_eval = self.engine.get_evaluation()

                    if after_eval['type'] != "mate":
                        review = "Missed Mate ❌"

                    else:
                        best_move_mate = best_move["Mate"]
                        after_eval_mate = after_eval["value"]

                        if best_move_mate * after_eval_mate > 0:
                            review = "Good Move ✔"
                        else:
                            review = "Blunder ❎"

            evaluation = self.engine.get_evaluation()["value"]
            evals.append(str(int(evaluation)/100))
            fen = self.engine.get_fen_position()
            fens.append(fen)

            reviews.append(review)

            if best == False:
                best_moves.append(f"Best Move: {best_move['Move']}")
            else:
                best_moves.append("")
        print("Analysis done")

        fens.append("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        evals.append("0.00")
        reviews.append("Game Over")

        best_moves.append(f"{game.headers['Termination']}")

        def board(fen_no):
            boardImage = fenToImage(
                fen=fen_no,
                squarelength=100,
                pieceSet=loadPiecesFolder("./pieces"),
                darkColor="#D18B47",
                lightColor="#FFCE9E"
            )

            img = boardImage.save("board.png", 'PNG')

        board(fens[m])
        sg.theme('DarkAmber')
        layout = [[sg.Text(players, font=("Calibre", 14))],
                  [sg.Text(f"{evals[m]}", key="-EVAL-", font=("", 12)),
                   sg.Push(),
                   sg.Button('End Analysis', font=("Calibre", 14)),],
                  [sg.Image('./board.png', key="-BOARD-")],
                  [sg.Text("")],
                  [sg.Text(f"{reviews[m]}", key="-REVIEW-",
                           font=("Calibre", 14))],
                  [sg.Text(f"Best Move: {best_moves[m]}",
                           key="-BEST-", font=("Calibre", 14))],
                  [sg.Text("")],
                  [sg.Button("Back", font=("Calibre", 14)), sg.Push(), sg.Button('Next', font=("Calibre", 14))]]

        window = sg.Window('Game Review', layout)

        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED or event == 'End Analysis':
                break
            if event == "Next":
                m += 1
                if m == len(fens):
                    break

            if event == "Back":
                m -= 1

            img = board(fens[m])
            window["-EVAL-"].update(f"{evals[m]}")
            window["-BOARD-"].update(filename="./board.png")
            window["-REVIEW-"].update(f"{reviews[m]}")
            window["-BEST-"].update(f"{best_moves[m]}")

        window.close()


if __name__ == "__main__":
    analysis = ChessAnalysis()
    analysis.info()
